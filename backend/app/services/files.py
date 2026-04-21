import io
import uuid
from datetime import datetime, timedelta

import structlog
from minio import Minio
from minio.error import S3Error
from sqlmodel import Session

from app.core.config import settings
from app.models.file import File
from app.services.base import CRUDBase

logger = structlog.get_logger()

PRESIGN_EXPIRY_SECONDS = 3600  # 1 hour


class FilesService(CRUDBase[File]):
    @property
    def _client(self) -> Minio:
        return Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

    def _ensure_bucket(self) -> None:
        client = self._client
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
        except S3Error as e:
            logger.error("minio_bucket_error", error=str(e))
            raise

    def upload(self, *, data: bytes, storage_key: str, content_type: str) -> None:
        self._ensure_bucket()
        self._client.put_object(
            settings.MINIO_BUCKET,
            storage_key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logger.info("file_uploaded", storage_key=storage_key)

    def presigned_url(self, storage_key: str) -> str:
        return self._client.presigned_get_object(
            settings.MINIO_BUCKET,
            storage_key,
            expires=timedelta(seconds=PRESIGN_EXPIRY_SECONDS),
        )

    def delete_from_storage(self, storage_key: str) -> None:
        try:
            self._client.remove_object(settings.MINIO_BUCKET, storage_key)
            logger.info("file_deleted_from_storage", storage_key=storage_key)
        except S3Error as e:
            logger.warning("minio_delete_error", storage_key=storage_key, error=str(e))

    def save_metadata(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        filename: str,
        storage_key: str,
        content_type: str,
        size_bytes: int,
    ) -> File:
        f = File(
            org_id=org_id,
            uploaded_by=uploaded_by,
            filename=filename,
            storage_key=storage_key,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        session.add(f)
        session.commit()
        session.refresh(f)
        return f

    def get_active_file(self, session: Session, *, file_id: uuid.UUID) -> File | None:
        f = session.get(File, file_id)
        if f and f.deleted_at is None:
            return f
        return None

    def soft_delete(self, session: Session, *, file: File) -> File:
        file.deleted_at = datetime.utcnow()
        session.add(file)
        session.commit()
        session.refresh(file)
        return file


files_service = FilesService(File)
