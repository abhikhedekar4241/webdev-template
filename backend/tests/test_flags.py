import uuid
from unittest.mock import patch

import pytest

from app.models.feature_flag import FeatureFlagOverride
from app.models.org import OrgMembership, Organization
from app.models.user import User
from app.services.flags import flags_service


@pytest.fixture(autouse=True)
def create_tables(session):
    User.__table__.create(session.get_bind(), checkfirst=True)
    Organization.__table__.create(session.get_bind(), checkfirst=True)
    OrgMembership.__table__.create(session.get_bind(), checkfirst=True)
    FeatureFlagOverride.__table__.create(session.get_bind(), checkfirst=True)
    yield
    FeatureFlagOverride.__table__.drop(session.get_bind())
    OrgMembership.__table__.drop(session.get_bind())
    Organization.__table__.drop(session.get_bind())
    User.__table__.drop(session.get_bind())


MOCK_FLAGS = {"flags": {"new_dashboard": False, "beta_exports": False}}


def test_flag_returns_yml_default_when_no_override(session):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = flags_service.is_enabled(session, org_id=uuid.uuid4(), flag_name="new_dashboard")
    assert result is False


def test_flag_returns_org_override(session):
    org_id = uuid.uuid4()
    override = FeatureFlagOverride(org_id=org_id, flag_name="new_dashboard", enabled=True)
    session.add(override)
    session.commit()

    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = flags_service.is_enabled(session, org_id=org_id, flag_name="new_dashboard")
    assert result is True


def test_unknown_flag_returns_false(session):
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        result = flags_service.is_enabled(
            session, org_id=uuid.uuid4(), flag_name="nonexistent_flag"
        )
    assert result is False


def test_set_override_creates_new(session):
    org_id = uuid.uuid4()
    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        flags_service.set_override(session, org_id=org_id, flag_name="new_dashboard", enabled=True)
        result = flags_service.is_enabled(session, org_id=org_id, flag_name="new_dashboard")
    assert result is True


def test_set_override_updates_existing(session):
    org_id = uuid.uuid4()
    override = FeatureFlagOverride(org_id=org_id, flag_name="new_dashboard", enabled=True)
    session.add(override)
    session.commit()

    with patch("app.services.flags.flags_service._load_yaml", return_value=MOCK_FLAGS):
        flags_service.set_override(session, org_id=org_id, flag_name="new_dashboard", enabled=False)
        result = flags_service.is_enabled(session, org_id=org_id, flag_name="new_dashboard")
    assert result is False
