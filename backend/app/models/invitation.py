import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

from app.models.org import OrgRole


class InvitationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class OrgInvitation(SQLModel, table=True):
    __tablename__ = "org_invitations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    invited_email: str = Field(index=True)
    role: OrgRole = Field(default=OrgRole.member)
    invited_by: uuid.UUID = Field(foreign_key="users.id")
    status: InvitationStatus = Field(default=InvitationStatus.pending)
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
