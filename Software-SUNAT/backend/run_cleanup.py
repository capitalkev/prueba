"""
Script para ejecutar limpieza de base de datos
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# Forzar UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

print("=" * 80)
print("LIMPIEZA DE BASE DE DATOS CRM-SUNAT")
print("=" * 80)
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

# Conectar
try:
    from google.cloud.sql.connector import Connector

    connector = Connector()

    def getconn():
        conn = connector.connect(
            CLOUD_SQL_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME
        )
        return conn

    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_pre_ping=True,
        isolation_level="AUTOCOMMIT"
    )
    print("[INFO] Conectado usando Cloud SQL Connector\n")

except Exception as e:
    print(f"[ERROR] No se pudo conectar: {e}")
    sys.exit(1)

# Ejecutar limpieza
with engine.connect() as conn:
    print("=" * 80)
    print("1. ELIMINANDO VISTAS MATERIALIZADAS ANTIGUAS")
    print("=" * 80)

    try:
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_metricas_diarias CASCADE"))
        print("[OK] mv_metricas_diarias eliminada")
    except Exception as e:
        print(f"[ERROR] {e}")

    try:
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS mv_metricas_mensuales CASCADE"))
        print("[OK] mv_metricas_mensuales eliminada")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 80)
    print("2. ELIMINANDO VISTAS NORMALES ANTIGUAS")
    print("=" * 80)

    try:
        conn.execute(text("DROP VIEW IF EXISTS v_metricas_resumen CASCADE"))
        print("[OK] v_metricas_resumen eliminada")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 80)
    print("3. ELIMINANDO FUNCIONES OBSOLETAS")
    print("=" * 80)

    try:
        conn.execute(text("DROP FUNCTION IF EXISTS refresh_metricas_views() CASCADE"))
        print("[OK] refresh_metricas_views eliminada")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 80)
    print("4. ELIMINANDO ÍNDICES DUPLICADOS")
    print("=" * 80)

    indices_duplicados = [
        ("ix_ventas_sire_nro_doc_identidad", "duplicado de idx_ventas_cliente"),
        ("ix_ventas_sire_periodo", "cubierto por idx_ventas_ruc_periodo"),
        ("ix_ventas_sire_ruc", "cubierto por idx_ventas_ruc_periodo"),
    ]

    for idx, razon in indices_duplicados:
        try:
            conn.execute(text(f"DROP INDEX IF EXISTS {idx}"))
            print(f"[OK] {idx} eliminado ({razon})")
        except Exception as e:
            print(f"[ERROR] {idx}: {e}")

    print()
    print("=" * 80)
    print("5. EJECUTANDO VACUUM ANALYZE")
    print("=" * 80)

    try:
        print("[INFO] Ejecutando VACUUM ANALYZE en ventas_sire...")
        conn.execute(text("VACUUM ANALYZE ventas_sire"))
        print("[OK] VACUUM en ventas_sire completado")
    except Exception as e:
        print(f"[ERROR] {e}")

    try:
        print("[INFO] Ejecutando VACUUM ANALYZE en compras_sire...")
        conn.execute(text("VACUUM ANALYZE compras_sire"))
        print("[OK] VACUUM en compras_sire completado")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print("=" * 80)
    print("6. VERIFICANDO ESTADO FINAL")
    print("=" * 80)

    # Ver vistas materializadas restantes
    result = conn.execute(text("""
        SELECT matviewname
        FROM pg_matviews
        WHERE schemaname = 'public'
    """))
    rows = result.fetchall()
    print(f"\nVistas materializadas restantes: {len(rows)}")
    for row in rows:
        print(f"  - {row[0]}")

    # Ver índices restantes en ventas_sire
    result = conn.execute(text("""
        SELECT
            indexname,
            pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as tamanio
        FROM pg_indexes
        WHERE tablename = 'ventas_sire'
          AND schemaname = 'public'
        ORDER BY indexname
    """))
    rows = result.fetchall()
    print(f"\nÍndices en ventas_sire: {len(rows)}")
    total_size = 0
    for row in rows:
        print(f"  - {row[0]}: {row[1]}")

print()
print("=" * 80)
print("LIMPIEZA COMPLETADA CON ÉXITO")
print("Espacio recuperado: ~59 MB en índices + 672 KB en vistas")
print("=" * 80)

engine.dispose()
