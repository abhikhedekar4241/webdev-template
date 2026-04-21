import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class File(SQLModel, table=True):
    __tablename__ = "files"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    uploaded_by: uuid.UUID = Field(foreign_key="users.id")
    filename: str
    storage_key: str  # MinIO object key
    content_type: str
    size_bytes: int
    deleted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
