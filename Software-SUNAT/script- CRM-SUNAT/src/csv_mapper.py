"""
Módulo de mapeo CSV a modelos de base de datos.
Proporciona funciones para convertir filas de CSV de SUNAT a instancias de modelo.
"""

import pandas as pd
from datetime import datetime
from typing import Optional
from models import CompraSire, VentaSire


def parse_date(date_value) -> Optional[datetime]:
    """
    Parsea una fecha en formato DD/MM/YYYY a objeto date.

    Args:
        date_value: Valor de fecha del CSV (puede ser string o pd.NaT)

    Returns:
        datetime.date o None si no se pudo parsear
    """
    if pd.isna(date_value):
        return None
    try:
        return pd.to_datetime(str(date_value), format='%d/%m/%Y').date()
    except (ValueError, TypeError):
        return None


def parse_numeric(value, decimal_places: int = 2) -> Optional[float]:
    """
    Parsea un valor numérico del CSV.

    Args:
        value: Valor del CSV
        decimal_places: Número de decimales (para redondeo)

    Returns:
        float o None si el valor es nulo
    """
    if pd.isna(value):
        return None
    try:
        return round(float(value), decimal_places)
    except (ValueError, TypeError):
        return None


def safe_str(value, default: str = None) -> Optional[str]:
    """
    Convierte un valor a string de forma segura.

    Args:
        value: Valor del CSV
        default: Valor por defecto si es nulo

    Returns:
        String o None
    """
    if pd.isna(value):
        return default
    return str(value).strip()


def row_to_compra_sire(row: pd.Series) -> CompraSire:
    """
    Convierte una fila del CSV de compras a una instancia de CompraSire.

    Args:
        row: Fila del DataFrame de pandas

    Returns:
        Instancia de CompraSire con todos los campos mapeados
    """
    return CompraSire(
        # Metadata y claves
        ruc=safe_str(row.get('RUC')),
        razon_social=safe_str(row.get('Apellidos y Nombres o Razón social')),
        periodo=safe_str(row.get('Periodo')),
        car_sunat=safe_str(row.get('CAR SUNAT')),
        ultima_actualizacion=datetime.now(),

        # Fechas
        fecha_emision=parse_date(row.get('Fecha de emisión')),
        fecha_vcto_pago=parse_date(row.get('Fecha Vcto/Pago')),

        # Información del comprobante
        tipo_cp_doc=safe_str(row.get('Tipo CP/Doc.')),
        serie_cdp=safe_str(row.get('Serie del CDP')),
        anio=safe_str(row.get('Año')),
        nro_cp_inicial=safe_str(row.get('Nro CP o Doc. Nro Inicial (Rango)')),
        nro_final=safe_str(row.get('Nro Final (Rango)')),

        # Información del proveedor
        tipo_doc_identidad=safe_str(row.get('Tipo Doc Identidad')),
        nro_doc_identidad=safe_str(row.get('Nro Doc Identidad')),
        apellidos_nombres_razon_social=safe_str(row.get('Apellidos Nombres/ Razón  Social')),

        # Bases imponibles y tributos - Domiciliado Gravado (DG)
        bi_gravado_dg=parse_numeric(row.get('BI Gravado DG')),
        igv_ipm_dg=parse_numeric(row.get('IGV / IPM DG')),

        # Bases imponibles y tributos - Domiciliado Gravado No Gravado (DGNG)
        bi_gravado_dgng=parse_numeric(row.get('BI Gravado DGNG')),
        igv_ipm_dgng=parse_numeric(row.get('IGV / IPM DGNG')),

        # Bases imponibles y tributos - Domiciliado No Gravado (DNG)
        bi_gravado_dng=parse_numeric(row.get('BI Gravado DNG')),
        igv_ipm_dng=parse_numeric(row.get('IGV / IPM DNG')),

        # Otros valores y tributos
        valor_adq_ng=parse_numeric(row.get('Valor Adq. NG')),
        isc=parse_numeric(row.get('ISC')),
        icbper=parse_numeric(row.get('ICBPER')),
        otros_trib_cargos=parse_numeric(row.get('Otros Trib/ Cargos')),
        total_cp=parse_numeric(row.get('Total CP')),

        # Moneda y tipo de cambio
        moneda=safe_str(row.get('Moneda')),
        tipo_cambio=parse_numeric(row.get('Tipo de Cambio'), decimal_places=4),

        # Información de documentos modificados
        fecha_emision_doc_modificado=parse_date(row.get('Fecha Emisión Doc Modificado')),
        tipo_cp_modificado=safe_str(row.get('Tipo CP Modificado')),
        serie_cp_modificado=safe_str(row.get('Serie CP Modificado')),
        cod_dam_dsi=safe_str(row.get('COD. DAM O DSI')),
        nro_cp_modificado=safe_str(row.get('Nro CP Modificado')),

        # Clasificación y proyectos
        clasif_bss_sss=safe_str(row.get('Clasif de Bss y Sss')),
        id_proyecto_operadores=safe_str(row.get('ID Proyecto Operadores')),
        porc_part=parse_numeric(row.get('PorcPart')),
        imb=parse_numeric(row.get('IMB')),

        # Información adicional
        car_orig_ind_e_i=safe_str(row.get('CAR Orig/ Ind E o I')),
        detraccion=safe_str(row.get('Detracción')),
        tipo_nota=safe_str(row.get('Tipo de Nota')),
        est_comp=safe_str(row.get('Est. Comp.')),
        incal=safe_str(row.get('Incal')),

        # Campos CLU (Campos Libres de Usuario)
        clu1=safe_str(row.get('CLU1')),
        clu2=safe_str(row.get('CLU2')),
        clu3=safe_str(row.get('CLU3')),
        clu4=safe_str(row.get('CLU4')),
        clu5=safe_str(row.get('CLU5')),
        clu6=safe_str(row.get('CLU6')),
        clu7=safe_str(row.get('CLU7')),
        clu8=safe_str(row.get('CLU8')),
        clu9=safe_str(row.get('CLU9')),
        clu10=safe_str(row.get('CLU10')),
        clu11=safe_str(row.get('CLU11')),
        clu12=safe_str(row.get('CLU12')),
        clu13=safe_str(row.get('CLU13')),
        clu14=safe_str(row.get('CLU14')),
        clu15=safe_str(row.get('CLU15')),
        clu16=safe_str(row.get('CLU16')),
        clu17=safe_str(row.get('CLU17')),
        clu18=safe_str(row.get('CLU18')),
        clu19=safe_str(row.get('CLU19')),
        clu20=safe_str(row.get('CLU20')),
        clu21=safe_str(row.get('CLU21')),
        clu22=safe_str(row.get('CLU22')),
        clu23=safe_str(row.get('CLU23')),
        clu24=safe_str(row.get('CLU24')),
        clu25=safe_str(row.get('CLU25')),
        clu26=safe_str(row.get('CLU26')),
        clu27=safe_str(row.get('CLU27')),
        clu28=safe_str(row.get('CLU28')),
        clu29=safe_str(row.get('CLU29')),
        clu30=safe_str(row.get('CLU30')),
        clu31=safe_str(row.get('CLU31')),
        clu32=safe_str(row.get('CLU32')),
        clu33=safe_str(row.get('CLU33')),
        clu34=safe_str(row.get('CLU34')),
        clu35=safe_str(row.get('CLU35')),
        clu36=safe_str(row.get('CLU36')),
        clu37=safe_str(row.get('CLU37')),
        clu38=safe_str(row.get('CLU38')),
        clu39=safe_str(row.get('CLU39')),
    )


def row_to_venta_sire(row: pd.Series) -> VentaSire:
    """
    Convierte una fila del CSV de ventas a una instancia de VentaSire.

    Args:
        row: Fila del DataFrame de pandas

    Returns:
        Instancia de VentaSire con todos los campos mapeados
    """
    return VentaSire(
        # Metadata y claves
        ruc=safe_str(row.get('Ruc') or row.get('RUC')),  # Puede venir como "Ruc" o "RUC"
        razon_social=safe_str(row.get('Razon Social')),
        periodo=safe_str(row.get('Periodo')),
        car_sunat=safe_str(row.get('CAR SUNAT')),
        ultima_actualizacion=datetime.now(),

        # Fechas
        fecha_emision=parse_date(row.get('Fecha de emisión')),
        fecha_vcto_pago=parse_date(row.get('Fecha Vcto/Pago')),

        # Información del comprobante
        tipo_cp_doc=safe_str(row.get('Tipo CP/Doc.')),
        serie_cdp=safe_str(row.get('Serie del CDP')),
        nro_cp_inicial=safe_str(row.get('Nro CP o Doc. Nro Inicial (Rango)')),
        nro_final=safe_str(row.get('Nro Final (Rango)')),

        # Información del cliente
        tipo_doc_identidad=safe_str(row.get('Tipo Doc Identidad')),
        nro_doc_identidad=safe_str(row.get('Nro Doc Identidad')),
        apellidos_nombres_razon_social=safe_str(row.get('Apellidos Nombres/ Razón Social')),

        # Valores de exportación y bases imponibles
        valor_facturado_exportacion=parse_numeric(row.get('Valor Facturado Exportación')),
        bi_gravada=parse_numeric(row.get('BI Gravada')),
        dscto_bi=parse_numeric(row.get('Dscto BI')),
        igv_ipm=parse_numeric(row.get('IGV / IPM')),
        dscto_igv_ipm=parse_numeric(row.get('Dscto IGV / IPM')),
        mto_exonerado=parse_numeric(row.get('Mto Exonerado')),
        mto_inafecto=parse_numeric(row.get('Mto Inafecto')),

        # Otros tributos
        isc=parse_numeric(row.get('ISC')),
        bi_grav_ivap=parse_numeric(row.get('BI Grav IVAP')),
        ivap=parse_numeric(row.get('IVAP')),
        icbper=parse_numeric(row.get('ICBPER')),
        otros_tributos=parse_numeric(row.get('Otros Tributos')),
        total_cp=parse_numeric(row.get('Total CP')),

        # Moneda y tipo de cambio
        moneda=safe_str(row.get('Moneda')),
        tipo_cambio=parse_numeric(row.get('Tipo Cambio'), decimal_places=4),

        # Información de documentos modificados
        fecha_emision_doc_modificado=parse_date(row.get('Fecha Emisión Doc Modificado')),
        tipo_cp_modificado=safe_str(row.get('Tipo CP Modificado')),
        serie_cp_modificado=safe_str(row.get('Serie CP Modificado')),
        nro_cp_modificado=safe_str(row.get('Nro CP Modificado')),

        # Información adicional
        id_proyecto_operadores_atribucion=safe_str(row.get('ID Proyecto Operadores Atribución')),
        tipo_nota=safe_str(row.get('Tipo de Nota')),
        est_comp=safe_str(row.get('Est. Comp')),
        valor_fob_embarcado=parse_numeric(row.get('Valor FOB Embarcado')),
        valor_op_gratuitas=parse_numeric(row.get('Valor OP Gratuitas')),
        tipo_operacion=safe_str(row.get('Tipo Operación')),
        dam_cp=safe_str(row.get('DAM / CP')),
        clu=safe_str(row.get('CLU')),
    )
