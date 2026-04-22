import pytest
from sqlmodel import Session, SQLModel, Field
from app.services.base import CRUDBase
import uuid

class BaseMockModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str

@pytest.fixture(name="service")
def service_fixture():
    return CRUDBase(BaseMockModel)

@pytest.fixture(autouse=True)
def create_mock_table(session: Session):
    BaseMockModel.__table__.create(session.get_bind(), checkfirst=True)
    yield
    # No need to drop, session is handled by conftest

def test_crud_create(session: Session, service: CRUDBase):
    obj_in = BaseMockModel(name="Test")
    obj = service.create(session, obj_in=obj_in)
    assert obj.id is not None
    assert obj.name == "Test"

def test_crud_get(session: Session, service: CRUDBase):
    obj = service.create(session, obj_in=BaseMockModel(name="GetMe"))
    fetched = service.get(session, obj.id)
    assert fetched.id == obj.id

def test_crud_get_multi(session: Session, service: CRUDBase):
    service.create(session, obj_in=BaseMockModel(name="1"))
    service.create(session, obj_in=BaseMockModel(name="2"))
    objs = service.get_multi(session, skip=0, limit=10)
    assert len(objs) >= 2

def test_crud_update_dict(session: Session, service: CRUDBase):
    obj = service.create(session, obj_in=BaseMockModel(name="Old"))
    updated = service.update(session, db_obj=obj, obj_in={"name": "New"})
    assert updated.name == "New"

def test_crud_update_model(session: Session, service: CRUDBase):
    obj = service.create(session, obj_in=BaseMockModel(name="Old"))
    update_model = BaseMockModel(name="New")
    updated = service.update(session, db_obj=obj, obj_in=update_model)
    assert updated.name == "New"

def test_crud_delete(session: Session, service: CRUDBase):
    obj = service.create(session, obj_in=BaseMockModel(name="DeleteMe"))
    service.delete(session, id=obj.id)
    assert service.get(session, obj.id) is None

def test_crud_delete_nonexistent(session: Session, service: CRUDBase):
    res = service.delete(session, id=uuid.uuid4())
    assert res is None
