import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str | None = Field(default=None)
    full_name: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
