"""
Eliminar vista materializada antes de recrearla
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
        pool_pre_ping=True,
        isolation_level="AUTOCOMMIT"
    )
    print("[INFO] Conectado\n")

except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

with engine.connect() as conn:
    # Verificar bloqueos primero
    print("[INFO] Verificando bloqueos en ventas_backend...")
    try:
        result = conn.execute(text("""
            SELECT
                l.pid,
                a.usename,
                a.application_name,
                a.state,
                LEFT(a.query, 100) as query
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE l.relation = 'ventas_backend'::regclass
        """))
        locks = result.fetchall()
        if locks:
            print(f"[WARN] Hay {len(locks)} proceso(s) bloqueando la vista:")
            for lock in locks:
                print(f"  PID {lock[0]}: {lock[1]} - {lock[2]} - {lock[3]}")
                print(f"    Query: {lock[4]}")
            print()
    except Exception as e:
        # La vista podría no existir, continuar
        print(f"[INFO] No se pudo verificar bloqueos (la vista podría no existir): {e}\n")

    print("[INFO] Eliminando vista materializada ventas_backend...")
    try:
        # Intentar con timeout de 10 segundos
        conn.execute(text("SET statement_timeout = '10s'"))
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS ventas_backend CASCADE"))
        print("[OK] Vista eliminada\n")
    except Exception as e:
        print(f"[ERROR] {e}")
        print("\n[SUGERENCIA] Si el error es por timeout o bloqueos:")
        print("  1. Ejecuta 'python check_locks.py' para ver qué está bloqueando")
        print("  2. Detén las aplicaciones que estén consultando la vista")
        print("  3. O usa 'python kill_blocking_processes.py' (crear si es necesario)\n")

engine.dispose()
print("[OK] Listo")
