# Email Verification (OTP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Block unverified users from using the app by sending a 6-digit OTP to their email on signup, requiring them to verify before they can log in.

**Architecture:** A new `EmailVerification` table stores short-lived OTPs keyed to a user. The `User` model gains an `is_verified` flag. After registration the user is redirected to a verification page; login is blocked (HTTP 403) until verified. Successful OTP entry auto-issues a JWT so the user lands directly in the app.

**Tech Stack:** FastAPI + SQLModel + Pydantic v2, Next.js 14 App Router, TanStack Query 5, Axios, Tailwind CSS.

---

## Files to Create / Modify

**Backend — create:**
- `backend/app/models/verification.py` — `EmailVerification` SQLModel
- `backend/alembic/versions/002_add_email_verification.py` — migration
- `backend/app/services/verification.py` — OTP generation, validation, resend logic
- `backend/app/emails/templates/verify_email.html` — OTP email template
- `backend/tests/test_email_verification.py` — all verification tests

**Backend — modify:**
- `backend/app/models/user.py` — add `is_verified: bool`
- `backend/app/api/v1/auth.py` — update login/register, add verify + resend endpoints, add `is_verified` to `UserResponse`
- `backend/app/services/auth.py` — accept `is_verified` kwarg on `create_user`
- `backend/seed.py` — mark seed users as verified

**Frontend — create:**
- `frontend/src/app/auth/verify-email/page.tsx` — OTP entry page

**Frontend — modify:**
- `frontend/src/services/auth.ts` — add `verifyEmail`, `resendVerification`, add `is_verified` to `UserData`
- `frontend/src/queries/auth.ts` — add `useVerifyEmail`, `useResendVerification`
- `frontend/src/app/auth/signup/page.tsx` — redirect to verify page after register
- `frontend/src/app/auth/login/page.tsx` — detect 403 unverified → redirect to verify page

---

## Task 1: User model — add `is_verified` + EmailVerification model + migration

**Files:**
- Modify: `backend/app/models/user.py`
- Create: `backend/app/models/verification.py`
- Create: `backend/alembic/versions/002_add_email_verification.py`
- Modify: `backend/seed.py`

- [ ] **Step 1: Add `is_verified` to User**

Replace `backend/app/models/user.py` entirely:

```python
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 2: Create EmailVerification model**

Create `backend/app/models/verification.py`:

```python
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class EmailVerification(SQLModel, table=True):
    __tablename__ = "email_verifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    otp: str = Field(max_length=6)
    expires_at: datetime
    used_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

- [ ] **Step 3: Create migration**

Create `backend/alembic/versions/002_add_email_verification.py`:

```python
"""add email verification

Revision ID: 002_add_email_verification
Revises: 001_add_orgs
Create Date: 2026-04-21 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "002_add_email_verification"
down_revision = "001_add_orgs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_verified to users — default False for new rows,
    # existing rows stay False (re-run seed.py in dev to fix dev users)
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )

    op.create_table(
        "email_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("otp", sa.String(length=6), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verifications_user_id"),
        "email_verifications",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_email_verifications_user_id"),
        table_name="email_verifications",
    )
    op.drop_table("email_verifications")
    op.drop_column("users", "is_verified")
```

- [ ] **Step 4: Update seed.py to mark seed users as verified**

In `backend/seed.py`, after each `auth_service.create_user(...)` call, add:

```python
# After creating admin user:
admin.is_verified = True
session.add(admin)
session.commit()
session.refresh(admin)

# After creating member user:
member.is_verified = True
session.add(member)
session.commit()
session.refresh(member)
```

- [ ] **Step 5: Run the migration**

```bash
docker compose exec backend alembic upgrade head
```

Expected output ends with: `Running upgrade 001_add_orgs -> 002_add_email_verification, add email verification`

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/user.py backend/app/models/verification.py \
        backend/alembic/versions/002_add_email_verification.py backend/seed.py
git commit -m "feat: add is_verified to User model and EmailVerification table"
```

---

## Task 2: Verification service

**Files:**
- Create: `backend/app/services/verification.py`
- Modify: `backend/app/services/auth.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_email_verification.py`:

```python
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.verification import EmailVerification
from app.services.auth import auth_service
from app.services.verification import verification_service


def auth_header(user_id: uuid.UUID) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(user_id))}"}


@pytest.fixture
def unverified_user(session):
    return auth_service.create_user(
        session,
        email="unverified@example.com",
        password="password123",
        full_name="Unverified User",
    )


def test_generate_otp_is_6_digits(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    assert len(otp_record.otp) == 6
    assert otp_record.otp.isdigit()


def test_otp_expires_in_10_minutes(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    delta = otp_record.expires_at - datetime.utcnow()
    assert 590 < delta.total_seconds() < 610


def test_verify_otp_marks_user_verified(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is not None
    assert result.is_verified is True


def test_verify_otp_marks_record_used(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    session.refresh(otp_record)
    assert otp_record.used_at is not None


def test_verify_wrong_otp_returns_none(session, unverified_user):
    verification_service.create_otp(session, user_id=unverified_user.id)
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp="000000"
    )
    assert result is None


def test_verify_expired_otp_returns_none(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    # Manually expire it
    otp_record.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.add(otp_record)
    session.commit()
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is None


def test_verify_used_otp_returns_none(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    # Try to use same OTP again
    session.refresh(unverified_user)
    result = verification_service.verify_otp(
        session, email=unverified_user.email, otp=otp_record.otp
    )
    assert result is None


def test_has_recent_otp_true_within_60s(session, unverified_user):
    verification_service.create_otp(session, user_id=unverified_user.id)
    assert verification_service.has_recent_otp(session, user_id=unverified_user.id) is True


def test_has_recent_otp_false_after_60s(session, unverified_user):
    otp_record = verification_service.create_otp(session, user_id=unverified_user.id)
    otp_record.created_at = datetime.utcnow() - timedelta(seconds=61)
    session.add(otp_record)
    session.commit()
    assert verification_service.has_recent_otp(session, user_id=unverified_user.id) is False
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker compose exec backend pytest tests/test_email_verification.py -v 2>&1 | head -20
```

Expected: ImportError or similar — `verification_service` not defined yet.

- [ ] **Step 3: Implement verification service**

Create `backend/app/services/verification.py`:

```python
import random
import string
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models.user import User
from app.models.verification import EmailVerification

OTP_EXPIRE_SECONDS = 600   # 10 minutes
RESEND_COOLDOWN_SECONDS = 60


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


class VerificationService:
    def create_otp(self, session: Session, *, user_id: uuid.UUID) -> EmailVerification:
        record = EmailVerification(
            user_id=user_id,
            otp=_generate_otp(),
            expires_at=datetime.utcnow() + timedelta(seconds=OTP_EXPIRE_SECONDS),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def verify_otp(
        self, session: Session, *, email: str, otp: str
    ) -> User | None:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            return None

        record = session.exec(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user.id,
                EmailVerification.otp == otp,
                EmailVerification.used_at.is_(None),  # type: ignore[union-attr]
                EmailVerification.expires_at > datetime.utcnow(),
            )
            .order_by(EmailVerification.created_at.desc())  # type: ignore[union-attr]
        ).first()

        if not record:
            return None

        record.used_at = datetime.utcnow()
        user.is_verified = True
        session.add(record)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def has_recent_otp(self, session: Session, *, user_id: uuid.UUID) -> bool:
        cutoff = datetime.utcnow() - timedelta(seconds=RESEND_COOLDOWN_SECONDS)
        record = session.exec(
            select(EmailVerification)
            .where(
                EmailVerification.user_id == user_id,
                EmailVerification.created_at > cutoff,
            )
            .order_by(EmailVerification.created_at.desc())  # type: ignore[union-attr]
        ).first()
        return record is not None


verification_service = VerificationService()
```

- [ ] **Step 4: Update `auth_service.create_user` to accept `is_verified`**

Replace `backend/app/services/auth.py` entirely:

```python
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services.base import CRUDBase


class AuthService(CRUDBase[User]):
    def get_by_email(self, session: Session, email: str) -> User | None:
        return session.exec(select(User).where(User.email == email)).first()

    def create_user(
        self,
        session: Session,
        *,
        email: str,
        password: str,
        full_name: str,
        is_verified: bool = False,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            is_verified=is_verified,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def authenticate(
        self, session: Session, *, email: str, password: str
    ) -> User | None:
        user = self.get_by_email(session, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


auth_service = AuthService(User)
```

- [ ] **Step 5: Run the verification tests**

```bash
docker compose exec backend pytest tests/test_email_verification.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/verification.py backend/app/services/auth.py \
        backend/tests/test_email_verification.py
git commit -m "feat: add verification service — OTP generation, validation, resend cooldown"
```

---

## Task 3: Email template for OTP

**Files:**
- Create: `backend/app/emails/templates/verify_email.html`

- [ ] **Step 1: Create OTP email template**

Create `backend/app/emails/templates/verify_email.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Verify your email</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f9fafb; margin: 0; padding: 40px 20px; }
    .card { background: white; border-radius: 12px; max-width: 480px; margin: 0 auto; padding: 40px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .otp { font-size: 36px; font-weight: 700; letter-spacing: 12px; color: #111827; text-align: center; margin: 28px 0; padding: 20px; background: #f3f4f6; border-radius: 8px; }
    .footer { margin-top: 32px; font-size: 12px; color: #9ca3af; }
  </style>
</head>
<body>
  <div class="card">
    <h1 style="font-size:22px;font-weight:700;color:#111827;margin:0 0 8px">Verify your email</h1>
    <p style="color:#6b7280;margin:0 0 4px">Hi {{ full_name }},</p>
    <p style="color:#6b7280;margin:0 0 24px">Use the code below to verify your email address. It expires in 10 minutes.</p>
    <div class="otp">{{ otp }}</div>
    <p style="color:#6b7280;font-size:14px">If you didn't create an account, you can safely ignore this email.</p>
    <div class="footer">This code expires in 10 minutes and can only be used once.</div>
  </div>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/emails/templates/verify_email.html
git commit -m "feat: add verify_email OTP email template"
```

---

## Task 4: Backend API endpoints — verify, resend, login guard

**Files:**
- Modify: `backend/app/api/v1/auth.py`
- Test: `backend/tests/test_email_verification.py`

- [ ] **Step 1: Write failing API tests**

Append to `backend/tests/test_email_verification.py`:

```python
# --- API tests ---


def test_login_unverified_returns_403(client: TestClient, session):
    auth_service.create_user(
        session,
        email="blocked@example.com",
        password="password123",
        full_name="Blocked",
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "blocked@example.com", "password": "password123"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Email not verified"


def test_register_creates_unverified_user(client: TestClient):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "password123", "full_name": "New"},
    )
    assert resp.status_code == 201
    assert resp.json()["is_verified"] is False


def test_verify_email_returns_token(client: TestClient, session):
    user = auth_service.create_user(
        session,
        email="verify@example.com",
        password="password123",
        full_name="Verify Me",
    )
    otp_record = verification_service.create_otp(session, user_id=user.id)
    resp = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "verify@example.com", "otp": otp_record.otp},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_verify_email_wrong_otp_returns_400(client: TestClient, session):
    auth_service.create_user(
        session,
        email="wrongotp@example.com",
        password="password123",
        full_name="Wrong OTP",
    )
    resp = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "wrongotp@example.com", "otp": "999999"},
    )
    assert resp.status_code == 400


def test_resend_verification_success(client: TestClient, session):
    auth_service.create_user(
        session,
        email="resend@example.com",
        password="password123",
        full_name="Resend",
    )
    resp = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "resend@example.com"},
    )
    assert resp.status_code == 200


def test_resend_verification_rate_limit(client: TestClient, session):
    user = auth_service.create_user(
        session,
        email="ratelimit@example.com",
        password="password123",
        full_name="Rate",
    )
    verification_service.create_otp(session, user_id=user.id)
    resp = client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "ratelimit@example.com"},
    )
    assert resp.status_code == 429


def test_login_after_verification_succeeds(client: TestClient, session):
    user = auth_service.create_user(
        session,
        email="afterverify@example.com",
        password="password123",
        full_name="After",
    )
    otp_record = verification_service.create_otp(session, user_id=user.id)
    client.post(
        "/api/v1/auth/verify-email",
        json={"email": "afterverify@example.com", "otp": otp_record.otp},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "afterverify@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()
```

- [ ] **Step 2: Run to confirm they fail**

```bash
docker compose exec backend pytest tests/test_email_verification.py -k "api" -v 2>&1 | head -30
```

Expected: 7 failures (endpoints don't exist yet).

- [ ] **Step 3: Rewrite `backend/app/api/v1/auth.py`**

Replace the entire file:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.core.security import create_access_token
from app.models.user import User
from app.services.auth import auth_service
from app.services.email import email_service
from app.services.verification import verification_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> TokenResponse:
    user = auth_service.authenticate(
        session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    body: RegisterRequest,
    session: Session = Depends(get_session),
) -> UserResponse:
    existing = auth_service.get_by_email(session, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = auth_service.create_user(
        session, email=body.email, password=body.password, full_name=body.full_name
    )
    otp_record = verification_service.create_otp(session, user_id=user.id)
    email_service.send(
        to=user.email,
        subject="Verify your email",
        template="verify_email",
        context={"full_name": user.full_name, "otp": otp_record.otp},
    )
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(
    body: VerifyEmailRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    user = verification_service.verify_otp(
        session, email=body.email, otp=body.otp
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/resend-verification", status_code=200)
def resend_verification(
    body: ResendVerificationRequest,
    session: Session = Depends(get_session),
) -> dict:
    user = auth_service.get_by_email(session, body.email)
    # Always return 200 even if email not found (avoid user enumeration)
    if not user or user.is_verified:
        return {"message": "If that email exists and is unverified, a new code was sent"}
    if verification_service.has_recent_otp(session, user_id=user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds before requesting another code",
        )
    otp_record = verification_service.create_otp(session, user_id=user.id)
    email_service.send(
        to=user.email,
        subject="Verify your email",
        template="verify_email",
        context={"full_name": user.full_name, "otp": otp_record.otp},
    )
    return {"message": "Verification code sent"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
    )
```

- [ ] **Step 4: Run the full test suite**

```bash
docker compose exec backend pytest tests/test_email_verification.py -v
```

Expected: all 16 tests (9 service + 7 API) PASS.

- [ ] **Step 5: Run the entire suite to check for regressions**

```bash
docker compose exec backend pytest -q
```

Expected: all tests pass (count will be ~92+).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/auth.py backend/tests/test_email_verification.py
git commit -m "feat: add verify-email and resend-verification endpoints, block unverified login"
```

---

## Task 5: Frontend — verify-email page

**Files:**
- Create: `frontend/src/app/auth/verify-email/page.tsx`

- [ ] **Step 1: Add `verifyEmail` and `resendVerification` to auth service**

Replace `frontend/src/services/auth.ts`:

```typescript
import api, { setToken, clearToken } from "./api";

export interface UserData {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
}

export const authService = {
  async login(email: string, password: string): Promise<string> {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    const { data } = await api.post<{ access_token: string }>("/api/v1/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    setToken(data.access_token);
    return data.access_token;
  },

  async register(email: string, password: string, fullName: string): Promise<UserData> {
    const { data } = await api.post<UserData>("/api/v1/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    return data;
  },

  async verifyEmail(email: string, otp: string): Promise<string> {
    const { data } = await api.post<{ access_token: string }>("/api/v1/auth/verify-email", {
      email,
      otp,
    });
    setToken(data.access_token);
    return data.access_token;
  },

  async resendVerification(email: string): Promise<void> {
    await api.post("/api/v1/auth/resend-verification", { email });
  },

  async me(): Promise<UserData> {
    const { data } = await api.get<UserData>("/api/v1/auth/me");
    return data;
  },

  logout(): void {
    clearToken();
  },
};
```

- [ ] **Step 2: Add `useVerifyEmail` and `useResendVerification` hooks**

Replace `frontend/src/queries/auth.ts`:

```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth";
import { orgsService } from "@/services/orgs";
import { useOrgStore } from "@/store/org";
import { useRouter } from "next/navigation";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => authService.me(),
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const { activeOrg, setActiveOrg } = useOrgStore();
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      if (!activeOrg) {
        try {
          const orgs = await orgsService.list();
          if (orgs.length > 0) {
            const first = orgs[0];
            setActiveOrg({ id: first.id, name: first.name, slug: first.slug });
          }
        } catch {
          // ignore — org auto-select is best-effort
        }
      }
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: ({
      email,
      password,
      fullName,
    }: {
      email: string;
      password: string;
      fullName: string;
    }) => authService.register(email, password, fullName),
  });
}

export function useVerifyEmail() {
  const queryClient = useQueryClient();
  const { activeOrg, setActiveOrg } = useOrgStore();
  return useMutation({
    mutationFn: ({ email, otp }: { email: string; otp: string }) =>
      authService.verifyEmail(email, otp),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      if (!activeOrg) {
        try {
          const orgs = await orgsService.list();
          if (orgs.length > 0) {
            const first = orgs[0];
            setActiveOrg({ id: first.id, name: first.name, slug: first.slug });
          }
        } catch {
          // ignore
        }
      }
    },
  });
}

export function useResendVerification() {
  return useMutation({
    mutationFn: (email: string) => authService.resendVerification(email),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const setActiveOrg = useOrgStore((s) => s.setActiveOrg);
  return () => {
    authService.logout();
    setActiveOrg(null);
    queryClient.clear();
    router.push("/auth/login");
  };
}
```

- [ ] **Step 3: Create verify-email page**

Create `frontend/src/app/auth/verify-email/page.tsx`:

```tsx
"use client";

import { useRef, useState, useEffect, KeyboardEvent, ClipboardEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, Mail } from "lucide-react";
import { useVerifyEmail, useResendVerification } from "@/queries/auth";
import { getApiError } from "@/lib/apiError";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") ?? "";

  const [digits, setDigits] = useState<string[]>(["", "", "", "", "", ""]);
  const [error, setError] = useState("");
  const [resendCooldown, setResendCooldown] = useState(0);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const verify = useVerifyEmail();
  const resend = useResendVerification();

  // Start a 60s cooldown on mount (OTP just sent during register)
  useEffect(() => {
    setResendCooldown(60);
  }, []);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const t = setTimeout(() => setResendCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCooldown]);

  const otp = digits.join("");

  function handleDigitChange(index: number, value: string) {
    if (!/^\d?$/.test(value)) return;
    const next = [...digits];
    next[index] = value;
    setDigits(next);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  }

  function handleKeyDown(index: number, e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  }

  function handlePaste(e: ClipboardEvent<HTMLInputElement>) {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    const next = [...digits];
    for (let i = 0; i < pasted.length; i++) next[i] = pasted[i];
    setDigits(next);
    const focusIndex = Math.min(pasted.length, 5);
    inputRefs.current[focusIndex]?.focus();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (otp.length < 6) return;
    setError("");
    try {
      await verify.mutateAsync({ email, otp });
      router.push("/dashboard");
    } catch (err) {
      setError(getApiError(err, "Invalid or expired code. Please try again."));
      setDigits(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    }
  }

  async function handleResend() {
    if (resendCooldown > 0 || !email) return;
    try {
      await resend.mutateAsync(email);
      setResendCooldown(60);
      setError("");
    } catch (err) {
      setError(getApiError(err, "Failed to resend code. Please try again."));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
            <LayoutDashboard className="h-5 w-5 text-primary-foreground" />
          </div>
        </div>

        {/* Icon + heading */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <Mail className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">Check your email</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            We sent a 6-digit code to{" "}
            <span className="font-medium text-foreground">{email || "your email"}</span>
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 6-digit input */}
          <div className="flex justify-center gap-3">
            {digits.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { inputRefs.current[i] = el; }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleDigitChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                onPaste={handlePaste}
                className="h-14 w-12 rounded-xl border border-input bg-background text-center text-xl font-semibold focus:border-primary focus:outline-none focus:ring-2 focus:ring-ring"
              />
            ))}
          </div>

          <button
            type="submit"
            disabled={otp.length < 6 || verify.isPending}
            className="flex h-10 w-full items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {verify.isPending ? "Verifying…" : "Verify email"}
          </button>
        </form>

        {/* Resend */}
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Didn&apos;t receive a code?{" "}
          {resendCooldown > 0 ? (
            <span className="text-muted-foreground">
              Resend in {resendCooldown}s
            </span>
          ) : (
            <button
              onClick={handleResend}
              disabled={resend.isPending}
              className="font-medium text-primary hover:underline disabled:opacity-50"
            >
              {resend.isPending ? "Sending…" : "Resend code"}
            </button>
          )}
        </p>

        <p className="mt-3 text-center text-sm text-muted-foreground">
          <Link href="/auth/login" className="font-medium text-primary hover:underline">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/services/auth.ts frontend/src/queries/auth.ts \
        frontend/src/app/auth/verify-email/page.tsx
git commit -m "feat: add verify-email page with 6-digit OTP input and resend cooldown"
```

---

## Task 6: Wire signup and login pages to verification flow

**Files:**
- Modify: `frontend/src/app/auth/signup/page.tsx`
- Modify: `frontend/src/app/auth/login/page.tsx`

- [ ] **Step 1: Update signup to redirect to verify page**

Replace `frontend/src/app/auth/signup/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, ArrowRight } from "lucide-react";
import { useRegister } from "@/queries/auth";

export default function SignupPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const register = useRegister();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await register.mutateAsync({ email, password, fullName });
      // Do NOT auto-login. Redirect to email verification.
      router.push(`/auth/verify-email?email=${encodeURIComponent(email)}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Registration failed";
      setError(typeof msg === "string" ? msg : "Registration failed");
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-primary p-10 lg:flex">
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-violet-600 opacity-90" />
        <div className="relative z-10 flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/20 backdrop-blur">
            <LayoutDashboard className="h-4.5 w-4.5 text-white" />
          </div>
          <span className="text-lg font-semibold text-white">Boilerplate</span>
        </div>
        <div className="relative z-10 space-y-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/20 text-xs text-white">✓</div>
            <p className="text-white/80 text-sm">Teams, roles &amp; permissions built-in</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/20 text-xs text-white">✓</div>
            <p className="text-white/80 text-sm">File uploads, audit logs &amp; feature flags</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/20 text-xs text-white">✓</div>
            <p className="text-white/80 text-sm">Background jobs &amp; metrics out of the box</p>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 lg:px-16">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <LayoutDashboard className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">Boilerplate</span>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold">Create your account</h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Get started in seconds
            </p>
          </div>

          {error && (
            <div className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Full name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Jane Smith"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Email address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="you@example.com"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Min. 8 characters"
              />
            </div>

            <button
              type="submit"
              disabled={register.isPending}
              className="flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {register.isPending ? "Creating account…" : (
                <>Create account <ArrowRight className="h-4 w-4" /></>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/auth/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Update login page to handle unverified redirect**

Replace `frontend/src/app/auth/login/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { LayoutDashboard, ArrowRight } from "lucide-react";
import { useLogin } from "@/queries/auth";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const login = useLogin();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await login.mutateAsync({ email, password });
      router.push(redirect);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (status === 403 && detail === "Email not verified") {
        router.push(`/auth/verify-email?email=${encodeURIComponent(email)}`);
        return;
      }
      setError("Invalid email or password");
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-primary p-10 lg:flex">
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-violet-600 opacity-90" />
        <div className="relative z-10 flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/20 backdrop-blur">
            <LayoutDashboard className="h-4.5 w-4.5 text-white" />
          </div>
          <span className="text-lg font-semibold text-white">Boilerplate</span>
        </div>
        <div className="relative z-10">
          <blockquote className="space-y-2">
            <p className="text-xl font-medium leading-relaxed text-white/90">
              &ldquo;The scaffolding that lets you ship your idea, not someone else&apos;s infrastructure.&rdquo;
            </p>
          </blockquote>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12 lg:px-16">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <LayoutDashboard className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-sm font-semibold">Boilerplate</span>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold">Welcome back</h1>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          {error && (
            <div className="mb-5 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Email address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="you@example.com"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="flex h-10 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={login.isPending}
              className="flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-primary text-sm font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {login.isPending ? "Signing in…" : (
                <>Sign in <ArrowRight className="h-4 w-4" /></>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{" "}
            <Link href="/auth/signup" className="font-medium text-primary hover:underline">
              Sign up free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Check TypeScript**

```bash
cd frontend && npx tsc --noEmit 2>&1
```

Expected: no errors.

- [ ] **Step 4: Run full backend test suite one more time**

```bash
docker compose exec backend pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/auth/signup/page.tsx \
        frontend/src/app/auth/login/page.tsx
git commit -m "feat: redirect signup to verify-email page, handle unverified 403 on login"
```

---

## Self-Review

**Spec coverage:**
- ✅ Email verification required before login — Task 4 (login blocks unverified with 403)
- ✅ 6-digit OTP sent on register — Task 4 (register sends OTP via email_service)
- ✅ OTP expires in 10 minutes — Task 2 (OTP_EXPIRE_SECONDS = 600)
- ✅ OTP can only be used once — Task 2 (used_at checked in verify_otp)
- ✅ Verify endpoint issues JWT (auto-login) — Task 4
- ✅ Resend endpoint with 60s rate limit — Task 4 (has_recent_otp guard)
- ✅ Signup redirects to verify page — Task 6
- ✅ Login detects unverified 403, redirects to verify page — Task 6
- ✅ Verify page: 6-digit input boxes, paste support, auto-advance, resend cooldown — Task 5
- ✅ Seed users marked as verified (won't be blocked in dev) — Task 1

**Placeholder scan:** Clean — no TBD, no "handle edge cases", all code blocks complete.

**Type consistency:**
- `verifyEmail(email, otp)` in service → `useVerifyEmail({ email, otp })` in hook ✅
- `UserResponse.is_verified` (backend) → `UserData.is_verified` (frontend) ✅
- `verification_service.create_otp(session, user_id=...)` consistent across Task 2 and Task 4 ✅
