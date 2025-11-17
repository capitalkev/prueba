-- ==================================================================================
-- FIX: Corregir vista materializada ventas_backend
-- ==================================================================================
-- Descripción: Corrige el cálculo de notas de crédito en la vista materializada
-- Problema: Las notas de crédito deben restarse correctamente del total
-- Uso: psql -h localhost -U postgres -d crm_sunat -f fix_ventas_backend_view.sql
-- ==================================================================================

\echo '=========================================='
\echo 'CORRIGIENDO VISTA MATERIALIZADA ventas_backend'
\echo '=========================================='
\echo ''

-- ==================================================================================
-- 1. ELIMINAR VISTA MATERIALIZADA EXISTENTE
-- ==================================================================================
\echo '1. Eliminando vista materializada existente...'

DROP MATERIALIZED VIEW IF EXISTS ventas_backend CASCADE;

\echo '   ✓ Vista eliminada'
\echo ''

-- ==================================================================================
-- 2. CREAR VISTA MATERIALIZADA CORREGIDA
-- ==================================================================================
\echo '2. Creando vista materializada corregida...'

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
    -- CAMPOS CALCULADOS PARA NOTAS DE CRÉDITO (CORREGIDOS)
    -- ==================================================================================

    -- ¿Tiene nota de crédito asociada?
    CASE
        WHEN v.tipo_cp_doc = '1' THEN (
            SELECT COUNT(*) > 0
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.tipo_cp_doc = '7'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE false
    END as tiene_nota_credito,

    -- Monto total de notas de crédito (negativo, ya incluye el signo)
    CASE
        WHEN v.tipo_cp_doc = '1' THEN (
            SELECT COALESCE(SUM(nc.total_cp), 0)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.tipo_cp_doc = '7'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE 0
    END as monto_nota_credito,

    -- Total neto = total_cp + monto_nota_credito (NC ya viene con signo negativo)
    CASE
        WHEN v.tipo_cp_doc = '1' THEN
            v.total_cp + COALESCE((
                SELECT SUM(nc.total_cp)
                FROM ventas_sire nc
                WHERE nc.ruc = v.ruc
                AND nc.tipo_cp_doc = '7'
                AND nc.nro_cp_modificado = v.nro_cp_inicial
                AND nc.nro_doc_identidad = v.nro_doc_identidad
            ), 0)
        ELSE v.total_cp
    END as total_neto,

    -- Serie-Número de notas de crédito asociadas
    CASE
        WHEN v.tipo_cp_doc = '1' THEN (
            SELECT STRING_AGG(nc.serie_cdp || '-' || nc.nro_cp_inicial, ', ' ORDER BY nc.fecha_emision)
            FROM ventas_sire nc
            WHERE nc.ruc = v.ruc
            AND nc.tipo_cp_doc = '7'
            AND nc.nro_cp_modificado = v.nro_cp_inicial
            AND nc.nro_doc_identidad = v.nro_doc_identidad
        )
        ELSE NULL
    END as notas_credito_asociadas

FROM ventas_sire v
WHERE v.tipo_cp_doc IN ('1', '7')  -- Solo facturas y notas de crédito
    AND v.serie_cdp NOT LIKE 'B%'  -- Excluir boletas
    AND v.apellidos_nombres_razon_social != '-'
    AND v.apellidos_nombres_razon_social IS NOT NULL;

\echo '   ✓ Vista materializada corregida creada'
\echo ''

-- ==================================================================================
-- 3. CREAR ÍNDICES EN LA VISTA MATERIALIZADA
-- ==================================================================================
\echo '3. Creando índices en ventas_backend...'

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
CREATE INDEX idx_ventas_backend_con_nc ON ventas_backend(tiene_nota_credito) WHERE tipo_cp_doc = '1';

\echo '   ✓ Índices creados'
\echo ''

-- ==================================================================================
-- 4. POBLAR LA VISTA MATERIALIZADA
-- ==================================================================================
\echo '4. Poblando vista materializada (esto puede tardar)...'

REFRESH MATERIALIZED VIEW ventas_backend;

\echo '   ✓ Vista poblada exitosamente'
\echo ''

-- ==================================================================================
-- 5. ACTUALIZAR FUNCIÓN DE REFRESH
-- ==================================================================================
\echo '5. Actualizando función de refresh...'

CREATE OR REPLACE FUNCTION refresh_ventas_backend()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ventas_backend;
    RAISE NOTICE 'Vista ventas_backend refrescada exitosamente a las %', NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_ventas_backend() IS 'Refresca la vista materializada ventas_backend de forma concurrente (sin bloquear consultas)';

\echo '   ✓ Función refresh_ventas_backend() actualizada'
\echo ''

-- ==================================================================================
-- 6. ANÁLISIS DE ESTADÍSTICAS
-- ==================================================================================
\echo '6. Actualizando estadísticas...'

ANALYZE ventas_backend;

\echo '   ✓ Estadísticas actualizadas'
\echo ''

-- ==================================================================================
-- 7. VERIFICACIÓN FINAL
-- ==================================================================================
\echo '7. Verificando corrección...'
\echo ''

\echo 'Registros en ventas_backend:'
SELECT
    COUNT(*) as total_registros,
    COUNT(CASE WHEN tipo_cp_doc = '1' THEN 1 END) as facturas,
    COUNT(CASE WHEN tipo_cp_doc = '7' THEN 1 END) as notas_credito,
    COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as facturas_con_nc
FROM ventas_backend;

\echo ''
\echo 'Ejemplo de factura con nota de crédito (si existe):'
SELECT
    id,
    ruc,
    serie_cdp || '-' || nro_cp_inicial as factura,
    nro_doc_identidad as cliente,
    total_cp as monto_original,
    monto_nota_credito,
    total_neto,
    moneda,
    tiene_nota_credito,
    notas_credito_asociadas
FROM ventas_backend
WHERE tiene_nota_credito = true
LIMIT 5;

\echo ''
\echo '=========================================='
\echo 'VISTA MATERIALIZADA CORREGIDA CON ÉXITO'
\echo '=========================================='
\echo ''
\echo 'NOTAS IMPORTANTES:'
\echo '- Las notas de crédito vienen con valor NEGATIVO de SUNAT'
\echo '- El cálculo total_neto = total_cp + monto_nota_credito es correcto'
\echo '- Si total_cp = 38940.00 y NC = -12154.13, total_neto = 26785.87'
\echo ''
\echo 'SIGUIENTE PASO:'
\echo 'Refrescar la vista después de cada carga de datos SUNAT:'
\echo '  SELECT refresh_ventas_backend();'
\echo ''
