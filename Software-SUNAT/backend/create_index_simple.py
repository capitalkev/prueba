"""
Script simple para crear el indice UNIQUE
"""
import psycopg2

# Credenciales
DB_USER = "postgres"
DB_PASSWORD = "Crm-sunat1"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "CRM-SUNAT"

print("Conectando a la base de datos...")

try:
    # Conectar
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

    cursor = conn.cursor()

    # Crear índice
    print("Creando indice UNIQUE en ventas_backend...")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ventas_backend_id_idx ON ventas_backend (id);")
    conn.commit()
    print("EXITO: Indice creado exitosamente!")

    # Verificar
    cursor.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'ventas_backend' AND indexname = 'ventas_backend_id_idx';
    """)

    row = cursor.fetchone()
    if row:
        print(f"VERIFICADO: {row[0]}")
    else:
        print("ADVERTENCIA: No se pudo verificar el indice")

    cursor.close()
    conn.close()
    print("Conexion cerrada")

except Exception as e:
    print(f"ERROR: {e}")
