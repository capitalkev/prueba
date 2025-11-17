"""
Verificar si realmente existe una NC para la factura SINOHYDRO
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
    print("INVESTIGACIÓN: NC para factura SINOHYDRO E001-496")
    print("=" * 80)

    # 1. Buscar la factura
    print("\n1. Datos de la FACTURA:")
    result = conn.execute(text("""
        SELECT
            id,
            ruc,
            tipo_cp_doc,
            serie_cdp,
            nro_cp_inicial,
            nro_doc_identidad,
            apellidos_nombres_razon_social,
            total_cp,
            moneda,
            fecha_emision
        FROM ventas_sire
        WHERE apellidos_nombres_razon_social LIKE '%SINOHYDRO%'
        AND tipo_cp_doc = '1'
        AND serie_cdp = 'E001'
        AND nro_cp_inicial = '496'
    """))

    factura = result.fetchone()
    if factura:
        print(f"   ID: {factura[0]}")
        print(f"   RUC empresa: {factura[1]}")
        print(f"   Tipo: {factura[2]} (factura)")
        print(f"   Serie-Número: {factura[3]}-{factura[4]}")
        print(f"   RUC cliente: {factura[5]}")
        print(f"   Cliente: {factura[6]}")
        print(f"   Monto: {factura[7]}")
        print(f"   Moneda: {factura[8]}")
        print(f"   Fecha: {factura[9]}")

        # 2. Buscar NC asociadas
        print("\n2. Buscando NOTAS DE CRÉDITO asociadas:")
        result = conn.execute(text("""
            SELECT
                id,
                tipo_cp_doc,
                serie_cdp,
                nro_cp_inicial,
                nro_cp_modificado,
                total_cp,
                fecha_emision
            FROM ventas_sire
            WHERE ruc = :ruc
            AND tipo_cp_doc = '7'
            AND nro_doc_identidad = :nro_doc_identidad
        """), {"ruc": factura[1], "nro_doc_identidad": factura[5]})

        nc_encontradas = result.fetchall()
        if nc_encontradas:
            print(f"   Se encontraron {len(nc_encontradas)} NC para el cliente:")
            for nc in nc_encontradas:
                print(f"\n   NC {nc[2]}-{nc[3]}:")
                print(f"      - Modifica: {nc[4]}")
                print(f"      - Monto: {nc[5]}")
                print(f"      - Fecha: {nc[6]}")
                print(f"      - Coincide con factura E001-496? {nc[4] == factura[4]}")
        else:
            print("   ❌ NO se encontraron NC para este cliente")

        # 3. Buscar NC con JOIN (como en tu query original)
        print("\n3. Query JOIN (tu método original):")
        result = conn.execute(text("""
            SELECT
                v.serie_cdp || '-' || v.nro_cp_inicial as factura,
                v.total_cp as monto_factura,
                p.serie_cdp || '-' || p.nro_cp_inicial as nc,
                p.total_cp AS total_nc,
                (v.total_cp + p.total_cp) AS diferencia_total
            FROM ventas_sire v
            JOIN (
              SELECT
                ruc,
                serie_cdp,
                nro_cp_inicial,
                TRIM(TRAILING '.0' FROM nro_cp_modificado::text) AS nro_cp_modificado,
                nro_doc_identidad,
                total_cp
              FROM ventas_sire
              WHERE tipo_cp_doc = '7'
            ) AS p
            ON v.ruc = p.ruc
            AND v.nro_cp_inicial = p.nro_cp_modificado
            AND v.nro_doc_identidad = p.nro_doc_identidad
            WHERE v.ruc = :ruc
            AND v.serie_cdp = 'E001'
            AND v.nro_cp_inicial = '496'
        """), {"ruc": factura[1]})

        match = result.fetchone()
        if match:
            print(f"   ✅ MATCH ENCONTRADO:")
            print(f"      Factura: {match[0]} = {match[1]}")
            print(f"      NC: {match[2]} = {match[3]}")
            print(f"      Diferencia (neto): {match[4]}")
        else:
            print(f"   ❌ NO HAY MATCH con la query JOIN")

    else:
        print("   ❌ No se encontró la factura")

    print("\n" + "=" * 80)

engine.dispose()
