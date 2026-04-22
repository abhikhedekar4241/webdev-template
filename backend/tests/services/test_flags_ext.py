from unittest.mock import patch

import pytest

from app.services.flags import flags_service


async def test_load_yaml_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        # We need to trigger _load_yaml. It's called by list_defaults
        result = flags_service.list_defaults()
        assert result == {}


async def test_unknown_flag_returns_false(session):
    with patch(
        "app.services.flags.flags_service._load_yaml", return_value={"flags": {}}
    ):
        assert (
            await flags_service.is_enabled(
                session, org_id=pytest.importorskip("uuid").uuid4(), flag_name="missing"
            )
            is False
        )


async def test_set_override_updates_existing(session, alice_org):
    await flags_service.set_override(
        session, org_id=alice_org.id, flag_name="f1", enabled=True
    )
    await flags_service.set_override(
        session, org_id=alice_org.id, flag_name="f1", enabled=False
    )
    assert (
        await flags_service.is_enabled(session, org_id=alice_org.id, flag_name="f1")
        is False
    )
