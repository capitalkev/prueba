"""
Configuración de conexión a PostgreSQL.
Soporta tanto conexión local como Cloud SQL usando Cloud SQL Python Connector.
"""

from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Variables de configuración
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "CRM-SUNAT")

# Cloud SQL connection name (formato: project:region:instance)
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
if CLOUD_SQL_CONNECTION_NAME:
    CLOUD_SQL_CONNECTION_NAME = CLOUD_SQL_CONNECTION_NAME.strip()

# Para conexión local
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def create_engine_cloud_sql():
    """
    Crea engine para Cloud SQL usando Cloud SQL Python Connector.

    Returns:
        Engine de SQLAlchemy
    """
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
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    logger.info(f"✅ Usando Cloud SQL Connector: {CLOUD_SQL_CONNECTION_NAME}")
    return engine


def create_engine_local():
    """
    Crea engine para conexión local TCP.

    Returns:
        Engine de SQLAlchemy
    """
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    engine = create_engine(
        url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    logger.info(f"✅ Usando conexión TCP: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    return engine


try:
    # Detectar si estamos en Cloud Run
    if CLOUD_SQL_CONNECTION_NAME and os.getenv("K_SERVICE"):
        # Estamos en Cloud Run - usar Cloud SQL Connector
        
        logger.info("Detectado entorno Cloud Run")
        engine = create_engine_cloud_sql()
    else:
        # Estamos en local - usar TCP
        logger.info("Detectado entorno local")
        engine = create_engine_local()

    # Crear sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Verificar conexión
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))  # <--- ¡AQUÍ ESTÁ LA CORRECCIÓN!
        result.fetchone()

    logger.info("✅ Conexión a la base de datos establecida con éxito.")
    print("✅ Conexión a la base de datos establecida con éxito.")

except Exception as e:
    logger.error(f"❌ No se pudo conectar a la base de datos: {e}")
    print(f"❌ No se pudo conectar a la base de datos: {e}")
    engine = None
    SessionLocal = None


def get_db():
    """
    Dependency para obtener sesión de base de datos (para FastAPI).

    Yields:
        Session: Sesión de SQLAlchemy
    """
    if SessionLocal is None:
        raise Exception("Base de datos no inicializada")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        