"""
Script para ejecutar auditoría de base de datos - FIXED
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# Forzar UTF-8 para evitar errores de encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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
        pool_pre_ping=True,
        isolation_level="AUTOCOMMIT"  # Evitar problemas de transacciones
    )
    print("[INFO] Conectado usando Cloud SQL Connector")

except Exception as e:
    print(f"[WARNING] No se pudo conectar con Cloud SQL Connector: {e}")
    print("[INFO] Intentando conexión local...")

    # Fallback a conexión local
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")

    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        isolation_level="AUTOCOMMIT"
    )
    print(f"[INFO] Conectado a {DB_HOST}:{DB_PORT}")

print()

# Función para ejecutar query con manejo de errores
def execute_query(conn, title, query):
    print(f"\n{'=' * 80}")
    print(title)
    print('=' * 80)

    try:
        result = conn.execute(text(query))
        rows = result.fetchall()

        if len(rows) == 0:
            print("(Sin resultados)")
            return []
        else:
            # Imprimir encabezados
            headers = list(result.keys())
            col_widths = [max(len(str(h)), 15) for h in headers]

            # Ajustar anchos basados en datos
            for row in rows:
                for i, val in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(val)) if val is not None else 0)

            # Imprimir encabezados
            header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
            print(header_line)
            print("-" * len(header_line))

            # Imprimir filas
            for row in rows:
                print(" | ".join(str(val if val is not None else '').ljust(w) for val, w in zip(row, col_widths)))

            return rows

    except Exception as e:
        print(f"[ERROR] {e}")
        return None


# Ejecutar queries
results = {}

with engine.connect() as conn:
    # 1. Vistas materializadas
    results['vm'] = execute_query(conn, "1. VISTAS MATERIALIZADAS", """
        SELECT
            matviewname as nombre,
            CASE WHEN ispopulated THEN 'POBLADA' ELSE 'VACIA' END as estado,
            pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as tamanio
        FROM pg_matviews
        WHERE schemaname = 'public'
        ORDER BY matviewname;
    """)

    # 2. Vistas normales
    results['v'] = execute_query(conn, "2. VISTAS NORMALES", """
        SELECT viewname as nombre
        FROM pg_views
        WHERE schemaname = 'public'
        ORDER BY viewname;
    """)

    # 3. Índices en ventas_sire (corregido: usar indexrelname)
    results['idx_ventas'] = execute_query(conn, "3. INDICES EN ventas_sire", """
        SELECT
            indexrelname as nombre,
            pg_size_pretty(pg_relation_size(indexrelid)) as tamanio,
            idx_scan as veces_usado
        FROM pg_stat_user_indexes
        WHERE tablename = 'ventas_sire'
            AND schemaname = 'public'
        ORDER BY indexrelname;
    """)

    # 4. Índices en compras_sire
    results['idx_compras'] = execute_query(conn, "4. INDICES EN compras_sire", """
        SELECT
            indexrelname as nombre,
            pg_size_pretty(pg_relation_size(indexrelid)) as tamanio,
            idx_scan as veces_usado
        FROM pg_stat_user_indexes
        WHERE tablename = 'compras_sire'
            AND schemaname = 'public'
        ORDER BY indexrelname;
    """)

    # 5. Funciones
    results['funcs'] = execute_query(conn, "5. FUNCIONES DE REFRESH", """
        SELECT proname as nombre
        FROM pg_proc
        WHERE pronamespace = 'public'::regnamespace
            AND (proname LIKE '%refresh%' OR proname LIKE '%actualizar%')
        ORDER BY proname;
    """)

    # 6. Tamaños de tablas
    results['sizes'] = execute_query(conn, "6. TAMANOS DE TABLAS", """
        SELECT
            tablename as nombre,
            pg_size_pretty(pg_total_relation_size('public.'||tablename)) as tamanio_total,
            pg_size_pretty(pg_relation_size('public.'||tablename)) as solo_datos,
            pg_size_pretty(pg_total_relation_size('public.'||tablename) - pg_relation_size('public.'||tablename)) as solo_indices
        FROM pg_tables
        WHERE schemaname = 'public'
            AND tablename IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios', 'periodos_fallidos')
        ORDER BY pg_total_relation_size('public.'||tablename) DESC;
    """)

    # 7. Índices nunca usados
    results['basura'] = execute_query(conn, "7. INDICES NUNCA USADOS (BASURA)", """
        SELECT
            tablename as tabla,
            indexrelname as indice,
            pg_size_pretty(pg_relation_size(indexrelid)) as tamanio_desperdiciado
        FROM pg_stat_user_indexes
        WHERE schemaname = 'public'
            AND idx_scan = 0
            AND indexrelname NOT LIKE '%pkey'
            AND tablename IN ('ventas_sire', 'compras_sire', 'enrolados', 'usuarios')
        ORDER BY pg_relation_size(indexrelid) DESC;
    """)

    # 8. Columnas de gestión
    results['columnas'] = execute_query(conn, "8. COLUMNAS DE GESTION EN ventas_sire", """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'ventas_sire'
            AND column_name IN ('estado1', 'estado2', 'ultima_actualizacion')
        ORDER BY column_name;
    """)

    # 9. Conteo de registros
    results['counts'] = execute_query(conn, "9. CONTEO DE REGISTROS", """
        SELECT 'ventas_sire' as tabla, COUNT(*) as registros FROM ventas_sire
        UNION ALL
        SELECT 'compras_sire', COUNT(*) FROM compras_sire
        UNION ALL
        SELECT 'enrolados', COUNT(*) FROM enrolados
        UNION ALL
        SELECT 'usuarios', COUNT(*) FROM usuarios;
    """)

# Resumen final
print("\n" + "=" * 80)
print("RESUMEN DE AUDITORIA")
print("=" * 80)

# Vistas materializadas
vm_count = len(results.get('vm', [])) if results.get('vm') is not None else 0
print(f"[OK] Vistas materializadas encontradas: {vm_count}")
if vm_count > 0:
    for row in results['vm']:
        print(f"     - {row[0]}: {row[1]} ({row[2]})")

# Vistas normales
v_count = len(results.get('v', [])) if results.get('v') is not None else 0
print(f"[OK] Vistas normales encontradas: {v_count}")
if v_count > 0:
    for row in results['v']:
        print(f"     - {row[0]}")

# Índices en ventas_sire
idx_ventas = len(results.get('idx_ventas', [])) if results.get('idx_ventas') is not None else 0
print(f"\n[OK] Indices en ventas_sire: {idx_ventas}")

# Índices en compras_sire
idx_compras = len(results.get('idx_compras', [])) if results.get('idx_compras') is not None else 0
print(f"[OK] Indices en compras_sire: {idx_compras}")

# Índices basura
basura_count = len(results.get('basura', [])) if results.get('basura') is not None else 0
if basura_count > 0:
    print(f"\n[WARNING] Indices NUNCA usados (basura): {basura_count}")
    for row in results['basura']:
        print(f"     - {row[0]}.{row[1]}: {row[2]} desperdiciado")
else:
    print(f"\n[OK] NO hay indices basura (todos se usan)")

# Columnas estado
columnas_count = len(results.get('columnas', [])) if results.get('columnas') is not None else 0
print(f"\n[OK] Columnas de gestion (estado1/estado2): {columnas_count}")

# Registros
registros = results.get('counts', [])
if registros and registros is not None:
    print("\n[OK] Registros por tabla:")
    for row in registros:
        print(f"     - {row[0]}: {row[1]:,} registros")

print("\n" + "=" * 80)
print("AUDITORIA COMPLETADA")
print("=" * 80)

# Cerrar conexión
engine.dispose()
