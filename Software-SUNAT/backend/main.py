from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Enrolado, VentaElectronica, CompraElectronica, Usuario, Base
from database import engine
from schemas import (
    UsuarioResponse,
    EnroladoResponse,
    VentaResponse,
    CompraResponse,
    ClienteConFacturas,
    MetricasResponse,
    PaginatedResponse,
    ActualizarEstadoRequest,
    ActualizarEstadoPerdidaRequest,
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


@app.get("/debug/me")
def debug_user_info(user_context: dict = Depends(get_user_context)):
    """Endpoint de debug para ver información del usuario autenticado"""
    return {
        "email": user_context["email"],
        "nombre": user_context["nombre"],
        "rol": user_context["rol"],
        "authorized_rucs": user_context["authorized_rucs"],
        "is_admin": user_context["rol"] == "admin",
        "can_see_all": user_context["authorized_rucs"] is None
    }


@app.post("/admin/assign-all-enrolados")
def assign_all_enrolados_to_admin(
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db)
):
    """
    Endpoint de administración: Asigna TODOS los enrolados sin email al usuario admin actual.
    Solo admins pueden usar este endpoint.
    """
    if user_context["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden usar este endpoint")

    email = user_context["email"]

    # Actualizar todos los enrolados que no tienen email asignado
    from sqlalchemy import update
    stmt = update(Enrolado).where(
        (Enrolado.email == None) | (Enrolado.email == "")
    ).values(email=email)

    result = db.execute(stmt)
    db.commit()

    return {
        "message": f"Enrolados asignados a {email}",
        "enrolados_actualizados": result.rowcount,
        "email_asignado": email
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
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db)
):
    """
    Obtiene enrolados (empresas registradas).
    Autenticación OBLIGATORIA: Filtra por email del usuario.
    Admin ve todos los enrolados, usuarios normales solo ven sus asignados.
    """
    repo = EnroladoRepository(db)
    authorized_rucs = user_context["authorized_rucs"]  # None si es admin

    if authorized_rucs is None:
        # Admin: retornar todos los enrolados
        return repo.get_all_enrolados()
    else:
        # Usuario normal: retornar solo enrolados asignados
        return repo.get_enrolados_by_rucs(authorized_rucs)


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


# ==================== ENDPOINTS DE USUARIOS ====================


@app.get("/api/usuarios/no-admin", response_model=List[UsuarioResponse])
def get_usuarios_no_admin(
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db)
):
    """
    Obtiene lista de usuarios que no son administradores.
    Usado para el selector de filtro por usuario en el frontend.
    """
    from models import Usuario

    usuarios = db.query(Usuario).filter(Usuario.rol != 'admin').all()
    return usuarios

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
    usuario_email: Optional[str] = Query(None, description="Filtrar por email de usuario (deprecated, usar usuario_emails)"),
    usuario_emails: Optional[List[str]] = Query(None, description="Filtrar por múltiples emails de usuario"),
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Obtiene ventas paginadas con filtros.
    Autenticación OBLIGATORIA: Filtra por RUCs según rol del usuario.
    Admin ve todo, usuarios normales solo ven sus enrolados asignados.
    """
    repo = VentaRepository(db)

    fecha_desde_date = (
        datetime.strptime(fecha_desde, "%Y-%m-%d").date() if fecha_desde else None
    )
    fecha_hasta_date = (
        datetime.strptime(fecha_hasta, "%Y-%m-%d").date() if fecha_hasta else None
    )

    print("🎯 [ENDPOINT] GET /api/ventas recibió:")
    print(f"  - usuario_email (deprecated): {usuario_email}")
    print(f"  - usuario_emails (nuevo): {usuario_emails}")
    print(f"  - fecha_desde: {fecha_desde}, fecha_hasta: {fecha_hasta}")
    print(f"  - page: {page}, page_size: {page_size}")

    authorized_rucs = user_context["authorized_rucs"] if user_context else None

    emails_to_filter = usuario_emails if usuario_emails else ([usuario_email] if usuario_email else None)
    print(f"🎯 [ENDPOINT] emails_to_filter calculado: {emails_to_filter}")

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
        usuario_emails=emails_to_filter,
    )

    items_with_calculation = [
        VentaResponse.from_orm_with_calculation(venta, usuario_nombre, usuario_email, nota_credito_monto)
        for venta, usuario_nombre, usuario_email, nota_credito_monto in items
    ]

    return PaginatedResponse.create(
        items=items_with_calculation, total=total, page=page, page_size=page_size
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
        ruc=ruc_empresa,
        periodo=periodo,
        sort_by=sort_by,
    )

    items_with_calculation = [
        VentaResponse.from_orm_with_calculation(venta, usuario_nombre, usuario_email, nota_credito_monto)
        for venta, usuario_nombre, usuario_email, nota_credito_monto in items
    ]

    return PaginatedResponse.create(
        items=items_with_calculation, total=total, page=page, page_size=page_size
    )


@app.get("/api/ventas/empresas")
def get_empresas_del_periodo(
    periodo: Optional[str] = Query(None, description="Periodo (YYYYMM). Si no se especifica, retorna todas las empresas de todos los períodos"),
    usuario_emails: Optional[List[str]] = Query(None, description="Filtrar empresas por usuarios asignados"),
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Obtiene lista de empresas únicas (RUC y razón social).
    Si no se especifica período, retorna todas las empresas que han tenido ventas en cualquier período.
    Autenticación OBLIGATORIA: Filtra por RUCs según rol del usuario.
    Admin ve todas las empresas, usuarios normales solo ven sus enrolados asignados.

    Si se proporciona usuario_emails, filtra las empresas para mostrar solo las asignadas a esos usuarios.
    """
    repo = VentaRepository(db)
    authorized_rucs = user_context["authorized_rucs"]
    empresas = repo.get_empresas_unicas_por_periodo(
        periodo=periodo,
        authorized_rucs=authorized_rucs,
        usuario_emails=usuario_emails
    )

    return empresas


@app.get("/api/ventas/ultima-actualizacion")
def get_ultima_actualizacion(
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Obtiene la fecha y hora de la última actualización de facturas.
    Retorna el timestamp más reciente de la columna ultima_actualizacion.
    Autenticación OBLIGATORIA: Filtra por RUCs según rol del usuario.
    """
    try:
        from datetime import timezone

        authorized_rucs = user_context["authorized_rucs"]  

        query = db.query(func.max(VentaElectronica.ultima_actualizacion))

        if authorized_rucs is not None:
            query = query.filter(VentaElectronica.ruc.in_(authorized_rucs))

        ultima_actualizacion = query.scalar()

        if ultima_actualizacion is None:
            return {
                "ultima_actualizacion": None,
                "mensaje": "No hay datos de facturas disponibles"
            }

        if ultima_actualizacion.tzinfo is None:
            ultima_actualizacion = ultima_actualizacion.replace(tzinfo=timezone.utc)

        return {
            "ultima_actualizacion": ultima_actualizacion.isoformat().replace('+00:00', 'Z'),
            "timestamp": int(ultima_actualizacion.timestamp())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener última actualización: {str(e)}")


@app.get("/api/ventas/clientes-con-facturas", response_model=List[ClienteConFacturas])
def get_clientes_con_facturas(
    periodo: Optional[str] = Query(None, description="Periodo (YYYYMM)"),
    sort_by: str = Query("fecha", description="Ordenar por: 'fecha' o 'monto'"),
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Endpoint principal para el CRM Frontend.
    Autenticación OBLIGATORIA: Filtra por RUCs según rol del usuario.
    Admin ve todo, usuarios normales solo ven sus enrolados asignados.
    """
    # Si no se especifica periodo, usar el mes actual
    if not periodo:
        periodo = datetime.now().strftime("%Y%m")

    repo = VentaRepository(db)
    authorized_rucs = user_context["authorized_rucs"]  # None si es admin
    return repo.get_clientes_con_facturas_optimizado(periodo=periodo, sort_by=sort_by, authorized_rucs=authorized_rucs)


@app.put("/api/ventas/{venta_id}/estado", response_model=VentaResponse)
def actualizar_estado_venta(
    venta_id: int,
    request: ActualizarEstadoRequest,
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Actualiza el estado1 de una factura.
    Autenticación OBLIGATORIA: Solo puede actualizar facturas de RUCs autorizados.

    Estados válidos: Sin gestión, Gestionando, Ganada, Perdida
    """
    # Buscar la venta
    venta = db.query(VentaElectronica).filter(VentaElectronica.id == venta_id).first()

    if not venta:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Verificar autorización
    authorized_rucs = user_context["authorized_rucs"]
    if authorized_rucs is not None and venta.ruc not in authorized_rucs:
        raise HTTPException(status_code=403, detail="No autorizado para modificar esta factura")

    # Validar estado
    estados_validos = ["Sin gestión", "Gestionando", "Ganada", "Perdida"]
    if request.estado1 not in estados_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
        )

    # Actualizar estado1
    venta.estado1 = request.estado1

    # Si el estado NO es Perdida, limpiar estado2
    if request.estado1 != "Perdida":
        venta.estado2 = None

    db.commit()
    db.refresh(venta)

    # Retornar la venta actualizada con cálculos
    return VentaResponse.from_orm_with_calculation(venta, None, None, None)


@app.put("/api/ventas/{venta_id}/perdida", response_model=VentaResponse)
def actualizar_estado_perdida(
    venta_id: int,
    request: ActualizarEstadoPerdidaRequest,
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db),
):
    """
    Actualiza una factura a estado 'Perdida' y especifica el motivo en estado2.
    Autenticación OBLIGATORIA: Solo puede actualizar facturas de RUCs autorizados.

    Motivos válidos: Por Tasa, Por Riesgo, Deudor no califica, Cliente no interesado, Competencia, Otro
    """
    # Buscar la venta
    venta = db.query(VentaElectronica).filter(VentaElectronica.id == venta_id).first()

    if not venta:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # Verificar autorización
    authorized_rucs = user_context["authorized_rucs"]
    if authorized_rucs is not None and venta.ruc not in authorized_rucs:
        raise HTTPException(status_code=403, detail="No autorizado para modificar esta factura")

    # Validar motivo de pérdida
    motivos_validos = [
        "Por Tasa",
        "Por Riesgo",
        "Deudor no califica",
        "Cliente no interesado",
        "Competencia",
        "Otro"
    ]
    if request.estado2 not in motivos_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Motivo inválido. Debe ser uno de: {', '.join(motivos_validos)}"
        )

    # Actualizar estado1 a "Perdida" y estado2 con el motivo
    venta.estado1 = "Perdida"
    venta.estado2 = request.estado2

    db.commit()
    db.refresh(venta)

    # Retornar la venta actualizada con cálculos
    return VentaResponse.from_orm_with_calculation(venta, None, None, None)


# ==================== ENDPOINTS DE MÉTRICAS ====================


@app.get("/api/metricas/{periodo}", response_model=MetricasResponse)
def get_metricas_periodo(
    periodo: str,
    ruc_empresa: Optional[str] = None,
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas agregadas de un periodo usando SQL optimizado.
    Autenticación OBLIGATORIA: Filtra por RUCs según rol del usuario.
    Admin ve todo, usuarios normales solo ven sus enrolados asignados.
    """
    repo = VentaRepository(db)
    authorized_rucs = user_context["authorized_rucs"]  # None si es admin
    return repo.get_metricas_periodo(periodo=periodo, ruc=ruc_empresa, authorized_rucs=authorized_rucs)


@app.get("/api/metricas/resumen")
def get_metricas_resumen(
    fecha_desde: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    fecha_hasta: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    rucs_empresa: Optional[List[str]] = Query(None, description="Lista de RUCs a filtrar"),
    moneda: Optional[List[str]] = Query(None, description="Lista de monedas (PEN, USD)"),
    usuario_emails: Optional[List[str]] = Query(None, description="Lista de emails de usuarios"),
    user_context: dict = Depends(get_user_context),
    db: Session = Depends(get_db)
):
    """
    Endpoint OPTIMIZADO que retorna solo métricas agregadas por moneda.

    VENTAJAS vs GET /api/ventas?page_size=10000:
    - Transfiere < 1 KB en vez de 10-15 MB
    - Query optimizado con índices (periodo, moneda)
    - Respuesta en 10-50ms en vez de 500-2000ms

    Respuesta:
    {
      "PEN": {
        "totalFacturado": 1234567.89,
        "montoGanado": 234567.89,
        "montoDisponible": 1000000.00,
        "cantidad": 1523
      },
      "USD": { ... }
    }
    """
    try:
        authorized_rucs = user_context["authorized_rucs"]

        if not authorized_rucs:
            raise HTTPException(status_code=403, detail="Usuario sin empresas autorizadas")

        # Query optimizado con agregaciones en SQL
        query = db.query(
            VentaElectronica.moneda,
            func.sum(VentaElectronica.total_cp).label('total_facturado'),
            func.sum(
                case(
                    (VentaElectronica.estado1 == 'Ganada', VentaElectronica.total_cp),
                    else_=0
                )
            ).label('monto_ganado'),
            func.count(VentaElectronica.id).label('cantidad')
        ).filter(
            VentaElectronica.fecha_emision >= fecha_desde,
            VentaElectronica.fecha_emision <= fecha_hasta,
            VentaElectronica.tipo_cp_doc != '7',  # Excluir NC
            ~VentaElectronica.serie_cdp.like('B%'),  # Excluir boletas
            VentaElectronica.ruc.in_(authorized_rucs)
        )

        # Filtros opcionales
        if rucs_empresa and len(rucs_empresa) > 0:
            query = query.filter(VentaElectronica.ruc.in_(rucs_empresa))

        if moneda and len(moneda) > 0:
            query = query.filter(VentaElectronica.moneda.in_(moneda))

        # Filtro por usuarios asignados
        if usuario_emails and len(usuario_emails) > 0:
            query = query.join(Enrolado, VentaElectronica.ruc == Enrolado.ruc)\
                         .join(Usuario, Enrolado.email == Usuario.email)\
                         .filter(Usuario.email.in_(usuario_emails))

        # Group by moneda
        query = query.group_by(VentaElectronica.moneda)

        # Ejecutar query
        results = query.all()

        # Transformar a diccionario
        metricas = {}
        for row in results:
            total_facturado = float(row.total_facturado or 0)
            monto_ganado = float(row.monto_ganado or 0)

            metricas[row.moneda] = {
                "totalFacturado": total_facturado,
                "montoGanado": monto_ganado,
                "montoDisponible": total_facturado - monto_ganado,
                "cantidad": row.cantidad
            }

        return metricas

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas: {str(e)}")


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
    import os

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
