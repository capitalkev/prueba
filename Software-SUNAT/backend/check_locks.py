"""
Verificar bloqueos activos en la base de datos
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

# Verificar procesos activos
print("[INFO] Verificando procesos activos...\n")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            pid,
            usename,
            application_name,
            state,
            query_start,
            state_change,
            LEFT(query, 100) as query
        FROM pg_stat_activity
        WHERE datname = :dbname
          AND pid <> pg_backend_pid()
        ORDER BY query_start DESC
    """), {"dbname": DB_NAME})

    rows = result.fetchall()
    if rows:
        print(f"Procesos activos: {len(rows)}\n")
        for row in rows:
            print(f"PID: {row[0]}")
            print(f"  Usuario: {row[1]}")
            print(f"  App: {row[2]}")
            print(f"  Estado: {row[3]}")
            print(f"  Inicio: {row[4]}")
            print(f"  Query: {row[6]}")
            print()
    else:
        print("No hay otros procesos activos\n")

# Verificar bloqueos
print("[INFO] Verificando bloqueos...\n")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT
            l.locktype,
            l.relation::regclass as relation,
            l.mode,
            l.granted,
            a.pid,
            a.usename,
            a.application_name,
            LEFT(a.query, 100) as query
        FROM pg_locks l
        JOIN pg_stat_activity a ON l.pid = a.pid
        WHERE l.relation IS NOT NULL
          AND a.datname = :dbname
        ORDER BY l.granted, a.pid
    """), {"dbname": DB_NAME})

    rows = result.fetchall()
    if rows:
        print(f"Bloqueos encontrados: {len(rows)}\n")
        for row in rows:
            print(f"Tipo: {row[0]}")
            print(f"  Relación: {row[1]}")
            print(f"  Modo: {row[2]}")
            print(f"  Granted: {row[3]}")
            print(f"  PID: {row[4]}")
            print(f"  Usuario: {row[5]}")
            print(f"  Query: {row[7]}")
            print()
    else:
        print("No hay bloqueos activos\n")

engine.dispose()
print("[OK] Verificación completada")
