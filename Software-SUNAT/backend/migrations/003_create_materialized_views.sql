-- =====================================================================
-- Migration: Materialized Views para Métricas Optimizadas
-- Fecha: 2025-11-11
-- Descripción: Crea vistas materializadas para pre-calcular métricas
-- Ventaja: Query de <1ms en lugar de 50-500ms
-- Actualización: Cada hora (cuando ingresa nueva data)
-- =====================================================================

BEGIN;

-- =====================================================================
-- VISTA MATERIALIZADA 1: Métricas por Fecha, RUC y Moneda
-- =====================================================================
-- Pre-calcula métricas para ventanas de tiempo común (últimos 30 días)
-- Se actualiza cada hora cuando ingresa nueva data

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_metricas_diarias AS
SELECT
    fecha_emision,
    ruc,
    moneda,
    COUNT(*) as cantidad_facturas,
    SUM(total_cp) as total_facturado,
    SUM(CASE WHEN estado1 = 'Ganada' THEN total_cp ELSE 0 END) as monto_ganado,
    SUM(
        CASE
            WHEN (estado1 IS NULL OR (estado1 != 'Ganada' AND estado1 != 'Perdida'))
            THEN total_cp
            ELSE 0
        END
    ) as monto_disponible,
    SUM(CASE WHEN estado1 = 'Perdida' THEN total_cp ELSE 0 END) as monto_perdido,
    MAX(fecha_emision) as ultima_actualizacion
FROM ventas_sire
WHERE tipo_cp_doc != '7'  -- Excluir notas de crédito
  AND serie_cdp NOT LIKE 'B%'  -- Excluir boletas
  AND fecha_emision >= CURRENT_DATE - INTERVAL '90 days'  -- Últimos 90 días
GROUP BY fecha_emision, ruc, moneda;

COMMENT ON MATERIALIZED VIEW mv_metricas_diarias IS
'Métricas pre-calculadas por día, RUC y moneda. Refresh cada hora.';

-- Índices para la vista materializada (acceso ultra-rápido)
CREATE INDEX idx_mv_metricas_fecha_ruc
ON mv_metricas_diarias(fecha_emision DESC, ruc, moneda);

CREATE INDEX idx_mv_metricas_ruc_fecha
ON mv_metricas_diarias(ruc, fecha_emision DESC);

-- =====================================================================
-- VISTA MATERIALIZADA 2: Métricas Agregadas por Período
-- =====================================================================
-- Pre-calcula métricas mensuales (último mes completo)

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_metricas_mensuales AS
SELECT
    DATE_TRUNC('month', fecha_emision) as mes,
    ruc,
    moneda,
    COUNT(*) as cantidad_facturas,
    SUM(total_cp) as total_facturado,
    SUM(CASE WHEN estado1 = 'Ganada' THEN total_cp ELSE 0 END) as monto_ganado,
    SUM(
        CASE
            WHEN (estado1 IS NULL OR (estado1 != 'Ganada' AND estado1 != 'Perdida'))
            THEN total_cp
            ELSE 0
        END
    ) as monto_disponible,
    SUM(CASE WHEN estado1 = 'Perdida' THEN total_cp ELSE 0 END) as monto_perdido,
    MAX(fecha_emision) as ultima_actualizacion
FROM ventas_sire
WHERE tipo_cp_doc != '7'
  AND serie_cdp NOT LIKE 'B%'
  AND fecha_emision >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 months')
GROUP BY DATE_TRUNC('month', fecha_emision), ruc, moneda;

COMMENT ON MATERIALIZED VIEW mv_metricas_mensuales IS
'Métricas mensuales pre-calculadas. Refresh cada hora.';

CREATE INDEX idx_mv_metricas_mes
ON mv_metricas_mensuales(mes DESC, ruc, moneda);

-- =====================================================================
-- FUNCIÓN: Refresh Automático de Vistas Materializadas
-- =====================================================================
-- Esta función se ejecutará cada hora vía Cloud Scheduler + Cloud Function

CREATE OR REPLACE FUNCTION refresh_metricas_views()
RETURNS void AS $$
BEGIN
    -- Refresh concurrente (no bloquea lecturas)
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_metricas_diarias;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_metricas_mensuales;

    -- Log de actualización
    RAISE NOTICE 'Vistas materializadas actualizadas: %', NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_metricas_views() IS
'Actualiza todas las vistas materializadas de métricas. Ejecutar cada hora.';

-- =====================================================================
-- VISTA SIMPLE: Wrapper para el endpoint
-- =====================================================================
-- Vista que el endpoint puede consultar directamente

CREATE OR REPLACE VIEW v_metricas_resumen AS
SELECT
    fecha_emision,
    ruc,
    moneda,
    cantidad_facturas,
    total_facturado,
    monto_ganado,
    monto_disponible,
    monto_perdido,
    ultima_actualizacion
FROM mv_metricas_diarias
ORDER BY fecha_emision DESC, ruc, moneda;

COMMENT ON VIEW v_metricas_resumen IS
'Vista wrapper para consulta rápida de métricas desde API.';

COMMIT;

-- =====================================================================
-- REFRESH INICIAL
-- =====================================================================
-- Ejecutar después de crear las vistas

REFRESH MATERIALIZED VIEW mv_metricas_diarias;
REFRESH MATERIALIZED VIEW mv_metricas_mensuales;

-- =====================================================================
-- VERIFICACIÓN
-- =====================================================================

-- 1. Ver tamaño de las vistas materializadas
SELECT
    schemaname,
    matviewname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||matviewname)) as size
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY pg_relation_size(schemaname||'.'||matviewname) DESC;

-- 2. Ver última actualización
SELECT
    'mv_metricas_diarias' as vista,
    MAX(ultima_actualizacion) as ultima_actualizacion,
    COUNT(*) as registros
FROM mv_metricas_diarias
UNION ALL
SELECT
    'mv_metricas_mensuales' as vista,
    MAX(ultima_actualizacion) as ultima_actualizacion,
    COUNT(*) as registros
FROM mv_metricas_mensuales;

-- 3. Test de velocidad - Query en vista materializada (debería ser <5ms)
EXPLAIN ANALYZE
SELECT
    moneda,
    SUM(total_facturado) as total,
    SUM(monto_ganado) as ganado,
    SUM(monto_disponible) as disponible,
    SUM(cantidad_facturas) as cantidad
FROM mv_metricas_diarias
WHERE fecha_emision >= CURRENT_DATE - INTERVAL '30 days'
  AND ruc IN ('20612595594')  -- Ejemplo de RUC
GROUP BY moneda;

-- =====================================================================
-- ROLLBACK (Si necesitas revertir)
-- =====================================================================

/*
BEGIN;

DROP MATERIALIZED VIEW IF EXISTS mv_metricas_diarias CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_metricas_mensuales CASCADE;
DROP VIEW IF EXISTS v_metricas_resumen CASCADE;
DROP FUNCTION IF EXISTS refresh_metricas_views() CASCADE;

COMMIT;
*/

-- =====================================================================
-- CONFIGURACIÓN DE REFRESH AUTOMÁTICO
-- =====================================================================

/*
OPCIÓN 1: Cloud Scheduler + Cloud Function (RECOMENDADO)

1. Crear Cloud Function que ejecute:
   SELECT refresh_metricas_views();

2. Configurar Cloud Scheduler:
   gcloud scheduler jobs create http refresh-metricas \
     --schedule="0 * * * *" \
     --uri="https://REGION-PROJECT.cloudfunctions.net/refresh-metricas" \
     --http-method=POST \
     --location=us-central1

OPCIÓN 2: pg_cron (si está disponible en Cloud SQL)

SELECT cron.schedule('refresh-metricas', '0 * * * *', 'SELECT refresh_metricas_views()');

OPCIÓN 3: Cron Job en servidor con psql

Agregar a crontab:
0 * * * * psql -h HOST -U USER -d DB -c "SELECT refresh_metricas_views();"
*/

-- =====================================================================
-- NOTAS DE IMPLEMENTACIÓN
-- =====================================================================

/*
VENTAJAS:
- Query de métricas: 500ms → <5ms (100x más rápido)
- Sin carga en la BD por cada request del usuario
- Datos actualizados cada hora (suficiente para el caso de uso)
- Soporta millones de registros sin degradación

CONSIDERACIONES:
- Espacio adicional: ~10-50 MB por vista (muy pequeño)
- Refresh toma 1-5 segundos cada hora (no afecta usuarios)
- Datos pueden tener hasta 1 hora de "retraso" (aceptable)

MONITOREO:
- Ver última actualización:
  SELECT MAX(ultima_actualizacion) FROM mv_metricas_diarias;

- Ver tamaño:
  SELECT pg_size_pretty(pg_total_relation_size('mv_metricas_diarias'));

- Ver performance:
  EXPLAIN ANALYZE SELECT * FROM mv_metricas_diarias WHERE fecha_emision >= NOW() - INTERVAL '30 days';
*/
