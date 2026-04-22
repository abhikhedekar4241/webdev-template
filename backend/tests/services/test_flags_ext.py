import pytest
from unittest.mock import patch
from app.services.flags import flags_service
import app.services.flags

def test_load_yaml_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        # We need to trigger _load_yaml. It's called by list_defaults
        result = flags_service.list_defaults()
        assert result == {}

def test_unknown_flag_returns_false(session):
    with patch("app.services.flags.flags_service._load_yaml", return_value={"flags": {}}):
        assert flags_service.is_enabled(session, org_id=pytest.importorskip("uuid").uuid4(), flag_name="missing") is False

def test_set_override_updates_existing(session, alice_org):
    flags_service.set_override(session, org_id=alice_org.id, flag_name="f1", enabled=True)
    flags_service.set_override(session, org_id=alice_org.id, flag_name="f1", enabled=False)
    assert flags_service.is_enabled(session, org_id=alice_org.id, flag_name="f1") is False
