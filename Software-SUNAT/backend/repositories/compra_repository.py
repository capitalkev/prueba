from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import date
from models import CompraElectronica
from repositories.base_repository import BaseRepository


class CompraRepository(BaseRepository[CompraElectronica]):
    """Repositorio especializado para consultas de compras"""

    def __init__(self, db: Session):
        super().__init__(CompraElectronica, db)

    def get_compras_paginadas(
        self,
        page: int = 1,
        page_size: int = 20,
        ruc_empresa: Optional[str] = None,
        periodo: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        authorized_rucs: Optional[List[str]] = None,
    ):
        """
        Obtiene compras paginadas con filtros optimizados

        Args:
            page: Número de página
            page_size: Cantidad de items por página
            ruc_empresa: RUC específico (opcional)
            periodo: Periodo a consultar (YYYYMM)
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
            authorized_rucs: Lista de RUCs autorizados para el usuario (control de acceso)

        Returns:
            tuple: (items, total_count)
        """
        query = self.db.query(CompraElectronica)

        # CONTROL DE ACCESO: Filtrar por RUCs autorizados
        if authorized_rucs is not None:
            if len(authorized_rucs) == 0:
                # Usuario sin RUCs autorizados, retornar vacío
                return [], 0
            query = query.filter(CompraElectronica.ruc.in_(authorized_rucs))

        # Aplicar filtros
        if ruc_empresa:
            query = query.filter(CompraElectronica.ruc == ruc_empresa)

        if periodo:
            query = query.filter(CompraElectronica.periodo == periodo)

        if fecha_desde:
            query = query.filter(CompraElectronica.fecha_emision >= fecha_desde)

        if fecha_hasta:
            query = query.filter(CompraElectronica.fecha_emision <= fecha_hasta)

        # Ordenar por fecha descendente
        query = query.order_by(desc(CompraElectronica.fecha_emision))

        # Contar total
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total
