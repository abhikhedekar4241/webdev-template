from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


async def test_password_hash_is_not_plaintext():
    hashed = hash_password("supersecret")
    assert hashed != "supersecret"


async def test_correct_password_verifies():
    hashed = hash_password("supersecret")
    assert verify_password("supersecret", hashed) is True


async def test_wrong_password_fails_verification():
    hashed = hash_password("supersecret")
    assert verify_password("wrongpassword", hashed) is False


async def test_create_and_decode_token():
    token = create_access_token(subject="user-abc-123")
    subject = decode_access_token(token)
    assert subject == "user-abc-123"


async def test_decode_invalid_token_returns_none():
    result = decode_access_token("not.a.valid.token")
    assert result is None


async def test_decode_tampered_token_returns_none():
    token = create_access_token(subject="user-123")
    tampered = token + "tampered"
    result = decode_access_token(tampered)
    assert result is None
