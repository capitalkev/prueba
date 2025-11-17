"""
Script para implementar vista materializada optimizada
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# Forzar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

print("=" * 80)
print("IMPLEMENTACIÓN DE VISTA MATERIALIZADA OPTIMIZADA")
print("=" * 80)
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Registros esperados: ~1.7M facturas")
print(f"Tiempo estimado: 3-5 minutos")
print("=" * 80)
print()

# Conectar
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
    print("[INFO] Conectado usando Cloud SQL Connector\n")

except Exception as e:
    print(f"[ERROR] No se pudo conectar: {e}")
    sys.exit(1)

with engine.connect() as conn:
    print("=" * 80)
    print("1. CREANDO VISTA MATERIALIZADA ventas_backend")
    print("=" * 80)
    print("[INFO] Esto tomará varios minutos...")
    print()

    start_time = datetime.now()

    try:
        # Crear vista materializada
        conn.execute(text("""
CREATE MATERIALIZED VIEW ventas_backend AS
SELECT
    -- Campos base
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

    -- Montos
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

    -- Información adicional
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

    -- Estados de gestión
    v.estado1,
    v.estado2,
    v.ultima_actualizacion,

    -- CAMPOS CALCULADOS
    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT COUNT(*) > 0
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '07'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE false
    END as tiene_nota_credito,

    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT COALESCE(SUM(
                CASE
                    WHEN nc.tipo_cambio IS NOT NULL AND nc.tipo_cambio > 0
                    THEN nc.total_cp / nc.tipo_cambio
                    ELSE nc.total_cp
                END
            ), 0)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '07'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE 0
    END as monto_nota_credito,

    CASE
        WHEN v.tipo_cp_doc = '01' THEN
            CASE
                WHEN v.tipo_cambio IS NOT NULL AND v.tipo_cambio > 0
                THEN v.total_cp / v.tipo_cambio
                ELSE v.total_cp
            END + COALESCE((
                SELECT SUM(
                    CASE
                        WHEN nc.tipo_cambio IS NOT NULL AND nc.tipo_cambio > 0
                        THEN nc.total_cp / nc.tipo_cambio
                        ELSE nc.total_cp
                    END
                )
                FROM ventas_sire nc
                WHERE nc.ruc = v.ruc
                AND nc.periodo = v.periodo
                AND nc.tipo_cp_doc = '07'
                AND nc.nro_cp_modificado = v.nro_cp_inicial
                AND nc.nro_doc_identidad = v.nro_doc_identidad
            ), 0)
        ELSE
            CASE
                WHEN v.tipo_cambio IS NOT NULL AND v.tipo_cambio > 0
                THEN v.total_cp / v.tipo_cambio
                ELSE v.total_cp
            END
    END as total_neto,

    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT STRING_AGG(nc.serie_cdp || '-' || nc.nro_cp_inicial, ', ' ORDER BY nc.fecha_emision)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '07'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE NULL
    END as notas_credito_asociadas

FROM ventas_sire v
WHERE v.tipo_cp_doc IN ('01', '07')
    AND v.serie_cdp NOT LIKE 'B%'
    AND v.apellidos_nombres_razon_social != '-'
    AND v.apellidos_nombres_razon_social IS NOT NULL
        """))

        duration = (datetime.now() - start_time).total_seconds()
        print(f"[OK] Vista materializada creada en {duration:.1f} segundos")

    except Exception as e:
        print(f"[ERROR] No se pudo crear vista: {e}")
        engine.dispose()
        sys.exit(1)

    print()
    print("=" * 80)
    print("2. CREANDO ÍNDICES EN LA VISTA MATERIALIZADA")
    print("=" * 80)

    indices = [
        ("idx_ventas_backend_id", "CREATE UNIQUE INDEX idx_ventas_backend_id ON ventas_backend(id)", "Índice único por ID (permite REFRESH CONCURRENTLY)"),
        ("idx_ventas_backend_ruc_periodo", "CREATE INDEX idx_ventas_backend_ruc_periodo ON ventas_backend(ruc, periodo)", "Índice compuesto RUC + Periodo"),
        ("idx_ventas_backend_tipo_doc", "CREATE INDEX idx_ventas_backend_tipo_doc ON ventas_backend(tipo_cp_doc)", "Índice por tipo de documento"),
        ("idx_ventas_backend_estado1", "CREATE INDEX idx_ventas_backend_estado1 ON ventas_backend(estado1) WHERE estado1 IS NOT NULL", "Índice parcial por estado1"),
        ("idx_ventas_backend_fecha", "CREATE INDEX idx_ventas_backend_fecha ON ventas_backend(fecha_emision)", "Índice por fecha de emisión"),
        ("idx_ventas_backend_cliente", "CREATE INDEX idx_ventas_backend_cliente ON ventas_backend(nro_doc_identidad)", "Índice por cliente"),
        ("idx_ventas_backend_moneda", "CREATE INDEX idx_ventas_backend_moneda ON ventas_backend(moneda)", "Índice por moneda"),
        ("idx_ventas_backend_metricas", "CREATE INDEX idx_ventas_backend_metricas ON ventas_backend(fecha_emision, moneda, estado1, total_neto)", "Índice compuesto para métricas"),
        ("idx_ventas_backend_con_nc", "CREATE INDEX idx_ventas_backend_con_nc ON ventas_backend(tiene_nota_credito) WHERE tipo_cp_doc = '01'", "Índice parcial facturas con NC"),
    ]

    for nombre, sql, desc in indices:
        try:
            start = datetime.now()
            conn.execute(text(sql))
            duration = (datetime.now() - start).total_seconds()
            print(f"[OK] {nombre} ({duration:.1f}s) - {desc}")
        except Exception as e:
            print(f"[ERROR] {nombre}: {e}")

    print()
    print("=" * 80)
    print("3. CREANDO FUNCIÓN DE REFRESH")
    print("=" * 80)

    try:
        conn.execute(text("""
CREATE OR REPLACE FUNCTION refresh_ventas_backend()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ventas_backend;
    RAISE NOTICE 'Vista ventas_backend refrescada exitosamente a las %', NOW();
END;
$$ LANGUAGE plpgsql
        """))
        print("[OK] Función refresh_ventas_backend() creada")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 80)
    print("4. ACTUALIZANDO ESTADÍSTICAS")
    print("=" * 80)

    try:
        conn.execute(text("ANALYZE ventas_backend"))
        print("[OK] Estadísticas de ventas_backend actualizadas")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 80)
    print("5. VERIFICANDO IMPLEMENTACIÓN")
    print("=" * 80)

    # Verificar vista
    result = conn.execute(text("""
        SELECT
            pg_size_pretty(pg_total_relation_size('ventas_backend')) as tamanio,
            (SELECT COUNT(*) FROM ventas_backend) as registros
    """))
    row = result.fetchone()
    print(f"\n[INFO] Vista materializada creada:")
    print(f"  - Tamaño total: {row[0]}")
    print(f"  - Registros: {row[1]:,}")

    # Verificar estadísticas
    result = conn.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN tipo_cp_doc = '01' THEN 1 END) as facturas,
            COUNT(CASE WHEN tipo_cp_doc = '07' THEN 1 END) as notas_credito,
            COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as facturas_con_nc
        FROM ventas_backend
    """))
    row = result.fetchone()
    print(f"\n[INFO] Estadísticas:")
    print(f"  - Total registros: {row[0]:,}")
    print(f"  - Facturas (01): {row[1]:,}")
    print(f"  - Notas de crédito (07): {row[2]:,}")
    print(f"  - Facturas con NC: {row[3]:,}")

    # Verificar índices
    result = conn.execute(text("""
        SELECT
            indexname,
            pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as tamanio
        FROM pg_indexes
        WHERE tablename = 'ventas_backend'
          AND schemaname = 'public'
        ORDER BY indexname
    """))
    rows = result.fetchall()
    print(f"\n[INFO] Índices creados ({len(rows)}):")
    for row in rows:
        print(f"  - {row[0]}: {row[1]}")

print()
print("=" * 80)
print("✓ OPTIMIZACIONES IMPLEMENTADAS CON ÉXITO")
print("=" * 80)
print()
print("SIGUIENTE PASO:")
print("1. Crear VentaBackendRepository")
print("2. Actualizar main.py para usar vista materializada")
print("3. Configurar auto-refresh")
print()

engine.dispose()
