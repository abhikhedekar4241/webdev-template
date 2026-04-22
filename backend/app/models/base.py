import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
    )


class SoftDeleteMixin(SQLModel):
    deleted_at: datetime | None = Field(sa_type=DateTime(timezone=True), default=None)


class UUIDModel(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
