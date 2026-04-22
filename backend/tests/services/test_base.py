import uuid

import pytest
from sqlmodel import Field, SQLModel

from app.services.base import CRUDBase


class BaseMockModel(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str


@pytest.fixture(name="service")
def service_fixture():
    return CRUDBase(BaseMockModel)


@pytest.fixture(autouse=True)
async def create_mock_table(session):
    await session.run_sync(
        lambda sync_session: BaseMockModel.__table__.create(
            sync_session.get_bind(), checkfirst=True
        )
    )
    yield


async def test_crud_create(session, service: CRUDBase):
    obj_in = BaseMockModel(name="Test")
    obj = await service.create(session, obj_in=obj_in)
    assert obj.id is not None
    assert obj.name == "Test"


async def test_crud_get(session, service: CRUDBase):
    obj = await service.create(session, obj_in=BaseMockModel(name="GetMe"))
    fetched = await service.get(session, obj.id)
    assert fetched.id == obj.id


async def test_crud_get_multi(session, service: CRUDBase):
    await service.create(session, obj_in=BaseMockModel(name="1"))
    await service.create(session, obj_in=BaseMockModel(name="2"))
    objs = await service.get_multi(session, skip=0, limit=10)
    assert len(objs) >= 2


async def test_crud_update_dict(session, service: CRUDBase):
    obj = await service.create(session, obj_in=BaseMockModel(name="Old"))
    updated = await service.update(session, db_obj=obj, obj_in={"name": "New"})
    assert updated.name == "New"


async def test_crud_update_model(session, service: CRUDBase):
    obj = await service.create(session, obj_in=BaseMockModel(name="Old"))
    update_model = BaseMockModel(name="New")
    updated = await service.update(session, db_obj=obj, obj_in=update_model)
    assert updated.name == "New"


async def test_crud_delete(session, service: CRUDBase):
    obj = await service.create(session, obj_in=BaseMockModel(name="DeleteMe"))
    await service.delete(session, id=obj.id)
    assert await service.get(session, obj.id) is None


async def test_crud_delete_nonexistent(session, service: CRUDBase):
    res = await service.delete(session, id=uuid.uuid4())
    assert res is None
