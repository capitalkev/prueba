# -*- coding: utf-8 -*-
"""Script para crear todas las tablas en la base de datos PostgreSQL."""

import sys
import io
from database import engine
from models import Base

# Fix para Windows: usar UTF-8 en stdout
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_tables():
    """Crea todas las tablas en la base de datos"""
    try:
        print("\nCreando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Tablas creadas exitosamente en la base de datos.")
        print("\nTablas creadas:")
        print("  - enrolados")
        print("  - periodos_fallidos")
        print("  - compras_sire (80 columnas)")
        print("  - ventas_sire (40 columnas)")
        print("\n[OK] Proceso completado.\n")
    except Exception as e:
        print(f"[ERROR] Error al crear las tablas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()
