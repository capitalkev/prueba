"""
Script para ejecutar fix_column_names.sql y corregir nombres de columnas
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

print("=" * 80)
print("CORRIGIENDO NOMBRES DE COLUMNAS EN VISTA MATERIALIZADA")
print("=" * 80)
print("Cambiando:")
print("  - monto_nota_credito → nota_credito_monto")
print("  - total_neto → monto_neto")
print("  - Agregando: monto_original")
print("=" * 80)
print()

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
    print("[INFO] Conectado a Cloud SQL\n")

except Exception as e:
    print(f"[ERROR] No se pudo conectar: {e}")
    sys.exit(1)

# Leer el SQL
sql_file = "fix_column_names.sql"
print(f"[INFO] Leyendo {sql_file}...")
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Ejecutar
with engine.connect() as conn:
    print("[INFO] Ejecutando script SQL...\n")
    start = datetime.now()

    try:
        # Ejecutar línea por línea para mejor control
        statements = sql_script.split(';')

        for i, stmt in enumerate(statements, 1):
            stmt = stmt.strip()
            if not stmt or stmt.startswith('--'):
                continue

            print(f"[{i}/{len(statements)}] Ejecutando statement...")

            if "DROP MATERIALIZED VIEW" in stmt:
                print("  → Eliminando vista antigua...")
            elif "CREATE MATERIALIZED VIEW" in stmt:
                print("  → Creando vista con nombres correctos (esto puede tomar 2-3 min)...")
            elif "CREATE UNIQUE INDEX" in stmt or "CREATE INDEX" in stmt:
                index_name = stmt.split("INDEX")[1].split("ON")[0].strip()
                print(f"  → Creando índice {index_name}...")
            elif "CREATE OR REPLACE FUNCTION" in stmt:
                print("  → Creando función refresh_ventas_backend()...")
            elif "ANALYZE" in stmt:
                print("  → Actualizando estadísticas...")

            conn.execute(text(stmt))

        duration = (datetime.now() - start).total_seconds()
        print(f"\n[OK] Script completado en {duration:.1f} segundos\n")

        # Verificar estructura
        print("[INFO] Verificando columnas creadas...")
        result = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'ventas_backend'
            AND column_name IN ('monto_original', 'tiene_nota_credito', 'nota_credito_monto', 'monto_neto')
            ORDER BY column_name
        """))

        print("\nColumnas verificadas:")
        for row in result:
            print(f"  ✓ {row[0]}: {row[1]}")

        # Muestra de datos
        print("\n[INFO] Muestra de factura con NC:")
        result = conn.execute(text("""
            SELECT
                serie_cdp || '-' || nro_cp_inicial as factura,
                apellidos_nombres_razon_social,
                moneda,
                monto_original,
                nota_credito_monto,
                monto_neto,
                tiene_nota_credito
            FROM ventas_backend
            WHERE tiene_nota_credito = true
            AND apellidos_nombres_razon_social LIKE '%SINOHYDRO%'
            LIMIT 1
        """))

        row = result.fetchone()
        if row:
            print(f"\n  Factura: {row[0]}")
            print(f"  Cliente: {row[1]}")
            print(f"  Moneda: {row[2]}")
            print(f"  ✓ monto_original: {row[3]:.2f}")
            print(f"  ✓ nota_credito_monto: {row[4]:.2f}")
            print(f"  ✓ monto_neto: {row[5]:.2f}")
            print(f"  ✓ tiene_nota_credito: {row[6]}")

        # Estadísticas finales
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as con_nc,
                pg_size_pretty(pg_total_relation_size('ventas_backend')) as tamanio
            FROM ventas_backend
        """))
        row = result.fetchone()

        print("\n" + "=" * 80)
        print("RESULTADOS FINALES:")
        print("=" * 80)
        print(f"Total facturas: {row[0]:,}")
        print(f"Con notas de crédito: {row[1]:,}")
        print(f"Tamaño vista: {row[2]}")
        print("=" * 80)
        print("\n✅ Vista corregida exitosamente!")
        print("   Los nombres de columna ahora coinciden con schemas.py:")
        print("   - monto_original")
        print("   - tiene_nota_credito")
        print("   - nota_credito_monto")
        print("   - monto_neto")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

engine.dispose()
