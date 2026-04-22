import uuid

import pytest
from sqlmodel import Field, SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.utils.pagination import paginate
from app.utils.query import apply_pagination_sorting_filtering

# --- Mock Model for Query Utils Tests ---


class MockModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: str
    age: int


@pytest.fixture(name="query_session")
async def query_session_fixture(session: AsyncSession):
    conn = await session.connection()
    await conn.run_sync(MockModel.__table__.create, checkfirst=True)

    m1 = MockModel(name="Alice", email="alice@example.com", age=30)
    m2 = MockModel(name="Bob", email="bob@example.com", age=25)
    m3 = MockModel(name="Charlie", email="charlie@gmail.com", age=35)
    session.add(m1)
    session.add(m2)
    session.add(m3)
    await session.commit()
    return session


# --- Pagination Tests ---


async def test_paginate_calculates_pages_correctly():
    result = await paginate(items=list(range(10)), total=25, page=1, size=10)
    assert result.pages == 3


async def test_paginate_returns_correct_metadata():
    result = await paginate(items=list(range(10)), total=25, page=2, size=10)
    assert result.total == 25
    assert result.page == 2
    assert result.size == 10


async def test_paginate_preserves_items():
    items = ["a", "b", "c"]
    result = await paginate(items=items, total=3, page=1, size=10)
    assert list(result.items) == ["a", "b", "c"]


async def test_paginate_empty_result():
    result = await paginate(items=[], total=0, page=1, size=10)
    assert result.total == 0
    assert result.pages == 0
    assert list(result.items) == []


async def test_paginate_last_page_with_remainder():
    result = await paginate(items=list(range(5)), total=25, page=3, size=10)
    assert result.pages == 3


# --- Query Utils Tests ---


async def test_apply_pagination_basic(query_session: AsyncSession):
    result = await apply_pagination_sorting_filtering(query_session, MockModel)
    assert result.total == 3
    assert len(result.items) == 3


async def test_apply_pagination_skip_limit(query_session: AsyncSession):
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, skip=1, limit=1
    )
    assert result.total == 3
    assert len(result.items) == 1
    assert result.items[0].name == "Bob"


async def test_apply_pagination_search(query_session: AsyncSession):
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, search="alice", search_fields=["name", "email"]
    )
    assert result.total == 1
    assert result.items[0].name == "Alice"


async def test_apply_pagination_search_multiple_fields(query_session: AsyncSession):
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, search="example.com", search_fields=["email"]
    )
    assert result.total == 2


async def test_apply_pagination_sorting_asc(query_session: AsyncSession):
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, sort_by="age", sort_order="asc"
    )
    assert result.items[0].name == "Bob"  # 25
    assert result.items[2].name == "Charlie"  # 35


async def test_apply_pagination_sorting_desc(query_session: AsyncSession):
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, sort_by="age", sort_order="desc"
    )
    assert result.items[0].name == "Charlie"  # 35
    assert result.items[2].name == "Bob"  # 25


async def test_apply_pagination_base_query(query_session: AsyncSession):
    base = select(MockModel).where(MockModel.age > 28)
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, base_query=base
    )
    assert result.total == 2  # Alice (30) and Charlie (35)


async def test_apply_pagination_invalid_sort_field(query_session: AsyncSession):
    # Should ignore invalid field and not crash
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, sort_by="nonexistent"
    )
    assert result.total == 3


async def test_apply_pagination_invalid_search_field(query_session: AsyncSession):
    # Should ignore invalid field
    result = await apply_pagination_sorting_filtering(
        query_session, MockModel, search="Alice", search_fields=["invalid"]
    )
    assert result.total == 3  # No filter applied
