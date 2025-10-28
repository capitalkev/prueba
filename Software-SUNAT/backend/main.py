from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Enrolado, VentaElectronica, CompraElectronica, Usuario, Base
from database import engine
from schemas import (
    EnroladoResponse,
    VentaResponse,
    CompraResponse,
    ClienteConFacturas,
    MetricasResponse,
    PaginatedResponse,
)
from repositories.venta_repository import VentaRepository
from repositories.compra_repository import CompraRepository
from repositories.enrolado_repository import EnroladoRepository
from auth import get_user_context, get_optional_user_context

app = FastAPI(
    title="CRM SUNAT API",
    description="API para consultar datos de ventas y compras de SUNAT",
    version="2.0.0",
)


@app.on_event("startup")
def create_tables():
    """Crea las tablas en la base de datos al iniciar la aplicación"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas de base de datos creadas/verificadas exitosamente")
    except Exception as e:
        print(f"⚠️ Error al crear tablas: {e}")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://operaciones-peru.web.app",
        "https://operaciones-peru.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Endpoint raíz - Información de la API"""
    return {
        "message": "CRM SUNAT API",
        "version": "2.0.0",
        "status": "running",
        "arquitectura": "Repository Pattern",
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Verifica la salud de la API y conexión a BD"""
    try:
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@app.get("/debug/columns")
def debug_columns(db: Session = Depends(get_db)):
    """Debug endpoint - muestra las columnas reales de ventas_sire y compras_sire"""
    try:
        from sqlalchemy import text

        # Query para obtener columnas de ventas_sire
        ventas_query = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'ventas_sire'
            ORDER BY ordinal_position
        """)
        ventas_columns = db.execute(ventas_query).fetchall()

        # Query para obtener columnas de compras_sire
        compras_query = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'compras_sire'
            ORDER BY ordinal_position
        """)
        compras_columns = db.execute(compras_query).fetchall()

        # Query para obtener una fila de ejemplo de ventas_sire
        sample_query = text("SELECT * FROM ventas_sire LIMIT 1")
        result = db.execute(sample_query)
        sample_row = result.fetchone()

        return {
            "ventas_sire_columns": [
                {"name": col[0], "type": col[1]} for col in ventas_columns
            ],
            "compras_sire_columns": [
                {"name": col[0], "type": col[1]} for col in compras_columns
            ],
            "sample_data_column_names": list(result.keys()) if sample_row else [],
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}


# ==================== ENDPOINTS DE USUARIOS ====================


@app.get("/api/users/me")
def get_current_user_info(user_context: dict = Depends(get_user_context)):
    """
    Obtiene información del usuario actual autenticado.
    Retorna email, nombre, rol y cantidad de RUCs autorizados.
    """
    rucs_count = len(user_context["authorized_rucs"]) if user_context["authorized_rucs"] is not None else "todos"

    return {
        "email": user_context["email"],
        "nombre": user_context["nombre"],
        "rol": user_context["rol"],
        "rucs_autorizados": rucs_count
    }


# ==================== ENDPOINTS DE ENROLADOS ====================


@app.get("/api/enrolados", response_model=List[EnroladoResponse])
def get_enrolados(
    user_context: Optional[dict] = Depends(get_optional_user_context),
    db: Session = Depends(get_db)
):
    """
    Obtiene enrolados (empresas registradas).
    Autenticación OPCIONAL: aplica filtros si hay token válido.
    """
    repo = EnroladoRepository(db)
    email = user_context["email"]
    return repo.get_enrolados_by_email(email)


@app.get("/api/enrolados/{ruc}", response_model=EnroladoResponse)
def get_enrolado_by_ruc(ruc: str, db: Session = Depends(get_db)):
    """Obtiene un enrolado por RUC"""
    repo = EnroladoRepository(db)
    enrolado = repo.get_by_ruc(ruc)
    if not enrolado:
        raise HTTPException(
            status_code=404, detail=f"Enrolado con RUC {ruc} no encontrado"
        )
    return enrolado


# ==================== ENDPOINTS DE VENTAS ====================


@app.get("/api/ventas", response_model=PaginatedResponse[VentaResponse])
def get_ventas(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(
        20, ge=1, le=10000, description="Elementos por página (máximo 10000)"
    ),
    ruc_empresa: Optional[str] = Query(None, description="Filtrar por RUC de empresa"),
    rucs_empresa: Optional[List[str]] = Query(
        None, description="Filtrar por múltiples RUCs"
    ),
    periodo: Optional[str] = Query(None, description="Filtrar por periodo (YYYYMM)"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    sort_by: str = Query("fecha", description="Ordenar por: 'fecha' o 'monto'"),
    moneda: Optional[str] = Query(
        None, description="Filtrar por moneda: 'PEN' o 'USD'"
    ),
    user_context: Optional[dict] = Depends(get_optional_user_context),
    db: Session = Depends(get_db),
):
    """
    Obtiene ventas paginadas con filtros.
    Autenticación OPCIONAL: Si hay token válido, aplica filtros por rol.
    Sin token: acceso público sin restricciones (modo admin implícito).
    """
    repo = VentaRepository(db)

    # Convertir strings de fecha a objetos date, si existen
    fecha_desde_date = (
        datetime.strptime(fecha_desde, "%Y-%m-%d").date() if fecha_desde else None
    )
    fecha_hasta_date = (
        datetime.strptime(fecha_hasta, "%Y-%m-%d").date() if fecha_hasta else None
    )

    # Obtener RUCs autorizados: None si es público o admin
    authorized_rucs = user_context["authorized_rucs"] if user_context else None

    items, total = repo.get_ventas_paginadas(
        page=page,
        page_size=page_size,
        ruc=ruc_empresa,
        rucs_empresa=rucs_empresa,
        periodo=periodo,
        fecha_desde=fecha_desde_date,
        fecha_hasta=fecha_hasta_date,
        sort_by=sort_by,
        moneda=moneda,
        authorized_rucs=authorized_rucs,
    )

    return PaginatedResponse.create(
        items=items, total=total, page=page, page_size=page_size
    )


@app.get(
    "/api/ventas/periodo/{periodo}", response_model=PaginatedResponse[VentaResponse]
)
def get_ventas_by_periodo(
    periodo: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ruc_empresa: Optional[str] = None,
    sort_by: str = Query("fecha", description="Ordenar por: 'fecha' o 'monto'"),
    db: Session = Depends(get_db),
):
    """Obtiene ventas de un periodo específico con paginación y ordenamiento"""
    repo = VentaRepository(db)
    items, total = repo.get_ventas_paginadas(
        page=page,
        page_size=page_size,
        ruc_empresa=ruc_empresa,
        periodo=periodo,
        sort_by=sort_by,
    )

    return PaginatedResponse.create(
        items=items, total=total, page=page, page_size=page_size
    )


@app.get("/api/ventas/empresas")
def get_empresas_del_periodo(
    periodo: Optional[str] = Query(None, description="Periodo (YYYYMM)"),
    user_context: Optional[dict] = Depends(get_optional_user_context),
    db: Session = Depends(get_db),
):
    """
    Obtiene lista de empresas únicas (RUC y razón social) para un período.
    Autenticación OPCIONAL: aplica filtros si hay token válido.
    """
    if not periodo:
        periodo = datetime.now().strftime("%Y%m")

    repo = VentaRepository(db)
    authorized_rucs = user_context["authorized_rucs"] if user_context else None
    empresas = repo.get_empresas_unicas_por_periodo(periodo, authorized_rucs=authorized_rucs)

    return empresas


@app.get("/api/ventas/clientes-con-facturas", response_model=List[ClienteConFacturas])
def get_clientes_con_facturas(
    periodo: Optional[str] = Query(None, description="Periodo (YYYYMM)"),
    sort_by: str = Query("fecha", description="Ordenar por: 'fecha' o 'monto'"),
    user_context: Optional[dict] = Depends(get_optional_user_context),
    db: Session = Depends(get_db),
):
    """
    Endpoint principal para el CRM Frontend.
    Autenticación OPCIONAL: aplica filtros si hay token válido.
    """
    # Si no se especifica periodo, usar el mes actual
    if not periodo:
        periodo = datetime.now().strftime("%Y%m")

    repo = VentaRepository(db)
    authorized_rucs = user_context["authorized_rucs"] if user_context else None
    return repo.get_clientes_con_facturas_optimizado(periodo=periodo, sort_by=sort_by, authorized_rucs=authorized_rucs)


# ==================== ENDPOINTS DE MÉTRICAS ====================


@app.get("/api/metricas/{periodo}", response_model=MetricasResponse)
def get_metricas_periodo(
    periodo: str,
    ruc_empresa: Optional[str] = None,
    user_context: Optional[dict] = Depends(get_optional_user_context),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas agregadas de un periodo usando SQL optimizado.
    Autenticación OPCIONAL: aplica filtros si hay token válido.
    """
    repo = VentaRepository(db)
    authorized_rucs = user_context["authorized_rucs"] if user_context else None
    return repo.get_metricas_periodo(periodo=periodo, ruc=ruc_empresa, authorized_rucs=authorized_rucs)


# ==================== ENDPOINTS DE COMPRAS ====================


@app.get("/api/compras", response_model=PaginatedResponse[CompraResponse])
def get_compras(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    ruc_empresa: Optional[str] = Query(None, description="Filtrar por RUC de empresa"),
    periodo: Optional[str] = Query(None, description="Filtrar por periodo (YYYYMM)"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Obtiene compras paginadas con filtros.
    Solo devuelve compras de RUCs autorizados para el usuario.

    **Paginación**: Por defecto 20 compras por página
    """
    repo = CompraRepository(db)
    authorized_rucs = user_context["authorized_rucs"]
    items, total = repo.get_compras_paginadas(
        page=page,
        page_size=page_size,
        ruc_empresa=ruc_empresa,
        periodo=periodo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        authorized_rucs=authorized_rucs,
    )

    return PaginatedResponse.create(
        items=items, total=total, page=page, page_size=page_size
    )


# ==================== ESTADÍSTICAS GENERALES ====================


@app.get("/api/estadisticas/resumen")
def get_resumen_general(db: Session = Depends(get_db)):
    """Estadísticas generales del sistema"""

    total_enrolados = db.query(func.count(Enrolado.id)).scalar()
    total_ventas = db.query(func.count(VentaElectronica.id)).scalar()
    total_compras = db.query(func.count(CompraElectronica.id)).scalar()

    monto_total_ventas = db.query(func.sum(VentaElectronica.total_cp)).scalar() or 0
    monto_total_compras = db.query(func.sum(CompraElectronica.total_cp)).scalar() or 0

    return {
        "total_enrolados": total_enrolados,
        "total_ventas": total_ventas,
        "total_compras": total_compras,
        "monto_total_ventas": float(monto_total_ventas),
        "monto_total_compras": float(monto_total_compras),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
