import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.db import get_session
from app.main import app
from app.services.auth import auth_service
from app.services.orgs import org_service


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def alice(session: Session):
    return auth_service.create_user(
        session, email="alice@example.com", password="password", full_name="Alice"
    )


@pytest.fixture
def bob(session: Session):
    return auth_service.create_user(
        session, email="bob@example.com", password="password", full_name="Bob"
    )


@pytest.fixture
def superuser(session: Session):
    user = auth_service.create_user(
        session,
        email="admin@example.com",
        password="password",
        full_name="Admin",
    )
    user.is_superuser = True
    user.is_verified = True
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def alice_org(session: Session, alice):
    return org_service.create_org(
        session, name="Alice Corp", slug="alice-corp", created_by=alice.id
    )
