import enum
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class OrgRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class Organization(SQLModel, table=True):
    __tablename__ = "organizations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    slug: str = Field(unique=True, index=True)
    created_by: uuid.UUID = Field(foreign_key="users.id")
    deleted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrgMembership(SQLModel, table=True):
    __tablename__ = "org_memberships"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    role: OrgRole = Field(default=OrgRole.member)
    joined_at: datetime = Field(default_factory=datetime.utcnow)
