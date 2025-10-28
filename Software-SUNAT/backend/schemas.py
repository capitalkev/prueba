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

# ==================== SCHEMAS DE ENROLADOS ====================

class EnroladoResponse(BaseModel):
    """Schema para respuesta de Enrolado (sin credenciales sensibles)"""
    id: int
    ruc: str
    estado: str

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE VENTAS ====================

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

    model_config = ConfigDict(from_attributes=True)


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
