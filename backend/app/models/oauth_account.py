import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class UserOAuthAccount(SQLModel, table=True):
    __tablename__ = "user_oauth_accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    provider: str  # e.g. "google"
    provider_user_id: str = Field(index=True)
    provider_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
