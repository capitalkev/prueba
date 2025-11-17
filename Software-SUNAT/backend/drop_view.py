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
    print("[INFO] Eliminando vista materializada ventas_backend...")
    try:
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS ventas_backend CASCADE"))
        print("[OK] Vista eliminada\n")
    except Exception as e:
        print(f"[ERROR] {e}\n")

engine.dispose()
print("[OK] Listo")
