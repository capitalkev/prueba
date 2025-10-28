# -*- coding: utf-8 -*-
"""
Script para carga manual de CSVs de SUNAT a la base de datos.
Útil como fallback cuando el proceso automático falla por timeouts o errores de API.
Permite cargar archivos CSV descargados manualmente desde SUNAT.
"""

import pandas as pd
import sys
import io

# Fix para Windows: usar UTF-8 en stdout
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import SessionLocal
from models import CompraSire, VentaSire, PeriodoFallido
from csv_mapper import row_to_compra_sire, row_to_venta_sire


def cargar_csv_manual(archivo_csv: str, ruc: str, periodo: str, tipo: str):
    """
    Carga manualmente un CSV descargado desde la API de SUNAT a la base de datos.
    Elimina datos existentes del periodo antes de insertar.
    Marca periodos fallidos como resueltos si existen.

    Args:
        archivo_csv: Ruta al archivo CSV
        ruc: RUC de la empresa
        periodo: Periodo en formato YYYYMM
        tipo: "compras" o "ventas"

    Uso:
        python cargar_csv_manual.py <archivo.csv> <RUC> <PERIODO> <TIPO>

    Ejemplos:
        python cargar_csv_manual.py propuesta_compras_20607723673_202410.csv 20607723673 202410 compras
        python cargar_csv_manual.py propuesta_ventas_20607723673_202410.csv 20607723673 202410 ventas
    """
    try:
        print(f"\n{'=' * 50}")
        print("Cargando CSV manualmente a la base de datos")
        print(f"Archivo: {archivo_csv}")
        print(f"RUC: {ruc}")
        print(f"Periodo: {periodo}")
        print(f"Tipo: {tipo}")
        print(f"{'=' * 50}\n")

        # Leer CSV
        df = pd.read_csv(archivo_csv, encoding='utf-8')

        if df.empty:
            print(f"❌ El archivo CSV está vacío: {archivo_csv}")
            return

        db = SessionLocal()
        try:
            # PASO 1: Eliminar data existente de este RUC + periodo + tipo
            print(f"🧹 Eliminando datos existentes para RUC {ruc}, periodo {periodo}, tipo {tipo}...")

            if tipo == "compras":
                registros_eliminados = db.query(CompraSire).filter(
                    CompraSire.ruc == ruc,
                    CompraSire.periodo == periodo
                ).delete()
            else:  # ventas
                registros_eliminados = db.query(VentaSire).filter(
                    VentaSire.ruc == ruc,
                    VentaSire.periodo == periodo
                ).delete()

            db.commit()

            if registros_eliminados > 0:
                print(f"🔄 {registros_eliminados} registros existentes eliminados.")
            else:
                print("ℹ️  No había registros previos para eliminar.")

            # PASO 2: Insertar nuevos registros usando el CSV mapper
            print(f"\n📥 Insertando {len(df)} registros de {tipo}...")
            registros_insertados = 0

            # Obtener el RUC real del CSV (primera fila)
            ruc_real = None
            if not df.empty:
                if tipo == "compras":
                    ruc_real = str(df.iloc[0].get('RUC', '')).strip()
                else:  # ventas
                    ruc_real = str(df.iloc[0].get('Ruc') or df.iloc[0].get('RUC', '')).strip()

            # Seleccionar mapper según tipo
            mapper_func = row_to_compra_sire if tipo == "compras" else row_to_venta_sire

            # Procesar cada fila del CSV
            for _, row in df.iterrows():
                registro = mapper_func(row)
                db.add(registro)
                registros_insertados += 1

            db.commit()
            print(f"✅ {registros_insertados} registros de {tipo} insertados exitosamente.")

            # PASO 3: Marcar el periodo fallido como resuelto si existe
            ruc_para_buscar = ruc_real if ruc_real else ruc
            periodo_fallido = db.query(PeriodoFallido).filter(
                PeriodoFallido.ruc == ruc_para_buscar,
                PeriodoFallido.periodo == periodo,
                PeriodoFallido.tipo == tipo,
                PeriodoFallido.resuelto is False
            ).first()

            if periodo_fallido:
                periodo_fallido.resuelto = True
                db.commit()
                print("✅ Periodo fallido marcado como resuelto en la base de datos.")
            else:
                print(f"ℹ️  No se encontró periodo fallido para RUC={ruc_para_buscar}, periodo={periodo}, tipo={tipo}")

            print(f"\n{'=' * 50}")
            print("✅ CARGA MANUAL COMPLETADA EXITOSAMENTE")
            print(f"{'=' * 50}\n")

        except Exception as e:
            db.rollback()
            print(f"❌ Error al guardar en la base de datos: {e}")
            print("\n⚠️  CONSEJO: Verifica que el CSV tenga la estructura correcta de SUNAT.")
        finally:
            db.close()

    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{archivo_csv}'")
        print("   Verifica que la ruta sea correcta y que el archivo exista.")
    except Exception as e:
        print(f"❌ Error al leer el archivo CSV: {e}")
        print("   Verifica que el archivo sea un CSV válido de SUNAT con codificación UTF-8.")


def mostrar_ayuda():
    """Muestra información de ayuda sobre cómo usar el script."""
    print("\n" + "=" * 70)
    print("CARGA MANUAL DE CSVs DE SUNAT A LA BASE DE DATOS")
    print("=" * 70)
    print("\nUSO:")
    print("  python cargar_csv_manual.py <archivo.csv> <RUC> <PERIODO> <TIPO>")
    print("\nPARÁMETROS:")
    print("  archivo.csv  - Ruta al archivo CSV descargado de SUNAT")
    print("  RUC          - RUC de la empresa (11 dígitos)")
    print("  PERIODO      - Periodo en formato YYYYMM (ej: 202410)")
    print("  TIPO         - Tipo de registro: 'compras' o 'ventas'")
    print("\nEJEMPLOS:")
    print("  # Cargar compras:")
    print("  python cargar_csv_manual.py propuesta_compras_20607723673_202410.csv 20607723673 202410 compras")
    print("\n  # Cargar ventas:")
    print("  python cargar_csv_manual.py propuesta_ventas_20607723673_202410.csv 20607723673 202410 ventas")
    print("\nNOTAS:")
    print("  - El script ELIMINA los datos existentes del periodo antes de insertar")
    print("  - Marca automáticamente los periodos fallidos como resueltos")
    print("  - El archivo CSV debe estar en formato UTF-8")
    print("  - Utiliza el CSV mapper para mapear TODAS las columnas automáticamente")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("\n❌ ERROR: Número incorrecto de argumentos\n")
        mostrar_ayuda()
        sys.exit(1)

    archivo = sys.argv[1]
    ruc = sys.argv[2]
    periodo = sys.argv[3]
    tipo = sys.argv[4].lower()

    # Validar tipo
    if tipo not in ["compras", "ventas"]:
        print("\n❌ ERROR: El tipo debe ser 'compras' o 'ventas'\n")
        mostrar_ayuda()
        sys.exit(1)

    # Validar RUC (debe ser 11 dígitos)
    if not ruc.isdigit() or len(ruc) != 11:
        print("\n❌ ERROR: El RUC debe tener exactamente 11 dígitos numéricos\n")
        print(f"   RUC proporcionado: {ruc} (longitud: {len(ruc)})\n")
        sys.exit(1)

    # Validar periodo (debe ser 6 dígitos en formato YYYYMM)
    if not periodo.isdigit() or len(periodo) != 6:
        print("\n❌ ERROR: El periodo debe tener formato YYYYMM (6 dígitos)\n")
        print(f"   Periodo proporcionado: {periodo} (longitud: {len(periodo)})\n")
        print("   Ejemplo válido: 202410\n")
        sys.exit(1)

    # Ejecutar carga manual
    cargar_csv_manual(archivo, ruc, periodo, tipo)
