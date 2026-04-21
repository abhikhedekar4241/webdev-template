import uuid
from datetime import datetime
from typing import Any

from sqlmodel import JSON, Column, Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event: str = Field(index=True)
    user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True)
    org_id: uuid.UUID | None = Field(default=None, foreign_key="organizations.id", nullable=True)
    extra: dict[str, Any] = Field(default_factory=dict, sa_column=Column("metadata", JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
