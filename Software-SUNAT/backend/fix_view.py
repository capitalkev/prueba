"""
Script para arreglar la vista materializada (sin filtrar boletas porque tipo '3' son facturas en Perú)
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
print("ARREGLANDO VISTA MATERIALIZADA")
print("=" * 80)

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
    print(f"[ERROR] No se pudo conectar: {e}")
    sys.exit(1)

with engine.connect() as conn:
    print("[INFO] Eliminando vista antigua...")
    try:
        conn.execute(text("DROP MATERIALIZED VIEW ventas_backend CASCADE"))
        print("[OK] Vista antigua eliminada\n")
    except Exception as e:
        print(f"[WARNING] {e}\n")

    print("[INFO] Recreando vista SIN filtro de tipo (incluye todos los tipos)...")
    print("[INFO] Esto tomará varios minutos para 1.7M registros...")
    print()

    start = datetime.now()

    try:
        # Vista SIN filtro de tipo_cp_doc (incluye todo menos boletas serie B)
        conn.execute(text("""
CREATE MATERIALIZED VIEW ventas_backend AS
SELECT
    v.id,
    v.ruc,
    v.razon_social,
    v.periodo,
    v.car_sunat,
    v.fecha_emision,
    v.fecha_vcto_pago,
    v.tipo_cp_doc,
    v.serie_cdp,
    v.nro_cp_inicial,
    v.nro_final,
    v.tipo_doc_identidad,
    v.nro_doc_identidad,
    v.apellidos_nombres_razon_social,
    v.valor_facturado_exportacion,
    v.bi_gravada,
    v.dscto_bi,
    v.igv_ipm,
    v.dscto_igv_ipm,
    v.mto_exonerado,
    v.mto_inafecto,
    v.isc,
    v.bi_grav_ivap,
    v.ivap,
    v.icbper,
    v.otros_tributos,
    v.total_cp,
    v.moneda,
    v.tipo_cambio,
    v.fecha_emision_doc_modificado,
    v.tipo_cp_modificado,
    v.serie_cp_modificado,
    v.nro_cp_modificado,
    v.id_proyecto_operadores_atribucion,
    v.tipo_nota,
    v.est_comp,
    v.valor_fob_embarcado,
    v.valor_op_gratuitas,
    v.tipo_operacion,
    v.dam_cp,
    v.clu,
    v.estado1,
    v.estado2,
    v.ultima_actualizacion,

    -- CAMPOS CALCULADOS
    (SELECT COUNT(*) > 0
     FROM ventas_sire nc
     WHERE nc.ruc = v.ruc
     AND nc.tipo_cp_doc = '7'
     AND nc.nro_cp_modificado = v.nro_cp_inicial
     AND nc.nro_doc_identidad = v.nro_doc_identidad
    ) as tiene_nota_credito,

    COALESCE((
        SELECT SUM(
            CASE WHEN nc.tipo_cambio IS NOT NULL AND nc.tipo_cambio > 0
            THEN nc.total_cp / nc.tipo_cambio
            ELSE nc.total_cp END
        )
        FROM ventas_sire nc
        WHERE nc.ruc = v.ruc
        AND nc.tipo_cp_doc = '7'
        AND nc.nro_cp_modificado = v.nro_cp_inicial
        AND nc.nro_doc_identidad = v.nro_doc_identidad
    ), 0) as monto_nota_credito,

    (CASE WHEN v.tipo_cambio IS NOT NULL AND v.tipo_cambio > 0
     THEN v.total_cp / v.tipo_cambio
     ELSE v.total_cp END) + COALESCE((
        SELECT SUM(
            CASE WHEN nc.tipo_cambio IS NOT NULL AND nc.tipo_cambio > 0
            THEN nc.total_cp / nc.tipo_cambio
            ELSE nc.total_cp END
        )
        FROM ventas_sire nc
        WHERE nc.ruc = v.ruc
        AND nc.tipo_cp_doc = '7'
        AND nc.nro_cp_modificado = v.nro_cp_inicial
        AND nc.nro_doc_identidad = v.nro_doc_identidad
    ), 0) as total_neto,

    (SELECT STRING_AGG(nc.serie_cdp || '-' || nc.nro_cp_inicial, ', ' ORDER BY nc.fecha_emision)
     FROM ventas_sire nc
     WHERE nc.ruc = v.ruc
     AND nc.tipo_cp_doc = '7'
     AND nc.nro_cp_modificado = v.nro_cp_inicial
     AND nc.nro_doc_identidad = v.nro_doc_identidad
    ) as notas_credito_asociadas

FROM ventas_sire v
WHERE v.tipo_cp_doc = '1'
    AND v.serie_cdp NOT LIKE 'B%'
    AND v.apellidos_nombres_razon_social != '-'
    AND v.apellidos_nombres_razon_social IS NOT NULL
        """))

        duration = (datetime.now() - start).total_seconds()
        print(f"[OK] Vista creada en {duration:.1f} segundos\n")

        # Recrear índices
        print("[INFO] Recreando índices...")
        indices = [
            "CREATE UNIQUE INDEX idx_ventas_backend_id ON ventas_backend(id)",
            "CREATE INDEX idx_ventas_backend_ruc_periodo ON ventas_backend(ruc, periodo)",
            "CREATE INDEX idx_ventas_backend_tipo_doc ON ventas_backend(tipo_cp_doc)",
            "CREATE INDEX idx_ventas_backend_estado1 ON ventas_backend(estado1) WHERE estado1 IS NOT NULL",
            "CREATE INDEX idx_ventas_backend_fecha ON ventas_backend(fecha_emision)",
            "CREATE INDEX idx_ventas_backend_cliente ON ventas_backend(nro_doc_identidad)",
            "CREATE INDEX idx_ventas_backend_moneda ON ventas_backend(moneda)",
            "CREATE INDEX idx_ventas_backend_metricas ON ventas_backend(fecha_emision, moneda, estado1, total_neto)",
            "CREATE INDEX idx_ventas_backend_con_nc ON ventas_backend(tiene_nota_credito) WHERE tiene_nota_credito = true",
        ]

        for sql in indices:
            try:
                conn.execute(text(sql))
                print(f"[OK] {sql.split()[2]}")
            except Exception as e:
                print(f"[ERROR] {e}")

        # Recrear función
        print("\n[INFO] Recreando función de refresh...")
        conn.execute(text("""
CREATE OR REPLACE FUNCTION refresh_ventas_backend()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ventas_backend;
    RAISE NOTICE 'Vista ventas_backend refrescada a las %', NOW();
END;
$$ LANGUAGE plpgsql
        """))
        print("[OK] Función creada\n")

        # Actualizar estadísticas
        print("[INFO] Actualizando estadísticas...")
        conn.execute(text("ANALYZE ventas_backend"))
        print("[OK] Estadísticas actualizadas\n")

        # Verificar
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN tipo_cp_doc = '1' THEN 1 END) as facturas,
                COUNT(CASE WHEN tipo_cp_doc = '3' THEN 1 END) as boletas,
                COUNT(CASE WHEN tipo_cp_doc = '7' THEN 1 END) as nc,
                COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as con_nc,
                pg_size_pretty(pg_total_relation_size('ventas_backend')) as tamanio
            FROM ventas_backend
        """))
        row = result.fetchone()

        print("=" * 80)
        print("RESULTADOS:")
        print("=" * 80)
        print(f"Total registros: {row[0]:,}")
        print(f"  - Facturas (tipo 1): {row[1]:,}")
        print(f"  - Boletas (tipo 3): {row[2]:,}")
        print(f"  - Notas crédito (tipo 7): {row[3]:,}")
        print(f"  - Facturas con NC: {row[4]:,}")
        print(f"Tamaño total: {row[5]}")
        print("=" * 80)

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

engine.dispose()
