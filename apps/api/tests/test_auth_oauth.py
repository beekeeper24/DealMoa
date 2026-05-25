from urllib.parse import parse_qs, urlparse

import pytest
from app.core.exceptions import UnsupportedOAuthProviderException
from app.modules.auth.oauth import (
    HttpOAuthClient,
    OAuthProviderConfig,
    normalize_oauth_profile,
)


def test_build_authorization_url_includes_required_oauth_params() -> None:
    client = HttpOAuthClient(
        {
            "google": OAuthProviderConfig(
                authorize_url="https://auth.example/authorize",
                token_url="https://auth.example/token",
                profile_url="https://auth.example/profile",
                client_id="client-1",
                client_secret="secret-1",
                scope="openid email profile",
            )
        }
    )

    url = client.build_authorization_url(
        provider="google",
        redirect_uri="http://localhost:3000/callback",
        state="state-1",
    )

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.example"
    assert parsed.path == "/authorize"
    assert parse_qs(parsed.query) == {
        "response_type": ["code"],
        "client_id": ["client-1"],
        "redirect_uri": ["http://localhost:3000/callback"],
        "scope": ["openid email profile"],
        "state": ["state-1"],
    }


def test_build_authorization_url_omits_empty_scope() -> None:
    client = HttpOAuthClient(
        {
            "naver": OAuthProviderConfig(
                authorize_url="https://auth.example/authorize",
                token_url="https://auth.example/token",
                profile_url="https://auth.example/profile",
                client_id="client-1",
                client_secret="secret-1",
                scope="",
            )
        }
    )

    url = client.build_authorization_url(
        provider="naver",
        redirect_uri="http://localhost:3000/callback",
        state="state-1",
    )

    assert "scope" not in parse_qs(urlparse(url).query)


@pytest.mark.parametrize(
    ("provider", "payload", "provider_user_id", "email", "nickname"),
    [
        (
            "google",
            {"sub": "google-user-1", "email": "user@example.com", "name": "Google User"},
            "google-user-1",
            "user@example.com",
            "Google User",
        ),
        (
            "kakao",
            {
                "id": 1234,
                "kakao_account": {
                    "email": "user@example.com",
                    "profile": {"nickname": "Kakao User"},
                },
            },
            "1234",
            "user@example.com",
            "Kakao User",
        ),
        (
            "naver",
            {
                "response": {
                    "id": "naver-user-1",
                    "email": "user@example.com",
                    "nickname": "Naver User",
                }
            },
            "naver-user-1",
            "user@example.com",
            "Naver User",
        ),
    ],
)
def test_normalize_oauth_profile(
    provider: str,
    payload: dict[str, object],
    provider_user_id: str,
    email: str,
    nickname: str,
) -> None:
    profile = normalize_oauth_profile(provider, payload)

    assert profile.provider == provider
    assert profile.provider_user_id == provider_user_id
    assert profile.email == email
    assert profile.nickname == nickname


def test_unknown_provider_raises_domain_exception() -> None:
    with pytest.raises(UnsupportedOAuthProviderException):
        normalize_oauth_profile("github", {})
