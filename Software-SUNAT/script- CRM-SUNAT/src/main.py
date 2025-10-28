# -*- coding: utf-8 -*-
"""
Script principal para procesamiento de registros SIRE de SUNAT.
Procesa histórico completo (14 meses) para enrolados pendientes y mes actual para enrolados completos.
Descarga compras (RCE) y ventas (RVIE) de múltiples empresas enroladas.
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

# Calcular periodos
hoy = datetime.now()
periodo_actual = hoy.strftime("%Y%m")


# =================================================================================================
# FUNCIONES AUXILIARES
# =================================================================================================

def generar_periodos(cantidad_meses: int) -> list:
    """
    Genera lista de periodos históricos en formato YYYYMM.

    Args:
        cantidad_meses: Número de meses hacia atrás desde hoy

    Returns:
        Lista de periodos en orden cronológico (más antiguo primero)
    """
    periodos = []
    for i in range(cantidad_meses):
        fecha_periodo = hoy - relativedelta(months=i)
        periodos.append(fecha_periodo.strftime("%Y%m"))
    periodos.reverse()
    return periodos


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
            registros_insertados = 0

            # Usar el mapper correspondiente según el tipo
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

    # Verificar si ya existe data de este periodo (excepto si es el mes actual)
    if periodo != periodo_actual and periodo_ya_procesado(ruc, periodo, tipo):
        print(f"   ⏭️  El periodo {periodo} ({tipo}) ya fue procesado anteriormente. Saltando...")
        return True

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

            registros = data.get("registros", [])
            if not registros:
                print(f"   ⏳ Esperando respuesta de SUNAT para {periodo}... (sin registros aún)")
                time.sleep(5)
                continue

            registro = registros[0]
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

            print("✅ Archivo CSV guardado exitosamente.")

            # ================== Guardar en Base de Datos ==================
            print("\n5. Guardando datos en la base de datos...")

            # Si es el mes actual, eliminar data existente antes de insertar
            if periodo == periodo_actual:
                db = SessionLocal()
                try:
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
                        print(f"   🔄 {registros_eliminados} registros del periodo actual eliminados para actualización.")
                except Exception as e:
                    db.rollback()
                    print(f"   ⚠️  Error al limpiar datos del periodo actual: {e}")
                finally:
                    db.close()

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


def procesar_enrolado(enrolado: Enrolado):
    """
    Procesa todos los periodos necesarios para un enrolado (compras y ventas).

    Args:
        enrolado: Instancia del enrolado a procesar
    """
    print(f"\n{'#' * 60}")
    print(f"# PROCESANDO RUC: {enrolado.ruc}")
    print(f"# Estado: {enrolado.estado}")
    print(f"{'#' * 60}")

    # Obtener token de acceso
    print("\n1. Obteniendo token de acceso...")
    token = obtener_token(
        enrolado.ruc,
        enrolado.client_id,
        enrolado.client_secret,
        enrolado.usuario_sol,
        enrolado.clave_sol,
    )

    if not token:
        print(f"❌ No se pudo obtener token para {enrolado.ruc}. Saltando...")
        return

    # Determinar qué periodos procesar según el estado
    if enrolado.estado == "pendiente":
        periodos = generar_periodos(14)
        print(f"\n📅 Procesamiento inicial: {len(periodos)} periodos ({periodos[0]} - {periodos[-1]})")
    else:
        periodos = [periodo_actual]
        print(f"\n📅 Actualización: solo periodo actual ({periodo_actual})")

    # Procesar cada periodo para COMPRAS y VENTAS
    exitos_compras = 0
    fallos_compras = 0
    exitos_ventas = 0
    fallos_ventas = 0

    for periodo in periodos:
        # Procesar COMPRAS
        print("\n--- Procesando COMPRAS ---")
        exito_compra = procesar_periodo(enrolado, periodo, token, "compras")
        if exito_compra:
            exitos_compras += 1
        else:
            fallos_compras += 1

        # Procesar VENTAS
        print("\n--- Procesando VENTAS ---")
        exito_venta = procesar_periodo(enrolado, periodo, token, "ventas")
        if exito_venta:
            exitos_ventas += 1
        else:
            fallos_ventas += 1

    # Actualizar estado del enrolado si completó el procesamiento inicial
    if enrolado.estado == "pendiente" and (exitos_compras > 0 or exitos_ventas > 0):
        db = SessionLocal()
        try:
            enrolado_db = db.query(Enrolado).filter(Enrolado.id == enrolado.id).first()
            enrolado_db.estado = "completo"
            db.commit()
            print("\n✅ Estado del enrolado actualizado a 'completo'")
        except Exception as e:
            db.rollback()
            print(f"\n⚠️  Error al actualizar estado del enrolado: {e}")
        finally:
            db.close()

    print(f"\n{'=' * 60}")
    print(f"Resumen para RUC {enrolado.ruc}:")
    print(f"  COMPRAS - Exitosos: {exitos_compras}, Fallidos: {fallos_compras}")
    print(f"  VENTAS  - Exitosos: {exitos_ventas}, Fallidos: {fallos_ventas}")
    print(f"{'=' * 60}")


# =================================================================================================
# FLUJO PRINCIPAL
# =================================================================================================

def main():
    """Flujo principal: procesa todos los enrolados."""
    print(f"\n{'*' * 60}")
    print("* INICIO DEL PROCESO AUTOMÁTICO DE ENROLADOS")
    print(f"* Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*' * 60}")

    # Obtener todos los enrolados
    db = SessionLocal()
    try:
        enrolados = db.query(Enrolado).all()

        if not enrolados:
            print("\n⚠️  No hay enrolados para procesar.")
            return

        print(f"\n📋 Se procesarán {len(enrolados)} enrolado(s):\n")
        for e in enrolados:
            print(f"  - RUC: {e.ruc} - Estado: {e.estado}")

    finally:
        db.close()

    # Procesar cada enrolado
    for enrolado in enrolados:
        procesar_enrolado(enrolado)

    print(f"\n{'*' * 60}")
    print("* PROCESO FINALIZADO")
    print(f"* Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*' * 60}")


if __name__ == "__main__":
    main()
