# Plan 9: Google OAuth + Org API Keys Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Google OAuth login (with auto-linking by email) and org-scoped API keys (opaque `sk_live_` tokens, SHA-256 hash, revocable) so users can sign in without a password and integrate programmatically.

**Architecture:** OAuth is backend-driven — FastAPI handles the Google redirect and callback, issues a JWT, and redirects to a frontend `/auth/callback` page that stores the token via the existing `setToken()` helper. API keys use an opaque token pattern: `sk_live_{64 hex chars}`, SHA-256 hash stored in DB; the existing `get_current_user` dep is extended to detect and authenticate API keys transparently, so all existing endpoints work with API keys without modification.

**Tech Stack:** httpx (already installed) for Google HTTP calls, hashlib + secrets (stdlib) for key generation/hashing, SQLModel + Alembic for new tables, React + TanStack Query for frontend.

---

## File Map

**Create (backend):**
- `backend/app/models/oauth_account.py` — `UserOAuthAccount` SQLModel
- `backend/app/models/api_key.py` — `OrgApiKey` SQLModel
- `backend/alembic/versions/003_add_oauth_and_api_keys.py` — migration
- `backend/app/services/oauth.py` — Google HTTP helpers (build auth URL, exchange code, fetch user info)
- `backend/app/services/api_keys.py` — `ApiKeyService` (create, list, revoke, authenticate)
- `backend/app/api/v1/api_keys.py` — API key endpoints
- `backend/tests/test_api_keys.py` — API key tests
- `backend/tests/test_oauth.py` — OAuth tests

**Modify (backend):**
- `backend/app/models/user.py` — `hashed_password: str | None`
- `backend/app/models/__init__.py` — add new model imports
- `backend/alembic/env.py` — add new model imports
- `backend/app/services/auth.py` — handle `None` hashed_password in `authenticate`
- `backend/app/core/config.py` — add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `BACKEND_URL`
- `backend/app/api/deps.py` — detect `sk_live_` tokens and authenticate as API key
- `backend/app/api/v1/auth.py` — add `/google` and `/google/callback` endpoints
- `backend/app/main.py` — register api_keys router

**Create (frontend):**
- `frontend/src/app/auth/callback/page.tsx` — reads `?token=`, stores via `setToken()`, redirects to dashboard
- `frontend/src/services/apiKeys.ts` — `create`, `list`, `revoke`
- `frontend/src/queries/apiKeys.ts` — TanStack Query hooks

**Modify (frontend):**
- `frontend/src/middleware.ts` — add `/auth/callback` to `PUBLIC_PATHS`
- `frontend/src/app/auth/login/page.tsx` — add "Continue with Google" button
- `frontend/src/app/auth/signup/page.tsx` — add "Continue with Google" button
- `frontend/src/app/orgs/[orgId]/settings/page.tsx` — add API Keys section
- `frontend/src/constants/queryKeys.ts` — add `apiKeys` keys

---

## Task 1: Models + Migration

**Files:**
- Create: `backend/app/models/oauth_account.py`
- Create: `backend/app/models/api_key.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/alembic/env.py`
- Modify: `backend/app/services/auth.py`
- Create: `backend/alembic/versions/003_add_oauth_and_api_keys.py`

- [ ] **Step 1: Create `app/models/oauth_account.py`**

```python
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class UserOAuthAccount(SQLModel, table=True):
    __tablename__ = "user_oauth_accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    provider: str  # e.g. "google"
    provider_user_id: str = Field(index=True)
    provider_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 2: Create `app/models/api_key.py`**

```python
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class OrgApiKey(SQLModel, table=True):
    __tablename__ = "org_api_keys"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    org_id: uuid.UUID = Field(foreign_key="organizations.id", index=True)
    name: str
    key_hash: str = Field(unique=True)
    key_prefix: str  # first 10 chars of raw key, for display only
    created_by: uuid.UUID = Field(foreign_key="users.id")
    last_used_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 3: Update `app/models/user.py` — make `hashed_password` nullable**

Replace line 12:
```python
    hashed_password: str
```
with:
```python
    hashed_password: str | None = Field(default=None)
```

- [ ] **Step 4: Update `app/models/__init__.py` — add new imports**

```python
from app.models.user import User  # noqa: F401
from app.models.org import Organization, OrgMembership, OrgRole  # noqa: F401
from app.models.invitation import InvitationStatus, OrgInvitation  # noqa: F401
from app.models.file import File  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.feature_flag import FeatureFlagOverride  # noqa: F401
from app.models.oauth_account import UserOAuthAccount  # noqa: F401
from app.models.api_key import OrgApiKey  # noqa: F401
```

- [ ] **Step 5: Update `alembic/env.py` — add new imports after existing model imports**

After the existing model imports (around line 14), add:
```python
from app.models.oauth_account import UserOAuthAccount  # noqa: F401
from app.models.api_key import OrgApiKey  # noqa: F401
```

- [ ] **Step 6: Update `app/services/auth.py` — handle `None` hashed_password**

The `authenticate` method must return `None` for OAuth-only users (no password). Replace the method:

```python
def authenticate(
    self, session: Session, *, email: str, password: str
) -> User | None:
    user = self.get_by_email(session, email=email)
    if not user:
        return None
    if user.hashed_password is None:
        return None  # OAuth-only account — no password login
    if not verify_password(password, user.hashed_password):
        return None
    return user
```

- [ ] **Step 7: Write the failing model import test**

Create `tests/test_oauth_models.py`:

```python
from app.models.oauth_account import UserOAuthAccount
from app.models.api_key import OrgApiKey


def test_oauth_account_model_has_expected_fields():
    fields = UserOAuthAccount.model_fields
    assert "user_id" in fields
    assert "provider" in fields
    assert "provider_user_id" in fields
    assert "provider_email" in fields


def test_api_key_model_has_expected_fields():
    fields = OrgApiKey.model_fields
    assert "org_id" in fields
    assert "key_hash" in fields
    assert "key_prefix" in fields
    assert "revoked_at" in fields
```

- [ ] **Step 8: Run tests to verify models import cleanly**

```bash
cd backend && python -m pytest tests/test_oauth_models.py -v
```

Expected: 2 PASS

- [ ] **Step 9: Create migration `alembic/versions/003_add_oauth_and_api_keys.py`**

```python
"""add oauth accounts and api keys

Revision ID: 003_add_oauth_and_api_keys
Revises: 002_add_email_verification
Create Date: 2026-04-22

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "003_add_oauth_and_api_keys"
down_revision = "002_add_email_verification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable (Google-only users have no password)
    op.alter_column("users", "hashed_password", nullable=True)

    # user_oauth_accounts
    op.create_table(
        "user_oauth_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_user_id", sa.String(), nullable=False),
        sa.Column("provider_email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_user"),
    )
    op.create_index(
        op.f("ix_user_oauth_accounts_user_id"),
        "user_oauth_accounts",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_user_oauth_accounts_provider_user_id"),
        "user_oauth_accounts",
        ["provider_user_id"],
    )

    # org_api_keys
    op.create_table(
        "org_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("key_prefix", sa.String(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash", name="uq_org_api_keys_key_hash"),
    )
    op.create_index(
        op.f("ix_org_api_keys_org_id"),
        "org_api_keys",
        ["org_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_org_api_keys_org_id"), table_name="org_api_keys")
    op.drop_table("org_api_keys")
    op.drop_index(
        op.f("ix_user_oauth_accounts_provider_user_id"),
        table_name="user_oauth_accounts",
    )
    op.drop_index(
        op.f("ix_user_oauth_accounts_user_id"),
        table_name="user_oauth_accounts",
    )
    op.drop_table("user_oauth_accounts")
    op.alter_column("users", "hashed_password", nullable=False)
```

- [ ] **Step 10: Commit**

```bash
git add backend/app/models/oauth_account.py \
        backend/app/models/api_key.py \
        backend/app/models/user.py \
        backend/app/models/__init__.py \
        backend/alembic/env.py \
        backend/app/services/auth.py \
        backend/alembic/versions/003_add_oauth_and_api_keys.py \
        backend/tests/test_oauth_models.py
git commit -m "feat: add UserOAuthAccount and OrgApiKey models with migration"
```

---

## Task 2: API Key Service + Auth Dep Update

**Files:**
- Create: `backend/app/services/api_keys.py`
- Modify: `backend/app/api/deps.py`
- Create: `backend/tests/test_api_keys.py` (service-level tests in this task)

- [ ] **Step 1: Write failing service tests**

Create `backend/tests/test_api_keys.py`:

```python
import uuid

import pytest

from app.models.org import OrgRole
from app.services.api_keys import ApiKeyService, _hash_key, api_key_service
from app.services.auth import auth_service
from app.services.orgs import org_service


@pytest.fixture
def owner_and_org(session):
    user = auth_service.create_user(
        session,
        email="apikey_owner@example.com",
        password="password123",
        full_name="Owner",
        is_verified=True,
    )
    org = org_service.create_org(
        session, name="API Key Org", slug="api-key-org", created_by=user.id
    )
    return user, org


def test_create_returns_record_and_raw_key(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="CI key", created_by=user.id
    )
    assert raw_key.startswith("sk_live_")
    assert len(raw_key) == 74  # "sk_live_" (8) + token_hex(32) = 64 hex chars
    assert record.key_prefix == raw_key[:10]
    assert record.key_hash == _hash_key(raw_key)
    assert record.revoked_at is None


def test_authenticate_valid_key(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    result = api_key_service.authenticate(session, raw_key=raw_key)
    assert result is not None
    assert result.id == record.id


def test_authenticate_wrong_key_returns_none(session, owner_and_org):
    user, org = owner_and_org
    api_key_service.create(session, org_id=org.id, name="Key", created_by=user.id)
    result = api_key_service.authenticate(session, raw_key="sk_live_" + "0" * 64)
    assert result is None


def test_authenticate_updates_last_used_at(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    assert record.last_used_at is None
    api_key_service.authenticate(session, raw_key=raw_key)
    session.refresh(record)
    assert record.last_used_at is not None


def test_authenticate_revoked_key_returns_none(session, owner_and_org):
    user, org = owner_and_org
    record, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    api_key_service.revoke(session, key_id=record.id, org_id=org.id)
    result = api_key_service.authenticate(session, raw_key=raw_key)
    assert result is None


def test_revoke_wrong_org_returns_false(session, owner_and_org):
    user, org = owner_and_org
    record, _ = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    result = api_key_service.revoke(session, key_id=record.id, org_id=uuid.uuid4())
    assert result is False


def test_list_excludes_revoked(session, owner_and_org):
    user, org = owner_and_org
    record, _ = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    api_key_service.revoke(session, key_id=record.id, org_id=org.id)
    keys = api_key_service.list_for_org(session, org_id=org.id)
    assert keys == []
```

- [ ] **Step 2: Run to verify tests fail**

```bash
cd backend && python -m pytest tests/test_api_keys.py -v
```

Expected: FAIL with `ImportError` (module not found yet)

- [ ] **Step 3: Create `app/services/api_keys.py`**

```python
import hashlib
import secrets
import uuid
from datetime import datetime

from sqlmodel import Session, select

from app.models.api_key import OrgApiKey
from app.services.base import CRUDBase

_KEY_PREFIX = "sk_live_"


def _generate_key() -> str:
    return _KEY_PREFIX + secrets.token_hex(32)


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


class ApiKeyService(CRUDBase[OrgApiKey]):
    def create(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        name: str,
        created_by: uuid.UUID,
    ) -> tuple[OrgApiKey, str]:
        """Generate a new API key. Returns (record, raw_key). Surface raw_key to
        the user immediately — it is not recoverable after this call."""
        raw_key = _generate_key()
        record = OrgApiKey(
            org_id=org_id,
            name=name,
            key_hash=_hash_key(raw_key),
            key_prefix=raw_key[:10],
            created_by=created_by,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record, raw_key

    def list_for_org(self, session: Session, *, org_id: uuid.UUID) -> list[OrgApiKey]:
        return list(
            session.exec(
                select(OrgApiKey)
                .where(OrgApiKey.org_id == org_id)
                .where(OrgApiKey.revoked_at.is_(None))  # type: ignore[arg-type]
                .order_by(OrgApiKey.created_at.desc())
            ).all()
        )

    def revoke(
        self, session: Session, *, key_id: uuid.UUID, org_id: uuid.UUID
    ) -> bool:
        key = session.get(OrgApiKey, key_id)
        if not key or key.org_id != org_id:
            return False
        key.revoked_at = datetime.utcnow()
        session.add(key)
        session.commit()
        return True

    def authenticate(self, session: Session, *, raw_key: str) -> OrgApiKey | None:
        """Verify a raw API key. Returns the record and updates last_used_at, or
        None if invalid/revoked/expired."""
        key_hash = _hash_key(raw_key)
        key = session.exec(
            select(OrgApiKey).where(OrgApiKey.key_hash == key_hash)
        ).first()
        if not key:
            return None
        if key.revoked_at is not None:
            return None
        if key.expires_at is not None and key.expires_at < datetime.utcnow():
            return None
        key.last_used_at = datetime.utcnow()
        session.add(key)
        session.commit()
        return key


api_key_service = ApiKeyService(OrgApiKey)
```

- [ ] **Step 4: Run service tests to verify they pass**

```bash
cd backend && python -m pytest tests/test_api_keys.py -v
```

Expected: 7 PASS

- [ ] **Step 5: Update `app/api/deps.py` to handle API key tokens**

Replace the entire file:

```python
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import decode_access_token
from app.models.user import User
from app.services.api_keys import api_key_service

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
```

- [ ] **Step 6: Run all tests to verify nothing broke**

```bash
cd backend && python -m pytest -v
```

Expected: All existing tests pass + 7 new tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/api_keys.py \
        backend/app/api/deps.py \
        backend/tests/test_api_keys.py
git commit -m "feat: add ApiKeyService and update auth dep to accept sk_live_ tokens"
```

---

## Task 3: API Key Endpoints + API Tests

**Files:**
- Create: `backend/app/api/v1/api_keys.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_api_keys.py` (append API tests)

- [ ] **Step 1: Append API-level tests to `tests/test_api_keys.py`**

Add these tests at the bottom of the file:

```python
from fastapi.testclient import TestClient

from app.core.security import create_access_token


def _auth(user_id):
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


def test_create_key_via_api(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    resp = client.post(
        f"/api/v1/orgs/{org.id}/api-keys",
        json={"name": "CI/CD Key"},
        headers=_auth(user.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["key"].startswith("sk_live_")
    assert data["key_prefix"] == data["key"][:10]
    assert "key_hash" not in data  # hash must never be returned


def test_list_keys_via_api(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    api_key_service.create(session, org_id=org.id, name="Key", created_by=user.id)
    resp = client.get(f"/api/v1/orgs/{org.id}/api-keys", headers=_auth(user.id))
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert "key" not in resp.json()[0]  # full key must not appear in list


def test_revoke_key_via_api(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    record, _ = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    resp = client.delete(
        f"/api/v1/orgs/{org.id}/api-keys/{record.id}", headers=_auth(user.id)
    )
    assert resp.status_code == 204


def test_api_key_authenticates_on_existing_endpoint(
    client: TestClient, session, owner_and_org
):
    user, org = owner_and_org
    _, raw_key = api_key_service.create(
        session, org_id=org.id, name="Key", created_by=user.id
    )
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {raw_key}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == user.email


def test_member_cannot_create_key(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    member = auth_service.create_user(
        session,
        email="member_nokey@example.com",
        password="password123",
        full_name="Member",
        is_verified=True,
    )
    org_service.add_member(session, org_id=org.id, user_id=member.id, role=OrgRole.member)
    resp = client.post(
        f"/api/v1/orgs/{org.id}/api-keys",
        json={"name": "Key"},
        headers=_auth(member.id),
    )
    assert resp.status_code == 403


def test_revoke_nonexistent_key_returns_404(client: TestClient, session, owner_and_org):
    user, org = owner_and_org
    resp = client.delete(
        f"/api/v1/orgs/{org.id}/api-keys/{uuid.uuid4()}",
        headers=_auth(user.id),
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run new API tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_api_keys.py::test_create_key_via_api -v
```

Expected: FAIL with 404 (router not registered yet)

- [ ] **Step 3: Create `app/api/v1/api_keys.py`**

```python
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.org import OrgRole
from app.models.user import User
from app.services.api_keys import api_key_service
from app.services.orgs import org_service

router = APIRouter(prefix="/api/v1/orgs", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None


class ApiKeyCreated(ApiKeyResponse):
    key: str  # full raw key — shown only once at creation time


def _require_owner_or_admin(session: Session, org_id: uuid.UUID, user: User) -> None:
    membership = org_service.get_membership(session, org_id=org_id, user_id=user.id)
    if not membership or membership.role not in (OrgRole.owner, OrgRole.admin):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


@router.post("/{org_id}/api-keys", response_model=ApiKeyCreated, status_code=201)
def create_api_key(
    org_id: uuid.UUID,
    body: ApiKeyCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreated:
    _require_owner_or_admin(session, org_id, current_user)
    record, raw_key = api_key_service.create(
        session, org_id=org_id, name=body.name, created_by=current_user.id
    )
    return ApiKeyCreated(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
        expires_at=record.expires_at,
        key=raw_key,
    )


@router.get("/{org_id}/api-keys", response_model=list[ApiKeyResponse])
def list_api_keys(
    org_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ApiKeyResponse]:
    membership = org_service.get_membership(
        session, org_id=org_id, user_id=current_user.id
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return api_key_service.list_for_org(session, org_id=org_id)  # type: ignore[return-value]


@router.delete("/{org_id}/api-keys/{key_id}", status_code=204)
def revoke_api_key(
    org_id: uuid.UUID,
    key_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    _require_owner_or_admin(session, org_id, current_user)
    revoked = api_key_service.revoke(session, key_id=key_id, org_id=org_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
```

- [ ] **Step 4: Register the router in `app/main.py`**

Add import at top with other routers:
```python
from app.api.v1 import api_keys, auth, files, flags, health, invitations, orgs
```

Add after `app.include_router(flags.router)`:
```python
app.include_router(api_keys.router)
```

- [ ] **Step 5: Run all tests**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass (including 6 new API tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/api_keys.py \
        backend/app/main.py \
        backend/tests/test_api_keys.py
git commit -m "feat: add API key endpoints (create, list, revoke)"
```

---

## Task 4: Google OAuth Backend

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/services/oauth.py`
- Modify: `backend/app/api/v1/auth.py`
- Create: `backend/tests/test_oauth.py`

- [ ] **Step 1: Update `app/core/config.py` — add Google + backend URL settings**

Add these fields inside the `Settings` class, after the `FRONTEND_URL` field:

```python
    # Google OAuth (optional — endpoints return 501 if not configured)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Backend base URL (used to build OAuth redirect URIs)
    BACKEND_URL: str = "http://localhost:8000"
```

- [ ] **Step 2: Write failing OAuth tests**

Create `backend/tests/test_oauth.py`:

```python
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.models.oauth_account import UserOAuthAccount
from app.services.auth import auth_service


def _google_token():
    return {"access_token": "fake_google_access_token", "token_type": "Bearer"}


def _google_user(sub="google-sub-123", email="oauth@example.com", name="OAuth User"):
    return {"sub": sub, "email": email, "name": name}


def test_google_login_not_configured_returns_501(client: TestClient):
    resp = client.get("/api/v1/auth/google")
    assert resp.status_code == 501


def test_google_callback_invalid_state_returns_400(client: TestClient):
    client.cookies.set("oauth_state", "correct")
    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"code": "abc", "state": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_google_callback_missing_code_redirects_to_error(client: TestClient):
    client.cookies.set("oauth_state", "state123")
    resp = client.get(
        "/api/v1/auth/google/callback",
        params={"state": "state123", "error": "access_denied"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 307)
    assert "oauth_failed" in resp.headers["location"]


def test_google_callback_creates_new_user(client: TestClient, session):
    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)
    location = resp.headers["location"]
    assert "/auth/callback?token=" in location

    # User was created and verified
    user = auth_service.get_by_email(session, email="oauth@example.com")
    assert user is not None
    assert user.is_verified is True
    assert user.hashed_password is None  # OAuth-only user


def test_google_callback_links_existing_email(client: TestClient, session):
    existing = auth_service.create_user(
        session,
        email="oauth@example.com",
        password="password123",
        full_name="Existing",
        is_verified=True,
    )
    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(email=existing.email),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)

    # OAuth account was linked to existing user
    session.expire_all()
    oauth = session.exec(
        select(UserOAuthAccount).where(UserOAuthAccount.user_id == existing.id)
    ).first()
    assert oauth is not None
    assert oauth.provider == "google"


def test_google_callback_uses_existing_oauth_account(client: TestClient, session):
    user = auth_service.create_user(
        session,
        email="oauth2@example.com",
        password="password123",
        full_name="Existing",
        is_verified=True,
    )
    oauth = UserOAuthAccount(
        user_id=user.id,
        provider="google",
        provider_user_id="google-sub-456",
        provider_email=user.email,
    )
    session.add(oauth)
    session.commit()

    client.cookies.set("oauth_state", "state123")
    with patch("app.api.v1.auth.oauth_service.exchange_code", return_value=_google_token()):
        with patch(
            "app.api.v1.auth.oauth_service.get_google_user_info",
            return_value=_google_user(sub="google-sub-456", email=user.email),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback",
                params={"code": "fake_code", "state": "state123"},
                follow_redirects=False,
            )
    assert resp.status_code in (302, 307)
    assert "/auth/callback?token=" in resp.headers["location"]
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_oauth.py -v
```

Expected: FAIL — `/api/v1/auth/google` returns 404 (not implemented yet)

- [ ] **Step 4: Create `app/services/oauth.py`**

```python
from urllib.parse import urlencode

import httpx

from app.core.config import settings

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_GOOGLE_SCOPES = "openid email profile"


def google_auth_url(redirect_uri: str, state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _GOOGLE_SCOPES,
        "state": state,
        "access_type": "online",
    }
    return f"{_GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for Google tokens."""
    with httpx.Client() as client:
        resp = client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


def get_google_user_info(access_token: str) -> dict:
    """Fetch Google user profile. Returns dict with sub, email, name."""
    with httpx.Client() as client:
        resp = client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 5: Add OAuth endpoints to `app/api/v1/auth.py`**

Add these imports at the top of `auth.py`:

```python
import secrets

import httpx
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlmodel import select

from app.models.oauth_account import UserOAuthAccount
from app.services import oauth as oauth_service
```

Add these two endpoints at the end of `auth.py` (after the existing `/me` endpoint):

```python
@router.get("/google")
def google_login(request: Request) -> RedirectResponse:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=501, detail="Google OAuth is not configured"
        )
    state = secrets.token_hex(16)
    redirect_uri = f"{settings.BACKEND_URL}/api/v1/auth/google/callback"
    url = oauth_service.google_auth_url(redirect_uri, state)
    response = RedirectResponse(url)
    response.set_cookie(
        "oauth_state", state, max_age=600, httponly=True, samesite="lax"
    )
    return response


@router.get("/google/callback")
def google_callback(
    request: Request,
    session: Session = Depends(get_session),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    _error_redirect = RedirectResponse(
        f"{settings.FRONTEND_URL}/auth/login?error=oauth_failed"
    )

    if error or not code or not state:
        return _error_redirect

    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_uri = f"{settings.BACKEND_URL}/api/v1/auth/google/callback"
    try:
        token_data = oauth_service.exchange_code(code, redirect_uri)
        user_info = oauth_service.get_google_user_info(token_data["access_token"])
    except httpx.HTTPError:
        return _error_redirect

    google_sub: str = user_info["sub"]
    google_email: str = user_info["email"]
    google_name: str = user_info.get("name", google_email)

    # 1. Existing OAuth account → log in directly
    existing_oauth = session.exec(
        select(UserOAuthAccount).where(
            UserOAuthAccount.provider == "google",
            UserOAuthAccount.provider_user_id == google_sub,
        )
    ).first()

    if existing_oauth:
        user = session.get(User, existing_oauth.user_id)
    else:
        # 2. Existing email → auto-link
        user = auth_service.get_by_email(session, email=google_email)
        if user:
            oauth_account = UserOAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=google_sub,
                provider_email=google_email,
            )
            if not user.is_verified:
                user.is_verified = True
                session.add(user)
            session.add(oauth_account)
            session.commit()
        else:
            # 3. New user
            user = User(
                email=google_email,
                full_name=google_name,
                is_verified=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            oauth_account = UserOAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=google_sub,
                provider_email=google_email,
            )
            session.add(oauth_account)
            session.commit()

    if not user:
        return _error_redirect

    jwt = create_access_token(str(user.id))
    response = RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={jwt}")
    response.delete_cookie("oauth_state")
    return response
```

- [ ] **Step 6: Run OAuth tests**

```bash
cd backend && python -m pytest tests/test_oauth.py -v
```

Expected: All 7 tests pass

- [ ] **Step 7: Run full test suite**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/config.py \
        backend/app/services/oauth.py \
        backend/app/api/v1/auth.py \
        backend/tests/test_oauth.py
git commit -m "feat: add Google OAuth login endpoints with auto-link by email"
```

---

## Task 5: Frontend — Callback Page + Google Button

**Files:**
- Create: `frontend/src/app/auth/callback/page.tsx`
- Modify: `frontend/src/middleware.ts`
- Modify: `frontend/src/app/auth/login/page.tsx`
- Modify: `frontend/src/app/auth/signup/page.tsx`

- [ ] **Step 1: Create `src/app/auth/callback/page.tsx`**

```tsx
"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { setToken } from "@/services/api";
import { orgsService } from "@/services/orgs";
import { useOrgStore } from "@/store/org";

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error || !token) {
      router.push("/auth/login?error=oauth_failed");
      return;
    }

    setToken(token);

    orgsService
      .list()
      .then((orgs) => {
        if (orgs.length > 0) {
          const first = orgs[0];
          setActiveOrg({ id: first.id, name: first.name, slug: first.slug });
        }
      })
      .catch(() => {
        // best-effort org auto-select
      })
      .finally(() => {
        router.push("/dashboard");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <p className="text-sm text-muted-foreground">Signing you in…</p>
    </div>
  );
}
```

- [ ] **Step 2: Add `/auth/callback` to `PUBLIC_PATHS` in `src/middleware.ts`**

```typescript
const PUBLIC_PATHS = [
  "/auth/login",
  "/auth/signup",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify-email",
  "/auth/callback",
];
```

- [ ] **Step 3: Add "Continue with Google" to `src/app/auth/login/page.tsx`**

Add a divider and Google button after the `</form>` closing tag and before the "Don't have an account?" paragraph:

```tsx
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs text-muted-foreground">
              <span className="bg-background px-2">or</span>
            </div>
          </div>

          <a
            href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google`}
            className="flex h-10 w-full items-center justify-center gap-2.5 rounded-lg border border-input bg-background text-sm font-medium transition-colors hover:bg-muted"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </a>
```

- [ ] **Step 4: Add "Continue with Google" to `src/app/auth/signup/page.tsx`**

Add the same divider and Google button after the `</form>` closing tag and before the "Already have an account?" paragraph:

```tsx
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs text-muted-foreground">
              <span className="bg-background px-2">or</span>
            </div>
          </div>

          <a
            href={`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/google`}
            className="flex h-10 w-full items-center justify-center gap-2.5 rounded-lg border border-input bg-background text-sm font-medium transition-colors hover:bg-muted"
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Continue with Google
          </a>
```

- [ ] **Step 5: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/auth/callback/page.tsx \
        frontend/src/middleware.ts \
        frontend/src/app/auth/login/page.tsx \
        frontend/src/app/auth/signup/page.tsx
git commit -m "feat: add /auth/callback page and Google OAuth button to login/signup"
```

---

## Task 6: Frontend — API Keys in Org Settings

**Files:**
- Modify: `frontend/src/constants/queryKeys.ts`
- Create: `frontend/src/services/apiKeys.ts`
- Create: `frontend/src/queries/apiKeys.ts`
- Modify: `frontend/src/app/orgs/[orgId]/settings/page.tsx`

- [ ] **Step 1: Update `src/constants/queryKeys.ts`**

```typescript
export const QUERY_KEYS = {
  me: ["me"] as const,
  orgs: {
    list: ["orgs"] as const,
    detail: (orgId: string) => ["orgs", orgId] as const,
    members: (orgId: string) => ["orgs", orgId, "members"] as const,
    flags: (orgId: string) => ["orgs", orgId, "flags"] as const,
    apiKeys: (orgId: string) => ["orgs", orgId, "api-keys"] as const,
  },
  invitations: {
    list: ["invitations"] as const,
  },
  files: {
    list: (orgId: string) => ["files", orgId] as const,
  },
} as const;
```

- [ ] **Step 2: Create `src/services/apiKeys.ts`**

```typescript
import api from "./api";

export interface ApiKeyData {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export interface ApiKeyCreated extends ApiKeyData {
  key: string; // full raw key — available only at creation time
}

export const apiKeysService = {
  list: (orgId: string) =>
    api
      .get<ApiKeyData[]>(`/api/v1/orgs/${orgId}/api-keys`)
      .then((r) => r.data),

  create: (orgId: string, name: string) =>
    api
      .post<ApiKeyCreated>(`/api/v1/orgs/${orgId}/api-keys`, { name })
      .then((r) => r.data),

  revoke: (orgId: string, keyId: string) =>
    api.delete(`/api/v1/orgs/${orgId}/api-keys/${keyId}`),
};
```

- [ ] **Step 3: Create `src/queries/apiKeys.ts`**

```typescript
"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants/queryKeys";
import { getApiError } from "@/lib/apiError";
import { apiKeysService } from "@/services/apiKeys";

export function useApiKeys(orgId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.orgs.apiKeys(orgId),
    queryFn: () => apiKeysService.list(orgId),
    enabled: !!orgId,
  });
}

export function useCreateApiKey(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => apiKeysService.create(orgId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.apiKeys(orgId),
      });
    },
    onError: (err) => {
      toast.error(getApiError(err, "Failed to create API key"));
    },
  });
}

export function useRevokeApiKey(orgId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => apiKeysService.revoke(orgId, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.orgs.apiKeys(orgId),
      });
      toast.success("API key revoked");
    },
    onError: () => {
      toast.error("Failed to revoke API key");
    },
  });
}
```

- [ ] **Step 4: Update `src/app/orgs/[orgId]/settings/page.tsx` — add API Keys section**

Add these imports at the top:

```tsx
import { useState } from "react";
import { Key, Copy, Check } from "lucide-react";
import { useApiKeys, useCreateApiKey, useRevokeApiKey } from "@/queries/apiKeys";
import type { ApiKeyCreated } from "@/services/apiKeys";
```

Add this `ApiKeysSection` component definition before the `OrgSettingsPage` export:

```tsx
function ApiKeysSection({ orgId }: { orgId: string }) {
  const { data: keys = [], isLoading } = useApiKeys(orgId);
  const createKey = useCreateApiKey(orgId);
  const revokeKey = useRevokeApiKey(orgId);

  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const result = await createKey.mutateAsync(newKeyName.trim());
      setCreatedKey(result);
      setNewKeyName("");
    } catch {
      // error handled in mutation
    }
  }

  function handleCopy() {
    if (!createdKey) return;
    navigator.clipboard.writeText(createdKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDismiss() {
    setCreatedKey(null);
    setShowModal(false);
    setCopied(false);
  }

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-5 py-4">
        <h2 className="font-semibold">API Keys</h2>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Keys authenticate as the key creator with full org access.
        </p>
      </div>
      <div className="p-5 space-y-4">
        {/* Create form */}
        {!createdKey && (
          <form onSubmit={handleCreate} className="flex gap-2">
            <input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g. CI/CD)"
              className="flex h-9 flex-1 rounded-lg border border-input bg-background px-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <button
              type="submit"
              disabled={createKey.isPending || !newKeyName.trim()}
              className="flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3 text-sm font-semibold text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              <Key className="h-3.5 w-3.5" />
              {createKey.isPending ? "Creating…" : "Create"}
            </button>
          </form>
        )}

        {/* Show newly created key — one time only */}
        {createdKey && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3 dark:border-amber-800 dark:bg-amber-950/30">
            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Copy your key now — it won&apos;t be shown again.
            </p>
            <div className="flex gap-2">
              <input
                readOnly
                value={createdKey.key}
                className="flex h-9 flex-1 rounded-lg border border-input bg-background px-3 font-mono text-xs focus-visible:outline-none"
              />
              <button
                onClick={handleCopy}
                className="flex h-9 items-center gap-1.5 rounded-lg border border-input bg-background px-3 text-sm hover:bg-muted"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5 text-green-600" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <button
              onClick={handleDismiss}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Done — dismiss
            </button>
          </div>
        )}

        {/* Key list */}
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-muted" />
            ))}
          </div>
        ) : keys.length === 0 ? (
          <p className="text-sm text-muted-foreground">No API keys yet.</p>
        ) : (
          <div className="divide-y divide-border rounded-lg border border-border">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium">{key.name}</p>
                  <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                    {key.key_prefix}…
                    {key.last_used_at
                      ? ` · last used ${new Date(key.last_used_at).toLocaleDateString()}`
                      : " · never used"}
                  </p>
                </div>
                <button
                  onClick={() => {
                    if (confirm(`Revoke "${key.name}"? This cannot be undone.`)) {
                      revokeKey.mutate(key.id);
                    }
                  }}
                  className="rounded-md px-2.5 py-1 text-xs font-medium text-destructive hover:bg-destructive/10"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

Insert the `<ApiKeysSection>` between the General section and the Danger zone section in the `OrgSettingsPage` JSX. Find the closing `</div>` of the General settings card and add:

```tsx
      <ApiKeysSection orgId={orgId} />
```

The full return JSX structure should be:
```
<div className="mx-auto max-w-lg px-6 py-8 space-y-6">
  <Link ...>Back to organization</Link>
  <div> {/* heading */} </div>
  <div> {/* General settings card */} </div>
  <ApiKeysSection orgId={orgId} />   {/* ← add this */}
  <div> {/* Danger zone card */} </div>
</div>
```

- [ ] **Step 5: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 6: Run backend tests one final time**

```bash
cd backend && python -m pytest -v
```

Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add frontend/src/constants/queryKeys.ts \
        frontend/src/services/apiKeys.ts \
        frontend/src/queries/apiKeys.ts \
        frontend/src/app/orgs/\[orgId\]/settings/page.tsx
git commit -m "feat: add API keys tab to org settings with create, list, and revoke"
```

---

## Self-Review Checklist

- [x] **Spec coverage:**
  - Google OAuth (login, callback, new user, link, re-use) — Tasks 4 & 5 ✓
  - API keys (create, list, revoke, authenticate) — Tasks 2, 3 & 6 ✓
  - `hashed_password` nullable — Task 1 ✓
  - `user_oauth_accounts` table — Task 1 ✓
  - `org_api_keys` table — Task 1 ✓
  - `/auth/callback` page — Task 5 ✓
  - Google button on login + signup — Task 5 ✓
  - API Keys section in org settings — Task 6 ✓
  - Error cases (501 not configured, 400 bad state, oauth_failed redirect) — Task 4 ✓

- [x] **Type consistency:** `api_key_service`, `_hash_key`, `_KEY_PREFIX` defined in Task 2 and referenced consistently in Tasks 3 & 6. `oauth_service` module defined in Task 4 and imported as `from app.services import oauth as oauth_service`.

- [x] **No placeholders:** All steps have complete code blocks.
