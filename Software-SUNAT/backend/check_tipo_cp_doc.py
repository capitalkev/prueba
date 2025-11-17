"""
Script para verificar los valores de tipo_cp_doc en la base de datos
y verificar el formato de las notas de crédito
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear conexión a la base de datos
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "crm_sunat")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("\n" + "=" * 80)
    print("1. VALORES DISTINTOS DE tipo_cp_doc")
    print("=" * 80)

    result = conn.execute(text("""
        SELECT tipo_cp_doc, COUNT(*) as cantidad
        FROM ventas_sire
        GROUP BY tipo_cp_doc
        ORDER BY tipo_cp_doc
    """))

    for row in result:
        print(f"   tipo_cp_doc = '{row.tipo_cp_doc}' → {row.cantidad:,} registros")

    print("\n" + "=" * 80)
    print("2. EJEMPLO DE FACTURA Y SU NOTA DE CRÉDITO")
    print("=" * 80)

    # Buscar una factura que tenga nota de crédito
    result = conn.execute(text("""
        SELECT
            f.tipo_cp_doc as factura_tipo,
            f.serie_cdp || '-' || f.nro_cp_inicial as factura_num,
            f.total_cp as factura_monto,
            f.nro_doc_identidad as cliente,
            f.moneda,
            nc.tipo_cp_doc as nc_tipo,
            nc.serie_cdp || '-' || nc.nro_cp_inicial as nc_num,
            nc.total_cp as nc_monto,
            nc.nro_cp_modificado as nc_modifica
        FROM ventas_sire f
        INNER JOIN ventas_sire nc ON
            nc.ruc = f.ruc
            AND nc.nro_cp_modificado = f.nro_cp_inicial
            AND nc.nro_doc_identidad = f.nro_doc_identidad
            AND nc.tipo_cp_doc = '7'
        WHERE f.tipo_cp_doc = '1'
        LIMIT 5
    """))

    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"\n   Factura: {row.factura_num} (tipo={row.factura_tipo})")
            print(f"   Monto factura: {row.factura_monto} {row.moneda}")
            print(f"   Cliente: {row.cliente}")
            print(f"   NC: {row.nc_num} (tipo={row.nc_tipo})")
            print(f"   Monto NC: {row.nc_monto} {row.moneda}")
            print(f"   NC modifica: {row.nc_modifica}")
            print(f"   MONTO NETO: {float(row.factura_monto) + float(row.nc_monto)} {row.moneda}")
            print(f"   " + "-" * 70)
    else:
        print("   No se encontraron facturas con notas de credito")

    print("\n" + "=" * 80)
    print("3. VERIFICAR SI EXISTE VISTA MATERIALIZADA ventas_backend")
    print("=" * 80)

    result = conn.execute(text("""
        SELECT
            matviewname,
            pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as tamaño,
            CASE WHEN ispopulated THEN 'POBLADA' ELSE 'VACÍA' END as estado
        FROM pg_matviews
        WHERE matviewname = 'ventas_backend'
    """))

    row = result.fetchone()
    if row:
        print(f"   Vista: {row.matviewname}")
        print(f"   Tamaño: {row.tamaño}")
        print(f"   Estado: {row.estado}")

        # Verificar registros en la vista
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN tipo_cp_doc = '1' THEN 1 END) as facturas,
                COUNT(CASE WHEN tipo_cp_doc = '7' THEN 1 END) as notas_credito,
                COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as facturas_con_nc
            FROM ventas_backend
        """))

        row2 = result.fetchone()
        print(f"\n   Total registros: {row2.total:,}")
        print(f"   Facturas: {row2.facturas:,}")
        print(f"   Notas de crédito: {row2.notas_credito:,}")
        print(f"   Facturas con NC: {row2.facturas_con_nc:,}")

        # Ejemplo de factura con NC en la vista
        print("\n   Ejemplo de factura con NC en la vista:")
        result = conn.execute(text("""
            SELECT
                serie_cdp || '-' || nro_cp_inicial as factura,
                total_cp,
                monto_nota_credito,
                total_neto,
                moneda,
                notas_credito_asociadas
            FROM ventas_backend
            WHERE tiene_nota_credito = true
            LIMIT 3
        """))

        for row3 in result:
            print(f"\n      Factura: {row3.factura}")
            print(f"      Total CP: {row3.total_cp} {row3.moneda}")
            print(f"      Monto NC: {row3.monto_nota_credito} {row3.moneda}")
            print(f"      Total Neto: {row3.total_neto} {row3.moneda}")
            print(f"      NC Asociadas: {row3.notas_credito_asociadas}")

    else:
        print("   La vista materializada ventas_backend NO EXISTE")
        print("   Ejecutar: 03_implement_optimizations.sql")

print("\n" + "=" * 80)
print("VERIFICACION COMPLETADA")
print("=" * 80)
