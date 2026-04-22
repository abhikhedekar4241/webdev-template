from typing import Any, Generic, TypeVar

import structlog
from sqlmodel import Session, SQLModel, select

logger = structlog.get_logger()
ModelType = TypeVar("ModelType", bound=SQLModel)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def get(self, session: Session, id: Any) -> ModelType | None:
        return session.get(self.model, id)

    def get_multi(
        self, session: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        return list(session.exec(select(self.model).offset(skip).limit(limit)).all())

    def create(self, session: Session, *, obj_in: SQLModel) -> ModelType:
        obj = self.model.model_validate(obj_in)
        session.add(obj)
        session.flush()
        logger.info("db_obj_created", model=self.model.__name__)
        return obj

    def update(
        self, session: Session, *, db_obj: ModelType, obj_in: dict | SQLModel
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        session.add(db_obj)
        session.flush()
        logger.info("db_obj_updated", model=self.model.__name__)
        return db_obj

    def delete(self, session: Session, *, id: Any) -> ModelType | None:
        obj = session.get(self.model, id)
        if obj:
            session.delete(obj)
            session.flush()
            logger.info("db_obj_deleted", model=self.model.__name__)
        return obj
