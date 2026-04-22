import secrets
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.core.security import create_access_token, hash_password
from app.models.oauth_account import UserOAuthAccount
from app.models.user import User
from app.schemas.auth import (
    OnboardingRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services import oauth as oauth_service
from app.services.auth import auth_service
from app.services.email import email_service
from app.services.orgs import org_service
from app.services.verification import verification_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = structlog.get_logger()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await auth_service.authenticate(
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
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    existing = await auth_service.get_by_email(session, email=body.email)
    if existing:
        if existing.is_verified:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        # Unverified — overwrite the pending registration so the real
        # owner can always claim their address.
        existing.full_name = body.full_name
        existing.hashed_password = hash_password(body.password)
        session.add(existing)
        user = existing
    else:
        user = await auth_service.create_user(
            session, email=body.email, password=body.password, full_name=body.full_name
        )

    otp_record = await verification_service.create_otp(session, user_id=user.id)
    otp = otp_record.otp  # capture before commit (objects expire after commit)
    await session.commit()
    await session.refresh(user)

    email_service.send(
        to=user.email,
        subject="Verify your email",
        template="verify_email",
        context={"full_name": user.full_name, "otp": otp},
    )
    return UserResponse.model_validate(user)


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    body: VerifyEmailRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    user = await verification_service.verify_otp(
        session, email=body.email, otp=body.otp
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    await session.commit()
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.post("/resend-verification", status_code=200)
async def resend_verification(
    body: ResendVerificationRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await auth_service.get_by_email(session, email=body.email)
    # Always return 200 even if email not found (avoid user enumeration)
    resend_msg = "If that email exists and is unverified, a new code was sent"
    if not user or user.is_verified:
        return {"message": resend_msg}
    if await verification_service.has_recent_otp(session, user_id=user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds before requesting another code",
        )
    otp_record = await verification_service.create_otp(session, user_id=user.id)
    otp = otp_record.otp  # capture before commit
    await session.commit()

    email_service.send(
        to=user.email,
        subject="Verify your email",
        template="verify_email",
        context={"full_name": user.full_name, "otp": otp},
    )
    return {"message": resend_msg}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    body: OnboardingRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Complete user onboarding by setting full name and optionally creating first org."""
    if current_user.onboarding_completed_at:
        raise HTTPException(status_code=400, detail="Onboarding already completed")

    # Update user profile
    current_user.full_name = body.full_name
    current_user.onboarding_completed_at = datetime.now(UTC)

    # Create first organization if provided
    if body.org_name:
        slug = body.org_name.lower().replace(" ", "-")
        # Check if slug exists, if so append random suffix
        existing_org = await org_service.get_by_slug(session, slug=slug)
        if existing_org:
            slug = f"{slug}-{secrets.token_hex(3)}"

        await org_service.create_org(
            session, name=body.org_name, slug=slug, created_by=current_user.id
        )

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.get("/google")
async def google_login(request: Request) -> RedirectResponse:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Google OAuth is not configured")
    state = secrets.token_hex(16)
    redirect_uri = f"{settings.BACKEND_URL}/api/v1/auth/google/callback"
    url = oauth_service.google_auth_url(redirect_uri, state)
    response = RedirectResponse(url)
    response.set_cookie(
        "oauth_state", state, max_age=600, httponly=True, samesite="lax"
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    session: AsyncSession = Depends(get_session),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    _error_redirect = RedirectResponse(
        f"{settings.FRONTEND_URL}/auth/login?error=oauth_failed"
    )
    _error_redirect.delete_cookie("oauth_state")

    if error or not code or not state:
        return _error_redirect

    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        return _error_redirect

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
    existing_oauth = (
        await session.exec(
            select(UserOAuthAccount).where(
                UserOAuthAccount.provider == "google",
                UserOAuthAccount.provider_user_id == google_sub,
            )
        )
    ).first()

    if existing_oauth:
        user = await session.get(User, existing_oauth.user_id)
    else:
        # 2. Existing email → auto-link
        user = await auth_service.get_by_email(session, email=google_email)
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
            await session.commit()
        else:
            # 3. New user
            user = User(
                email=google_email,
                full_name=google_name,
                is_verified=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            oauth_account = UserOAuthAccount(
                user_id=user.id,
                provider="google",
                provider_user_id=google_sub,
                provider_email=google_email,
            )
            session.add(oauth_account)
            await session.commit()

    if not user or not user.is_active:
        return _error_redirect

    token = create_access_token(str(user.id))
    response = RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={token}")
    response.delete_cookie("oauth_state")
    return response
