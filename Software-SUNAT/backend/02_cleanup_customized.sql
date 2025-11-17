-- ==================================================================================
-- LIMPIEZA PERSONALIZADA BASADA EN AUDITORÍA
-- ==================================================================================
-- Base de datos: CRM-SUNAT
-- Fecha: 2025-11-16
-- ==================================================================================

\echo '=========================================='
\echo 'INICIANDO LIMPIEZA PERSONALIZADA'
\echo '=========================================='
\echo ''

-- ==================================================================================
-- 1. ELIMINAR VISTAS MATERIALIZADAS ANTIGUAS
-- ==================================================================================
\echo '1. Eliminando vistas materializadas antiguas...'

DROP MATERIALIZED VIEW IF EXISTS mv_metricas_diarias CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_metricas_mensuales CASCADE;

\echo '   ✓ Vistas materializadas antiguas eliminadas'
\echo ''

-- ==================================================================================
-- 2. ELIMINAR VISTA NORMAL ANTIGUA
-- ==================================================================================
\echo '2. Eliminando vistas normales antiguas...'

DROP VIEW IF EXISTS v_metricas_resumen CASCADE;

\echo '   ✓ Vista v_metricas_resumen eliminada'
\echo ''

-- ==================================================================================
-- 3. ELIMINAR FUNCIÓN ANTIGUA
-- ==================================================================================
\echo '3. Eliminando funciones obsoletas...'

DROP FUNCTION IF EXISTS refresh_metricas_views() CASCADE;

\echo '   ✓ Función refresh_metricas_views eliminada'
\echo ''

-- ==================================================================================
-- 4. ELIMINAR ÍNDICES DUPLICADOS EN ventas_sire
-- ==================================================================================
\echo '4. Eliminando índices duplicados...'

-- Estos índices están duplicados (SQLAlchemy los creó automáticamente)
-- ix_ventas_sire_nro_doc_identidad es igual a idx_ventas_cliente
DROP INDEX IF EXISTS ix_ventas_sire_nro_doc_identidad;

-- ix_ventas_sire_periodo está cubierto por idx_ventas_ruc_periodo (compuesto)
DROP INDEX IF EXISTS ix_ventas_sire_periodo;

-- ix_ventas_sire_ruc está cubierto por idx_ventas_ruc_periodo (compuesto)
DROP INDEX IF EXISTS ix_ventas_sire_ruc;

\echo '   ✓ Índices duplicados eliminados'
\echo '   - ix_ventas_sire_nro_doc_identidad (duplicado de idx_ventas_cliente)'
\echo '   - ix_ventas_sire_periodo (cubierto por idx_ventas_ruc_periodo)'
\echo '   - ix_ventas_sire_ruc (cubierto por idx_ventas_ruc_periodo)'
\echo ''

-- ==================================================================================
-- 5. VACUUM PARA RECUPERAR ESPACIO
-- ==================================================================================
\echo '5. Ejecutando VACUUM ANALYZE para recuperar espacio...'

VACUUM ANALYZE ventas_sire;
VACUUM ANALYZE compras_sire;

\echo '   ✓ VACUUM completado'
\echo ''

-- ==================================================================================
-- 6. VERIFICAR ESTADO DESPUÉS DE LIMPIEZA
-- ==================================================================================
\echo '6. Verificando estado después de limpieza...'
\echo ''

\echo 'Vistas materializadas restantes:'
SELECT matviewname FROM pg_matviews WHERE schemaname = 'public';

\echo ''
\echo 'Vistas normales restantes:'
SELECT viewname FROM pg_views WHERE schemaname = 'public';

\echo ''
\echo 'Funciones restantes con "refresh":'
SELECT proname FROM pg_proc
WHERE pronamespace = 'public'::regnamespace
  AND proname LIKE '%refresh%';

\echo ''
\echo 'Índices en ventas_sire (después de limpieza):'
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as tamanio
FROM pg_indexes
WHERE tablename = 'ventas_sire'
  AND schemaname = 'public'
ORDER BY indexname;

\echo ''
\echo '=========================================='
\echo 'LIMPIEZA COMPLETADA'
\echo 'Espacio recuperado: ~59 MB'
\echo '=========================================='
