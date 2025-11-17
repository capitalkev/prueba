"""
Terminar transacciones idle que están bloqueando ventas_backend
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

print("[INFO] Conectando...")

try:
    from google.cloud.sql.connector import Connector

    connector = Connector()

    def getconn():
        conn = connector.connect(
            CLOUD_SQL_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True
    )
    print("[INFO] Conectado\n")

except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

with engine.connect() as conn:
    # Buscar transacciones idle in transaction que tienen locks en ventas_backend
    print("[INFO] Buscando transacciones 'idle in transaction' con locks...\n")
    result = conn.execute(text("""
        SELECT DISTINCT
            a.pid,
            a.usename,
            a.application_name,
            a.state,
            a.state_change,
            LEFT(a.query, 80) as query
        FROM pg_stat_activity a
        JOIN pg_locks l ON a.pid = l.pid
        WHERE a.state = 'idle in transaction'
          AND a.pid <> pg_backend_pid()
          AND l.relation = 'ventas_backend'::regclass
        ORDER BY a.state_change
    """))

    idle_processes = result.fetchall()

    if not idle_processes:
        print("[INFO] No hay transacciones 'idle in transaction' bloqueando ventas_backend\n")
    else:
        print(f"[WARN] Encontradas {len(idle_processes)} transacciones idle:\n")
        for proc in idle_processes:
            print(f"PID {proc[0]}: {proc[1]} - {proc[2]}")
            print(f"  Estado: {proc[3]} desde {proc[4]}")
            print(f"  Query: {proc[5]}")
            print()

        print("[INFO] Terminando transacciones idle...")
        terminated = 0
        for proc in idle_processes:
            pid = proc[0]
            try:
                conn.execute(text(f"SELECT pg_terminate_backend({pid})"))
                print(f"  [OK] PID {pid} terminado")
                terminated += 1
            except Exception as e:
                print(f"  [ERROR] No se pudo terminar PID {pid}: {e}")

        print(f"\n[OK] {terminated}/{len(idle_processes)} transacciones terminadas\n")

    # Buscar y terminar los DROP colgados
    print("[INFO] Buscando procesos DROP colgados...\n")
    result = conn.execute(text("""
        SELECT
            pid,
            query_start,
            state,
            LEFT(query, 80) as query
        FROM pg_stat_activity
        WHERE query ILIKE '%DROP MATERIALIZED VIEW%ventas_backend%'
          AND pid <> pg_backend_pid()
        ORDER BY query_start
    """))

    drop_processes = result.fetchall()

    if not drop_processes:
        print("[INFO] No hay procesos DROP colgados\n")
    else:
        print(f"[WARN] Encontrados {drop_processes} procesos DROP:\n")
        for proc in drop_processes:
            print(f"PID {proc[0]}: iniciado {proc[1]}")
            print(f"  Estado: {proc[2]}")
            print(f"  Query: {proc[3]}")
            print()

        print("[INFO] Terminando procesos DROP colgados...")
        for proc in drop_processes:
            pid = proc[0]
            try:
                conn.execute(text(f"SELECT pg_terminate_backend({pid})"))
                print(f"  [OK] PID {pid} terminado")
            except Exception as e:
                print(f"  [ERROR] No se pudo terminar PID {pid}: {e}")

        print()

engine.dispose()
print("[OK] Limpieza completada")
print("\n[SIGUIENTE PASO] Ahora ejecuta: python drop_view.py")
