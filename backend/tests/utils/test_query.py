import uuid
import pytest
from sqlmodel import Session, SQLModel, Field, select
from app.utils.pagination import paginate
from app.utils.query import apply_pagination_sorting_filtering


# --- Mock Model for Query Utils Tests ---

class MockModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: str
    age: int


@pytest.fixture(name="query_session")
def query_session_fixture(session: Session):
    # MockModel needs to be created in the current session's engine
    MockModel.__table__.create(session.get_bind(), checkfirst=True)
    
    m1 = MockModel(name="Alice", email="alice@example.com", age=30)
    m2 = MockModel(name="Bob", email="bob@example.com", age=25)
    m3 = MockModel(name="Charlie", email="charlie@gmail.com", age=35)
    session.add(m1)
    session.add(m2)
    session.add(m3)
    session.commit()
    return session


# --- Pagination Tests ---


def test_paginate_calculates_pages_correctly():
    result = paginate(items=list(range(10)), total=25, page=1, size=10)
    assert result.pages == 3


def test_paginate_returns_correct_metadata():
    result = paginate(items=list(range(10)), total=25, page=2, size=10)
    assert result.total == 25
    assert result.page == 2
    assert result.size == 10


def test_paginate_preserves_items():
    items = ["a", "b", "c"]
    result = paginate(items=items, total=3, page=1, size=10)
    assert list(result.items) == ["a", "b", "c"]


def test_paginate_empty_result():
    result = paginate(items=[], total=0, page=1, size=10)
    assert result.total == 0
    assert result.pages == 0
    assert list(result.items) == []


def test_paginate_last_page_with_remainder():
    result = paginate(items=list(range(5)), total=25, page=3, size=10)
    assert result.pages == 3


# --- Query Utils Tests ---


def test_apply_pagination_basic(query_session: Session):
    result = apply_pagination_sorting_filtering(query_session, MockModel)
    assert result.total == 3
    assert len(result.items) == 3


def test_apply_pagination_skip_limit(query_session: Session):
    result = apply_pagination_sorting_filtering(query_session, MockModel, skip=1, limit=1)
    assert result.total == 3
    assert len(result.items) == 1
    assert result.items[0].name == "Bob"


def test_apply_pagination_search(query_session: Session):
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        search="alice", 
        search_fields=["name", "email"]
    )
    assert result.total == 1
    assert result.items[0].name == "Alice"


def test_apply_pagination_search_multiple_fields(query_session: Session):
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        search="example.com", 
        search_fields=["email"]
    )
    assert result.total == 2


def test_apply_pagination_sorting_asc(query_session: Session):
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        sort_by="age", 
        sort_order="asc"
    )
    assert result.items[0].name == "Bob" # 25
    assert result.items[2].name == "Charlie" # 35


def test_apply_pagination_sorting_desc(query_session: Session):
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        sort_by="age", 
        sort_order="desc"
    )
    assert result.items[0].name == "Charlie" # 35
    assert result.items[2].name == "Bob" # 25


def test_apply_pagination_base_query(query_session: Session):
    base = select(MockModel).where(MockModel.age > 28)
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        base_query=base
    )
    assert result.total == 2 # Alice (30) and Charlie (35)


def test_apply_pagination_invalid_sort_field(query_session: Session):
    # Should ignore invalid field and not crash
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        sort_by="nonexistent"
    )
    assert result.total == 3


def test_apply_pagination_invalid_search_field(query_session: Session):
    # Should ignore invalid field
    result = apply_pagination_sorting_filtering(
        query_session, 
        MockModel, 
        search="Alice", 
        search_fields=["invalid"]
    )
    assert result.total == 3 # No filter applied
