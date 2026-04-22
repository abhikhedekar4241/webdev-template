from typing import Any, Generic, TypeVar

import structlog
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

logger = structlog.get_logger()
ModelType = TypeVar("ModelType", bound=SQLModel)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> ModelType | None:
        return await session.get(self.model, id)

    async def get_multi(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        return list(
            (await session.exec(select(self.model).offset(skip).limit(limit))).all()
        )

    async def create(self, session: AsyncSession, *, obj_in: SQLModel) -> ModelType:
        obj = self.model.model_validate(obj_in)
        session.add(obj)
        await session.flush()
        logger.info("db_obj_created", model=self.model.__name__)
        return obj

    async def update(
        self, session: AsyncSession, *, db_obj: ModelType, obj_in: dict | SQLModel
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        session.add(db_obj)
        await session.flush()
        logger.info("db_obj_updated", model=self.model.__name__)
        return db_obj

    async def delete(self, session: AsyncSession, *, id: Any) -> ModelType | None:
        obj = await session.get(self.model, id)
        if obj:
            await session.delete(obj)
            await session.flush()
            logger.info("db_obj_deleted", model=self.model.__name__)
        return obj
