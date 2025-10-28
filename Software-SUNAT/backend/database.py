from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from google.cloud.sql.connector import Connector

load_dotenv() 

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME") 

if not CLOUD_SQL_CONNECTION_NAME:
    raise ValueError("ERROR: La variable de entorno CLOUD_SQL_CONNECTION_NAME no está definida.")
if not DB_USER:
    raise ValueError("ERROR: La variable de entorno DB_USER no está definida.")
if not DB_PASSWORD:
    raise ValueError("ERROR: La variable de entorno DB_PASSWORD no está definida.")
if not DB_NAME:
    raise ValueError("ERROR: La variable de entorno DB_NAME no está definida.")

print(f"[INFO] Configurando conexión para: {CLOUD_SQL_CONNECTION_NAME}")

connector = Connector()

def getconn():
    """Función helper para el conector"""
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
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("[INFO] Conexión a la base de datos verificada con éxito.")
except Exception as e:
    print(f"[ERROR] No se pudo verificar la conexión a la base de datos: {e}")

def get_db():
    """
    Dependency para obtener sesión de base de datos (para FastAPI).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()