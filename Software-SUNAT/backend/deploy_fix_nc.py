"""
Script para desplegar la corrección de notas de crédito a Cloud SQL
Ejecuta fix_ventas_backend_view.sql en la base de datos de producción
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "CRM-SUNAT")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

# Usar Cloud SQL Connector para conectar a Cloud SQL
try:
    from google.cloud.sql.connector import Connector
    import pg8000

    logger.info("Usando Google Cloud SQL Connector...")

    # Inicializar Cloud SQL Connector
    connector = Connector()

    def getconn():
        conn = connector.connect(
            CLOUD_SQL_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
        )
        return conn

    # Crear engine con Cloud SQL
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )

except ImportError:
    logger.warning("Cloud SQL Connector no disponible, intentando conexión local...")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)

logger.info("=" * 80)
logger.info("DESPLEGANDO CORRECCIÓN DE NOTAS DE CRÉDITO")
logger.info("=" * 80)

# Leer el archivo SQL
logger.info("\n1. Leyendo fix_ventas_backend_view.sql...")
with open("fix_ventas_backend_view.sql", "r", encoding="utf-8") as f:
    sql_content = f.read()

# Dividir en comandos individuales
# Filtrar comandos psql (\echo, etc.)
sql_commands = []
current_command = []

for line in sql_content.split("\n"):
    # Ignorar comandos psql
    if line.strip().startswith("\\"):
        continue

    # Ignorar comentarios
    if line.strip().startswith("--"):
        continue

    current_command.append(line)

    # Si encuentra punto y coma, es fin de comando
    if ";" in line:
        cmd = "\n".join(current_command).strip()
        if cmd and not cmd.startswith("--"):
            sql_commands.append(cmd)
        current_command = []

logger.info(f"   Encontrados {len(sql_commands)} comandos SQL")

# Ejecutar comandos
logger.info("\n2. Ejecutando comandos en Cloud SQL...")
with engine.connect() as conn:
    for i, cmd in enumerate(sql_commands, 1):
        try:
            # Mostrar preview del comando
            preview = cmd[:100].replace("\n", " ")
            logger.info(f"\n   [{i}/{len(sql_commands)}] Ejecutando: {preview}...")

            # Ejecutar
            conn.execute(text(cmd))
            conn.commit()

            logger.info(f"   ✓ Comando {i} ejecutado exitosamente")

        except Exception as e:
            logger.error(f"   ✗ Error en comando {i}: {e}")
            logger.error(f"   Comando: {cmd[:200]}")
            # Continuar con los demás comandos
            continue

logger.info("\n3. Verificando vista materializada...")
with engine.connect() as conn:
    # Verificar que la vista existe
    result = conn.execute(text("""
        SELECT
            matviewname,
            pg_size_pretty(pg_total_relation_size('public.'||matviewname)) as tamanio,
            CASE WHEN ispopulated THEN 'POBLADA' ELSE 'VACIA' END as estado
        FROM pg_matviews
        WHERE matviewname = 'ventas_backend'
    """))

    row = result.fetchone()
    if row:
        logger.info(f"   ✓ Vista materializada: {row[0]}")
        logger.info(f"   ✓ Tamaño: {row[1]}")
        logger.info(f"   ✓ Estado: {row[2]}")

        # Verificar registros
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN tipo_cp_doc = '1' THEN 1 END) as facturas,
                COUNT(CASE WHEN tipo_cp_doc = '7' THEN 1 END) as notas_credito,
                COUNT(CASE WHEN tiene_nota_credito = true THEN 1 END) as facturas_con_nc
            FROM ventas_backend
        """))

        row2 = result.fetchone()
        logger.info(f"\n   Registros en ventas_backend:")
        logger.info(f"   - Total: {row2[0]:,}")
        logger.info(f"   - Facturas: {row2[1]:,}")
        logger.info(f"   - Notas de crédito: {row2[2]:,}")
        logger.info(f"   - Facturas con NC: {row2[3]:,}")

        # Mostrar ejemplo
        logger.info(f"\n   Ejemplo de factura con NC:")
        result = conn.execute(text("""
            SELECT
                serie_cdp || '-' || nro_cp_inicial as factura,
                total_cp,
                monto_nota_credito,
                total_neto,
                moneda,
                notas_credito_asociadas
            FROM ventas_backend
            WHERE tiene_nota_credito = true
            LIMIT 3
        """))

        for row3 in result:
            logger.info(f"\n      Factura: {row3[0]}")
            logger.info(f"      Total original: {row3[1]} {row3[4]}")
            logger.info(f"      Monto NC: {row3[2]} {row3[4]}")
            logger.info(f"      Total neto: {row3[3]} {row3[4]}")
            logger.info(f"      NC asociadas: {row3[5]}")

    else:
        logger.error("   ✗ La vista materializada NO se creó correctamente")

logger.info("\n" + "=" * 80)
logger.info("✅ DESPLIEGUE COMPLETADO")
logger.info("=" * 80)
logger.info("\nSIGUIENTES PASOS:")
logger.info("1. Verificar que main.py tenga los cambios (FROM ventas_backend)")
logger.info("2. Desplegar el backend a Cloud Run")
logger.info("3. Verificar en el frontend que muestre los montos netos")
logger.info("")
