import httpx
import respx

from app.services.oauth import exchange_code, get_google_user_info, google_auth_url


async def test_google_auth_url():
    url = google_auth_url("http://localhost/callback", "state123")
    assert "accounts.google.com" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url
    assert "state=state123" in url


@respx.mock
async def test_exchange_code():
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "abc"})
    )
    result = exchange_code("code123", "http://localhost/callback")
    assert result["access_token"] == "abc"


@respx.mock
async def test_get_google_user_info():
    respx.get("https://www.googleapis.com/oauth2/v3/userinfo").mock(
        return_value=httpx.Response(200, json={"email": "test@gmail.com"})
    )
    result = get_google_user_info("token123")
    assert result["email"] == "test@gmail.com"
