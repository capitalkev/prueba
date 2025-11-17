-- ==================================================================================
-- PASO 2: LIMPIEZA DE ÍNDICES Y TABLAS BASURA
-- ==================================================================================
-- Descripción: Elimina vistas materializadas, índices y funciones obsoletas
-- IMPORTANTE: Ejecutar solo después de revisar el resultado de 01_audit_current_state.sql
-- Uso: psql -h localhost -U postgres -d crm_sunat -f 02_cleanup_garbage.sql
-- ==================================================================================

\echo '=========================================='
\echo 'INICIANDO LIMPIEZA DE BASE DE DATOS'
\echo '=========================================='
\echo ''

-- ==================================================================================
-- 1. ELIMINAR VISTAS MATERIALIZADAS ANTIGUAS (si existen)
-- ==================================================================================
\echo '1. Eliminando vistas materializadas antiguas...'

DROP MATERIALIZED VIEW IF EXISTS ventas_backend CASCADE;
DROP MATERIALIZED VIEW IF EXISTS compras_backend CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_ventas_metricas CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_compras_metricas CASCADE;

\echo '   ✓ Vistas materializadas eliminadas'
\echo ''

-- ==================================================================================
-- 2. ELIMINAR VISTAS NORMALES ANTIGUAS (si existen)
-- ==================================================================================
\echo '2. Eliminando vistas normales antiguas...'

DROP VIEW IF EXISTS ventas_metricas_dashboard CASCADE;
DROP VIEW IF EXISTS compras_metricas_dashboard CASCADE;
DROP VIEW IF EXISTS v_ventas_dashboard CASCADE;
DROP VIEW IF EXISTS v_compras_dashboard CASCADE;

\echo '   ✓ Vistas normales eliminadas'
\echo ''

-- ==================================================================================
-- 3. ELIMINAR FUNCIONES DE REFRESH ANTIGUAS
-- ==================================================================================
\echo '3. Eliminando funciones obsoletas...'

DROP FUNCTION IF EXISTS refresh_ventas_backend() CASCADE;
DROP FUNCTION IF EXISTS refresh_compras_backend() CASCADE;
DROP FUNCTION IF EXISTS refresh_all_materialized_views() CASCADE;

\echo '   ✓ Funciones eliminadas'
\echo ''

-- ==================================================================================
-- 4. ELIMINAR ÍNDICES DUPLICADOS O INNECESARIOS EN ventas_sire
-- ==================================================================================
\echo '4. Limpiando índices en ventas_sire...'

-- Nota: Los índices se eliminan solo si NO son los principales
-- Mantener solo: idx_ventas_ruc_periodo, idx_ventas_cliente, idx_ventas_fecha, idx_ventas_estado1

-- Eliminar índices parciales antiguos o duplicados si existen
DROP INDEX IF EXISTS idx_ventas_estado2;
DROP INDEX IF EXISTS idx_ventas_backend_id;
DROP INDEX IF EXISTS idx_ventas_backend_ruc_periodo;
DROP INDEX IF EXISTS idx_ventas_backend_tipo_doc;
DROP INDEX IF EXISTS idx_ventas_backend_estado1;
DROP INDEX IF EXISTS idx_ventas_backend_estado2;
DROP INDEX IF EXISTS idx_ventas_backend_anulada;
DROP INDEX IF EXISTS idx_ventas_backend_fecha;
DROP INDEX IF EXISTS idx_ventas_backend_cliente;
DROP INDEX IF EXISTS idx_ventas_backend_moneda;
DROP INDEX IF EXISTS idx_ventas_backend_metrics;

\echo '   ✓ Índices obsoletos eliminados'
\echo ''

-- ==================================================================================
-- 5. ELIMINAR ÍNDICES DUPLICADOS O INNECESARIOS EN compras_sire
-- ==================================================================================
\echo '5. Limpiando índices en compras_sire...'

-- Mantener solo: idx_compras_ruc_periodo, idx_compras_proveedor, idx_compras_fecha

DROP INDEX IF EXISTS idx_compras_estado1;
DROP INDEX IF EXISTS idx_compras_estado2;

\echo '   ✓ Índices obsoletos eliminados'
\echo ''

-- ==================================================================================
-- 6. ELIMINAR TRIGGERS ANTIGUOS (si existen)
-- ==================================================================================
\echo '6. Eliminando triggers obsoletos...'

DROP TRIGGER IF EXISTS trigger_refresh_ventas_backend ON ventas_sire;
DROP TRIGGER IF EXISTS trigger_refresh_compras_backend ON compras_sire;

\echo '   ✓ Triggers eliminados'
\echo ''

-- ==================================================================================
-- 7. VACUUM PARA RECUPERAR ESPACIO
-- ==================================================================================
\echo '7. Ejecutando VACUUM para recuperar espacio...'

VACUUM ANALYZE ventas_sire;
VACUUM ANALYZE compras_sire;
VACUUM ANALYZE enrolados;
VACUUM ANALYZE usuarios;

\echo '   ✓ VACUUM completado'
\echo ''

-- ==================================================================================
-- 8. VERIFICAR ESTADO DESPUÉS DE LIMPIEZA
-- ==================================================================================
\echo '8. Verificando estado después de limpieza...'
\echo ''

\echo 'Vistas materializadas restantes:'
SELECT matviewname FROM pg_matviews WHERE schemaname = 'public';

\echo ''
\echo 'Vistas normales restantes:'
SELECT viewname FROM pg_views WHERE schemaname = 'public';

\echo ''
\echo 'Funciones restantes:'
SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace ORDER BY proname;

\echo ''
\echo 'Índices en ventas_sire:'
SELECT indexname FROM pg_indexes WHERE tablename = 'ventas_sire' AND schemaname = 'public' ORDER BY indexname;

\echo ''
\echo 'Índices en compras_sire:'
SELECT indexname FROM pg_indexes WHERE tablename = 'compras_sire' AND schemaname = 'public' ORDER BY indexname;

\echo ''
\echo '=========================================='
\echo 'LIMPIEZA COMPLETADA'
\echo 'Base de datos lista para nuevas mejoras'
\echo '=========================================='
