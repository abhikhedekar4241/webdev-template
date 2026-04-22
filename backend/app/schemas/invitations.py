import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.org import OrgRole


class InvitationCreate(BaseModel):
    org_id: uuid.UUID
    email: EmailStr
    role: OrgRole


class InvitationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    org_name: str
    invited_email: str
    role: OrgRole
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
