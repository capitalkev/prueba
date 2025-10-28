# -*- coding: utf-8 -*-
"""
Script para procesamiento mensual paralelo de registros SIRE de SUNAT.
Procesa mes a mes retrocediendo desde el mes actual hasta 14 meses atrás.
Cada mes se procesa en paralelo para todos los enrolados.
Descarga compras (RCE) y ventas (RVIE) de múltiples empresas enroladas concurrentemente.
"""

import requests
import time
import os
import zipfile
import io
import pandas as pd
import re
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from sqlalchemy import func
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix para Windows: usar UTF-8 en stdout
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import CompraSire, VentaSire, Enrolado, PeriodoFallido
from csv_mapper import row_to_compra_sire, row_to_venta_sire

# =================================================================================================
# CONFIGURACIÓN
# =================================================================================================

load_dotenv()

# Constantes de API
URL_BASE_SIRE = "https://api-sire.sunat.gob.pe/v1/contribuyente/migeigv"
COD_LIBRO_RCE = os.getenv("COD_LIBRO_RCE", "080000")  # Código de libro para RCE (Compras)
COD_LIBRO_RVIE = os.getenv("COD_LIBRO_RVIE", "140000")  # Código de libro para RVIE (Ventas)
TIPO_ARCHIVO_SOLICITUD = 1

# Configuración de paralelización
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "3"))  # Número de enrolados a procesar en paralelo

# Número de meses a retroceder (14 meses = mes actual + 13 meses anteriores)
NUMERO_MESES = 14


# =================================================================================================
# FUNCIONES AUXILIARES
# =================================================================================================

def periodo_ya_procesado(ruc: str, periodo: str, tipo: str) -> bool:
    """
    Verifica si ya existen datos de este RUC y periodo en la BD.

    Args:
        ruc: RUC de la empresa
        periodo: Periodo en formato YYYYMM
        tipo: "compras" o "ventas"

    Returns:
        True si ya hay datos, False si no
    """
    db = SessionLocal()
    try:
        if tipo == "compras":
            count = (
                db.query(func.count(CompraSire.id))
                .filter(
                    CompraSire.ruc == ruc,
                    CompraSire.periodo == periodo,
                )
                .scalar()
            )
        else:  # ventas
            count = (
                db.query(func.count(VentaSire.id))
                .filter(
                    VentaSire.ruc == ruc,
                    VentaSire.periodo == periodo,
                )
                .scalar()
            )
        return count > 0
    finally:
        db.close()


def limpiar_csv_con_errores(archivo_csv: str, ruc: str, periodo: str, tipo: str) -> tuple:
    """
    Limpia un CSV eliminando líneas problemáticas y guardándolas en un log.

    Args:
        archivo_csv: Ruta al archivo CSV
        ruc: RUC de la empresa
        periodo: Periodo en formato YYYYMM
        tipo: "compras" o "ventas"

    Returns:
        Tupla (archivo_limpio, lineas_problematicas)
    """
    lineas_problematicas = []
    lineas_limpias = []

    os.makedirs("auxiliares", exist_ok=True)

    try:
        with open(archivo_csv, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        if not lineas:
            return None, []

        header = lineas[0]
        num_columnas_esperadas = len(header.split(','))
        lineas_limpias.append(header)

        for i, linea in enumerate(lineas[1:], start=2):
            num_columnas = len(linea.split(','))

            if num_columnas != num_columnas_esperadas:
                print(f"   ⚠️  Línea {i} tiene {num_columnas} campos, esperados {num_columnas_esperadas}. Moviendo a log...")
                lineas_problematicas.append({
                    'numero_linea': i,
                    'contenido': linea,
                    'num_columnas': num_columnas,
                    'esperadas': num_columnas_esperadas
                })
            else:
                lineas_limpias.append(linea)

        if lineas_problematicas:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_log = f"auxiliares/lineas_problematicas_{tipo}_{ruc}_{periodo}_{timestamp}.txt"

            with open(archivo_log, 'w', encoding='utf-8') as f:
                f.write(f"=== LÍNEAS PROBLEMÁTICAS - {tipo.upper()} ===\n")
                f.write(f"RUC: {ruc}\n")
                f.write(f"Periodo: {periodo}\n")
                f.write(f"Archivo original: {archivo_csv}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Columnas esperadas: {num_columnas_esperadas}\n")
                f.write(f"Total líneas problemáticas: {len(lineas_problematicas)}\n")
                f.write("=" * 80 + "\n\n")

                for linea_prob in lineas_problematicas:
                    f.write(f"Línea {linea_prob['numero_linea']} ({linea_prob['num_columnas']} columnas):\n")
                    f.write(linea_prob['contenido'])
                    f.write("\n" + "-" * 80 + "\n\n")

            print(f"   📝 {len(lineas_problematicas)} línea(s) problemática(s) guardadas en: {archivo_log}")

        archivo_limpio = archivo_csv.replace('.csv', '_limpio.csv')
        with open(archivo_limpio, 'w', encoding='utf-8') as f:
            f.writelines(lineas_limpias)

        return archivo_limpio, lineas_problematicas

    except Exception as e:
        print(f"   ❌ Error al limpiar CSV: {e}")
        return None, []


def guardar_csv_en_bd(archivo_csv: str, ruc: str, periodo: str, tipo: str) -> bool:
    """
    Lee el CSV y guarda los datos en la base de datos usando el CSV mapper.
    IMPORTANTE: Elimina datos existentes del periodo antes de insertar (modo refresh).

    Args:
        archivo_csv: Ruta al archivo CSV
        ruc: RUC de la empresa
        periodo: Periodo en formato YYYYMM
        tipo: "compras" o "ventas"

    Returns:
        True si se guardó exitosamente, False si hubo error
    """
    try:
        df = pd.read_csv(archivo_csv, encoding="utf-8")

        if df.empty:
            print(f"   ⚠️  El archivo CSV está vacío: {archivo_csv}")
            return False

        db = SessionLocal()
        try:
            # PASO 1: Eliminar datos existentes del periodo antes de insertar nuevos
            print(f"   🧹 Limpiando datos existentes de {tipo} para RUC {ruc}, periodo {periodo}...")
            if tipo == "compras":
                registros_eliminados = (
                    db.query(CompraSire)
                    .filter(
                        CompraSire.ruc == ruc,
                        CompraSire.periodo == periodo,
                    )
                    .delete()
                )
            else:  # ventas
                registros_eliminados = (
                    db.query(VentaSire)
                    .filter(
                        VentaSire.ruc == ruc,
                        VentaSire.periodo == periodo,
                    )
                    .delete()
                )

            db.commit()
            if registros_eliminados > 0:
                print(f"   ✅ {registros_eliminados} registros antiguos eliminados.")
            else:
                print("   ℹ️  No había registros previos para eliminar.")

            # PASO 2: Insertar nuevos registros usando el mapper
            registros_insertados = 0
            mapper_func = row_to_compra_sire if tipo == "compras" else row_to_venta_sire

            for _, row in df.iterrows():
                registro = mapper_func(row)
                db.add(registro)
                registros_insertados += 1

            db.commit()
            print(f"   ✅ {registros_insertados} registros de {tipo} guardados en la base de datos.")
            return True

        except Exception as e:
            db.rollback()
            print(f"   ❌ Error al guardar en la base de datos: {e}")
            return False
        finally:
            db.close()

    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Error al leer el archivo CSV: {error_msg}")

        # Verificar si es un error de tokenización (líneas con campos incorrectos)
        if "Error tokenizing data" in error_msg or "Expected" in error_msg:
            print("   🔧 Detectado error de campos. Intentando limpiar el CSV...")

            match = re.search(r'line (\d+)', error_msg)
            if match:
                linea_error = match.group(1)
                print(f"   📍 Error detectado en línea {linea_error}")

            archivo_limpio, lineas_problematicas = limpiar_csv_con_errores(
                archivo_csv, ruc, periodo, tipo
            )

            if archivo_limpio and os.path.exists(archivo_limpio):
                print(f"   🔄 Reintentando con archivo limpio...")
                return guardar_csv_en_bd(archivo_limpio, ruc, periodo, tipo)
            else:
                print("   ❌ No se pudo limpiar el archivo CSV.")
                return False
        else:
            return False


def registrar_periodo_fallido(ruc: str, periodo: str, tipo: str, motivo: str):
    """
    Registra un periodo que falló en la base de datos.

    Args:
        ruc: RUC de la empresa
        periodo: Periodo en formato YYYYMM
        tipo: "compras" o "ventas"
        motivo: Descripción del error
    """
    db = SessionLocal()
    try:
        # Verificar si ya existe este registro de fallo
        existe = (
            db.query(PeriodoFallido)
            .filter(
                PeriodoFallido.ruc == ruc,
                PeriodoFallido.periodo == periodo,
                PeriodoFallido.tipo == tipo,
                PeriodoFallido.resuelto is False,
            )
            .first()
        )

        if not existe:
            fallo = PeriodoFallido(
                ruc=ruc, periodo=periodo, tipo=tipo, motivo=motivo, resuelto=False
            )
            db.add(fallo)
            db.commit()
            print(f"   📝 Periodo {periodo} ({tipo}) registrado como fallido en la BD.")
    except Exception as e:
        db.rollback()
        print(f"   ⚠️  Error al registrar periodo fallido: {e}")
    finally:
        db.close()


# =================================================================================================
# FUNCIONES DE INTEGRACIÓN CON SUNAT API
# =================================================================================================

def obtener_token(client_ruc: str, client_id: str, client_secret: str, usuario_sol: str, clave_sol: str) -> str:
    """
    Obtiene token de acceso OAuth2 de SUNAT para un enrolado.

    Args:
        client_ruc: RUC del cliente
        client_id: ID del cliente SUNAT
        client_secret: Secret del cliente SUNAT
        usuario_sol: Usuario SOL
        clave_sol: Clave SOL

    Returns:
        Token de acceso o None si falla
    """
    payload = {
        "grant_type": "password",
        "scope": URL_BASE_SIRE,
        "client_id": client_id,
        "client_secret": client_secret,
        "username": f"{client_ruc}{usuario_sol.upper()}",
        "password": clave_sol,
    }
    url_token = f"https://api-seguridad.sunat.gob.pe/v1/clientessol/{client_id}/oauth2/token/"

    try:
        response = requests.post(url_token, data=payload, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        token = token_data.get("access_token")
        print("   ✅ Token obtenido exitosamente.")
        return token
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error al obtener el token: {e}")
        if e.response is not None:
            print(f"   Respuesta de SUNAT: {e.response.text}")
        return None


def procesar_periodo(enrolado: Enrolado, periodo: str, token: str, tipo: str) -> bool:
    """
    Procesa un periodo específico para un enrolado (compras o ventas).

    Args:
        enrolado: Instancia del enrolado a procesar
        periodo: Periodo en formato YYYYMM
        token: Token de acceso OAuth2
        tipo: "compras" o "ventas"

    Returns:
        True si se procesó exitosamente, False si hubo error
    """
    ruc = enrolado.ruc
    tipo_texto = "COMPRAS" if tipo == "compras" else "VENTAS"
    print(f"\n{'=' * 20} {tipo_texto} - PERÍODO: {periodo} {'=' * 20}")

    # Determinar URL según tipo
    if tipo == "compras":
        url_solicitud = f"{URL_BASE_SIRE}/libros/rce/propuesta/web/propuesta/{periodo}/exportacioncomprobantepropuesta"
        cod_libro = COD_LIBRO_RCE
    else:  # ventas
        url_solicitud = f"{URL_BASE_SIRE}/libros/rvie/propuesta/web/propuesta/{periodo}/exportapropuesta"
        cod_libro = COD_LIBRO_RVIE

    # ================== Solicitar descarga de la propuesta ==================
    print(f"2. Solicitando la descarga para el período {periodo} ({tipo})...")
    params_solicitud = {"codTipoArchivo": TIPO_ARCHIVO_SOLICITUD, "codOrigenEnvio": "2"}
    headers_api = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    try:
        response = requests.get(url_solicitud, headers=headers_api, params=params_solicitud, timeout=30.0)
        response.raise_for_status()
        ticket = response.json().get("numTicket")
        print(f"   ✅ Solicitud enviada. Ticket obtenido: {ticket}")
    except requests.exceptions.RequestException as e:
        motivo = f"Error al solicitar descarga: {str(e)}"
        print(f"   ❌ {motivo}")
        if e.response is not None:
            print(f"   Respuesta de SUNAT: {e.response.text}")
        registrar_periodo_fallido(ruc, periodo, tipo, motivo)
        return False

    # ================== Consultar estado del Ticket hasta que esté listo ==================
    print("\n3. Consultando estado del ticket (esto puede tardar)...")
    url_consulta = f"{URL_BASE_SIRE}/libros/rvierce/gestionprocesosmasivos/web/masivo/consultaestadotickets"
    params_consulta = {
        "numTicket": ticket,
        "perIni": periodo,
        "perFin": periodo,
        "page": "1",
        "perPage": "20",
    }

    info_descarga = {}
    while True:
        try:
            response = requests.get(url_consulta, headers=headers_api, params=params_consulta, timeout=60.0)
            response.raise_for_status()
            data = response.json()

            # Validar que existan registros en la respuesta
            registros = data.get("registros", [])
            if not registros or len(registros) == 0:
                motivo = f"No se encontraron registros para el ticket {ticket}. Respuesta: {data}"
                print(f"   ⚠️  {motivo}")
                registrar_periodo_fallido(ruc, periodo, tipo, motivo)
                return False

            registro = registros[0]
            estado = registro.get("desEstadoProceso")
            print(f"   Estado actual para {periodo}: {estado}")

            if estado == "Terminado":
                archivo_reporte = registro.get("archivoReporte", [])
                if not archivo_reporte or len(archivo_reporte) == 0:
                    motivo = f"No se encontró archivo de reporte en la respuesta para ticket {ticket}"
                    print(f"   ⚠️  {motivo}")
                    registrar_periodo_fallido(ruc, periodo, tipo, motivo)
                    return False

                archivo_info = archivo_reporte[0]
                info_descarga = {
                    "codTipoArchivoReporte": archivo_info.get("codTipoAchivoReporte"),
                    "nomArchivoReporte": archivo_info.get("nomArchivoReporte"),
                    "nomArchivoContenido": archivo_info.get("nomArchivoContenido"),
                    "codProceso": registro.get("codProceso"),
                    "numTicket": registro.get("numTicket"),
                    "perTributario": registro.get("perTributario"),
                }
                print("   ✅ Proceso terminado. Información de descarga lista.")
                break
            elif estado in ["Error", "Rechazado"]:
                motivo = f"Proceso de ticket {ticket} con estado: {estado}"
                print(f"   ❌ {motivo}")
                registrar_periodo_fallido(ruc, periodo, tipo, motivo)
                return False

            time.sleep(5)

        except requests.exceptions.RequestException as e:
            motivo = f"Error al consultar estado del ticket: {str(e)}"
            print(f"   ❌ {motivo}")
            registrar_periodo_fallido(ruc, periodo, tipo, motivo)
            return False
        except (IndexError, KeyError, TypeError) as e:
            motivo = f"Error al procesar respuesta del ticket {ticket}: {str(e)}"
            print(f"   ❌ {motivo}")
            registrar_periodo_fallido(ruc, periodo, tipo, motivo)
            return False

    if not info_descarga:
        return False

    # ================== Descargar y Descomprimir el archivo ==================
    print("\n4. Descargando y extrayendo el archivo...")
    url_descarga = f"{URL_BASE_SIRE}/libros/rvierce/gestionprocesosmasivos/web/masivo/archivoreporte"
    params_descarga = {
        "nomArchivoReporte": info_descarga.get("nomArchivoReporte"),
        "codTipoArchivoReporte": info_descarga.get("codTipoArchivoReporte"),
        "perTributario": info_descarga.get("perTributario"),
        "codProceso": info_descarga.get("codProceso"),
        "numTicket": info_descarga.get("numTicket"),
        "codLibro": cod_libro,
    }

    try:
        response = requests.get(
            url_descarga,
            headers={"Authorization": f"Bearer {token}"},
            params=params_descarga,
            timeout=500,
        )
        response.raise_for_status()

        zip_file_in_memory = io.BytesIO(response.content)

        with zipfile.ZipFile(zip_file_in_memory) as z:
            nombre_csv_original = info_descarga.get("nomArchivoContenido")
            nombre_csv_salida = f"propuesta_{tipo}_{ruc}_{periodo}.csv"

            print(f"   Extrayendo '{nombre_csv_original}' y guardando como '{nombre_csv_salida}'...")

            csv_content = z.read(nombre_csv_original)
            with open(nombre_csv_salida, "wb") as f:
                f.write(csv_content)

            print("   ✅ Archivo CSV guardado exitosamente.")

            # ================== Guardar en Base de Datos ==================
            print("\n5. Guardando datos en la base de datos...")

            exito = guardar_csv_en_bd(nombre_csv_salida, ruc, periodo, tipo)
            return exito

    except requests.exceptions.RequestException as e:
        motivo = f"Error al descargar archivo: {str(e)}"
        print(f"   ❌ {motivo}")
        registrar_periodo_fallido(ruc, periodo, tipo, motivo)
        return False
    except (zipfile.BadZipFile, KeyError) as e:
        motivo = f"Error al procesar archivo ZIP: {str(e)}"
        print(f"   ❌ {motivo}")
        registrar_periodo_fallido(ruc, periodo, tipo, motivo)
        return False


def procesar_enrolado(enrolado: Enrolado, periodo: str):
    """
    Procesa un mes específico para un enrolado (compras y ventas).
    Obtiene tokens FRESCOS para cada tipo para evitar expiración en modo paralelo.

    Args:
        enrolado: Instancia del enrolado a procesar
        periodo: Periodo a procesar en formato YYYYMM
    """
    print(f"\n{'#' * 60}")
    print(f"# PROCESANDO RUC: {enrolado.ruc}")
    print(f"# Estado: {enrolado.estado}")
    print(f"{'#' * 60}")

    # Procesar el periodo especificado
    print(f"\n📅 Procesando periodo: {periodo}")

    # Procesar COMPRAS y VENTAS
    exitos_compras = 0
    fallos_compras = 0
    exitos_ventas = 0
    fallos_ventas = 0

    # Procesar COMPRAS - Obtener token fresco
    print("\n--- Procesando COMPRAS ---")
    print("1. Obteniendo token de acceso FRESCO para COMPRAS...")
    token_compras = obtener_token(
        enrolado.ruc,
        enrolado.client_id,
        enrolado.client_secret,
        enrolado.usuario_sol,
        enrolado.clave_sol,
    )

    if token_compras:
        exito_compra = procesar_periodo(enrolado, periodo, token_compras, "compras")
        if exito_compra:
            exitos_compras += 1
        else:
            fallos_compras += 1
    else:
        print(f"❌ No se pudo obtener token para COMPRAS de {enrolado.ruc}.")
        fallos_compras += 1

    # Liberar token de memoria
    token_compras = None

    # Procesar VENTAS - Obtener token fresco
    print("\n--- Procesando VENTAS ---")
    print("1. Obteniendo token de acceso FRESCO para VENTAS...")
    token_ventas = obtener_token(
        enrolado.ruc,
        enrolado.client_id,
        enrolado.client_secret,
        enrolado.usuario_sol,
        enrolado.clave_sol,
    )

    if token_ventas:
        exito_venta = procesar_periodo(enrolado, periodo, token_ventas, "ventas")
        if exito_venta:
            exitos_ventas += 1
        else:
            fallos_ventas += 1
    else:
        print(f"❌ No se pudo obtener token para VENTAS de {enrolado.ruc}.")
        fallos_ventas += 1

    # Liberar token de memoria
    token_ventas = None

    print(f"\n{'=' * 60}")
    print(f"Resumen para RUC {enrolado.ruc}:")
    print(f"  COMPRAS - Exitosos: {exitos_compras}, Fallidos: {fallos_compras}")
    print(f"  VENTAS  - Exitosos: {exitos_ventas}, Fallidos: {fallos_ventas}")
    print(f"{'=' * 60}")


# =================================================================================================
# FLUJO PRINCIPAL
# =================================================================================================

def main():
    """Flujo principal: procesa mes a mes retrocediendo, todos los enrolados EN PARALELO por cada mes."""
    print(f"\n{'*' * 80}")
    print("* PROCESO MES A MES RETROCEDIENDO - ENROLADOS (MODO PARALELO)")
    print(f"* Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"* Número de meses a procesar: {NUMERO_MESES}")
    print(f"* Workers paralelos por mes: {MAX_WORKERS}")
    print(f"{'*' * 80}")

    # Obtener todos los enrolados pendientes
    db = SessionLocal()
    try:
        enrolados = db.query(Enrolado).filter(Enrolado.estado == "pendiente").all()

        if not enrolados:
            print("\n⚠️  No hay enrolados pendientes para procesar.")
            return

        print(f"\n📋 Se procesarán {len(enrolados)} enrolado(s):\n")
        for e in enrolados:
            print(f"  - RUC: {e.ruc} - Estado: {e.estado}")

    finally:
        db.close()

    # Calcular los periodos (mes actual y retrocediendo)
    hoy = datetime.now()
    periodos = []
    for i in range(NUMERO_MESES):
        fecha = hoy - relativedelta(months=i)
        periodo = fecha.strftime("%Y%m")
        periodos.append(periodo)

    print(f"\n📅 Periodos a procesar ({len(periodos)} meses):")
    print(f"   Desde: {periodos[-1]} hasta: {periodos[0]}\n")

    # Estadísticas globales
    estadisticas_globales = {
        "meses_procesados": 0,
        "total_exitosos": 0,
        "total_fallidos": 0
    }

    inicio_total = time.time()

    # Procesar mes a mes
    for idx, periodo in enumerate(periodos, 1):
        print(f"\n{'=' * 80}")
        print(f"  📅 MES {idx}/{len(periodos)}: {periodo}")
        print(f"{'=' * 80}")

        # Procesar todos los enrolados en paralelo para este mes
        print(f"\n🚀 Procesando {len(enrolados)} enrolados en paralelo para periodo {periodo}...\n")

        resultados_mes = {}
        exitosos = 0
        fallidos = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Enviar todos los enrolados al pool de workers con el periodo específico
            future_to_enrolado = {
                executor.submit(procesar_enrolado, enrolado, periodo): enrolado
                for enrolado in enrolados
            }

            # Procesar resultados a medida que se completan
            for future in as_completed(future_to_enrolado):
                enrolado = future_to_enrolado[future]
                try:
                    resultado = future.result()
                    resultados_mes[enrolado.ruc] = "✅ Completado"
                    exitosos += 1
                    print(f"\n✅ Finalizado RUC: {enrolado.ruc} - Periodo: {periodo}")
                except Exception as exc:
                    resultados_mes[enrolado.ruc] = f"❌ Error: {exc}"
                    fallidos += 1
                    print(f"\n❌ Error al procesar RUC {enrolado.ruc} - Periodo {periodo}: {exc}")

        # Resumen del mes
        print(f"\n{'=' * 80}")
        print(f"  📊 RESUMEN PERIODO {periodo}")
        print(f"{'=' * 80}")
        print(f"  ✅ Exitosos: {exitosos}/{len(enrolados)}")
        print(f"  ❌ Fallidos: {fallidos}/{len(enrolados)}")
        print(f"{'=' * 80}\n")

        estadisticas_globales["meses_procesados"] += 1
        estadisticas_globales["total_exitosos"] += exitosos
        estadisticas_globales["total_fallidos"] += fallidos

        # Pausa entre meses (excepto el último)
        if idx < len(periodos):
            print(f"⏸️  Pausa de 10 segundos antes del siguiente mes...\n")
            time.sleep(10)

    # Marcar enrolados como completos
    db = SessionLocal()
    try:
        enrolados_actualizados = db.query(Enrolado).filter(
            Enrolado.estado == "pendiente"
        ).update({"estado": "completo"})
        db.commit()

        print(f"\n✅ {enrolados_actualizados} enrolados marcados como 'completo'\n")

    finally:
        db.close()

    # Resumen final global
    duracion_total = (time.time() - inicio_total) / 60  # en minutos

    print(f"\n{'*' * 80}")
    print("* 🎉 PROCESO COMPLETADO")
    print(f"{'*' * 80}")
    print(f"  📅 Meses procesados: {estadisticas_globales['meses_procesados']}")
    print(f"  🏢 Enrolados procesados: {len(enrolados)}")
    print(f"  ✅ Total exitosos: {estadisticas_globales['total_exitosos']}")
    print(f"  ❌ Total fallidos: {estadisticas_globales['total_fallidos']}")
    print(f"  ⏱️  Tiempo total: {duracion_total:.2f} minutos")
    print(f"{'*' * 80}")
    print(f"\n💡 Para verificar los datos cargados ejecuta: python verificar_datos.py\n")


if __name__ == "__main__":
    main()
