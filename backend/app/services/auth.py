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
        self, session: Session, *, email: str, password: str, full_name: str
    ) -> User:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
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
