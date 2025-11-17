-- ==================================================================================
-- QUERIES DE EJEMPLO PARA EL BACKEND
-- ==================================================================================
-- Descripción: Ejemplos de queries optimizadas para usar en tu backend
-- Fecha: 2025-11-15
-- ==================================================================================

-- ==================================================================================
-- 1. OBTENER MÉTRICAS DEL DASHBOARD
-- ==================================================================================

-- Query simple para obtener todas las métricas
SELECT * FROM ventas_metricas_dashboard;

-- Resultado esperado:
-- pipeline_activo_pen | pipeline_activo_usd | performance_cierres_pen_pct | ...
-- 36,654,086.65       | 7,491,311.78        | 0.01                        | ...


-- ==================================================================================
-- 2. LISTADO DE FACTURAS CON PAGINACIÓN Y FILTROS
-- ==================================================================================

-- Ejemplo con filtros dinámicos (últimos 30 días)
SELECT
    serie_cdp || '-' || nro_cp_inicial as numero_factura,
    razon_social as cliente,
    apellidos_nombres_razon_social as proveedor_cliente,
    CASE
        WHEN esta_anulada THEN
            CASE
                WHEN moneda = 'PEN' THEN 'S/ ' || ROUND(total_neto::numeric, 2) || ' (Anulada)'
                WHEN moneda = 'USD' THEN '$ ' || ROUND(total_neto::numeric, 2) || ' (Anulada)'
                ELSE ROUND(total_neto::numeric, 2)::text || ' (Anulada)'
            END
        ELSE
            CASE
                WHEN moneda = 'PEN' THEN 'S/ ' || ROUND(total_neto::numeric, 2)
                WHEN moneda = 'USD' THEN '$ ' || ROUND(total_neto::numeric, 2)
                ELSE ROUND(total_neto::numeric, 2)::text
            END
    END as monto_display,
    CASE
        WHEN esta_anulada THEN
            CASE
                WHEN moneda = 'PEN' THEN 'S/ ' || ROUND(total_cp::numeric, 2)
                WHEN moneda = 'USD' THEN '$ ' || ROUND(total_cp::numeric, 2)
                ELSE ROUND(total_cp::numeric, 2)::text
            END
        ELSE NULL
    END as monto_original,
    fecha_emision,
    COALESCE(estado1, 'Sin gestión') as estado_gestion,
    esta_anulada,
    notas_credito_asociadas
FROM ventas_backend
WHERE tipo_cp_doc = '01'  -- Solo facturas
    AND fecha_emision >= CURRENT_DATE - INTERVAL '30 days'
    -- Filtros adicionales dinámicos:
    -- AND razon_social = 'NOMBRE_CLIENTE'
    -- AND moneda = 'PEN'
    -- AND estado1 = 'GESTIONADO'
ORDER BY fecha_emision DESC, id DESC
LIMIT 50 OFFSET 0;  -- Paginación: página 1


-- ==================================================================================
-- 3. FILTRAR POR CLIENTE ESPECÍFICO
-- ==================================================================================

SELECT
    serie_cdp || '-' || nro_cp_inicial as numero_factura,
    fecha_emision,
    total_neto,
    moneda,
    esta_anulada,
    estado1,
    estado2
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND razon_social = 'MALIKKA SALUD S.A.C.'
ORDER BY fecha_emision DESC;


-- ==================================================================================
-- 4. FILTRAR POR MONEDA Y ESTADO
-- ==================================================================================

-- Facturas en PEN sin gestión
SELECT
    serie_cdp || '-' || nro_cp_inicial as numero_factura,
    razon_social,
    total_neto,
    fecha_emision
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND moneda = 'PEN'
    AND (estado1 IS NULL OR estado1 = 'Sin gestión')
    AND NOT esta_anulada
ORDER BY total_neto DESC;


-- ==================================================================================
-- 5. FACTURAS ANULADAS CON DETALLES DE NOTAS DE CRÉDITO
-- ==================================================================================

SELECT
    serie_cdp || '-' || nro_cp_inicial as factura,
    razon_social as cliente,
    total_cp as monto_original,
    monto_nota_credito,
    total_neto as monto_final,
    notas_credito_asociadas,
    fecha_emision
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND esta_anulada = true
ORDER BY fecha_emision DESC;


-- ==================================================================================
-- 6. MÉTRICAS POR CLIENTE (TOP 10)
-- ==================================================================================

SELECT
    razon_social as cliente,
    COUNT(*) as total_facturas,
    SUM(CASE WHEN esta_anulada THEN 1 ELSE 0 END) as facturas_anuladas,
    SUM(CASE WHEN moneda = 'PEN' THEN total_neto ELSE 0 END) as total_pen,
    SUM(CASE WHEN moneda = 'USD' THEN total_neto ELSE 0 END) as total_usd
FROM ventas_backend
WHERE tipo_cp_doc = '01'
GROUP BY razon_social
ORDER BY (SUM(CASE WHEN moneda = 'PEN' THEN total_neto ELSE 0 END) +
          SUM(CASE WHEN moneda = 'USD' THEN total_neto ELSE 0 END)) DESC
LIMIT 10;


-- ==================================================================================
-- 7. FACTURAS PENDIENTES DE GESTIÓN (Sin estado1)
-- ==================================================================================

SELECT
    serie_cdp || '-' || nro_cp_inicial as numero_factura,
    razon_social,
    apellidos_nombres_razon_social as cliente_final,
    total_neto,
    moneda,
    fecha_emision,
    CURRENT_DATE - fecha_emision as dias_sin_gestion
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND estado1 IS NULL
    AND NOT esta_anulada
ORDER BY fecha_emision ASC;


-- ==================================================================================
-- 8. RESUMEN POR PERIODO
-- ==================================================================================

SELECT
    periodo,
    COUNT(*) as total_facturas,
    SUM(CASE WHEN esta_anulada THEN 1 ELSE 0 END) as anuladas,
    SUM(CASE WHEN moneda = 'PEN' THEN total_neto ELSE 0 END) as total_pen,
    SUM(CASE WHEN moneda = 'USD' THEN total_neto ELSE 0 END) as total_usd
FROM ventas_backend
WHERE tipo_cp_doc = '01'
GROUP BY periodo
ORDER BY periodo DESC;


-- ==================================================================================
-- 9. FACTURAS CON ESTADO ESPECÍFICO
-- ==================================================================================

-- Facturas gestionadas y contactadas
SELECT
    serie_cdp || '-' || nro_cp_inicial as numero_factura,
    razon_social,
    total_neto,
    moneda,
    estado1,
    estado2,
    fecha_emision
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND estado1 = 'GESTIONADO'
    AND estado2 = 'CONTACTADO'
ORDER BY fecha_emision DESC;


-- ==================================================================================
-- 10. ACTUALIZAR ESTADOS DE GESTIÓN
-- ==================================================================================

-- IMPORTANTE: Actualizar en ventas_sire (data lake), no en ventas_backend
-- Luego refrescar la vista materializada

-- Ejemplo: Marcar factura como gestionada
UPDATE ventas_sire
SET
    estado1 = 'GESTIONADO',
    estado2 = 'CONTACTADO',
    ultima_actualizacion = NOW()
WHERE id = 2554;

-- Después de actualizar, refrescar la vista:
SELECT refresh_ventas_backend();


-- ==================================================================================
-- 11. BÚSQUEDA POR NÚMERO DE FACTURA
-- ==================================================================================

SELECT
    id,
    serie_cdp || '-' || nro_cp_inicial as numero_factura,
    razon_social,
    apellidos_nombres_razon_social as cliente,
    total_cp as monto_original,
    total_neto as monto_actual,
    moneda,
    esta_anulada,
    notas_credito_asociadas,
    estado1,
    estado2,
    fecha_emision
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND (serie_cdp || '-' || nro_cp_inicial) ILIKE '%F001-11956%';


-- ==================================================================================
-- 12. MÉTRICAS POR ESTADO DE GESTIÓN
-- ==================================================================================

SELECT
    COALESCE(estado1, 'Sin gestión') as estado,
    COUNT(*) as cantidad_facturas,
    SUM(CASE WHEN moneda = 'PEN' THEN total_neto ELSE 0 END) as total_pen,
    SUM(CASE WHEN moneda = 'USD' THEN total_neto ELSE 0 END) as total_usd,
    ROUND(AVG(total_neto)::numeric, 2) as promedio
FROM ventas_backend
WHERE tipo_cp_doc = '01'
    AND NOT esta_anulada
GROUP BY estado1
ORDER BY cantidad_facturas DESC;


-- ==================================================================================
-- 13. REFRESCAR VISTA MATERIALIZADA
-- ==================================================================================

-- Ejecutar después de cada actualización de datos desde SUNAT
SELECT refresh_ventas_backend();

-- Verificar última actualización
SELECT
    schemaname,
    matviewname,
    hasindexes,
    ispopulated
FROM pg_matviews
WHERE matviewname = 'ventas_backend';
