-- =====================================================================
-- Migration: Índices de Performance para Software-SUNAT
-- Fecha: 2025-11-10
-- Descripción: Añade índices compuestos críticos para optimizar queries
-- Impacto esperado: 50-300ms reducidos por query
-- =====================================================================

-- Verificar índices existentes antes de ejecutar
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'ventas_sire' ORDER BY indexname;

BEGIN;

-- =====================================================================
-- ÍNDICE 1: Para /api/metricas - Agrupa por moneda en período específico
-- =====================================================================
-- Queries beneficiadas:
--   - GET /api/metricas/{periodo}
--   - Agregaciones por moneda
-- Mejora esperada: 200-800ms → 10-50ms

CREATE INDEX IF NOT EXISTS idx_ventas_periodo_moneda
ON ventas_sire(periodo, moneda)
WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%';

COMMENT ON INDEX idx_ventas_periodo_moneda IS
'Optimiza queries de métricas agrupadas por moneda. Excluye notas de crédito y boletas.';

-- =====================================================================
-- ÍNDICE 2: Para filtros combinados RUC + Período + Moneda
-- =====================================================================
-- Queries beneficiadas:
--   - GET /api/ventas con filtros de empresa y moneda
--   - Filtros de dashboard por empresa específica
-- Mejora esperada: Full table scan → Index scan

CREATE INDEX IF NOT EXISTS idx_ventas_ruc_periodo_moneda
ON ventas_sire(ruc, periodo, moneda);

COMMENT ON INDEX idx_ventas_ruc_periodo_moneda IS
'Optimiza queries filtradas por empresa, período y moneda simultáneamente.';

-- =====================================================================
-- ÍNDICE 3: Para búsqueda de usuarios autorizados
-- =====================================================================
-- Queries beneficiadas:
--   - auth.py:128 - get_rucs_autorizados_por_usuario
--   - JOIN entre enrolados y usuarios
-- Mejora esperada: 10-50ms reducidos

CREATE INDEX IF NOT EXISTS idx_enrolados_email
ON enrolados(email);

COMMENT ON INDEX idx_enrolados_email IS
'Optimiza búsqueda de empresas (enrolados) por email de usuario autorizado.';

-- =====================================================================
-- ÍNDICE 4: Para subquery de Notas de Crédito
-- =====================================================================
-- Queries beneficiadas:
--   - venta_repository.py:55-78 - Subquery de NC
--   - Matching de facturas con sus NC
-- Mejora esperada: 50-200ms reducidos en subquery

CREATE INDEX IF NOT EXISTS idx_ventas_tipo_nro_ruc
ON ventas_sire(tipo_cp_doc, nro_cp_inicial, ruc)
WHERE tipo_cp_doc = '7';

COMMENT ON INDEX idx_ventas_tipo_nro_ruc IS
'Optimiza subquery de notas de crédito (tipo_cp_doc = 7). Solo indexa NC.';

-- =====================================================================
-- ÍNDICE 5: Para filtros por estado de factura
-- =====================================================================
-- Queries beneficiadas:
--   - Filtros por estado1 (Nueva Oportunidad, Ganada, Perdida, etc.)
--   - Agregaciones por empresa y estado
-- Mejora esperada: 30-100ms reducidos

CREATE INDEX IF NOT EXISTS idx_ventas_ruc_estado1
ON ventas_sire(ruc, estado1);

COMMENT ON INDEX idx_ventas_ruc_estado1 IS
'Optimiza queries filtradas por empresa y estado de factura (pipeline).';

-- =====================================================================
-- ÍNDICE 6 (OPCIONAL): Para búsqueda por cliente (deudor)
-- =====================================================================
-- Queries beneficiadas:
--   - Búsqueda de facturas por RUC de cliente
--   - Filtros por nombre de deudor
-- Nota: Ya existe idx_ventas_cliente en nro_doc_identidad

-- CREATE INDEX IF NOT EXISTS idx_ventas_cliente_ruc
-- ON ventas_sire(nro_doc_identidad, ruc);
-- Descomentar si se necesita búsqueda frecuente por cliente específico

-- =====================================================================
-- ÍNDICE 7: Para ordenamiento por fecha
-- =====================================================================
-- Queries beneficiadas:
--   - ORDER BY fecha_emision DESC (query más común)
-- Nota: Ya existe idx_ventas_fecha pero sin dirección

-- Recrear índice con dirección DESC para optimizar queries
DROP INDEX IF EXISTS idx_ventas_fecha;

CREATE INDEX idx_ventas_fecha_desc
ON ventas_sire(fecha_emision DESC);

COMMENT ON INDEX idx_ventas_fecha_desc IS
'Optimiza ORDER BY fecha_emision DESC (orden más común en listados).';

-- =====================================================================
-- ÍNDICES PARA COMPRAS (Opcional - si se detectan problemas similares)
-- =====================================================================

CREATE INDEX IF NOT EXISTS idx_compras_periodo_moneda
ON compras_sire(periodo, moneda)
WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%';

CREATE INDEX IF NOT EXISTS idx_compras_ruc_periodo_moneda
ON compras_sire(ruc, periodo, moneda);

COMMENT ON INDEX idx_compras_periodo_moneda IS 'Métricas de compras por período y moneda.';
COMMENT ON INDEX idx_compras_ruc_periodo_moneda IS 'Filtros combinados para compras.';

-- =====================================================================
-- ESTADÍSTICAS DE ÍNDICES (Ejecutar después de CREATE INDEX)
-- =====================================================================

-- Analizar tablas para actualizar estadísticas del query planner
ANALYZE ventas_sire;
ANALYZE compras_sire;
ANALYZE enrolados;

COMMIT;

-- =====================================================================
-- VERIFICACIÓN POST-MIGRACIÓN
-- =====================================================================

-- 1. Verificar que todos los índices se crearon correctamente
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('ventas_sire', 'compras_sire', 'enrolados')
ORDER BY tablename, indexname;

-- 2. Ver tamaño de índices creados
SELECT
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND relname IN ('ventas_sire', 'compras_sire', 'enrolados')
ORDER BY pg_relation_size(indexrelid) DESC;

-- 3. Verificar uso de índices en query específica (ejemplo)
EXPLAIN ANALYZE
SELECT
    moneda,
    SUM(total_cp) as total,
    COUNT(*) as cantidad
FROM ventas_sire
WHERE periodo = '202510'
  AND tipo_cp_doc != '7'
  AND serie_cdp NOT LIKE 'B%'
GROUP BY moneda;

-- Si el query plan muestra "Index Scan using idx_ventas_periodo_moneda", el índice funciona correctamente

-- =====================================================================
-- ROLLBACK (En caso de problemas)
-- =====================================================================

/*
-- Ejecutar solo si necesitas revertir los cambios:

BEGIN;

DROP INDEX IF EXISTS idx_ventas_periodo_moneda;
DROP INDEX IF EXISTS idx_ventas_ruc_periodo_moneda;
DROP INDEX IF EXISTS idx_enrolados_email;
DROP INDEX IF EXISTS idx_ventas_tipo_nro_ruc;
DROP INDEX IF EXISTS idx_ventas_ruc_estado1;
DROP INDEX IF EXISTS idx_ventas_fecha_desc;
DROP INDEX IF EXISTS idx_compras_periodo_moneda;
DROP INDEX IF EXISTS idx_compras_ruc_periodo_moneda;

-- Recrear índice original de fecha
CREATE INDEX idx_ventas_fecha ON ventas_sire(fecha_emision);

COMMIT;
*/

-- =====================================================================
-- NOTAS DE IMPLEMENTACIÓN
-- =====================================================================

/*
IMPORTANTE:

1. TIEMPO DE CREACIÓN:
   - Con 100,000 registros: 1-5 minutos por índice
   - Con 1,000,000 registros: 10-30 minutos por índice
   - Ejecutar en horario de bajo tráfico (madrugada)

2. ESPACIO EN DISCO:
   - Cada índice puede ocupar 10-50 MB (depende de datos)
   - Total estimado: 200-500 MB adicionales
   - Verificar espacio disponible antes de ejecutar

3. BLOQUEOS:
   - CREATE INDEX bloquea escrituras en la tabla
   - En producción, considerar CREATE INDEX CONCURRENTLY:
     CREATE INDEX CONCURRENTLY idx_name ON table(column);
   - CONCURRENTLY es más lento pero no bloquea la tabla

4. MONITOREO POST-IMPLEMENTACIÓN:
   - Revisar logs de PostgreSQL para errores
   - Monitorear tiempos de query con pg_stat_statements
   - Verificar que el query planner usa los índices nuevos

5. MANTENIMIENTO:
   - Los índices se mantienen automáticamente
   - VACUUM ANALYZE periódico ayuda a mantener estadísticas actualizadas
   - Revisar índices no usados cada 3-6 meses:

     SELECT indexrelname, idx_scan
     FROM pg_stat_user_indexes
     WHERE schemaname = 'public' AND idx_scan = 0
     ORDER BY indexrelname;

*/
