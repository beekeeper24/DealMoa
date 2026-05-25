from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx

from app.core.exceptions import OAuthProviderException, UnsupportedOAuthProviderException

SUPPORTED_OAUTH_PROVIDERS = {"google", "kakao", "naver"}


@dataclass(frozen=True)
class OAuthProviderConfig:
    authorize_url: str
    token_url: str
    profile_url: str
    client_id: str
    client_secret: str
    scope: str


@dataclass(frozen=True)
class OAuthProfile:
    provider: str
    provider_user_id: str
    email: str
    nickname: str | None


class OAuthClient(Protocol):
    def build_authorization_url(
        self,
        *,
        provider: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        pass

    def exchange_code_for_profile(
        self,
        *,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> OAuthProfile:
        pass


class HttpOAuthClient:
    def __init__(self, configs: dict[str, OAuthProviderConfig]) -> None:
        self.configs = configs

    def build_authorization_url(
        self,
        *,
        provider: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        config = self._config(provider)
        query_params = {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        if config.scope:
            query_params["scope"] = config.scope
        query = urlencode(query_params)
        return f"{config.authorize_url}?{query}"

    def exchange_code_for_profile(
        self,
        *,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> OAuthProfile:
        config = self._config(provider)
        try:
            with httpx.Client(timeout=10.0) as client:
                token_payload = {
                    "grant_type": "authorization_code",
                    "client_id": config.client_id,
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
                if config.client_secret:
                    token_payload["client_secret"] = config.client_secret
                token_response = client.post(
                    config.token_url,
                    data=token_payload,
                    headers={"Accept": "application/json"},
                )
                token_response.raise_for_status()
                access_token = token_response.json()["access_token"]
                profile_response = client.get(
                    config.profile_url,
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {access_token}",
                    },
                )
                profile_response.raise_for_status()
                return normalize_oauth_profile(provider, profile_response.json())
        except (KeyError, httpx.HTTPError):
            raise OAuthProviderException(provider) from None

    def _config(self, provider: str) -> OAuthProviderConfig:
        if provider not in SUPPORTED_OAUTH_PROVIDERS or provider not in self.configs:
            raise UnsupportedOAuthProviderException(provider)
        return self.configs[provider]


def normalize_oauth_profile(provider: str, payload: dict[str, Any]) -> OAuthProfile:
    if provider == "google":
        return OAuthProfile(
            provider=provider,
            provider_user_id=str(payload["sub"]),
            email=str(payload["email"]),
            nickname=payload.get("name"),
        )
    if provider == "kakao":
        account = payload.get("kakao_account", {})
        profile = account.get("profile", {})
        return OAuthProfile(
            provider=provider,
            provider_user_id=str(payload["id"]),
            email=str(account["email"]),
            nickname=profile.get("nickname"),
        )
    if provider == "naver":
        response = payload.get("response", {})
        return OAuthProfile(
            provider=provider,
            provider_user_id=str(response["id"]),
            email=str(response["email"]),
            nickname=response.get("nickname"),
        )
    raise UnsupportedOAuthProviderException(provider)
