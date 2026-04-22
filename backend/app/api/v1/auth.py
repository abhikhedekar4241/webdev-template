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
    existing = auth_service.get_by_email(session, email=body.email)
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
    user = auth_service.get_by_email(session, email=body.email)
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
