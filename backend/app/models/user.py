from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field

from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDModel


class User(UUIDModel, TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "users"

    email: str = Field(unique=True, index=True)
    hashed_password: str | None = Field(default=None)
    full_name: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    is_superuser: bool = Field(default=False)
    onboarding_completed_at: datetime | None = Field(
        sa_type=DateTime(timezone=True), default=None
    )
