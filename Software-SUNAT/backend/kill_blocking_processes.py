"""
Terminar procesos que están bloqueando ventas_backend
ADVERTENCIA: Usa este script con cuidado, terminará conexiones activas
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
    # Buscar procesos bloqueantes
    print("[INFO] Buscando procesos que bloquean ventas_backend...\n")
    try:
        result = conn.execute(text("""
            SELECT
                l.pid,
                a.usename,
                a.application_name,
                a.state,
                a.query_start,
                LEFT(a.query, 100) as query
            FROM pg_locks l
            JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE l.relation = 'ventas_backend'::regclass
              AND a.pid <> pg_backend_pid()
        """))

        processes = result.fetchall()

        if not processes:
            print("[INFO] No hay procesos bloqueando ventas_backend")
            engine.dispose()
            sys.exit(0)

        print(f"[WARN] Encontrados {len(processes)} proceso(s) bloqueantes:\n")
        pids = []
        for proc in processes:
            pid = proc[0]
            pids.append(pid)
            print(f"PID: {pid}")
            print(f"  Usuario: {proc[1]}")
            print(f"  App: {proc[2]}")
            print(f"  Estado: {proc[3]}")
            print(f"  Inicio: {proc[4]}")
            print(f"  Query: {proc[5]}")
            print()

        # Confirmar antes de terminar
        print("[ADVERTENCIA] Esto terminará las conexiones activas listadas arriba.")
        respuesta = input("¿Deseas continuar? (escribe 'SI' para confirmar): ")

        if respuesta.strip().upper() != 'SI':
            print("\n[INFO] Operación cancelada")
            engine.dispose()
            sys.exit(0)

        # Terminar procesos
        print("\n[INFO] Terminando procesos...")
        for pid in pids:
            try:
                conn.execute(text(f"SELECT pg_terminate_backend({pid})"))
                print(f"  [OK] Proceso {pid} terminado")
            except Exception as e:
                print(f"  [ERROR] No se pudo terminar proceso {pid}: {e}")

        print("\n[OK] Procesos terminados")
        print("[INFO] Ahora puedes ejecutar 'python drop_view.py' nuevamente")

    except Exception as e:
        print(f"[ERROR] {e}")

engine.dispose()
