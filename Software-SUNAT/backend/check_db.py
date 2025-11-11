# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Configurar conexión directa
DB_USER = "postgres"
DB_PASSWORD = "Crm-sunat1"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "CRM-SUNAT"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("DEBUG METRICAS - Analisis de Base de Datos")
print("Conectando a: {}@{}:{}/{}".format(DB_USER, DB_HOST, DB_PORT, DB_NAME))
print("=" * 80)

try:
    with engine.connect() as conn:
        # 1. Verificar cantidad total de facturas
        result = conn.execute(text("""
            SELECT COUNT(*) as total
            FROM ventas_sire
            WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%'
        """))
        total_facturas = result.scalar()
        print("\n[OK] Total facturas en BD (excluyendo notas y boletas): {}".format(total_facturas))

        # 2. Verificar facturas del mes actual
        result = conn.execute(text("""
            SELECT
                COUNT(*) as cantidad,
                SUM(total_cp) as total,
                moneda
            FROM ventas_sire
            WHERE tipo_cp_doc != '7'
              AND serie_cdp NOT LIKE 'B%'
              AND fecha_emision >= DATE_TRUNC('month', CURRENT_DATE)
              AND fecha_emision < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
            GROUP BY moneda
        """))
        print("\n[MES ACTUAL] Facturas de Noviembre 2025:")
        mes_actual = result.fetchall()
        if mes_actual:
            for row in mes_actual:
                print("   {}: {} facturas, Total: {:,.2f}".format(row.moneda, row.cantidad, float(row.total)))
        else:
            print("   [!] NO HAY FACTURAS EN NOVIEMBRE 2025")

        # 3. Verificar últimos 30 días
        result = conn.execute(text("""
            SELECT
                COUNT(*) as cantidad,
                SUM(total_cp) as total,
                moneda
            FROM ventas_sire
            WHERE tipo_cp_doc != '7'
              AND serie_cdp NOT LIKE 'B%'
              AND fecha_emision >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY moneda
        """))
        print("\n[ULTIMOS 30 DIAS]:")
        ultimos_30 = result.fetchall()
        if ultimos_30:
            for row in ultimos_30:
                print("   {}: {} facturas, Total: {:,.2f}".format(row.moneda, row.cantidad, float(row.total)))
        else:
            print("   [!] NO HAY FACTURAS EN LOS ULTIMOS 30 DIAS")

        # 4. Verificar rango de fechas disponibles
        result = conn.execute(text("""
            SELECT
                MIN(fecha_emision) as min_fecha,
                MAX(fecha_emision) as max_fecha,
                COUNT(*) as total
            FROM ventas_sire
            WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%'
        """))
        rango = result.fetchone()
        print("\n[RANGO DE FECHAS]:")
        print("   Desde: {}".format(rango.min_fecha))
        print("   Hasta: {}".format(rango.max_fecha))
        print("   Total: {} facturas".format(rango.total))

        # 5. Verificar enrolados y sus emails
        result = conn.execute(text("""
            SELECT ruc, razon_social, email
            FROM enrolados
            ORDER BY ruc
        """))
        enrolados = result.fetchall()
        print("\n[ENROLADOS] Total: {}".format(len(enrolados)))
        for enr in enrolados:
            email_display = enr.email if enr.email else "[SIN EMAIL]"
            print("   {} - {} [{}]".format(enr.ruc, enr.razon_social, email_display))

        # 6. Verificar facturas por enrolado
        result = conn.execute(text("""
            SELECT
                v.ruc,
                e.razon_social,
                e.email,
                COUNT(*) as cantidad,
                SUM(v.total_cp) as total
            FROM ventas_sire v
            LEFT JOIN enrolados e ON v.ruc = e.ruc
            WHERE v.tipo_cp_doc != '7' AND v.serie_cdp NOT LIKE 'B%'
            GROUP BY v.ruc, e.razon_social, e.email
            ORDER BY cantidad DESC
        """))
        print("\n[FACTURAS POR ENROLADO]:")
        por_enrolado = result.fetchall()
        for row in por_enrolado:
            email_display = row.email if row.email else "[SIN EMAIL]"
            print("   {} ({}): {} facturas, Total: {:,.2f} [{}]".format(
                row.ruc, row.razon_social, row.cantidad, float(row.total), email_display))

        # 7. Simular query del endpoint /api/metricas/resumen para mes actual
        print("\n[SIMULACION ENDPOINT /api/metricas/resumen]")
        fecha_desde = datetime.now().replace(day=1).date()
        fecha_hasta = (fecha_desde + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        result = conn.execute(text("""
            SELECT
                v.moneda,
                SUM(CASE WHEN v.tipo_cp_doc != '7' AND v.serie_cdp NOT LIKE 'B%' THEN v.total_cp ELSE 0 END)::numeric as total_facturado,
                SUM(CASE WHEN v.estado1 = 'Ganada' AND v.tipo_cp_doc != '7' AND v.serie_cdp NOT LIKE 'B%' THEN v.total_cp ELSE 0 END)::numeric as monto_ganado,
                SUM(CASE WHEN (v.estado1 IS NULL OR (v.estado1 != 'Ganada' AND v.estado1 != 'Perdida')) AND v.tipo_cp_doc != '7' AND v.serie_cdp NOT LIKE 'B%' THEN v.total_cp ELSE 0 END)::numeric as monto_disponible,
                COUNT(CASE WHEN v.tipo_cp_doc != '7' AND v.serie_cdp NOT LIKE 'B%' THEN v.id END)::integer as cantidad
            FROM ventas_sire v
            LEFT JOIN enrolados e ON v.ruc = e.ruc
            WHERE v.fecha_emision >= :fecha_desde
              AND v.fecha_emision <= :fecha_hasta
            GROUP BY v.moneda
        """), {"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta})

        metricas = result.fetchall()
        print("   Rango: {} a {}".format(fecha_desde, fecha_hasta))
        if metricas:
            for row in metricas:
                print("   {}:".format(row.moneda))
                print("      Total Facturado: {:,.2f}".format(float(row.total_facturado)))
                print("      Monto Ganado: {:,.2f}".format(float(row.monto_ganado)))
                print("      Monto Disponible: {:,.2f}".format(float(row.monto_disponible)))
                print("      Cantidad: {}".format(row.cantidad))
        else:
            print("   [!] NO HAY DATOS EN EL RANGO ESPECIFICADO")

except Exception as e:
    print("\n[ERROR] {}".format(str(e)))

print("\n" + "=" * 80)
print("FIN DEL ANALISIS")
print("=" * 80)
