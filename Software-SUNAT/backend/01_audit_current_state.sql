-- ==================================================================================
-- PASO 1: AUDITORÍA RÁPIDA DEL ESTADO ACTUAL
-- ==================================================================================
-- Descripción: Ejecuta esto primero para ver qué tienes en tu base de datos
-- Uso: psql -h localhost -U postgres -d crm_sunat -f 01_audit_current_state.sql
-- ==================================================================================

\echo '=========================================='
\echo 'AUDITANDO BASE DE DATOS CRM-SUNAT'
\echo '=========================================='
\echo ''

-- ==================================================================================
-- 1. VISTAS MATERIALIZADAS EXISTENTES
-- ==================================================================================
\echo '1. VISTAS MATERIALIZADAS:'
SELECT
    matviewname as nombre,
    CASE WHEN ispopulated THEN 'POBLADA' ELSE 'VACÍA' END as estado,
    pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as tamaño
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY matviewname;

\echo ''

-- ==================================================================================
-- 2. VISTAS NORMALES EXISTENTES
-- ==================================================================================
\echo '2. VISTAS NORMALES:'
SELECT viewname as nombre
FROM pg_views
WHERE schemaname = 'public'
ORDER BY viewname;

\echo ''

-- ==================================================================================
-- 3. TODOS LOS ÍNDICES EN ventas_sire
-- ==================================================================================
\echo '3. ÍNDICES EN ventas_sire:'
SELECT
    indexname as nombre,
    pg_size_pretty(pg_relation_size(indexrelid)) as tamaño,
    idx_scan as veces_usado
FROM pg_stat_user_indexes
WHERE tablename = 'ventas_sire'
    AND schemaname = 'public'
ORDER BY indexname;

\echo ''

-- ==================================================================================
-- 4. TODOS LOS ÍNDICES EN compras_sire
-- ==================================================================================
\echo '4. ÍNDICES EN compras_sire:'
SELECT
    indexname as nombre,
    pg_size_pretty(pg_relation_size(indexrelid)) as tamaño,
    idx_scan as veces_usado
FROM pg_stat_user_indexes
WHERE tablename = 'compras_sire'
    AND schemaname = 'public'
ORDER BY indexname;

\echo ''

-- ==================================================================================
-- 5. FUNCIONES RELACIONADAS
-- ==================================================================================
\echo '5. FUNCIONES DE REFRESH:'
SELECT proname as nombre
FROM pg_proc
WHERE pronamespace = 'public'::regnamespace
    AND (proname LIKE '%refresh%' OR proname LIKE '%ventas%')
ORDER BY proname;

\echo ''

-- ==================================================================================
-- 6. TAMAÑOS DE TABLAS PRINCIPALES
-- ==================================================================================
\echo '6. TAMAÑOS DE TABLAS:'
SELECT
    tablename as nombre,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) as tamaño_total,
    pg_size_pretty(pg_relation_size('public.'||tablename)) as solo_datos,
    pg_size_pretty(pg_total_relation_size('public.'||tablename) - pg_relation_size('public.'||tablename)) as solo_indices
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios', 'periodos_fallidos')
ORDER BY pg_total_relation_size('public.'||tablename) DESC;

\echo ''

-- ==================================================================================
-- 7. ÍNDICES NUNCA USADOS (CANDIDATOS A ELIMINAR)
-- ==================================================================================
\echo '7. ÍNDICES NUNCA USADOS (BASURA):'
SELECT
    tablename as tabla,
    indexname as indice,
    pg_size_pretty(pg_relation_size(indexrelid)) as tamaño_desperdiciado
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND idx_scan = 0
    AND indexrelname NOT LIKE '%pkey'
    AND tablename IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios')
ORDER BY pg_relation_size(indexrelid) DESC;

\echo ''

-- ==================================================================================
-- 8. VERIFICAR COLUMNAS estado1 Y estado2
-- ==================================================================================
\echo '8. COLUMNAS DE GESTIÓN EN ventas_sire:'
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'ventas_sire'
    AND column_name IN ('estado1', 'estado2', 'ultima_actualizacion')
ORDER BY column_name;

\echo ''

-- ==================================================================================
-- 9. RESUMEN DE REGISTROS
-- ==================================================================================
\echo '9. CONTEO DE REGISTROS:'
SELECT 'ventas_sire' as tabla, COUNT(*) as registros FROM ventas_sire
UNION ALL
SELECT 'compras_sire', COUNT(*) FROM compras_sire
UNION ALL
SELECT 'enrolados', COUNT(*) FROM enrolados
UNION ALL
SELECT 'usuarios', COUNT(*) FROM usuarios;

\echo ''
\echo '=========================================='
\echo 'AUDITORÍA COMPLETADA'
\echo 'Revisa los resultados y guárdalos'
\echo '=========================================='
