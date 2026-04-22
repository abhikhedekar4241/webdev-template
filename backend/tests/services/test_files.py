import uuid
from unittest.mock import MagicMock, patch
from sqlmodel import Session
from app.services.files import FilesService, files_service

def test_save_file_metadata(session: Session, alice, alice_org):
    f = files_service.save_metadata(
        session,
        org_id=alice_org.id,
        uploaded_by=alice.id,
        filename="report.pdf",
        storage_key="acme/report.pdf",
        content_type="application/pdf",
        size_bytes=1024,
    )
    assert f.id is not None
    assert f.filename == "report.pdf"
    assert f.deleted_at is None


def test_get_file(session: Session, alice, alice_org):
    f = files_service.save_metadata(
        session,
        org_id=alice_org.id,
        uploaded_by=alice.id,
        filename="doc.txt",
        storage_key="acme/doc.txt",
        content_type="text/plain",
        size_bytes=256,
    )
    fetched = files_service.get_active_file(session, file_id=f.id)
    assert fetched is not None
    assert fetched.filename == "doc.txt"


def test_soft_delete_file(session: Session, alice, alice_org):
    f = files_service.save_metadata(
        session,
        org_id=alice_org.id,
        uploaded_by=alice.id,
        filename="bye.txt",
        storage_key="acme/bye.txt",
        content_type="text/plain",
        size_bytes=10,
    )
    files_service.soft_delete(session, file=f)
    deleted = files_service.get_active_file(session, file_id=f.id)
    assert deleted is None


def test_get_presigned_url_calls_minio():
    mock_client = MagicMock()
    mock_client.presigned_get_object.return_value = "https://minio.example.com/key?sig=abc"

    with patch.object(FilesService, "_client", new_callable=property, fget=lambda self: mock_client):
        url = files_service.presigned_url("acme/doc.txt")

    assert url == "https://minio.example.com/key?sig=abc"
    mock_client.presigned_get_object.assert_called_once()
