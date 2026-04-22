import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class UserOAuthAccount(SQLModel, table=True):
    __tablename__ = "user_oauth_accounts"
    __table_args__ = (
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    provider: str  # e.g. "google"
    provider_user_id: str = Field(index=True)
    provider_email: str
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
