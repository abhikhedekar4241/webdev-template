import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class OrgApiKey(SQLModel, table=True):
    __tablename__ = "org_api_keys"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    name: str
    key_hash: str = Field(unique=True)
    key_prefix: str  # first 10 chars of raw key, for display only
    created_by: uuid.UUID = Field(foreign_key="users.id")
    last_used_at: datetime | None = Field(sa_type=DateTime(timezone=True), default=None)
    expires_at: datetime | None = Field(sa_type=DateTime(timezone=True), default=None)
    revoked_at: datetime | None = Field(sa_type=DateTime(timezone=True), default=None)
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
