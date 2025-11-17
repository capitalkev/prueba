"""
Script para crear el índice UNIQUE en la vista materializada ventas_backend
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Credenciales directas
DB_USER = "postgres"
DB_PASSWORD = "Crm-sunat1"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "CRM-SUNAT"

# Crear conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

print("Conectando a la base de datos...")

try:
    with engine.connect() as conn:
        # Crear índice UNIQUE
        print("Creando indice UNIQUE en ventas_backend...")
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ventas_backend_id_idx ON ventas_backend (id);"))
        conn.commit()
        print("EXITO: Indice creado exitosamente!")

        # Verificar que el índice existe
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'ventas_backend' AND indexname = 'ventas_backend_id_idx';
        """))

        row = result.fetchone()
        if row:
            print(f"VERIFICADO: {row[0]}")
            print(f"Definicion: {row[1]}")
        else:
            print("ADVERTENCIA: No se pudo verificar el indice")

except Exception as e:
    print(f"ERROR: {e}")
finally:
    engine.dispose()
    print("Conexion cerrada")
