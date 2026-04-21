import secrets
import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models.user import User
from app.models.verification import EmailVerification
from app.services.base import CRUDBase

OTP_EXPIRE_SECONDS = 600   # 10 minutes
RESEND_COOLDOWN_SECONDS = 60


def _generate_otp() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


class VerificationService(CRUDBase[EmailVerification]):
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


verification_service = VerificationService(EmailVerification)
