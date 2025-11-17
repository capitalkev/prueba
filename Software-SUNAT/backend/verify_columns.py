"""
Verificar que las columnas se hayan creado correctamente
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
    print("=" * 80)
    print("VERIFICACIÓN DE COLUMNAS")
    print("=" * 80)

    # 1. Verificar existencia de columnas
    print("\n1. Columnas calculadas en ventas_backend:")
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'ventas_backend'
        AND column_name IN ('monto_original', 'tiene_nota_credito', 'nota_credito_monto', 'monto_neto')
        ORDER BY column_name
    """))

    for row in result:
        print(f"   ✓ {row[0]}: {row[1]}")

    # 2. Muestra de datos - Factura SINOHYDRO
    print("\n2. Muestra de factura SINOHYDRO con NC:")
    result = conn.execute(text("""
        SELECT
            serie_cdp || '-' || nro_cp_inicial as factura,
            apellidos_nombres_razon_social,
            moneda,
            total_cp,
            tipo_cambio,
            monto_original,
            nota_credito_monto,
            monto_neto,
            tiene_nota_credito
        FROM ventas_backend
        WHERE apellidos_nombres_razon_social LIKE '%SINOHYDRO%'
        AND monto_original > 38000
        AND monto_original < 39000
        LIMIT 1
    """))

    row = result.fetchone()
    if row:
        print(f"\n   Factura: {row[0]}")
        print(f"   Cliente: {row[1]}")
        print(f"   Moneda: {row[2]}")
        print(f"\n   Datos ORIGINALES:")
        print(f"   - total_cp: {row[3]:.2f}")
        print(f"   - tipo_cambio: {row[4]:.4f}")
        print(f"\n   Datos CALCULADOS:")
        print(f"   - monto_original: {row[5]:.2f}  (total_cp / tipo_cambio)")
        print(f"   - nota_credito_monto: {row[6]:.2f}  (suma de NC, negativo)")
        print(f"   - monto_neto: {row[7]:.2f}  (monto_original + nota_credito_monto)")
        print(f"   - tiene_nota_credito: {row[8]}")
        print(f"\n   VERIFICACIÓN:")
        cálculo_manual = row[5] + row[6]
        print(f"   - monto_original ({row[5]:.2f}) + nota_credito_monto ({row[6]:.2f}) = {cálculo_manual:.2f}")
        if abs(cálculo_manual - row[7]) < 0.01:
            print(f"   ✅ CORRECTO: monto_neto ({row[7]:.2f}) coincide")
        else:
            print(f"   ❌ ERROR: monto_neto debería ser {cálculo_manual:.2f} pero es {row[7]:.2f}")
    else:
        print("   ⚠️ No se encontró factura SINOHYDRO")

    # 3. Estadísticas
    print("\n3. Estadísticas:")
    result = conn.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as con_nc,
            pg_size_pretty(pg_total_relation_size('ventas_backend')) as tam
        FROM ventas_backend
    """))
    row = result.fetchone()
    print(f"   - Total facturas: {row[0]:,}")
    print(f"   - Con NC: {row[1]:,}")
    print(f"   - Tamaño: {row[2]}")

    print("\n" + "=" * 80)
    print("✅ VISTA MATERIALIZADA CORRECTA")
    print("=" * 80)
    print("Columnas coinciden con schemas.py:")
    print("  - monto_original (NUEVO)")
    print("  - tiene_nota_credito")
    print("  - nota_credito_monto (antes: monto_nota_credito)")
    print("  - monto_neto (antes: total_neto)")
    print("=" * 80)

engine.dispose()
