-- ==================================================================================
-- SCRIPT SQL COMPLETO PARA BASE DE DATOS CRM-SUNAT
-- ==================================================================================
-- Descripción: Configuración completa de la base de datos para el sistema CRM-SUNAT
-- Incluye: Campos de gestión, vistas materializadas y métricas para dashboard
-- Fecha: 2025-11-15
-- ==================================================================================

-- ==================================================================================
-- PASO 1: AGREGAR CAMPOS DE GESTIÓN A LA TABLA ventas_sire
-- ==================================================================================

-- Agregar campos estado1 y estado2 para gestión de facturas
ALTER TABLE ventas_sire
ADD COLUMN IF NOT EXISTS estado1 VARCHAR(100),
ADD COLUMN IF NOT EXISTS estado2 VARCHAR(100);

-- Crear índices para mejorar performance en consultas por estado
CREATE INDEX IF NOT EXISTS idx_ventas_estado1 ON ventas_sire(estado1) WHERE estado1 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ventas_estado2 ON ventas_sire(estado2) WHERE estado2 IS NOT NULL;

-- Agregar comentarios descriptivos
COMMENT ON COLUMN ventas_sire.estado1 IS 'Estado de gestión 1 (ej: GESTIONADO, SIN GESTIÓN, etc.)';
COMMENT ON COLUMN ventas_sire.estado2 IS 'Estado de gestión 2 (ej: CONTACTADO, PENDIENTE, etc.)';

-- ==================================================================================
-- PASO 2: CREAR VISTA MATERIALIZADA PARA EL BACKEND
-- ==================================================================================

-- Eliminar vista si existe (para recrear)
DROP MATERIALIZED VIEW IF EXISTS ventas_backend CASCADE;

-- Crear vista materializada optimizada
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

    -- Estados de gestión (preservados por UPSERT)
    v.estado1,
    v.estado2,
    v.ultima_actualizacion,

    -- ==================================================================================
    -- CAMPOS CALCULADOS PARA ANULACIÓN
    -- ==================================================================================

    -- ¿Está anulada por nota de crédito?
    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT COUNT(*) > 0
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '07'
            AND nc.serie_cp_modificado = v.serie_cdp
            AND nc.nro_cp_modificado = v.nro_cp_inicial
        )
        ELSE false
    END as esta_anulada,

    -- Monto de la(s) nota(s) de crédito asociada(s)
    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT COALESCE(SUM(nc.total_cp), 0)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '07'
            AND nc.serie_cp_modificado = v.serie_cdp
            AND nc.nro_cp_modificado = v.nro_cp_inicial
        )
        ELSE NULL
    END as monto_nota_credito,

    -- Total neto después de notas de crédito (para facturas tipo '01')
    CASE
        WHEN v.tipo_cp_doc = '01' THEN
            v.total_cp + COALESCE((
                SELECT SUM(nc.total_cp)
                FROM ventas_sire nc
                WHERE nc.ruc = v.ruc
                AND nc.periodo = v.periodo
                AND nc.tipo_cp_doc = '07'
                AND nc.serie_cp_modificado = v.serie_cdp
                AND nc.nro_cp_modificado = v.nro_cp_inicial
            ), 0)
        ELSE v.total_cp
    END as total_neto,

    -- Serie y número de las notas de crédito asociadas (para mostrar en UI)
    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT STRING_AGG(nc.serie_cdp || '-' || nc.nro_cp_inicial, ', ' ORDER BY nc.fecha_emision)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '07'
            AND nc.serie_cp_modificado = v.serie_cdp
            AND nc.nro_cp_modificado = v.nro_cp_inicial
        )
        ELSE NULL
    END as notas_credito_asociadas

FROM ventas_sire v
WHERE v.tipo_cp_doc IN ('01', '07');

-- ==================================================================================
-- CREAR ÍNDICES PARA OPTIMIZACIÓN DE CONSULTAS
-- ==================================================================================

-- Índice único por ID (requerido para REFRESH CONCURRENTLY)
CREATE UNIQUE INDEX idx_ventas_backend_id ON ventas_backend(id);

-- Índice compuesto para filtros principales
CREATE INDEX idx_ventas_backend_ruc_periodo ON ventas_backend(ruc, periodo);

-- Índice por tipo de documento
CREATE INDEX idx_ventas_backend_tipo_doc ON ventas_backend(tipo_cp_doc);

-- Índices para estados de gestión (usado en filtros)
CREATE INDEX idx_ventas_backend_estado1 ON ventas_backend(estado1) WHERE estado1 IS NOT NULL;
CREATE INDEX idx_ventas_backend_estado2 ON ventas_backend(estado2) WHERE estado2 IS NOT NULL;

-- Índice para facturas anuladas
CREATE INDEX idx_ventas_backend_anulada ON ventas_backend(esta_anulada) WHERE tipo_cp_doc = '01';

-- Índice por fecha de emisión (para rangos de fechas)
CREATE INDEX idx_ventas_backend_fecha ON ventas_backend(fecha_emision);

-- Índice por cliente
CREATE INDEX idx_ventas_backend_cliente ON ventas_backend(nro_doc_identidad);

-- Índice por moneda (para filtros de moneda)
CREATE INDEX idx_ventas_backend_moneda ON ventas_backend(moneda);

-- Índice compuesto para métricas por moneda y estado
CREATE INDEX idx_ventas_backend_metrics ON ventas_backend(moneda, estado1, total_neto);

-- Agregar comentarios descriptivos
COMMENT ON MATERIALIZED VIEW ventas_backend IS 'Vista optimizada para backend. Incluye solo facturas (01) y notas de crédito (07) con cálculos de anulación y totales netos.';
COMMENT ON COLUMN ventas_backend.esta_anulada IS 'TRUE si la factura tiene una nota de crédito asociada';
COMMENT ON COLUMN ventas_backend.monto_nota_credito IS 'Suma de montos de notas de crédito asociadas (valor negativo)';
COMMENT ON COLUMN ventas_backend.total_neto IS 'Total original + notas de crédito (resultado final a pagar)';
COMMENT ON COLUMN ventas_backend.notas_credito_asociadas IS 'Serie-Número de las notas de crédito que anulan esta factura';

-- ==================================================================================
-- PASO 3: FUNCIÓN PARA REFRESCAR LA VISTA MATERIALIZADA
-- ==================================================================================

CREATE OR REPLACE FUNCTION refresh_ventas_backend()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ventas_backend;
    RAISE NOTICE 'Vista ventas_backend refrescada exitosamente a las %', NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_ventas_backend() IS 'Refresca la vista materializada ventas_backend de forma concurrente (sin bloquear consultas)';

-- ==================================================================================
-- PASO 4: VISTA PARA MÉTRICAS DEL DASHBOARD
-- ==================================================================================

CREATE OR REPLACE VIEW ventas_metricas_dashboard AS
SELECT
    -- Pipeline Activo (facturas no anuladas)
    SUM(CASE WHEN moneda = 'PEN' AND tipo_cp_doc = '01' AND NOT esta_anulada THEN total_neto ELSE 0 END) as pipeline_activo_pen,
    SUM(CASE WHEN moneda = 'USD' AND tipo_cp_doc = '01' AND NOT esta_anulada THEN total_neto ELSE 0 END) as pipeline_activo_usd,

    -- Total facturado (incluyendo anuladas, para calcular performance de cierres)
    SUM(CASE WHEN moneda = 'PEN' AND tipo_cp_doc = '01' THEN total_cp ELSE 0 END) as total_facturado_pen,
    SUM(CASE WHEN moneda = 'USD' AND tipo_cp_doc = '01' THEN total_cp ELSE 0 END) as total_facturado_usd,

    -- Total cerrado (facturas completamente anuladas)
    SUM(CASE WHEN moneda = 'PEN' AND tipo_cp_doc = '01' AND esta_anulada AND total_neto = 0 THEN total_cp ELSE 0 END) as total_cerrado_pen,
    SUM(CASE WHEN moneda = 'USD' AND tipo_cp_doc = '01' AND esta_anulada AND total_neto = 0 THEN total_cp ELSE 0 END) as total_cerrado_usd,

    -- Performance de cierres (%)
    CASE
        WHEN SUM(CASE WHEN moneda = 'PEN' AND tipo_cp_doc = '01' THEN total_cp ELSE 0 END) > 0 THEN
            ROUND((SUM(CASE WHEN moneda = 'PEN' AND tipo_cp_doc = '01' AND esta_anulada AND total_neto = 0 THEN total_cp ELSE 0 END) * 100.0 /
             SUM(CASE WHEN moneda = 'PEN' AND tipo_cp_doc = '01' THEN total_cp ELSE 0 END))::numeric, 2)
        ELSE 0
    END as performance_cierres_pen_pct,

    CASE
        WHEN SUM(CASE WHEN moneda = 'USD' AND tipo_cp_doc = '01' THEN total_cp ELSE 0 END) > 0 THEN
            ROUND((SUM(CASE WHEN moneda = 'USD' AND tipo_cp_doc = '01' AND esta_anulada AND total_neto = 0 THEN total_cp ELSE 0 END) * 100.0 /
             SUM(CASE WHEN moneda = 'USD' AND tipo_cp_doc = '01' THEN total_cp ELSE 0 END))::numeric, 2)
        ELSE 0
    END as performance_cierres_usd_pct,

    -- Contadores
    COUNT(CASE WHEN tipo_cp_doc = '01' AND NOT esta_anulada THEN 1 END) as total_facturas_activas,
    COUNT(CASE WHEN tipo_cp_doc = '01' AND esta_anulada THEN 1 END) as total_facturas_anuladas,
    COUNT(CASE WHEN tipo_cp_doc = '07' THEN 1 END) as total_notas_credito

FROM ventas_backend;

COMMENT ON VIEW ventas_metricas_dashboard IS 'Métricas agregadas para el dashboard: pipeline activo, performance de cierres, etc.';

-- ==================================================================================
-- PASO 5: REFRESCAR VISTA MATERIALIZADA INICIALMENTE
-- ==================================================================================

-- Nota: Este paso puede tardar dependiendo del volumen de datos
SELECT refresh_ventas_backend();

-- ==================================================================================
-- FIN DEL SCRIPT
-- ==================================================================================

-- Verificar que todo se creó correctamente
SELECT
    'ventas_backend' as objeto,
    'Materialized View' as tipo,
    COUNT(*) as registros
FROM ventas_backend
UNION ALL
SELECT
    'ventas_metricas_dashboard' as objeto,
    'View' as tipo,
    1 as registros
FROM ventas_metricas_dashboard;

-- Mostrar métricas iniciales
SELECT * FROM ventas_metricas_dashboard;
