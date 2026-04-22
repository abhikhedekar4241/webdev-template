import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
import yaml
from sqlmodel import Session, select

from app.models.feature_flag import FeatureFlagOverride

logger = structlog.get_logger()

_FLAGS_PATH = Path(__file__).parent.parent.parent / "flags.yml"


class FlagsService:
    def _load_yaml(self) -> dict[str, Any]:
        try:
            with open(_FLAGS_PATH) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("flags_yml_not_found", path=str(_FLAGS_PATH))
            return {"flags": {}}

    def is_enabled(
        self, session: Session, *, org_id: uuid.UUID, flag_name: str
    ) -> bool:
        override = session.exec(
            select(FeatureFlagOverride)
            .where(FeatureFlagOverride.org_id == org_id)
            .where(FeatureFlagOverride.flag_name == flag_name)
        ).first()

        if override is not None:
            return override.enabled

        data = self._load_yaml()
        flags = data.get("flags", {})
        return bool(flags.get(flag_name, False))

    def set_override(
        self,
        session: Session,
        *,
        org_id: uuid.UUID,
        flag_name: str,
        enabled: bool,
    ) -> FeatureFlagOverride:
        existing = session.exec(
            select(FeatureFlagOverride)
            .where(FeatureFlagOverride.org_id == org_id)
            .where(FeatureFlagOverride.flag_name == flag_name)
        ).first()

        if existing:
            existing.enabled = enabled
            existing.updated_at = datetime.now(UTC)
            session.add(existing)
            session.flush()
            return existing

        override = FeatureFlagOverride(
            org_id=org_id, flag_name=flag_name, enabled=enabled
        )
        session.add(override)
        session.flush()
        return override

    def list_defaults(self) -> dict[str, bool]:
        data = self._load_yaml()
        return data.get("flags", {})


flags_service = FlagsService()
