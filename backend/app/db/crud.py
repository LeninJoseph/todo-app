from typing import Any, Generic, Mapping, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDBase(Generic[ModelT]):
    """Reusable CRUD operations for any SQLAlchemy model."""

    def __init__(self, model: type[ModelT]):
        self.model = model
        self._columns = {c.key for c in model.__table__.columns}

    def _check(self, data: Mapping[str, Any]) -> None:
        unknown = set(data) - self._columns
        if unknown:
            raise ValueError(f"Unknown fields for {self.model.__name__}: {sorted(unknown)}")

    def get(self, db: Session, id: int) -> ModelT | None:
        return db.get(self.model, id)

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.id).offset(skip).limit(limit)
        return list(db.scalars(stmt))

    def create(self, db: Session, data: Mapping[str, Any]) -> ModelT:
        self._check(data)
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, id: int, data: Mapping[str, Any]) -> ModelT | None:
        self._check(data)
        obj = db.get(self.model, id)
        if obj is None:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, id: int) -> bool:
        obj = db.get(self.model, id)
        if obj is None:
            return False
        db.delete(obj)
        db.commit()
        return True

