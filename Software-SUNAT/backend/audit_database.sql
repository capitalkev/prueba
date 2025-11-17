-- ==================================================================================
-- SCRIPT DE AUDITORÍA COMPLETA - BASE DE DATOS CRM-SUNAT
-- ==================================================================================
-- Descripción: Queries para verificar qué índices, vistas materializadas y
--              optimizaciones tienes actualmente en tu base de datos
-- Fecha: 2025-11-16
-- Uso: Ejecutar cada query por separado y revisar los resultados
-- ==================================================================================

-- ==================================================================================
-- 1. VERIFICAR TODAS LAS TABLAS EXISTENTES
-- ==================================================================================

SELECT
    schemaname,
    tablename,
    tableowner,
    tablespace,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- ==================================================================================
-- 2. VERIFICAR VISTAS MATERIALIZADAS
-- ==================================================================================

SELECT
    schemaname,
    matviewname as nombre_vista,
    matviewowner as propietario,
    tablespace,
    hasindexes as tiene_indices,
    ispopulated as esta_poblada,
    definition as definicion
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY matviewname;

-- ==================================================================================
-- 3. VERIFICAR TODAS LAS VISTAS NORMALES
-- ==================================================================================

SELECT
    schemaname,
    viewname as nombre_vista,
    viewowner as propietario,
    definition as definicion
FROM pg_views
WHERE schemaname = 'public'
ORDER BY viewname;

-- ==================================================================================
-- 4. VERIFICAR ÍNDICES EN LA TABLA ventas_sire
-- ==================================================================================

SELECT
    indexname as nombre_indice,
    indexdef as definicion,
    tablespace
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename = 'ventas_sire'
ORDER BY indexname;

-- ==================================================================================
-- 5. VERIFICAR ÍNDICES EN LA TABLA compras_sire
-- ==================================================================================

SELECT
    indexname as nombre_indice,
    indexdef as definicion,
    tablespace
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename = 'compras_sire'
ORDER BY indexname;

-- ==================================================================================
-- 6. VERIFICAR ÍNDICES EN LA VISTA MATERIALIZADA ventas_backend (si existe)
-- ==================================================================================

SELECT
    indexname as nombre_indice,
    indexdef as definicion,
    tablespace
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename = 'ventas_backend'
ORDER BY indexname;

-- ==================================================================================
-- 7. VERIFICAR TODOS LOS ÍNDICES DE TODAS LAS TABLAS
-- ==================================================================================

SELECT
    t.tablename as tabla,
    i.indexname as nombre_indice,
    i.indexdef as definicion,
    pg_size_pretty(pg_relation_size(i.indexname::regclass)) as tamaño
FROM pg_indexes i
JOIN pg_tables t ON i.tablename = t.tablename
WHERE t.schemaname = 'public'
    AND t.tablename IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios', 'periodos_fallidos', 'ventas_backend')
ORDER BY t.tablename, i.indexname;

-- ==================================================================================
-- 8. VERIFICAR FUNCIONES RELACIONADAS CON VISTAS MATERIALIZADAS
-- ==================================================================================

SELECT
    n.nspname as schema,
    p.proname as nombre_funcion,
    pg_get_function_result(p.oid) as tipo_retorno,
    pg_get_functiondef(p.oid) as definicion
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
    AND p.proname LIKE '%refresh%'
    OR p.proname LIKE '%ventas%'
    OR p.proname LIKE '%backend%'
ORDER BY p.proname;

-- ==================================================================================
-- 9. VERIFICAR TRIGGERS (para auto-refresh de vistas)
-- ==================================================================================

SELECT
    event_object_table as tabla,
    trigger_name as nombre_trigger,
    event_manipulation as evento,
    action_statement as accion,
    action_timing as momento
FROM information_schema.triggers
WHERE event_object_schema = 'public'
ORDER BY event_object_table, trigger_name;

-- ==================================================================================
-- 10. ESTADÍSTICAS DE TAMAÑO DE TABLAS Y VISTAS
-- ==================================================================================

SELECT
    schemaname,
    tablename as nombre,
    'table' as tipo,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamaño_total,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as tamaño_datos,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as tamaño_indices
FROM pg_tables
WHERE schemaname = 'public'
UNION ALL
SELECT
    schemaname,
    matviewname as nombre,
    'materialized view' as tipo,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as tamaño_total,
    pg_size_pretty(pg_relation_size(schemaname||'.'||matviewname)) as tamaño_datos,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname) - pg_relation_size(schemaname||'.'||matviewname)) as tamaño_indices
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY tipo, tamaño_total DESC;

-- ==================================================================================
-- 11. VERIFICAR SI EXISTE LA VISTA ventas_backend
-- ==================================================================================

SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_matviews
            WHERE schemaname = 'public'
            AND matviewname = 'ventas_backend'
        ) THEN 'SÍ - Vista Materializada'
        WHEN EXISTS (
            SELECT 1 FROM pg_views
            WHERE schemaname = 'public'
            AND viewname = 'ventas_backend'
        ) THEN 'SÍ - Vista Normal'
        WHEN EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'ventas_backend'
        ) THEN 'SÍ - Tabla Normal'
        ELSE 'NO EXISTE'
    END as existe_ventas_backend;

-- ==================================================================================
-- 12. VERIFICAR SI EXISTE LA VISTA ventas_metricas_dashboard
-- ==================================================================================

SELECT
    CASE
        WHEN EXISTS (
            SELECT 1 FROM pg_matviews
            WHERE schemaname = 'public'
            AND matviewname = 'ventas_metricas_dashboard'
        ) THEN 'SÍ - Vista Materializada'
        WHEN EXISTS (
            SELECT 1 FROM pg_views
            WHERE schemaname = 'public'
            AND viewname = 'ventas_metricas_dashboard'
        ) THEN 'SÍ - Vista Normal'
        WHEN EXISTS (
            SELECT 1 FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'ventas_metricas_dashboard'
        ) THEN 'SÍ - Tabla Normal'
        ELSE 'NO EXISTE'
    END as existe_metricas_dashboard;

-- ==================================================================================
-- 13. CONTAR REGISTROS EN TABLAS PRINCIPALES
-- ==================================================================================

SELECT
    'ventas_sire' as tabla,
    COUNT(*) as total_registros,
    COUNT(DISTINCT ruc) as total_rucs,
    COUNT(DISTINCT periodo) as total_periodos,
    MIN(fecha_emision) as fecha_mas_antigua,
    MAX(fecha_emision) as fecha_mas_reciente
FROM ventas_sire
UNION ALL
SELECT
    'compras_sire' as tabla,
    COUNT(*) as total_registros,
    COUNT(DISTINCT ruc) as total_rucs,
    COUNT(DISTINCT periodo) as total_periodos,
    MIN(fecha_emision) as fecha_mas_antigua,
    MAX(fecha_emision) as fecha_mas_reciente
FROM compras_sire;

-- ==================================================================================
-- 14. SI EXISTE ventas_backend, CONTAR REGISTROS
-- ==================================================================================

-- Ejecutar solo si la vista existe (verificar primero con query #11)
-- Descomentar si ventas_backend existe:
/*
SELECT
    'ventas_backend' as vista,
    COUNT(*) as total_registros,
    COUNT(DISTINCT ruc) as total_rucs,
    COUNT(DISTINCT periodo) as total_periodos,
    MIN(fecha_emision) as fecha_mas_antigua,
    MAX(fecha_emision) as fecha_mas_reciente,
    COUNT(CASE WHEN esta_anulada = true THEN 1 END) as total_anuladas,
    COUNT(CASE WHEN tipo_cp_doc = '01' THEN 1 END) as total_facturas,
    COUNT(CASE WHEN tipo_cp_doc = '07' THEN 1 END) as total_notas_credito
FROM ventas_backend;
*/

-- ==================================================================================
-- 15. VERIFICAR COLUMNAS estado1 Y estado2 EN ventas_sire
-- ==================================================================================

SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name = 'ventas_sire'
    AND column_name IN ('estado1', 'estado2')
ORDER BY column_name;

-- ==================================================================================
-- 16. VERIFICAR ÍNDICES PARCIALES (con WHERE clause)
-- ==================================================================================

SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND indexdef LIKE '%WHERE%'
ORDER BY tablename, indexname;

-- ==================================================================================
-- 17. VERIFICAR ÚLTIMA ACTUALIZACIÓN DE VISTAS MATERIALIZADAS
-- ==================================================================================

-- PostgreSQL no guarda timestamp de última actualización, pero podemos ver stats
SELECT
    schemaname,
    matviewname,
    CASE
        WHEN ispopulated THEN 'Poblada'
        ELSE 'Vacía - necesita REFRESH'
    END as estado,
    hasindexes,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as tamaño
FROM pg_matviews
WHERE schemaname = 'public';

-- ==================================================================================
-- 18. VERIFICAR CONSTRAINTS Y CHECKS EN TABLAS
-- ==================================================================================

SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    CASE tc.constraint_type
        WHEN 'PRIMARY KEY' THEN (
            SELECT string_agg(kcu.column_name, ', ')
            FROM information_schema.key_column_usage kcu
            WHERE kcu.constraint_name = tc.constraint_name
        )
        WHEN 'FOREIGN KEY' THEN (
            SELECT string_agg(kcu.column_name, ', ')
            FROM information_schema.key_column_usage kcu
            WHERE kcu.constraint_name = tc.constraint_name
        )
        WHEN 'UNIQUE' THEN (
            SELECT string_agg(kcu.column_name, ', ')
            FROM information_schema.key_column_usage kcu
            WHERE kcu.constraint_name = tc.constraint_name
        )
        ELSE NULL
    END as columnas
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public'
    AND tc.table_name IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios')
ORDER BY tc.table_name, tc.constraint_type;

-- ==================================================================================
-- 19. ANÁLISIS DE PERFORMANCE - Índices más usados
-- ==================================================================================

SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as veces_usado,
    idx_tup_read as tuplas_leidas,
    idx_tup_fetch as tuplas_obtenidas,
    pg_size_pretty(pg_relation_size(indexrelid)) as tamaño_indice
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND tablename IN ('ventas_sire', 'compras_sire', 'ventas_backend')
ORDER BY idx_scan DESC;

-- ==================================================================================
-- 20. ÍNDICES NO USADOS (candidatos para eliminar)
-- ==================================================================================

SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as veces_usado,
    pg_size_pretty(pg_relation_size(indexrelid)) as tamaño_desperdiciado
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
    AND idx_scan = 0  -- Nunca usado
    AND indexrelname NOT LIKE '%pkey'  -- Excluir primary keys
ORDER BY pg_relation_size(indexrelid) DESC;

-- ==================================================================================
-- 21. VERIFICAR SECUENCIAS (para IDs autoincrementales)
-- ==================================================================================

SELECT
    schemaname,
    sequencename,
    last_value as ultimo_valor,
    min_value,
    max_value,
    increment_by,
    cycle
FROM pg_sequences
WHERE schemaname = 'public'
ORDER BY sequencename;

-- ==================================================================================
-- 22. RESUMEN EJECUTIVO - TODO EN UNO
-- ==================================================================================

WITH tabla_stats AS (
    SELECT 'ventas_sire' as nombre, COUNT(*) as registros FROM ventas_sire
    UNION ALL
    SELECT 'compras_sire', COUNT(*) FROM compras_sire
    UNION ALL
    SELECT 'enrolados', COUNT(*) FROM enrolados
    UNION ALL
    SELECT 'usuarios', COUNT(*) FROM usuarios
),
vista_exists AS (
    SELECT
        (SELECT COUNT(*) FROM pg_matviews WHERE matviewname = 'ventas_backend') as ventas_backend_mv,
        (SELECT COUNT(*) FROM pg_views WHERE viewname = 'ventas_metricas_dashboard') as metricas_dash_v
),
indice_count AS (
    SELECT tablename, COUNT(*) as num_indices
    FROM pg_indexes
    WHERE schemaname = 'public'
        AND tablename IN ('ventas_sire', 'compras_sire', 'ventas_backend')
    GROUP BY tablename
)
SELECT
    '=== RESUMEN EJECUTIVO ===' as seccion,
    '' as detalle
UNION ALL
SELECT 'Tablas:', '' UNION ALL
SELECT '  - ' || nombre || ': ' || registros || ' registros', '' FROM tabla_stats
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'Vistas Materializadas:', ''
UNION ALL
SELECT
    '  - ventas_backend: ' || CASE WHEN ventas_backend_mv > 0 THEN '✓ EXISTE' ELSE '✗ NO EXISTE' END,
    ''
FROM vista_exists
UNION ALL
SELECT 'Vistas Normales:', ''
UNION ALL
SELECT
    '  - ventas_metricas_dashboard: ' || CASE WHEN metricas_dash_v > 0 THEN '✓ EXISTE' ELSE '✗ NO EXISTE' END,
    ''
FROM vista_exists
UNION ALL
SELECT '', ''
UNION ALL
SELECT 'Índices por Tabla:', ''
UNION ALL
SELECT '  - ' || tablename || ': ' || num_indices || ' índices', ''
FROM indice_count;

-- ==================================================================================
-- FIN DEL SCRIPT DE AUDITORÍA
-- ==================================================================================

/*
INSTRUCCIONES DE USO:

1. Conectarse a la base de datos:
   psql -h localhost -U postgres -d crm_sunat

2. Ejecutar el script completo:
   \i audit_database.sql

3. O ejecutar queries individuales según lo que necesites verificar

4. QUERIES MÁS IMPORTANTES:
   - Query #22: Resumen ejecutivo de todo
   - Query #2: Ver vistas materializadas
   - Query #7: Ver todos los índices
   - Query #10: Ver tamaños de tablas
   - Query #19: Ver índices más usados

5. PARA INVESTIGAR PERFORMANCE:
   - Query #19: Índices que se están usando
   - Query #20: Índices que NO se usan (desperdiciar espacio)
*/
