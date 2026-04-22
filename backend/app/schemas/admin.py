import uuid
from datetime import datetime
from pydantic import BaseModel


class SystemStats(BaseModel):
    user_count: int
    org_count: int
    total_storage_bytes: int


class AdminUser(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    is_verified: bool
    created_at: datetime


class UserListResponse(BaseModel):
    items: list[AdminUser]
    total: int


class AdminOrg(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_by: uuid.UUID
    created_at: datetime


class OrgListResponse(BaseModel):
    items: list[AdminOrg]
    total: int


class ImpersonateResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
