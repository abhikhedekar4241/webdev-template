import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_superuser, get_session
from app.core.security import create_access_token
from app.models.file import File
from app.models.org import Organization
from app.models.user import User
from app.schemas.admin import (
    OrgListResponse,
    SystemStats,
    UserListResponse,
    ImpersonateResponse,
)
from app.utils.query import apply_pagination_sorting_filtering

router = APIRouter()


@router.get("/stats", response_model=SystemStats)
async def get_stats(
    session: AsyncSession = Depends(get_session),
    current_superuser: User = Depends(get_current_superuser),
):
    """Get global system statistics."""
    user_count = (await session.exec(select(func.count(User.id)))).one()
    org_count = (await session.exec(select(func.count(Organization.id)))).one()
    total_storage = (await session.exec(select(func.sum(File.size_bytes)))).one() or 0

    return {
        "user_count": user_count,
        "org_count": org_count,
        "total_storage_bytes": total_storage,
    }


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    sort_by: str | None = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_superuser: User = Depends(get_current_superuser),
):
    """List all users in the system."""
    return apply_pagination_sorting_filtering(
        session=session,
        model=User,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        search_fields=["email", "full_name"],
    )


@router.get("/orgs", response_model=OrgListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    sort_by: str | None = None,
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
    current_superuser: User = Depends(get_current_superuser),
):
    """List all organizations in the system."""
    return apply_pagination_sorting_filtering(
        session=session,
        model=Organization,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        search_fields=["name", "slug"],
    )


@router.post("/impersonate/{user_id}", response_model=ImpersonateResponse)
async def impersonate_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_superuser: User = Depends(get_current_superuser),
):
    """Get a short-lived access token for any user (impersonation)."""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Issue a 15-minute impersonation token
    token = create_access_token(
        subject=str(user.id), expires_delta=timedelta(minutes=15)
    )
    return {"access_token": token, "token_type": "bearer"}
