from app.models.oauth_account import UserOAuthAccount
from app.models.api_key import OrgApiKey

async def test_oauth_account_model_has_expected_fields():
    fields = UserOAuthAccount.model_fields
    assert "user_id" in fields
    assert "provider" in fields
    assert "provider_user_id" in fields
    assert "provider_email" in fields


async def test_api_key_model_has_expected_fields():
    fields = OrgApiKey.model_fields
    assert "org_id" in fields
    assert "key_hash" in fields
    assert "key_prefix" in fields
    assert "revoked_at" in fields
