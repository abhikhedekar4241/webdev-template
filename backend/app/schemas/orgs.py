import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.org import OrgRole


class OrgCreate(BaseModel):
    name: str
    slug: str


class OrgUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: OrgRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class RoleUpdate(BaseModel):
    role: OrgRole
