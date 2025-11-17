"""
Script para ejecutar auditoría de base de datos
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

load_dotenv()

# Configuración
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

print("=" * 80)
print("AUDITORÍA DE BASE DE DATOS CRM-SUNAT")
print("=" * 80)
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Base de datos: {DB_NAME}")
print("=" * 80)
print()

# Intentar conexión con Cloud SQL Connector
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
        pool_pre_ping=True
    )
    print("[INFO] Conectado usando Cloud SQL Connector")

except Exception as e:
    print(f"[WARNING] No se pudo conectar con Cloud SQL Connector: {e}")
    print("[INFO] Intentando conexión local...")

    # Fallback a conexión local
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")

    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    print(f"[INFO] Conectado a {DB_HOST}:{DB_PORT}")

print()

# Queries de auditoría
queries = {
    "1. VISTAS MATERIALIZADAS": """
        SELECT
            matviewname as nombre,
            CASE WHEN ispopulated THEN 'POBLADA' ELSE 'VACÍA' END as estado,
            pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as tamaño
        FROM pg_matviews
        WHERE schemaname = 'public'
        ORDER BY matviewname;
    """,

    "2. VISTAS NORMALES": """
        SELECT viewname as nombre
        FROM pg_views
        WHERE schemaname = 'public'
        ORDER BY viewname;
    """,

    "3. ÍNDICES EN ventas_sire": """
        SELECT
            indexname as nombre,
            pg_size_pretty(pg_relation_size(indexrelid)) as tamaño,
            idx_scan as veces_usado
        FROM pg_stat_user_indexes
        WHERE tablename = 'ventas_sire'
            AND schemaname = 'public'
        ORDER BY indexname;
    """,

    "4. ÍNDICES EN compras_sire": """
        SELECT
            indexname as nombre,
            pg_size_pretty(pg_relation_size(indexrelid)) as tamaño,
            idx_scan as veces_usado
        FROM pg_stat_user_indexes
        WHERE tablename = 'compras_sire'
            AND schemaname = 'public'
        ORDER BY indexname;
    """,

    "5. FUNCIONES DE REFRESH": """
        SELECT proname as nombre
        FROM pg_proc
        WHERE pronamespace = 'public'::regnamespace
            AND (proname LIKE '%refresh%' OR proname LIKE '%ventas%')
        ORDER BY proname;
    """,

    "6. TAMAÑOS DE TABLAS": """
        SELECT
            tablename as nombre,
            pg_size_pretty(pg_total_relation_size('public.'||tablename)) as tamaño_total,
            pg_size_pretty(pg_relation_size('public.'||tablename)) as solo_datos,
            pg_size_pretty(pg_total_relation_size('public.'||tablename) - pg_relation_size('public.'||tablename)) as solo_indices
        FROM pg_tables
        WHERE schemaname = 'public'
            AND tablename IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios', 'periodos_fallidos')
        ORDER BY pg_total_relation_size('public.'||tablename) DESC;
    """,

    "7. ÍNDICES NUNCA USADOS (BASURA)": """
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
    """,

    "8. COLUMNAS DE GESTIÓN EN ventas_sire": """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'ventas_sire'
            AND column_name IN ('estado1', 'estado2', 'ultima_actualizacion')
        ORDER BY column_name;
    """,

    "9. CONTEO DE REGISTROS": """
        SELECT 'ventas_sire' as tabla, COUNT(*) as registros FROM ventas_sire
        UNION ALL
        SELECT 'compras_sire', COUNT(*) FROM compras_sire
        UNION ALL
        SELECT 'enrolados', COUNT(*) FROM enrolados
        UNION ALL
        SELECT 'usuarios', COUNT(*) FROM usuarios;
    """
}

# Ejecutar queries
results = {}

with engine.connect() as conn:
    for title, query in queries.items():
        print(f"\n{'=' * 80}")
        print(title)
        print('=' * 80)

        try:
            result = conn.execute(text(query))
            rows = result.fetchall()

            if len(rows) == 0:
                print("(Sin resultados)")
                results[title] = []
            else:
                # Imprimir encabezados
                headers = result.keys()
                col_widths = [max(len(str(h)), 15) for h in headers]

                # Ajustar anchos basados en datos
                for row in rows:
                    for i, val in enumerate(row):
                        col_widths[i] = max(col_widths[i], len(str(val)))

                # Imprimir encabezados
                header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
                print(header_line)
                print("-" * len(header_line))

                # Imprimir filas
                for row in rows:
                    print(" | ".join(str(val if val is not None else '').ljust(w) for val, w in zip(row, col_widths)))

                results[title] = rows

        except Exception as e:
            print(f"[ERROR] {e}")
            results[title] = f"ERROR: {e}"

# Resumen final
print("\n" + "=" * 80)
print("RESUMEN DE AUDITORÍA")
print("=" * 80)

# Vistas materializadas
vm_count = len(results.get("1. VISTAS MATERIALIZADAS", []))
print(f"✓ Vistas materializadas encontradas: {vm_count}")

# Vistas normales
v_count = len(results.get("2. VISTAS NORMALES", []))
print(f"✓ Vistas normales encontradas: {v_count}")

# Índices en ventas_sire
idx_ventas = len(results.get("3. ÍNDICES EN ventas_sire", []))
print(f"✓ Índices en ventas_sire: {idx_ventas}")

# Índices en compras_sire
idx_compras = len(results.get("4. ÍNDICES EN compras_sire", []))
print(f"✓ Índices en compras_sire: {idx_compras}")

# Índices basura
basura = results.get("7. ÍNDICES NUNCA USADOS (BASURA)", [])
print(f"⚠ Índices NUNCA usados (basura): {len(basura)}")

# Columnas estado
columnas = results.get("8. COLUMNAS DE GESTIÓN EN ventas_sire", [])
print(f"✓ Columnas de gestión (estado1/estado2): {len(columnas)}")

# Registros
registros = results.get("9. CONTEO DE REGISTROS", [])
if registros:
    print("\n📊 Registros por tabla:")
    for row in registros:
        print(f"   - {row[0]}: {row[1]:,} registros")

print("\n" + "=" * 80)
print("AUDITORÍA COMPLETADA")
print("=" * 80)
print()

# Guardar resultados en archivo
output_file = f"audit_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
print(f"[INFO] Guardando resultados en: {output_file}")

# Cerrar conexión
engine.dispose()
