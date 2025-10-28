import requests
import time
import os
import zipfile
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
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
TIPO_ARCHIVO_SOLICITUD = 1 # 0 para txt, 1 para csv

# --- Generar la lista de períodos (últimos 13 meses + mes actual) ---
periodos = []
hoy = datetime.now()
for i in range(14):
    fecha_periodo = hoy - relativedelta(months=i)
    periodos.append(fecha_periodo.strftime("%Y%m"))
periodos.reverse() # Para procesar del más antiguo al más reciente
print(f"Se procesarán los siguientes períodos: {periodos}")

# 1. ================== Obtener el token de acceso ==================
print("\n1. Obteniendo token de acceso...")
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

# Bucle principal para procesar cada período
for periodo in periodos:
    print(f"\n{'='*20} INICIANDO PERÍODO: {periodo} {'='*20}")
    
    # 2. ================== Solicitar descarga de la propuesta ==================
    print(f"2. Solicitando la descarga para el período {periodo}...")
    ticket = None
    params_solicitud = {
        "codTipoArchivo": TIPO_ARCHIVO_SOLICITUD,
        "codOrigenEnvio": "2"
    }
    headers_api = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    url_solicitud = f"{URL_BASE_SIRE}/libros/rce/propuesta/web/propuesta/{periodo}/exportacioncomprobantepropuesta"

    try:
        response = requests.get(url_solicitud, headers=headers_api, params=params_solicitud, timeout=30.0)
        response.raise_for_status()
        ticket = response.json().get("numTicket")
        print(f"   ✅ Solicitud enviada. Ticket obtenido: {ticket}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error al solicitar la descarga para el período {periodo}: {e}")
        if e.response is not None:
            print(f"   Respuesta de SUNAT: {e.response.text}")
        continue # Saltar al siguiente período

    # 3. ================== Consultar estado del Ticket hasta que esté listo ==================
    print("\n3. Consultando estado del ticket (esto puede tardar)...")
    info_descarga = {}
    url_consulta = f"{URL_BASE_SIRE}/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
    params_consulta = {
        "numTicket": ticket,
        "perIni": periodo,
        "perFin": periodo,
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
            print(f"   Estado actual para {periodo}: {estado}")

            if estado == "Terminado":
                archivo_info = registro.get("archivoReporte", [{}])[0]
                info_descarga = {
                    "codTipoArchivoReporte": archivo_info.get("codTipoAchivoReporte"),
                    "nomArchivoReporte": archivo_info.get("nomArchivoReporte"),
                    "nomArchivoContenido": archivo_info.get("nomArchivoContenido"),
                    "codProceso": registro.get("codProceso"),
                    "numTicket": registro.get("numTicket"),
                    "perTributario": registro.get("perTributario")
                }
                print("   ✅ Proceso terminado. Información de descarga lista.")
                break
            elif estado in ["Error", "Rechazado"]:
                print(f"   ❌ El proceso del ticket {ticket} para el período {periodo} ha fallado.")
                info_descarga = {} # Limpiar para evitar descarga incorrecta
                break

            time.sleep(5)

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error al consultar el estado del ticket: {e}")
            info_descarga = {} # Limpiar para evitar descarga incorrecta
            break
    
    if not info_descarga:
        continue # Saltar al siguiente período

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

        zip_file_in_memory = io.BytesIO(response.content)

        with zipfile.ZipFile(zip_file_in_memory) as z:
            nombre_csv_original = info_descarga.get("nomArchivoContenido")
            # Nombre de archivo de salida personalizado con el período
            nombre_csv_salida = f"propuesta_compras_{periodo}.csv"
            
            print(f"   Extrayendo '{nombre_csv_original}' y guardando como '{nombre_csv_salida}'...")
            
            csv_content = z.read(nombre_csv_original)
            
            with open(nombre_csv_salida, "wb") as f:
                f.write(csv_content)
                
            print(f"   ✅ Archivo para el período {periodo} guardado exitosamente.")

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error al descargar el archivo para el período {periodo}: {e}")
    except (zipfile.BadZipFile, KeyError) as e:
        print(f"   ❌ Error al procesar el archivo ZIP para el período {periodo}: {e}")

print(f"\n{'='*20} PROCESO FINALIZADO {'='*20}")