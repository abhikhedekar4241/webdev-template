from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)

class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int

async def apply_pagination_sorting_filtering(
    session: AsyncSession,
    model: type[T],
    *,
    skip: int = 0,
    limit: int = 100,
    sort_by: str | None = None,
    sort_order: str = "asc",
    search: str | None = None,
    search_fields: list[str] | None = None,
    base_query: Any | None = None,
) -> PaginatedResponse[T]:
    """
    Apply pagination, sorting, and filtering to a query.
    """
    if base_query is not None:
        query = base_query
    else:
        query = select(model)

    # Search
    if search and search_fields:
        filters = []
        for field in search_fields:
            col = getattr(model, field, None)
            if col:
                filters.append(col.ilike(f"%{search}%"))

        if filters:
            from sqlalchemy import or_
            query = query.where(or_(*filters))

    # Sorting
    if sort_by:
        col = getattr(model, sort_by, None)
        if col:
            if sort_order == "desc":
                query = query.order_by(col.desc())
            else:
                query = query.order_by(col.asc())

    # Total count before pagination
    total = (await session.exec(select(func.count()).select_from(query.subquery()))).one()

    # Pagination
    items = (await session.exec(query.offset(skip).limit(limit))).all()

    return PaginatedResponse(items=items, total=total)
