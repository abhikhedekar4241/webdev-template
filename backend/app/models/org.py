import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDModel


class OrgRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Organization(UUIDModel, TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "organizations"

    name: str
    slug: str = Field(unique=True, index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id")


class OrgMembership(UUIDModel, table=True):
    __tablename__ = "org_memberships"

    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    role: OrgRole = Field(default=OrgRole.member)
    joined_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC)
    )

