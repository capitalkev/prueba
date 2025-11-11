#!/usr/bin/env python3
"""
Script de debug para verificar las métricas desde la base de datos
"""
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar conexión
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Crm-sunat1")
DB_HOST = "localhost"  # Usar localhost directamente
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "CRM-SUNAT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"📡 Conectando a: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
engine = create_engine(DATABASE_URL)

print("=" * 80)
print("DEBUG MÉTRICAS - Análisis de Base de Datos")
print("=" * 80)

with engine.connect() as conn:
    # 1. Verificar cantidad total de facturas
    result = conn.execute(text("""
        SELECT COUNT(*) as total
        FROM ventas_sire
        WHERE tipo_cp_doc != '7' AND serie_cdp NOT LIKE 'B%'
    """))
    total_facturas = result.scalar()
    print(f"\n✅ Total facturas en BD (excluyendo notas y boletas): {total_facturas}")

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
    print(f"\n📅 Facturas del MES ACTUAL (Noviembre 2025):")
    mes_actual = result.fetchall()
    for row in mes_actual:
        print(f"   {row.moneda}: {row.cantidad} facturas, Total: {row.total:,.2f}")

    if not mes_actual:
        print("   ⚠️ NO HAY FACTURAS EN NOVIEMBRE 2025")

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
    print(f"\n📊 Facturas de los ÚLTIMOS 30 DÍAS:")
    ultimos_30 = result.fetchall()
    for row in ultimos_30:
        print(f"   {row.moneda}: {row.cantidad} facturas, Total: {row.total:,.2f}")

    if not ultimos_30:
        print("   ⚠️ NO HAY FACTURAS EN LOS ÚLTIMOS 30 DÍAS")

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
    print(f"\n📆 Rango de fechas en BD:")
    print(f"   Desde: {rango.min_fecha}")
    print(f"   Hasta: {rango.max_fecha}")
    print(f"   Total: {rango.total} facturas")

    # 5. Verificar enrolados y sus emails
    result = conn.execute(text("""
        SELECT ruc, razon_social, email
        FROM enrolados
        ORDER BY ruc
    """))
    enrolados = result.fetchall()
    print(f"\n👥 Enrolados registrados ({len(enrolados)}):")
    for enr in enrolados:
        email_display = enr.email if enr.email else "❌ SIN EMAIL"
        print(f"   {enr.ruc} - {enr.razon_social} [{email_display}]")

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
    print(f"\n📈 Facturas por enrolado:")
    por_enrolado = result.fetchall()
    for row in por_enrolado:
        email_display = row.email if row.email else "❌ SIN EMAIL"
        print(f"   {row.ruc} ({row.razon_social}): {row.cantidad} facturas, Total: {row.total:,.2f} [{email_display}]")

    # 7. Simular query del endpoint /api/metricas/resumen para mes actual
    print(f"\n🔍 Simulando query del endpoint /api/metricas/resumen (mes actual):")
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
    print(f"   Rango: {fecha_desde} a {fecha_hasta}")
    for row in metricas:
        print(f"   {row.moneda}:")
        print(f"      Total Facturado: {row.total_facturado:,.2f}")
        print(f"      Monto Ganado: {row.monto_ganado:,.2f}")
        print(f"      Monto Disponible: {row.monto_disponible:,.2f}")
        print(f"      Cantidad: {row.cantidad}")

    if not metricas:
        print("   ⚠️ NO HAY DATOS EN EL RANGO ESPECIFICADO")

print("\n" + "=" * 80)
print("FIN DEL ANÁLISIS")
print("=" * 80)
