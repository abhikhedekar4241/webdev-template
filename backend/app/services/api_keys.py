import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.api_key import OrgApiKey
from app.services.base import CRUDBase

_KEY_PREFIX = "sk_live_"


def _generate_key() -> str:
    return _KEY_PREFIX + secrets.token_hex(33)


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
        session.flush()
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
        if key.revoked_at is not None:
            return True  # already revoked — preserve original timestamp
        key.revoked_at = datetime.now(UTC)
        session.add(key)
        session.flush()
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
        if key.expires_at is not None and key.expires_at < datetime.now(UTC):
            return None
        key.last_used_at = datetime.now(UTC)
        session.add(key)
        session.flush()
        return key


api_key_service = ApiKeyService(OrgApiKey)
