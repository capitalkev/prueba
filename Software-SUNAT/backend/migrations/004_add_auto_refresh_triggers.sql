-- =====================================================================
-- Migration: Triggers para Auto-Refresh de Materialized Views
-- Fecha: 2025-11-11
-- Descripción: Actualiza automáticamente las MVs cuando se insertan datos
-- Ventaja: No necesita cron jobs, se actualiza en tiempo real
-- =====================================================================

BEGIN;

-- =====================================================================
-- OPCIÓN 1: Refresh Incremental con Triggers (RECOMENDADO)
-- =====================================================================
-- Actualiza la MV solo cuando se insertan/actualizan datos en ventas_sire

-- Tabla de control para evitar múltiples refreshes simultáneos
CREATE TABLE IF NOT EXISTS mv_refresh_log (
    id SERIAL PRIMARY KEY,
    view_name VARCHAR(100) NOT NULL,
    last_refresh TIMESTAMP NOT NULL DEFAULT NOW(),
    refresh_duration_ms INTEGER,
    rows_affected INTEGER,
    triggered_by VARCHAR(50)
);

-- Función que hace refresh CONCURRENTE (no bloquea lecturas)
CREATE OR REPLACE FUNCTION auto_refresh_metricas_mv()
RETURNS TRIGGER AS $$
DECLARE
    last_refresh_time TIMESTAMP;
    time_diff_minutes INTEGER;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    -- Obtener última actualización
    SELECT last_refresh INTO last_refresh_time
    FROM mv_refresh_log
    WHERE view_name = 'mv_metricas_diarias'
    ORDER BY last_refresh DESC
    LIMIT 1;

    -- Si no existe registro o han pasado más de 5 minutos, hacer refresh
    time_diff_minutes := EXTRACT(EPOCH FROM (NOW() - COALESCE(last_refresh_time, NOW() - INTERVAL '1 hour'))) / 60;

    IF time_diff_minutes >= 5 THEN
        start_time := clock_timestamp();

        -- Refresh concurrente (no bloquea)
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_metricas_diarias;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_metricas_mensuales;

        end_time := clock_timestamp();

        -- Registrar la actualización
        INSERT INTO mv_refresh_log (view_name, last_refresh, refresh_duration_ms, triggered_by)
        VALUES (
            'mv_metricas_diarias',
            end_time,
            EXTRACT(MILLISECONDS FROM (end_time - start_time))::INTEGER,
            TG_OP
        );

        RAISE NOTICE 'Materialized views actualizadas automáticamente en % ms',
            EXTRACT(MILLISECONDS FROM (end_time - start_time))::INTEGER;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger AFTER INSERT (cuando se suben nuevos datos)
DROP TRIGGER IF EXISTS trigger_refresh_metricas_on_insert ON ventas_sire;

CREATE TRIGGER trigger_refresh_metricas_on_insert
    AFTER INSERT ON ventas_sire
    FOR EACH STATEMENT  -- Se ejecuta UNA vez por batch, no por cada fila
    EXECUTE FUNCTION auto_refresh_metricas_mv();

-- Trigger AFTER UPDATE (cuando se actualizan estados)
DROP TRIGGER IF EXISTS trigger_refresh_metricas_on_update ON ventas_sire;

CREATE TRIGGER trigger_refresh_metricas_on_update
    AFTER UPDATE OF estado1, estado2 ON ventas_sire
    FOR EACH STATEMENT
    EXECUTE FUNCTION auto_refresh_metricas_mv();

COMMENT ON FUNCTION auto_refresh_metricas_mv() IS
'Auto-actualiza MVs cuando se insertan/actualizan ventas. Throttle de 5 minutos.';

-- =====================================================================
-- OPCIÓN 2: pg_cron (SI ESTÁ DISPONIBLE EN CLOUD SQL)
-- =====================================================================
-- Ejecutar cada hora automáticamente usando pg_cron

-- Verificar si pg_cron está disponible
DO $$
BEGIN
    -- Intentar crear job de pg_cron
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        -- Eliminar job anterior si existe
        PERFORM cron.unschedule('refresh-metricas-hourly');

        -- Crear job que se ejecuta cada hora
        PERFORM cron.schedule(
            'refresh-metricas-hourly',
            '0 * * * *',  -- Cada hora en punto
            'SELECT refresh_metricas_views();'
        );

        RAISE NOTICE 'pg_cron job configurado: actualización cada hora';
    ELSE
        RAISE NOTICE 'pg_cron no está disponible. Usando solo triggers.';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'No se pudo configurar pg_cron: %. Usando solo triggers.', SQLERRM;
END $$;

-- =====================================================================
-- ÍNDICES ÚNICOS NECESARIOS PARA REFRESH CONCURRENTE
-- =====================================================================
-- REFRESH MATERIALIZED VIEW CONCURRENTLY requiere índice único

-- Para mv_metricas_diarias
DROP INDEX IF EXISTS idx_mv_metricas_diarias_unique;
CREATE UNIQUE INDEX idx_mv_metricas_diarias_unique
ON mv_metricas_diarias (fecha_emision, ruc, moneda);

-- Para mv_metricas_mensuales
DROP INDEX IF EXISTS idx_mv_metricas_mensuales_unique;
CREATE UNIQUE INDEX idx_mv_metricas_mensuales_unique
ON mv_metricas_mensuales (mes, ruc, moneda);

COMMIT;

-- =====================================================================
-- VERIFICACIÓN Y TESTING
-- =====================================================================

-- 1. Ver configuración de triggers
SELECT
    trigger_name,
    event_manipulation,
    action_timing,
    event_object_table
FROM information_schema.triggers
WHERE event_object_table = 'ventas_sire'
ORDER BY trigger_name;

-- 2. Ver último refresh
SELECT
    view_name,
    last_refresh,
    refresh_duration_ms,
    triggered_by
FROM mv_refresh_log
ORDER BY last_refresh DESC
LIMIT 10;

-- 3. Ver jobs de pg_cron (si está disponible)
SELECT * FROM cron.job WHERE jobname LIKE '%metricas%';

-- 4. Test manual: Insertar datos de prueba y ver si se actualiza
-- (NO ejecutar en producción, solo para testing)
/*
INSERT INTO ventas_sire (
    ruc, periodo, fecha_emision, tipo_cp_doc, serie_cdp,
    nro_cp_inicial, moneda, total_cp, estado1
) VALUES (
    '20612595594', '202511', CURRENT_DATE, '01', 'F001',
    '00000001', 'PEN', 1000.00, NULL
);

-- Esperar 5 segundos y verificar log
SELECT * FROM mv_refresh_log ORDER BY last_refresh DESC LIMIT 1;
*/

-- =====================================================================
-- MONITOREO Y MANTENIMIENTO
-- =====================================================================

-- Query para ver performance de refreshes
CREATE OR REPLACE VIEW v_mv_refresh_stats AS
SELECT
    view_name,
    COUNT(*) as total_refreshes,
    AVG(refresh_duration_ms) as avg_duration_ms,
    MAX(refresh_duration_ms) as max_duration_ms,
    MIN(refresh_duration_ms) as min_duration_ms,
    MAX(last_refresh) as last_refresh
FROM mv_refresh_log
GROUP BY view_name;

-- Ver estadísticas
SELECT * FROM v_mv_refresh_stats;

-- Limpiar logs antiguos (más de 30 días)
CREATE OR REPLACE FUNCTION cleanup_mv_refresh_log()
RETURNS void AS $$
BEGIN
    DELETE FROM mv_refresh_log
    WHERE last_refresh < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ROLLBACK (Si necesitas revertir)
-- =====================================================================

/*
BEGIN;

-- Eliminar triggers
DROP TRIGGER IF EXISTS trigger_refresh_metricas_on_insert ON ventas_sire;
DROP TRIGGER IF EXISTS trigger_refresh_metricas_on_update ON ventas_sire;

-- Eliminar función
DROP FUNCTION IF EXISTS auto_refresh_metricas_mv() CASCADE;

-- Eliminar tabla de log
DROP TABLE IF EXISTS mv_refresh_log CASCADE;

-- Eliminar vista de stats
DROP VIEW IF EXISTS v_mv_refresh_stats CASCADE;

-- Eliminar job de pg_cron (si existe)
SELECT cron.unschedule('refresh-metricas-hourly');

COMMIT;
*/

-- =====================================================================
-- NOTAS DE IMPLEMENTACIÓN
-- =====================================================================

/*
CÓMO FUNCIONA:

1. TRIGGERS:
   - Se ejecutan automáticamente cuando se insertan/actualizan datos
   - Tienen throttle de 5 minutos (no refresh cada segundo)
   - Usan REFRESH CONCURRENTLY (no bloquea lecturas)
   - FOR EACH STATEMENT (eficiente para inserts masivos)

2. THROTTLE DE 5 MINUTOS:
   - Si subes datos cada hora, el refresh se ejecutará 1 vez por hora
   - Si subes datos más frecuente, máximo 1 refresh cada 5 minutos
   - Evita sobrecarga en la BD

3. LOGGING:
   - Tabla mv_refresh_log registra cada actualización
   - Útil para monitorear performance y troubleshooting
   - Se puede limpiar automáticamente cada 30 días

4. BACKUP CON pg_cron:
   - Si pg_cron está disponible, se configura como backup
   - Se ejecuta cada hora como red de seguridad
   - Independiente de los triggers

VENTAJAS:
- ✅ Completamente automático
- ✅ No necesita cron jobs externos
- ✅ Se actualiza cuando hay nuevos datos
- ✅ Throttle evita sobrecarga
- ✅ CONCURRENTLY no bloquea usuarios

LIMITACIONES:
- Refresh toma 1-5 segundos (aceptable)
- Datos pueden tener hasta 5 minutos de "retraso"
- Si subes 100k registros a la vez, el refresh será al final del batch

ALTERNATIVA SI NO FUNCIONA:
Si los triggers causan problemas, puedes ejecutar manualmente:
  SELECT refresh_metricas_views();

O configurar Cloud Scheduler:
  gcloud scheduler jobs create http refresh-metricas \
    --schedule="0 * * * *" \
    --uri="https://backend-url/api/admin/refresh-metricas"
*/
