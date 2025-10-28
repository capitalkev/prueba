from sqlalchemy import Column, Integer, String, Numeric, Date, Index, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Enrolado(Base):
    """
    Modelo para empresas enroladas en el sistema.
    Almacena credenciales SUNAT y estado de procesamiento.
    """
    __tablename__ = "enrolados"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(11), nullable=False, unique=True, index=True)
    usuario_sol = Column(String(50), nullable=False)
    clave_sol = Column(String(100), nullable=False)
    client_id = Column(String(100), nullable=False)
    client_secret = Column(String(100), nullable=False)
    estado = Column(String(20), default="pendiente", nullable=False)  # "pendiente" o "completo"

    def __repr__(self):
        return f"<Enrolado(ruc={self.ruc}, estado={self.estado})>"


class PeriodoFallido(Base):
    """
    Modelo para tracking de periodos que fallaron durante el procesamiento.
    Permite reintento manual y seguimiento de errores.
    """
    __tablename__ = "periodos_fallidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(11), nullable=False, index=True)
    periodo = Column(String(6), nullable=False, index=True)
    tipo = Column(String(10), nullable=False)  # "compras" o "ventas"
    fecha_fallo = Column(DateTime, default=datetime.now)
    motivo = Column(Text)
    resuelto = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index('idx_ruc_periodo_tipo_fallo', 'ruc', 'periodo', 'tipo'),
    )

    def __repr__(self):
        return f"<PeriodoFallido(ruc={self.ruc}, periodo={self.periodo}, tipo={self.tipo}, resuelto={self.resuelto})>"


class CompraSire(Base):
    """
    Modelo completo para Registro de Compras Electrónicas (RCE) - SIRE SUNAT.
    Almacena todas las columnas del CSV de compras descargado de SUNAT (80 columnas).
    """
    __tablename__ = "compras_sire"

    # Metadata y claves
    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(11), nullable=False, index=True, comment="RUC de la empresa")
    razon_social = Column(String(500), comment="Razón social de la empresa")
    periodo = Column(String(6), nullable=False, index=True, comment="Periodo tributario YYYYMM")
    car_sunat = Column(String(100), comment="Código de Autenticación de Registro SUNAT")
    ultima_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="Fecha y hora de última actualización")

    # Fechas
    fecha_emision = Column(Date, comment="Fecha de emisión del comprobante")
    fecha_vcto_pago = Column(Date, comment="Fecha de vencimiento o pago")

    # Información del comprobante
    tipo_cp_doc = Column(String(10), comment="Tipo de comprobante o documento")
    serie_cdp = Column(String(20), comment="Serie del comprobante de pago")
    anio = Column(String(4), comment="Año del comprobante")
    nro_cp_inicial = Column(String(50), comment="Número de comprobante o número inicial del rango")
    nro_final = Column(String(50), comment="Número final del rango")

    # Información del proveedor
    tipo_doc_identidad = Column(String(2), comment="Tipo de documento de identidad del proveedor")
    nro_doc_identidad = Column(String(15), index=True, comment="Número de documento del proveedor")
    apellidos_nombres_razon_social = Column(String(500), comment="Apellidos y nombres o razón social del proveedor")

    # Bases imponibles y tributos - Domiciliado Gravado (DG)
    bi_gravado_dg = Column(Numeric(15, 2), comment="Base imponible gravada - Domiciliado Gravado")
    igv_ipm_dg = Column(Numeric(15, 2), comment="IGV/IPM - Domiciliado Gravado")

    # Bases imponibles y tributos - Domiciliado Gravado No Gravado (DGNG)
    bi_gravado_dgng = Column(Numeric(15, 2), comment="Base imponible gravada - Domiciliado Gravado No Gravado")
    igv_ipm_dgng = Column(Numeric(15, 2), comment="IGV/IPM - Domiciliado Gravado No Gravado")

    # Bases imponibles y tributos - Domiciliado No Gravado (DNG)
    bi_gravado_dng = Column(Numeric(15, 2), comment="Base imponible gravada - Domiciliado No Gravado")
    igv_ipm_dng = Column(Numeric(15, 2), comment="IGV/IPM - Domiciliado No Gravado")

    # Otros valores y tributos
    valor_adq_ng = Column(Numeric(15, 2), comment="Valor de adquisición no gravado")
    isc = Column(Numeric(15, 2), comment="Impuesto Selectivo al Consumo")
    icbper = Column(Numeric(15, 2), comment="Impuesto al Consumo de Bolsas de Plástico")
    otros_trib_cargos = Column(Numeric(15, 2), comment="Otros tributos y cargos")
    total_cp = Column(Numeric(15, 2), comment="Total del comprobante de pago")

    # Moneda y tipo de cambio
    moneda = Column(String(3), comment="Código de moneda (PEN, USD, etc.)")
    tipo_cambio = Column(Numeric(10, 4), comment="Tipo de cambio")

    # Información de documentos modificados
    fecha_emision_doc_modificado = Column(Date, comment="Fecha de emisión del documento modificado")
    tipo_cp_modificado = Column(String(10), comment="Tipo de comprobante modificado")
    serie_cp_modificado = Column(String(20), comment="Serie del comprobante modificado")
    cod_dam_dsi = Column(String(50), comment="Código DAM o DSI")
    nro_cp_modificado = Column(String(50), comment="Número del comprobante modificado")

    # Clasificación y proyectos
    clasif_bss_sss = Column(String(50), comment="Clasificación de bienes y servicios")
    id_proyecto_operadores = Column(String(50), comment="ID de proyecto para operadores de atribución")
    porc_part = Column(Numeric(5, 2), comment="Porcentaje de participación")
    imb = Column(Numeric(15, 2), comment="Importe de base")

    # Información adicional
    car_orig_ind_e_i = Column(String(100), comment="CAR original o indicador de exportación/importación")
    detraccion = Column(String(10), comment="Indicador de detracción")
    tipo_nota = Column(String(10), comment="Tipo de nota (crédito/débito)")
    est_comp = Column(String(5), comment="Estado del comprobante")
    incal = Column(String(5), comment="Indicador de cálculo")

    # Campos CLU (Campos Libres de Usuario) - 39 campos adicionales
    clu1 = Column(String(200), comment="Campo libre de usuario 1")
    clu2 = Column(String(200), comment="Campo libre de usuario 2")
    clu3 = Column(String(200), comment="Campo libre de usuario 3")
    clu4 = Column(String(200), comment="Campo libre de usuario 4")
    clu5 = Column(String(200), comment="Campo libre de usuario 5")
    clu6 = Column(String(200), comment="Campo libre de usuario 6")
    clu7 = Column(String(200), comment="Campo libre de usuario 7")
    clu8 = Column(String(200), comment="Campo libre de usuario 8")
    clu9 = Column(String(200), comment="Campo libre de usuario 9")
    clu10 = Column(String(200), comment="Campo libre de usuario 10")
    clu11 = Column(String(200), comment="Campo libre de usuario 11")
    clu12 = Column(String(200), comment="Campo libre de usuario 12")
    clu13 = Column(String(200), comment="Campo libre de usuario 13")
    clu14 = Column(String(200), comment="Campo libre de usuario 14")
    clu15 = Column(String(200), comment="Campo libre de usuario 15")
    clu16 = Column(String(200), comment="Campo libre de usuario 16")
    clu17 = Column(String(200), comment="Campo libre de usuario 17")
    clu18 = Column(String(200), comment="Campo libre de usuario 18")
    clu19 = Column(String(200), comment="Campo libre de usuario 19")
    clu20 = Column(String(200), comment="Campo libre de usuario 20")
    clu21 = Column(String(200), comment="Campo libre de usuario 21")
    clu22 = Column(String(200), comment="Campo libre de usuario 22")
    clu23 = Column(String(200), comment="Campo libre de usuario 23")
    clu24 = Column(String(200), comment="Campo libre de usuario 24")
    clu25 = Column(String(200), comment="Campo libre de usuario 25")
    clu26 = Column(String(200), comment="Campo libre de usuario 26")
    clu27 = Column(String(200), comment="Campo libre de usuario 27")
    clu28 = Column(String(200), comment="Campo libre de usuario 28")
    clu29 = Column(String(200), comment="Campo libre de usuario 29")
    clu30 = Column(String(200), comment="Campo libre de usuario 30")
    clu31 = Column(String(200), comment="Campo libre de usuario 31")
    clu32 = Column(String(200), comment="Campo libre de usuario 32")
    clu33 = Column(String(200), comment="Campo libre de usuario 33")
    clu34 = Column(String(200), comment="Campo libre de usuario 34")
    clu35 = Column(String(200), comment="Campo libre de usuario 35")
    clu36 = Column(String(200), comment="Campo libre de usuario 36")
    clu37 = Column(String(200), comment="Campo libre de usuario 37")
    clu38 = Column(String(200), comment="Campo libre de usuario 38")
    clu39 = Column(String(200), comment="Campo libre de usuario 39")

    __table_args__ = (
        Index('idx_compras_ruc_periodo', 'ruc', 'periodo'),
        Index('idx_compras_proveedor', 'nro_doc_identidad'),
        Index('idx_compras_fecha', 'fecha_emision'),
    )

    def __repr__(self):
        return f"<CompraSire(ruc={self.ruc}, periodo={self.periodo}, proveedor={self.nro_doc_identidad}, total={self.total_cp})>"


class VentaSire(Base):
    """
    Modelo completo para Registro de Ventas e Ingresos Electrónicos (RVIE) - SIRE SUNAT.
    Almacena todas las columnas del CSV de ventas descargado de SUNAT (40 columnas).
    """
    __tablename__ = "ventas_sire"

    # Metadata y claves
    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(11), nullable=False, index=True, comment="RUC de la empresa")
    razon_social = Column(String(500), comment="Razón social de la empresa")
    periodo = Column(String(6), nullable=False, index=True, comment="Periodo tributario YYYYMM")
    car_sunat = Column(String(100), comment="Código de Autenticación de Registro SUNAT")
    ultima_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="Fecha y hora de última actualización")

    # Fechas
    fecha_emision = Column(Date, comment="Fecha de emisión del comprobante")
    fecha_vcto_pago = Column(Date, comment="Fecha de vencimiento o pago")

    # Información del comprobante
    tipo_cp_doc = Column(String(10), comment="Tipo de comprobante o documento")
    serie_cdp = Column(String(20), comment="Serie del comprobante de pago")
    nro_cp_inicial = Column(String(50), comment="Número de comprobante o número inicial del rango")
    nro_final = Column(String(50), comment="Número final del rango")

    # Información del cliente
    tipo_doc_identidad = Column(String(2), comment="Tipo de documento de identidad del cliente")
    nro_doc_identidad = Column(String(15), index=True, comment="Número de documento del cliente")
    apellidos_nombres_razon_social = Column(String(500), comment="Apellidos y nombres o razón social del cliente")

    # Valores de exportación y bases imponibles
    valor_facturado_exportacion = Column(Numeric(15, 2), comment="Valor facturado de exportación")
    bi_gravada = Column(Numeric(15, 2), comment="Base imponible gravada")
    dscto_bi = Column(Numeric(15, 2), comment="Descuento de base imponible")
    igv_ipm = Column(Numeric(15, 2), comment="IGV/IPM")
    dscto_igv_ipm = Column(Numeric(15, 2), comment="Descuento de IGV/IPM")
    mto_exonerado = Column(Numeric(15, 2), comment="Monto exonerado")
    mto_inafecto = Column(Numeric(15, 2), comment="Monto inafecto")

    # Otros tributos
    isc = Column(Numeric(15, 2), comment="Impuesto Selectivo al Consumo")
    bi_grav_ivap = Column(Numeric(15, 2), comment="Base imponible gravada con IVAP")
    ivap = Column(Numeric(15, 2), comment="Impuesto a la Venta de Arroz Pilado")
    icbper = Column(Numeric(15, 2), comment="Impuesto al Consumo de Bolsas de Plástico")
    otros_tributos = Column(Numeric(15, 2), comment="Otros tributos")
    total_cp = Column(Numeric(15, 2), comment="Total del comprobante de pago")

    # Moneda y tipo de cambio
    moneda = Column(String(3), comment="Código de moneda (PEN, USD, etc.)")
    tipo_cambio = Column(Numeric(10, 4), comment="Tipo de cambio")

    # Información de documentos modificados
    fecha_emision_doc_modificado = Column(Date, comment="Fecha de emisión del documento modificado")
    tipo_cp_modificado = Column(String(10), comment="Tipo de comprobante modificado")
    serie_cp_modificado = Column(String(20), comment="Serie del comprobante modificado")
    nro_cp_modificado = Column(String(50), comment="Número del comprobante modificado")

    # Información adicional
    id_proyecto_operadores_atribucion = Column(String(50), comment="ID de proyecto para operadores de atribución")
    tipo_nota = Column(String(10), comment="Tipo de nota (crédito/débito)")
    est_comp = Column(String(5), comment="Estado del comprobante")
    valor_fob_embarcado = Column(Numeric(15, 2), comment="Valor FOB embarcado")
    valor_op_gratuitas = Column(Numeric(15, 2), comment="Valor de operaciones gratuitas")
    tipo_operacion = Column(String(10), comment="Tipo de operación")
    dam_cp = Column(String(50), comment="DAM o comprobante de pago")
    clu = Column(String(200), comment="Campo libre de usuario")

    __table_args__ = (
        Index('idx_ventas_ruc_periodo', 'ruc', 'periodo'),
        Index('idx_ventas_cliente', 'nro_doc_identidad'),
        Index('idx_ventas_fecha', 'fecha_emision'),
    )

    def __repr__(self):
        return f"<VentaSire(ruc={self.ruc}, periodo={self.periodo}, cliente={self.nro_doc_identidad}, total={self.total_cp})>"


# Alias para backward compatibility (opcional, remover si no se necesita)
CompraElectronica = CompraSire
VentaElectronica = VentaSire
