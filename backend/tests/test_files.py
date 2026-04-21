import io
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.services.auth import auth_service
from app.services.files import FilesService, files_service
from app.services.orgs import org_service


def auth_header(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alice(session):
    return auth_service.create_user(
        session, email="alice@example.com", password="pass", full_name="Alice"
    )


@pytest.fixture
def bob(session):
    return auth_service.create_user(
        session, email="bob@example.com", password="pass", full_name="Bob"
    )


@pytest.fixture
def org(session, alice):
    return org_service.create_org(
        session, name="Acme", slug="acme", created_by=alice.id
    )


def _mock_minio():
    mock = MagicMock()
    mock.bucket_exists.return_value = True
    mock.put_object.return_value = None
    mock.presigned_get_object.return_value = "https://minio.example.com/presigned"
    mock.remove_object.return_value = None
    return mock


# --- Upload ---


def test_upload_file_as_member(client: TestClient, alice, org):
    mock = _mock_minio()
    with patch.object(
        FilesService, "_client", new_callable=property, fget=lambda self: mock
    ):
        resp = client.post(
            f"/api/v1/files/?org_id={org.id}",
            headers=auth_header(alice.id),
            files={
                "file": ("report.pdf", io.BytesIO(b"pdf content"), "application/pdf")
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "report.pdf"
    assert data["content_type"] == "application/pdf"


def test_upload_file_as_non_member_returns_403(client: TestClient, bob, org):
    mock = _mock_minio()
    with patch.object(
        FilesService, "_client", new_callable=property, fget=lambda self: mock
    ):
        resp = client.post(
            f"/api/v1/files/?org_id={org.id}",
            headers=auth_header(bob.id),
            files={"file": ("x.txt", io.BytesIO(b"data"), "text/plain")},
        )
    assert resp.status_code == 403


# --- Presigned URL ---


def test_get_file_url_as_member(client: TestClient, alice, org, session):
    f = files_service.save_metadata(
        session,
        org_id=org.id,
        uploaded_by=alice.id,
        filename="doc.pdf",
        storage_key="acme/doc.pdf",
        content_type="application/pdf",
        size_bytes=512,
    )
    mock = _mock_minio()
    with patch.object(
        FilesService, "_client", new_callable=property, fget=lambda self: mock
    ):
        resp = client.get(
            f"/api/v1/files/{f.id}/url",
            headers=auth_header(alice.id),
        )
    assert resp.status_code == 200
    assert "url" in resp.json()


def test_get_file_url_not_found(client: TestClient, alice):
    resp = client.get(
        f"/api/v1/files/{uuid.uuid4()}/url",
        headers=auth_header(alice.id),
    )
    assert resp.status_code == 404


# --- Soft delete ---


def test_delete_file_as_uploader(client: TestClient, alice, org, session):
    f = files_service.save_metadata(
        session,
        org_id=org.id,
        uploaded_by=alice.id,
        filename="bye.txt",
        storage_key="acme/bye.txt",
        content_type="text/plain",
        size_bytes=10,
    )
    mock = _mock_minio()
    with patch.object(
        FilesService, "_client", new_callable=property, fget=lambda self: mock
    ):
        resp = client.delete(
            f"/api/v1/files/{f.id}",
            headers=auth_header(alice.id),
        )
    assert resp.status_code == 204


def test_delete_file_as_non_member_returns_403(
    client: TestClient, bob, org, session, alice
):
    f = files_service.save_metadata(
        session,
        org_id=org.id,
        uploaded_by=alice.id,
        filename="secret.txt",
        storage_key="acme/secret.txt",
        content_type="text/plain",
        size_bytes=10,
    )
    resp = client.delete(
        f"/api/v1/files/{f.id}",
        headers=auth_header(bob.id),
    )
    assert resp.status_code == 403
