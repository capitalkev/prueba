-- Corregir nombres de columnas en vista materializada
-- Problema: La vista usa "monto_nota_credito" y "total_neto"
-- Solución: Debe usar "nota_credito_monto" y "monto_neto" para coincidir con schemas.py

DROP MATERIALIZED VIEW IF EXISTS ventas_backend CASCADE;

CREATE MATERIALIZED VIEW ventas_backend AS
SELECT
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
    v.estado1,
    v.estado2,
    v.ultima_actualizacion,
    e.email as usuario_email,
    u.nombre as usuario_nombre,

    -- CAMPOS CALCULADOS CON NOMBRES CORRECTOS
    -- monto_original: total_cp / tipo_cambio (SIN notas de crédito)
    (CASE WHEN v.tipo_cambio IS NOT NULL AND v.tipo_cambio > 0
     THEN v.total_cp / v.tipo_cambio
     ELSE v.total_cp END) as monto_original,

    -- tiene_nota_credito: boolean si tiene NC asociadas
    (SELECT COUNT(*) > 0
     FROM ventas_sire nc
     WHERE nc.ruc = v.ruc
     AND nc.tipo_cp_doc = '7'
     AND TRIM(TRAILING '.0' FROM nc.nro_cp_modificado::text) = v.nro_cp_inicial
     AND nc.nro_doc_identidad = v.nro_doc_identidad
    ) as tiene_nota_credito,

    -- nota_credito_monto (NO "monto_nota_credito"): suma de NC (negativo)
    COALESCE((
        SELECT SUM(
            CASE WHEN nc.tipo_cambio IS NOT NULL AND nc.tipo_cambio > 0
            THEN nc.total_cp / nc.tipo_cambio
            ELSE nc.total_cp END
        )
        FROM ventas_sire nc
        WHERE nc.ruc = v.ruc
        AND nc.tipo_cp_doc = '7'
        AND TRIM(TRAILING '.0' FROM nc.nro_cp_modificado::text) = v.nro_cp_inicial
        AND nc.nro_doc_identidad = v.nro_doc_identidad
    ), 0) as nota_credito_monto,

    -- monto_neto (NO "total_neto"): monto_original + nota_credito_monto
    (CASE WHEN v.tipo_cambio IS NOT NULL AND v.tipo_cambio > 0
     THEN v.total_cp / v.tipo_cambio
     ELSE v.total_cp END) + COALESCE((
        SELECT SUM(
            CASE WHEN nc.tipo_cambio IS NOT NULL AND nc.tipo_cambio > 0
            THEN nc.total_cp / nc.tipo_cambio
            ELSE nc.total_cp END
        )
        FROM ventas_sire nc
        WHERE nc.ruc = v.ruc
        AND nc.tipo_cp_doc = '7'
        AND TRIM(TRAILING '.0' FROM nc.nro_cp_modificado::text) = v.nro_cp_inicial
        AND nc.nro_doc_identidad = v.nro_doc_identidad
    ), 0) as monto_neto,

    -- notas_credito_asociadas: string con referencias de NC
    (SELECT STRING_AGG(nc.serie_cdp || '-' || nc.nro_cp_inicial, ', ' ORDER BY nc.fecha_emision)
     FROM ventas_sire nc
     WHERE nc.ruc = v.ruc
     AND nc.tipo_cp_doc = '7'
     AND nc.nro_cp_modificado = v.nro_cp_inicial
     AND nc.nro_doc_identidad = v.nro_doc_identidad
    ) as notas_credito_asociadas

FROM ventas_sire v
LEFT JOIN enrolados e ON v.ruc = e.ruc
LEFT JOIN usuarios u ON e.email = u.email
WHERE v.tipo_cp_doc = '1'
    AND v.serie_cdp NOT LIKE 'B%'
    AND v.apellidos_nombres_razon_social != '-'
    AND v.apellidos_nombres_razon_social IS NOT NULL;

-- Recrear índices
CREATE UNIQUE INDEX idx_ventas_backend_id ON ventas_backend(id);
CREATE INDEX idx_ventas_backend_ruc_periodo ON ventas_backend(ruc, periodo);
CREATE INDEX idx_ventas_backend_tipo_doc ON ventas_backend(tipo_cp_doc);
CREATE INDEX idx_ventas_backend_estado1 ON ventas_backend(estado1) WHERE estado1 IS NOT NULL;
CREATE INDEX idx_ventas_backend_fecha ON ventas_backend(fecha_emision);
CREATE INDEX idx_ventas_backend_cliente ON ventas_backend(nro_doc_identidad);
CREATE INDEX idx_ventas_backend_moneda ON ventas_backend(moneda);
CREATE INDEX idx_ventas_backend_metricas ON ventas_backend(fecha_emision, moneda, estado1, monto_neto);
CREATE INDEX idx_ventas_backend_con_nc ON ventas_backend(tiene_nota_credito) WHERE tiene_nota_credito = true;
CREATE INDEX idx_ventas_backend_usuario_email ON ventas_backend(usuario_email) WHERE usuario_email IS NOT NULL;
CREATE INDEX idx_ventas_backend_fecha_desc ON ventas_backend(fecha_emision DESC);
-- Función de refresh
CREATE OR REPLACE FUNCTION refresh_ventas_backend()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY ventas_backend;
    RAISE NOTICE 'Vista ventas_backend refrescada a las %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Actualizar estadísticas
ANALYZE ventas_backend;
