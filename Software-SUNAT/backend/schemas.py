from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Generic, TypeVar
from datetime import date, datetime
from math import ceil

# ==================== SCHEMAS DE PAGINACIÓN ====================

T = TypeVar('T')

class PaginationMetadata(BaseModel):
    """Metadata de paginación"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico para respuestas paginadas"""
    items: List[T]
    pagination: PaginationMetadata

    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        """Método helper para crear respuesta paginada"""
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            pagination=PaginationMetadata(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
        )

# ==================== SCHEMAS DE USUARIOS ====================

class UsuarioResponse(BaseModel):
    """Schema para respuesta de Usuario"""
    email: str
    nombre: str
    rol: str

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE ENROLADOS ====================

class EnroladoResponse(BaseModel):
    """Schema para respuesta de Enrolado (sin credenciales sensibles)"""
    id: int
    ruc: str
    estado: str

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE VENTAS ====================

class ActualizarEstadoRequest(BaseModel):
    """Schema para actualizar el estado1 de una factura"""
    estado1: str  # Sin gestión, Gestionando, Ganada, Perdida

class ActualizarEstadoPerdidaRequest(BaseModel):
    """Schema para actualizar estado1 a 'Perdida' y especificar motivo en estado2"""
    estado2: str  # Por Tasa, Por Riesgo, Deudor no califica, Cliente no interesado, Competencia, Otro

class VentaResponse(BaseModel):
    """Schema para respuesta de Venta Electrónica"""
    id: int
    ruc: str
    razon_social: Optional[str] = None
    periodo: str
    car_sunat: Optional[str] = None
    fecha_emision: Optional[date] = None
    tipo_cp_doc: Optional[str] = None
    serie_cdp: Optional[str] = None
    nro_cp_inicial: Optional[str] = None
    nro_doc_identidad: Optional[str] = None
    apellidos_nombres_razon_social: Optional[str] = None
    total_cp: Optional[float] = None
    moneda: Optional[str] = None
    tipo_cambio: Optional[float] = None
    monto_original: Optional[float] = None  # Monto en moneda original (total_cp / tipo_cambio)
    usuario_nombre: Optional[str] = None  # Nombre del usuario asociado al enrolado
    usuario_email: Optional[str] = None  # Email del usuario asociado al enrolado
    # Información de notas de crédito
    nota_credito_monto: Optional[float] = None  # Monto de la nota de crédito asociada (si existe)
    monto_neto: Optional[float] = None  # Monto después de restar la nota de crédito
    tiene_nota_credito: bool = False  # Indica si tiene nota de crédito asociada
    # Estados de gestión CRM
    estado1: Optional[str] = "Sin gestión"  # Estado de gestión: Sin gestión, Gestionando, Ganada, Perdida
    estado2: Optional[str] = None  # Motivo de pérdida cuando estado1 = Perdida
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_calculation(cls, venta, usuario_nombre=None, usuario_email=None, nota_credito_monto=None):
        """Crea VentaResponse calculando monto_original (total_cp / tipo_cambio) y monto_neto

        Args:
            venta: Objeto VentaElectronica
            usuario_nombre: Nombre del usuario (opcional)
            usuario_email: Email del usuario (opcional)
            nota_credito_monto: Monto de la nota de crédito asociada (opcional)
        """
        import logging

        data = {
            "id": venta.id,
            "ruc": venta.ruc,
            "razon_social": venta.razon_social,
            "periodo": venta.periodo,
            "car_sunat": venta.car_sunat,
            "fecha_emision": venta.fecha_emision,
            "tipo_cp_doc": venta.tipo_cp_doc,
            "serie_cdp": venta.serie_cdp,
            "nro_cp_inicial": venta.nro_cp_inicial,
            "nro_doc_identidad": venta.nro_doc_identidad,
            "apellidos_nombres_razon_social": venta.apellidos_nombres_razon_social,
            "total_cp": float(venta.total_cp) if venta.total_cp else None,
            "moneda": venta.moneda,
            "tipo_cambio": float(venta.tipo_cambio) if venta.tipo_cambio else None,
            "usuario_nombre": usuario_nombre,
            "usuario_email": usuario_email,
            "estado1": venta.estado1 if (hasattr(venta, 'estado1') and venta.estado1) else "Sin gestión",
            "estado2": venta.estado2 if hasattr(venta, 'estado2') else None,
        }

        # Calcular monto_original: SIEMPRE dividir total_cp / tipo_cambio
        # PEN tiene tipo_cambio=1.000, USD tiene tipo_cambio real, etc.
        if venta.total_cp and venta.tipo_cambio and venta.tipo_cambio > 0:
            monto_calc = float(venta.total_cp) / float(venta.tipo_cambio)
            data["monto_original"] = monto_calc
            logging.info(f"✅ Cálculo: {venta.total_cp} / {venta.tipo_cambio} = {monto_calc} ({venta.moneda})")
        else:
            # Si no hay tipo_cambio válido, usar total_cp directamente
            data["monto_original"] = float(venta.total_cp) if venta.total_cp else None
            logging.warning(f"⚠️ Sin tipo_cambio: total_cp={venta.total_cp}, tipo_cambio={venta.tipo_cambio}")

        # Usar valores pre-calculados de la vista materializada si existen
        # La vista usa: total_neto, monto_nota_credito, tiene_nota_credito
        if hasattr(venta, 'total_neto') and venta.total_neto is not None:
            # Usar valores pre-calculados de la vista materializada
            # total_neto ya está en la moneda correcta (sin dividir por tipo_cambio nuevamente)
            data["monto_neto"] = float(venta.total_neto)
            data["tiene_nota_credito"] = getattr(venta, 'tiene_nota_credito', False)
            data["nota_credito_monto"] = float(venta.monto_nota_credito) if hasattr(venta, 'monto_nota_credito') and venta.monto_nota_credito is not None else None
            # Actualizar monto_original para que sea consistente con total_cp (sin dividir tipo_cambio)
            data["monto_original"] = float(venta.total_cp) if venta.total_cp else None
        elif nota_credito_monto is not None and nota_credito_monto != 0:
            # Fallback: calcular si no vienen de la vista materializada
            data["nota_credito_monto"] = float(nota_credito_monto)
            data["tiene_nota_credito"] = True
            # Calcular monto_neto: total_cp + nota_credito_monto (nota_credito_monto ya incluye el signo)
            if data["monto_original"] is not None:
                monto_neto_calculado = data["monto_original"] + float(nota_credito_monto)
                # Si el resultado es negativo, redondear a 0
                data["monto_neto"] = max(0, monto_neto_calculado)
            else:
                data["monto_neto"] = None
        else:
            data["nota_credito_monto"] = None
            data["tiene_nota_credito"] = False
            data["monto_neto"] = data["monto_original"]  # Sin nota de crédito, monto_neto = monto_original

        return cls(**data)


# ==================== SCHEMAS PARA EL CRM ====================

class FacturaParaCRM(BaseModel):
    """Schema de factura adaptado para el frontend CRM"""
    id: str
    debtor: str
    amount: float
    emissionDate: Optional[str] = None
    dueDate: Optional[str] = None
    status: str
    log: List[dict] = []
    ruc_cliente: Optional[str] = None
    tipo_comprobante: Optional[str] = None
    moneda: Optional[str] = None
    car_sunat: Optional[str] = None


class ClienteConFacturas(BaseModel):
    """Schema que combina enrolado con sus facturas"""
    id: int
    name: str
    ruc: str
    availableInvoices: List[FacturaParaCRM]


# ==================== SCHEMAS DE MÉTRICAS ====================

class MetricasResponse(BaseModel):
    """Schema para métricas agregadas de un periodo separadas por moneda"""
    periodo: str
    total_pen: float
    facturas_pen: int
    total_usd: float
    facturas_usd: int


# ==================== SCHEMAS DE PERIODOS FALLIDOS ====================

class PeriodoFallidoResponse(BaseModel):
    """Schema para periodos fallidos"""
    id: int
    ruc: str
    periodo: str
    tipo: str
    fecha_fallo: datetime
    motivo: Optional[str] = None
    resuelto: bool

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE COMPRAS ====================

class CompraResponse(BaseModel):
    """Schema para respuesta de Compra Electrónica"""
    id: int
    ruc: str
    razon_social: Optional[str] = None
    periodo: str
    car_sunat: Optional[str] = None
    fecha_emision: Optional[date] = None
    tipo_cp_doc: Optional[str] = None
    serie_cdp: Optional[str] = None
    nro_cp_inicial: Optional[str] = None
    nro_doc_identidad: Optional[str] = None
    apellidos_nombres_razon_social: Optional[str] = None
    total_cp: Optional[float] = None
    moneda: Optional[str] = None
    tipo_cambio: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
