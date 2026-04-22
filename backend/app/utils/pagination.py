from collections.abc import Sequence
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int


async def paginate(
    items: Sequence[T],
    total: int,
    page: int,
    size: int,
) -> PaginatedResponse[T]:
    pages = (total + size - 1) // size if size > 0 else 0
    return PaginatedResponse(
        items=items, total=total, page=page, size=size, pages=pages
    )
