import io
import uuid
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.services.files import FilesService, files_service
from tests.helpers import get_auth_header


def _mock_minio():
    mock = MagicMock()
    mock.bucket_exists.return_value = True
    mock.put_object.return_value = None
    mock.presigned_get_object.return_value = "https://minio.example.com/presigned"
    mock.remove_object.return_value = None
    return mock


async def test_upload_file_as_member(client: TestClient, alice, alice_org):
    mock = _mock_minio()
    with patch.object(
        FilesService, "_client", new_callable=property, fget=lambda self: mock
    ):
        resp = await client.post(
            f"/api/v1/files/?org_id={alice_org.id}",
            headers=get_auth_header(alice.id),
            files={
                "file": ("report.pdf", io.BytesIO(b"pdf content"), "application/pdf")
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "report.pdf"
    assert data["content_type"] == "application/pdf"


async def test_upload_file_as_non_member_returns_403(
    client: TestClient, bob, alice_org
):
    mock = _mock_minio()
    with patch.object(
        FilesService, "_client", new_callable=property, fget=lambda self: mock
    ):
        resp = await client.post(
            f"/api/v1/files/?org_id={alice_org.id}",
            headers=get_auth_header(bob.id),
            files={"file": ("x.txt", io.BytesIO(b"data"), "text/plain")},
        )
    assert resp.status_code == 403


async def test_get_file_url_as_member(
    client: TestClient, alice, alice_org, session: Session
):
    f = await files_service.save_metadata(
        session,
        org_id=alice_org.id,
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
        resp = await client.get(
            f"/api/v1/files/{f.id}/url",
            headers=get_auth_header(alice.id),
        )
    assert resp.status_code == 200
    assert "url" in resp.json()


async def test_get_file_url_not_found(client: TestClient, alice):
    resp = await client.get(
        f"/api/v1/files/{uuid.uuid4()}/url",
        headers=get_auth_header(alice.id),
    )
    assert resp.status_code == 404


async def test_delete_file_as_uploader(
    client: TestClient, alice, alice_org, session: Session
):
    f = await files_service.save_metadata(
        session,
        org_id=alice_org.id,
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
        resp = await client.delete(
            f"/api/v1/files/{f.id}",
            headers=get_auth_header(alice.id),
        )
    assert resp.status_code == 204


async def test_delete_file_as_non_member_returns_403(
    client: TestClient, bob, alice_org, session: Session, alice
):
    f = await files_service.save_metadata(
        session,
        org_id=alice_org.id,
        uploaded_by=alice.id,
        filename="secret.txt",
        storage_key="acme/secret.txt",
        content_type="text/plain",
        size_bytes=10,
    )
    resp = await client.delete(
        f"/api/v1/files/{f.id}",
        headers=get_auth_header(bob.id),
    )
    assert resp.status_code == 403
