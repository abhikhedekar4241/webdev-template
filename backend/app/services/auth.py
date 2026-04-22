import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services.base import CRUDBase

logger = structlog.get_logger()


class AuthService(CRUDBase[User]):
    async def get_by_email(self, session: AsyncSession, *, email: str) -> User | None:
        return (await session.exec(select(User).where(User.email == email))).first()

    async def create_user(
        self,
        session: AsyncSession,
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
        await session.flush()
        await session.refresh(user)
        logger.info("user_created", email=email, user_id=str(user.id))
        return user

    async def authenticate(
        self, session: AsyncSession, *, email: str, password: str
    ) -> User | None:
        user = await self.get_by_email(session, email=email)
        if not user:
            logger.warning("auth_failed_user_not_found", email=email)
            return None
        if user.hashed_password is None:
            logger.warning("auth_failed_oauth_only", email=email)
            return None  # OAuth-only account — no password login
        if not verify_password(password, user.hashed_password):
            logger.warning("auth_failed_invalid_password", email=email)
            return None
        return user


auth_service = AuthService(User)
