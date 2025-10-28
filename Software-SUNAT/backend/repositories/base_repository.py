from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Type, TypeVar, Generic
from math import ceil

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Repositorio base con operaciones CRUD genéricas"""

    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[T]:
        """Obtiene un registro por ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Obtiene todos los registros con paginación"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def get_paginated(self, page: int = 1, page_size: int = 20, filters: dict = None, order_by=None):
        """
        Obtiene registros paginados con filtros opcionales

        Returns:
            tuple: (items, total_count)
        """
        query = self.db.query(self.model)

        # Aplicar filtros si existen
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        # Aplicar ordenamiento
        if order_by is not None:
            query = query.order_by(order_by)

        # Contar total antes de aplicar paginación
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def count(self, filters: dict = None) -> int:
        """Cuenta registros con filtros opcionales"""
        query = self.db.query(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.scalar()

    def create(self, obj: T) -> T:
        """Crea un nuevo registro"""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: T) -> T:
        """Actualiza un registro existente"""
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: T) -> None:
        """Elimina un registro"""
        self.db.delete(obj)
        self.db.commit()
