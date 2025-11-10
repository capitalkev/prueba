"""
Script para actualizar estado1 de registros existentes en lotes
Ejecutar DESPUÉS de agregar las columnas con 001_add_estado1_estado2_optimized.sql

Este script es OPCIONAL. Solo necesario si quieres llenar los valores existentes.
La aplicación funciona perfectamente con NULL mostrando "Sin gestión".
"""

import os
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()

# Construir URL de base de datos
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'crm_sunat')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def update_estados_in_batches(batch_size=1000):
    """
    Actualiza estado1 a 'Sin gestión' para todos los registros con estado1 NULL
    Lo hace en lotes para evitar timeouts
    """
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Contar registros con estado1 NULL
        count_query = text("SELECT COUNT(*) FROM ventas_sire WHERE estado1 IS NULL")
        total_null = conn.execute(count_query).scalar()

        print(f"📊 Total de registros con estado1 NULL: {total_null:,}")

        if total_null == 0:
            print("✅ No hay registros por actualizar")
            return

        # Calcular número de lotes
        num_batches = (total_null + batch_size - 1) // batch_size
        print(f"🔄 Procesando en {num_batches} lotes de {batch_size} registros...")

        # Actualizar en lotes
        updated_total = 0
        for i in range(num_batches):
            start_time = time.time()

            # Actualizar un lote
            update_query = text("""
                UPDATE ventas_sire
                SET estado1 = 'Sin gestión'
                WHERE id IN (
                    SELECT id FROM ventas_sire
                    WHERE estado1 IS NULL
                    LIMIT :batch_size
                )
            """)

            result = conn.execute(update_query, {"batch_size": batch_size})
            conn.commit()

            updated_count = result.rowcount
            updated_total += updated_count

            elapsed = time.time() - start_time
            progress = (updated_total / total_null) * 100

            print(f"  Lote {i+1}/{num_batches}: {updated_count:,} registros actualizados "
                  f"({progress:.1f}% completado) - {elapsed:.2f}s")

            # Pausa breve entre lotes para no sobrecargar la BD
            if i < num_batches - 1:
                time.sleep(0.1)

        print(f"\n✅ Actualización completada: {updated_total:,} registros actualizados")

        # Verificar resultado
        verify_query = text("SELECT COUNT(*) FROM ventas_sire WHERE estado1 IS NULL")
        remaining_null = conn.execute(verify_query).scalar()
        print(f"📊 Registros restantes con NULL: {remaining_null:,}")

if __name__ == "__main__":
    print("=" * 60)
    print("Script de actualización de estado1 en lotes")
    print("=" * 60)
    print()

    # Confirmar ejecución
    response = input("¿Deseas actualizar los registros existentes? (s/n): ").strip().lower()

    if response == 's':
        try:
            update_estados_in_batches(batch_size=1000)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    else:
        print("❌ Operación cancelada")
        print("NOTA: La aplicación funciona perfectamente sin actualizar los registros existentes")
        print("      Los NULL se muestran como 'Sin gestión' automáticamente")
