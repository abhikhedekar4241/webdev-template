import uuid

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import decode_access_token
from app.models.user import User
from app.models.org import OrgRole
from app.services.api_keys import api_key_service
from app.services.orgs import org_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_API_KEY_PREFIX = "sk_live_"


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    if token.startswith(_API_KEY_PREFIX):
        key_record = api_key_service.authenticate(session, raw_key=token)
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key")
        user = session.get(User, key_record.created_by)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        return user

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")
    user = session.get(User, uid)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user does not have enough privileges"
        )
    return current_user


def require_org(session: Session, org_id: uuid.UUID, user_id: uuid.UUID):
    """Return org if user is a member, else raise 404."""
    org = org_service.get_org_for_member(session, org_id=org_id, user_id=user_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def require_role(
    session: Session, org_id: uuid.UUID, user_id: uuid.UUID, allowed: list[OrgRole]
):
    """Raise 403 if user doesn't have one of the allowed roles in the org."""
    membership = org_service.get_membership(session, org_id=org_id, user_id=user_id)
    if not membership or membership.role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return membership
