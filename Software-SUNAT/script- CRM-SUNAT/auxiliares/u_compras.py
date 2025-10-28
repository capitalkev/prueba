import requests
import time
import os
import zipfile
import io
from dotenv import load_dotenv

# --- Carga de variables de entorno ---
load_dotenv()
CLIENT_RUC = os.getenv("CLIENT_RUC")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USUARIO_SOL = os.getenv("USUARIO_SOL")
CLAVE_SOL = os.getenv("CLAVE_SOL")

# --- Constantes ---
URL_BASE_SIRE = "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv"
COD_LIBRO_RCE = "080000"  # Código de libro para RCE (Compras)
PERIODO = "202412"
TIPO_ARCHIVO_SOLICITUD = 1 # 0 para txt, 1 para csv

# 1. ================== Obtener el token de acceso ==================
print("1. Obteniendo token de acceso...")
token = None
payload = {
    "grant_type": "password",
    "scope": URL_BASE_SIRE,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "username": f"{CLIENT_RUC}{USUARIO_SOL}",
    "password": CLAVE_SOL,
}
url_token = f"https://api-seguridad.sunat.gob.pe/v1/clientessol/{CLIENT_ID}/oauth2/token/"

try:
    response = requests.post(url_token, data=payload, timeout=30)
    response.raise_for_status()
    token_data = response.json()
    token = token_data.get("access_token")
    print("   ✅ Token obtenido exitosamente.")
except requests.exceptions.RequestException as e:
    print(f"   ❌ Error al obtener el token: {e}")
    if e.response is not None:
        print(f"   Respuesta de SUNAT: {e.response.text}")

# Si no se obtuvo el token, se detiene el script
if not token:
    exit()

# 2. ================== Solicitar descarga de la propuesta ==================
print("\n2. Solicitando la descarga de la propuesta...")
ticket = None
params_solicitud = {
    "codTipoArchivo": TIPO_ARCHIVO_SOLICITUD,
    "codOrigenEnvio": "2"
}
headers_api = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}
url_solicitud = f"{URL_BASE_SIRE}/libros/rce/propuesta/web/propuesta/{PERIODO}/exportacioncomprobantepropuesta"

try:
    response = requests.get(url_solicitud, headers=headers_api, params=params_solicitud, timeout=30.0)
    response.raise_for_status()
    ticket = response.json().get("numTicket")
    print(f"   ✅ Solicitud enviada. Ticket obtenido: {ticket}")
except requests.exceptions.RequestException as e:
    print(f"   ❌ Error al solicitar la descarga: {e}")
    if e.response is not None:
        print(f"   Respuesta de SUNAT: {e.response.text}")

# Si no se obtuvo el ticket, se detiene el script
if not ticket:
    exit()

# 3. ================== Consultar estado del Ticket hasta que esté listo ==================
print("\n3. Consultando estado del ticket (esto puede tardar)...")
info_descarga = {}
url_consulta = f"{URL_BASE_SIRE}/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
params_consulta = {
    "numTicket": ticket,
    "perIni": PERIODO,
    "perFin": PERIODO,
    "page": "1",
    "perPage": "20"
}

while True:
    try:
        response = requests.get(url_consulta, headers=headers_api, params=params_consulta, timeout=60.0)
        response.raise_for_status()
        data = response.json()

        registro = data.get("registros", [{}])[0]
        estado = registro.get("desEstadoProceso")
        print(f"   Estado actual: {estado}")

        if estado == "Terminado":
            archivo_info = registro.get("archivoReporte", [{}])[0]
            info_descarga = {
                "codTipoArchivoReporte": archivo_info.get("codTipoAchivoReporte"),
                "nomArchivoReporte": archivo_info.get("nomArchivoReporte"), # Nombre del .zip
                "nomArchivoContenido": archivo_info.get("nomArchivoContenido"), # Nombre del .csv
                "codProceso": registro.get("codProceso"),
                "numTicket": registro.get("numTicket"),
                "perTributario": registro.get("perTributario")
            }
            print("   ✅ Proceso terminado. Información de descarga lista.")
            break
        elif estado in ["Error", "Rechazado"]:
            print("   ❌ El proceso del ticket ha fallado.")
            break

        time.sleep(5)  # Esperar 5 segundos antes de volver a consultar

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error al consultar el estado del ticket: {e}")
        break

# Si no se obtuvo la información de descarga, se detiene el script
if not info_descarga:
    exit()

# 4. ================== Descargar y Descomprimir el archivo ==================
print("\n4. Descargando y extrayendo el archivo...")
url_descarga = f"{URL_BASE_SIRE}/libros/rvierce/gestionprocesosmasivos/web/masivo/archivoreporte"
params_descarga = {
    "nomArchivoReporte": info_descarga.get("nomArchivoReporte"),
    "codTipoArchivoReporte": info_descarga.get("codTipoArchivoReporte"),
    "perTributario": info_descarga.get("perTributario"),
    "codProceso": info_descarga.get("codProceso"),
    "numTicket": info_descarga.get("numTicket"),
    "codLibro": COD_LIBRO_RCE
}

try:
    response = requests.get(url_descarga, headers={"Authorization": f"Bearer {token}"}, params=params_descarga, timeout=500)
    response.raise_for_status()

    # Usar io.BytesIO para tratar el contenido descargado como un archivo en memoria
    zip_file_in_memory = io.BytesIO(response.content)

    # Abrir el archivo ZIP
    with zipfile.ZipFile(zip_file_in_memory) as z:
        nombre_csv = info_descarga.get("nomArchivoContenido")
        print(f"   Extrayendo '{nombre_csv}' del archivo ZIP...")
        
        # Extraer el contenido del CSV
        csv_content = z.read(nombre_csv)
        
        # Guardar el archivo CSV en el disco
        with open(nombre_csv, "wb") as f:
            f.write(csv_content)
            
        print(f"   ✅ Archivo '{nombre_csv}' guardado exitosamente.")

except requests.exceptions.RequestException as e:
    print(f"   ❌ Error al descargar el archivo: {e}")
except zipfile.BadZipFile:
    print("   ❌ Error: El archivo descargado no es un ZIP válido.")
except KeyError:
    print(f"   ❌ Error: No se encontró el archivo '{info_descarga.get('nomArchivoContenido')}' dentro del ZIP.")