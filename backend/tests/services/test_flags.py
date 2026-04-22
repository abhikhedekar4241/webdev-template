import uuid
from unittest.mock import patch

from app.models.feature_flag import FeatureFlagOverride
from app.services.flags import flags_service

MOCK_FLAGS = {"flags": {"new_dashboard": False, "beta_exports": False}}


async def test_flag_returns_yml_default_when_no_override(session):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = await flags_service.is_enabled(
            session, org_id=uuid.uuid4(), flag_name="new_dashboard"
        )
    assert result is False


async def test_flag_returns_org_override(session):
    org_id = uuid.uuid4()
    override = FeatureFlagOverride(
        org_id=org_id, flag_name="new_dashboard", enabled=True
    )
    session.add(override)
    await session.commit()

    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = await flags_service.is_enabled(
            session, org_id=org_id, flag_name="new_dashboard"
        )
    assert result is True
