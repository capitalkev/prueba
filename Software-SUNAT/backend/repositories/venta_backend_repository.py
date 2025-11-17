from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Tuple
from datetime import date

from models import VentaBackend, Enrolado, Usuario
from repositories.base_repository import BaseRepository


class VentaBackendRepository(BaseRepository[VentaBackend]):
    """
    Repositorio optimizado que usa la vista materializada ventas_backend.

    VENTAJAS:
    - 90%+ más rápido que VentaRepository
    - Sin subqueries complejos (campos pre-calculados)
    - Menor uso de CPU y memoria
    - total_neto, monto_nota_credito, tiene_nota_credito ya calculados

    IMPORTANTE:
    - Esta vista debe refrescarse después de cargar datos SUNAT
    - Usar refresh_ventas_backend() después de importaciones
    """

    def __init__(self, db: Session):
        super().__init__(VentaBackend, db)
        

    def get_ventas_paginadas(
        self,
        page: int = 1,
        page_size: int = 20,
        ruc: Optional[str] = None,
        rucs_empresa: Optional[List[str]] = None,
        periodo: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        sort_by: str = "fecha",
        moneda: Optional[str] = None,
        authorized_rucs: Optional[List[str]] = None,
        usuario_emails: Optional[List[str]] = None,
    ) -> Tuple[List[Tuple[VentaBackend, Optional[str], Optional[str]]], int]:
        """
        Query optimizado usando vista materializada.

        Args:
            page: Número de página (1-indexed)
            page_size: Registros por página
            ruc: Filtrar por un solo RUC
            rucs_empresa: Filtrar por múltiples RUCs
            periodo: Filtrar por periodo (YYYYMM)
            fecha_desde: Fecha inicio
            fecha_hasta: Fecha fin
            sort_by: "fecha" o "monto"
            moneda: "PEN" o "USD"
            authorized_rucs: RUCs autorizados (control de acceso)
            usuario_emails: Filtrar por emails de usuarios asignados

        Returns:
            Tuple de (lista de tuplas (venta, usuario_nombre, usuario_email), total_count)
        """

        query = self.db.query(
            VentaBackend,
            VentaBackend.usuario_nombre,
            VentaBackend.usuario_email
        ).filter(VentaBackend.tipo_cp_doc == "1")

        # Aplicar filtros
        if authorized_rucs is not None:
            query = query.filter(VentaBackend.ruc.in_(authorized_rucs))

        if ruc:
            query = query.filter(VentaBackend.ruc == ruc)

        if rucs_empresa and len(rucs_empresa) > 0:
            query = query.filter(VentaBackend.ruc.in_(rucs_empresa))

        if periodo:
            query = query.filter(VentaBackend.periodo == periodo)

        if fecha_desde:
            query = query.filter(VentaBackend.fecha_emision >= fecha_desde)

        if fecha_hasta:
            query = query.filter(VentaBackend.fecha_emision <= fecha_hasta)

        if moneda:
            query = query.filter(VentaBackend.moneda == moneda)

        if usuario_emails and len(usuario_emails) > 0:
            if "UNASSIGNED" in usuario_emails:
                # Incluir sin asignar + los especificados
                query = query.filter(
                    (VentaBackend.usuario_email.is_(None)) | (VentaBackend.usuario_email.in_(usuario_emails))
                )
            else:
                query = query.filter(VentaBackend.usuario_email.in_(usuario_emails))

        # Contar total
        total = query.count()

        # Ordenamiento
        if sort_by == "monto":
            query = query.order_by(desc(VentaBackend.monto_neto))
        else:
            # Por defecto: fecha descendente
            query = query.order_by(
                desc(VentaBackend.fecha_emision), desc(VentaBackend.id)
            )

        # Paginación
        offset = (page - 1) * page_size
        items = query.limit(page_size).offset(offset).all()

        # Devolvemos 0 como total, ya no lo calculamos aquí
        return items, total

    def get_empresas_unicas_por_periodo(
        self,
        periodo: Optional[str] = None,
        authorized_rucs: Optional[List[str]] = None,
        usuario_emails: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Obtiene lista de empresas únicas con ventas.

        Args:
            periodo: Filtrar por periodo (opcional)
            authorized_rucs: RUCs autorizados
            usuario_emails: Filtrar por usuarios

        Returns:
            Lista de dict con {ruc, razon_social}
        """
        query = self.db.query(VentaBackend.ruc, VentaBackend.razon_social).distinct()

        # Aplicar filtros
        if authorized_rucs is not None:
            query = query.filter(VentaBackend.ruc.in_(authorized_rucs))

        if periodo:
            query = query.filter(VentaBackend.periodo == periodo)

        if usuario_emails and len(usuario_emails) > 0:
            query = query.join(Enrolado, VentaBackend.ruc == Enrolado.ruc).filter(
                Enrolado.email.in_(usuario_emails)
            )

        query = query.order_by(VentaBackend.razon_social)

        results = query.all()

        return [{"ruc": row.ruc, "razon_social": row.razon_social} for row in results]

    def get_metricas_periodo(
        self,
        periodo: str,
        ruc: Optional[str] = None,
        authorized_rucs: Optional[List[str]] = None,
    ) -> dict:
        """
        Obtiene métricas agregadas de un periodo.

        IMPORTANTE: Usa total_neto (ya incluye notas de crédito)

        Args:
            periodo: Periodo (YYYYMM)
            ruc: RUC específico (opcional)
            authorized_rucs: RUCs autorizados

        Returns:
            Dict con métricas por moneda
        """
        query = self.db.query(
            VentaBackend.moneda,
            func.sum(VentaBackend.total_neto).label("total_facturado"),
            func.count(VentaBackend.id).label("cantidad"),
        ).filter(
            VentaBackend.periodo == periodo,
            VentaBackend.tipo_cp_doc != "7",  # Excluir notas de crédito
        )

        # Filtros de acceso
        if authorized_rucs is not None:
            query = query.filter(VentaBackend.ruc.in_(authorized_rucs))

        if ruc:
            query = query.filter(VentaBackend.ruc == ruc)

        query = query.group_by(VentaBackend.moneda)

        results = query.all()

        # Transformar a formato esperado
        metricas = {
            "total_pen": 0,
            "facturas_pen": 0,
            "total_usd": 0,
            "facturas_usd": 0,
        }

        for row in results:
            if row.moneda == "PEN":
                metricas["total_pen"] = float(row.total_facturado or 0)
                metricas["facturas_pen"] = int(row.cantidad or 0)
            elif row.moneda == "USD":
                metricas["total_usd"] = float(row.total_facturado or 0)
                metricas["facturas_usd"] = int(row.cantidad or 0)

        return metricas
