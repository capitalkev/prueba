from sqlalchemy.orm import Session
from typing import Optional, List

from models import Enrolado
from repositories.base_repository import BaseRepository


class EnroladoRepository(BaseRepository[Enrolado]):
    """Repositorio especializado para consultas de enrolados"""

    def __init__(self, db: Session):
        super().__init__(Enrolado, db)

    def get_by_ruc(self, ruc: str) -> Optional[Enrolado]:
        """Obtiene un enrolado por RUC"""
        return self.db.query(Enrolado).filter(Enrolado.ruc == ruc).first()

    def get_enrolados_por_estado(self, estado: str):
        """Obtiene enrolados filtrados por estado (pendiente/completo)"""
        return self.db.query(Enrolado).filter(Enrolado.estado == estado).all()

    def get_all_enrolados(self):
        """Obtiene todos los enrolados"""
        return self.db.query(Enrolado).all()

    def get_enrolados_by_email(self, email: str) -> List[Enrolado]:
        """
        Obtiene todos los enrolados asociados a un email específico.
        Usado para control de acceso basado en usuario.

        Args:
            email: Email del usuario

        Returns:
            List[Enrolado]: Lista de enrolados autorizados para el email
        """
        return self.db.query(Enrolado).filter(Enrolado.email == email).all()

    def get_rucs_by_email(self, email: str) -> List[str]:
        """
        Obtiene la lista de RUCs autorizados para un email.

        Args:
            email: Email del usuario

        Returns:
            List[str]: Lista de RUCs autorizados
        """
        enrolados = self.get_enrolados_by_email(email)
        return [enrolado.ruc for enrolado in enrolados]

    def get_enrolados_by_rucs(self, rucs: List[str]) -> List[Enrolado]:
        """
        Obtiene enrolados filtrados por lista de RUCs.

        Args:
            rucs: Lista de RUCs autorizados

        Returns:
            List[Enrolado]: Lista de enrolados que coinciden con los RUCs
        """
        if not rucs:
            return []
        return self.db.query(Enrolado).filter(Enrolado.ruc.in_(rucs)).all()
