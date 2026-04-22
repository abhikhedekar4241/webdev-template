import pytest
from unittest.mock import MagicMock, patch
from app.services.files import FilesService
from app.models.file import File
import io

@pytest.fixture
def mock_minio():
    with patch("app.services.files.Minio") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        yield mock_client

def test_ensure_bucket_creates_if_not_exists(mock_minio):
    service = FilesService(File)
    mock_minio.bucket_exists.return_value = False
    
    service._ensure_bucket()
    
    mock_minio.bucket_exists.assert_called_once()
    mock_minio.make_bucket.assert_called_once()
    assert service._bucket_verified is True

def test_ensure_bucket_already_verified(mock_minio):
    service = FilesService(File)
    service._bucket_verified = True
    
    service._ensure_bucket()
    
    mock_minio.bucket_exists.assert_not_called()

def test_delete_from_storage_error(mock_minio):
    from minio.error import S3Error
    # code, message, resource, request_id, host_id, response
    mock_minio.remove_object.side_effect = S3Error("code", "msg", "res", "req", "host", None)
    
    service = FilesService(File)
    # Should not raise
    service.delete_from_storage("some-key")
    mock_minio.remove_object.assert_called_once()

def test_upload_calls_ensure_bucket(mock_minio):
    service = FilesService(File)
    mock_minio.bucket_exists.return_value = True
    
    data = io.BytesIO(b"test")
    service.upload(data=data, length=4, storage_key="k", content_type="text/plain")
    
    mock_minio.bucket_exists.assert_called_once()
    mock_minio.put_object.assert_called_once()

def test_presigned_url(mock_minio):
    service = FilesService(File)
    mock_minio.presigned_get_object.return_value = "http://url"
    
    assert service.presigned_url("k") == "http://url"
