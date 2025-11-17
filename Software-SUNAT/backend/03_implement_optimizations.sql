-- ==================================================================================
-- PASO 3: IMPLEMENTAR OPTIMIZACIONES - VISTAS MATERIALIZADAS E ÍNDICES
-- ==================================================================================
-- Descripción: Crea vistas materializadas optimizadas e índices estratégicos
-- IMPORTANTE: Ejecutar solo después de 02_cleanup_garbage.sql
-- Uso: psql -h localhost -U postgres -d crm_sunat -f 03_implement_optimizations.sql
-- ==================================================================================

\echo '=========================================='
\echo 'IMPLEMENTANDO OPTIMIZACIONES'
\echo '=========================================='
\echo ''

-- ==================================================================================
-- 1. VERIFICAR QUE EXISTEN COLUMNAS estado1 Y estado2
-- ==================================================================================
\echo '1. Verificando/agregando columnas de gestión...'

-- Agregar columnas estado1 y estado2 si no existen
ALTER TABLE ventas_sire
ADD COLUMN IF NOT EXISTS estado1 VARCHAR(100),
ADD COLUMN IF NOT EXISTS estado2 VARCHAR(100);

-- Agregar comentarios descriptivos
COMMENT ON COLUMN ventas_sire.estado1 IS 'Estado de gestión: Sin gestión, Gestionando, Ganada, Perdida';
COMMENT ON COLUMN ventas_sire.estado2 IS 'Motivo de pérdida: Por Tasa, Por Riesgo, Deudor no califica, Cliente no interesado, Competencia, Otro';

\echo '   ✓ Columnas de gestión verificadas'
\echo ''

-- ==================================================================================
-- 2. CREAR ÍNDICES ESENCIALES EN ventas_sire
-- ==================================================================================
\echo '2. Creando índices esenciales en ventas_sire...'

-- Índice compuesto principal (RUC + Periodo)
CREATE INDEX IF NOT EXISTS idx_ventas_ruc_periodo ON ventas_sire(ruc, periodo);

-- Índice por cliente
CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas_sire(nro_doc_identidad);

-- Índice por fecha de emisión (para rangos de fechas)
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas_sire(fecha_emision);

-- Índice parcial por estado1 (solo registros con estado)
CREATE INDEX IF NOT EXISTS idx_ventas_estado1 ON ventas_sire(estado1) WHERE estado1 IS NOT NULL;

-- Índice por tipo de documento (para filtrar facturas vs notas de crédito)
CREATE INDEX IF NOT EXISTS idx_ventas_tipo_doc ON ventas_sire(tipo_cp_doc);

-- Índice por moneda (para filtros de moneda)
CREATE INDEX IF NOT EXISTS idx_ventas_moneda ON ventas_sire(moneda);

-- Índice compuesto para queries de métricas
CREATE INDEX IF NOT EXISTS idx_ventas_metricas ON ventas_sire(fecha_emision, moneda, estado1)
WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%';

-- Índice para búsqueda de notas de crédito
CREATE INDEX IF NOT EXISTS idx_ventas_nc_lookup ON ventas_sire(ruc, nro_cp_modificado, nro_doc_identidad)
WHERE tipo_cp_doc = '7';

\echo '   ✓ Índices en ventas_sire creados'
\echo ''

-- ==================================================================================
-- 3. CREAR ÍNDICES ESENCIALES EN compras_sire
-- ==================================================================================
\echo '3. Creando índices esenciales en compras_sire...'

-- Índice compuesto principal
CREATE INDEX IF NOT EXISTS idx_compras_ruc_periodo ON compras_sire(ruc, periodo);

-- Índice por proveedor
CREATE INDEX IF NOT EXISTS idx_compras_proveedor ON compras_sire(nro_doc_identidad);

-- Índice por fecha
CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras_sire(fecha_emision);

\echo '   ✓ Índices en compras_sire creados'
\echo ''

-- ==================================================================================
-- 4. CREAR VISTA MATERIALIZADA OPTIMIZADA: ventas_backend
-- ==================================================================================
\echo '4. Creando vista materializada ventas_backend...'

CREATE MATERIALIZED VIEW ventas_backend AS
SELECT
    -- Campos base de la factura
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

    -- ==================================================================================
    -- CAMPOS CALCULADOS PARA NOTAS DE CRÉDITO
    -- ==================================================================================

    -- ¿Tiene nota de crédito asociada?
    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT COUNT(*) > 0
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '7'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE false
    END as tiene_nota_credito,

    -- Monto total de notas de crédito (suma, valor negativo)
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
            AND nc.tipo_cp_doc = '7'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE 0
    END as monto_nota_credito,

    -- Total neto = total_cp + monto_nota_credito (NC es negativo)
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
                AND nc.tipo_cp_doc = '7'
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

    -- Serie-Número de notas de crédito asociadas
    CASE
        WHEN v.tipo_cp_doc = '01' THEN (
            SELECT STRING_AGG(nc.serie_cdp || '-' || nc.nro_cp_inicial, ', ' ORDER BY nc.fecha_emision)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.periodo = v.periodo
            AND nc.tipo_cp_doc = '7'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE NULL
    END as notas_credito_asociadas

FROM ventas_sire v
WHERE v.tipo_cp_doc IN ('01', '07')  -- Solo facturas y notas de crédito
    AND v.serie_cdp NOT LIKE 'B%'    -- Excluir boletas
    AND v.apellidos_nombres_razon_social != '-'
    AND v.apellidos_nombres_razon_social IS NOT NULL;

\echo '   ✓ Vista materializada ventas_backend creada'
\echo ''

-- ==================================================================================
-- 5. CREAR ÍNDICES EN LA VISTA MATERIALIZADA
-- ==================================================================================
\echo '5. Creando índices en ventas_backend...'

-- Índice único por ID (requerido para REFRESH CONCURRENTLY)
CREATE UNIQUE INDEX idx_ventas_backend_id ON ventas_backend(id);

-- Índice compuesto principal
CREATE INDEX idx_ventas_backend_ruc_periodo ON ventas_backend(ruc, periodo);

-- Índice por tipo de documento
CREATE INDEX idx_ventas_backend_tipo_doc ON ventas_backend(tipo_cp_doc);

-- Índice parcial por estado1
CREATE INDEX idx_ventas_backend_estado1 ON ventas_backend(estado1) WHERE estado1 IS NOT NULL;

-- Índice por fecha
CREATE INDEX idx_ventas_backend_fecha ON ventas_backend(fecha_emision);

-- Índice por cliente
CREATE INDEX idx_ventas_backend_cliente ON ventas_backend(nro_doc_identidad);

-- Índice por moneda
CREATE INDEX idx_ventas_backend_moneda ON ventas_backend(moneda);

-- Índice compuesto para métricas
CREATE INDEX idx_ventas_backend_metricas ON ventas_backend(fecha_emision, moneda, estado1, total_neto);

-- Índice para facturas con NC
CREATE INDEX idx_ventas_backend_con_nc ON ventas_backend(tiene_nota_credito) WHERE tipo_cp_doc = '01';

\echo '   ✓ Índices en ventas_backend creados'
\echo ''

-- ==================================================================================
-- 6. CREAR FUNCIÓN DE REFRESH
-- ==================================================================================
\echo '6. Creando función de refresh...'

CREATE OR REPLACE FUNCTION refresh_ventas_backend()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ventas_backend;
    RAISE NOTICE 'Vista ventas_backend refrescada exitosamente a las %', NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_ventas_backend() IS 'Refresca la vista materializada ventas_backend de forma concurrente (sin bloquear consultas)';

\echo '   ✓ Función refresh_ventas_backend() creada'
\echo ''

-- ==================================================================================
-- 7. POBLAR LA VISTA MATERIALIZADA INICIALMENTE
-- ==================================================================================
\echo '7. Poblando vista materializada (esto puede tardar)...'

REFRESH MATERIALIZED VIEW ventas_backend;

\echo '   ✓ Vista poblada exitosamente'
\echo ''

-- ==================================================================================
-- 8. ANÁLISIS DE ESTADÍSTICAS
-- ==================================================================================
\echo '8. Actualizando estadísticas para el query planner...'

ANALYZE ventas_sire;
ANALYZE compras_sire;
ANALYZE ventas_backend;

\echo '   ✓ Estadísticas actualizadas'
\echo ''

-- ==================================================================================
-- 9. VERIFICACIÓN FINAL
-- ==================================================================================
\echo '9. Verificando implementación...'
\echo ''

\echo 'Vista materializada creada:'
SELECT
    matviewname,
    pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as tamaño,
    CASE WHEN ispopulated THEN 'POBLADA' ELSE 'VACÍA' END as estado
FROM pg_matviews
WHERE matviewname = 'ventas_backend';

\echo ''
\echo 'Registros en ventas_backend:'
SELECT
    COUNT(*) as total_registros,
    COUNT(CASE WHEN tipo_cp_doc = '01' THEN 1 END) as facturas,
    COUNT(CASE WHEN tipo_cp_doc = '07' THEN 1 END) as notas_credito,
    COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as facturas_con_nc
FROM ventas_backend;

\echo ''
\echo 'Índices creados en ventas_backend:'
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as tamaño
FROM pg_stat_user_indexes
WHERE tablename = 'ventas_backend'
ORDER BY indexname;

\echo ''
\echo '=========================================='
\echo 'OPTIMIZACIONES IMPLEMENTADAS CON ÉXITO'
\echo '=========================================='
\echo ''
\echo 'SIGUIENTE PASO:'
\echo 'Ejecutar 04_modify_backend.sql para actualizar el código del backend'
\echo ''
