from dataclasses import dataclass

from app.core.exceptions import InvalidRefreshTokenException, UnauthorizedException
from app.main import create_app
from app.modules.auth.router import get_auth_use_cases
from app.modules.auth.use_cases import AuthenticatedUser, AuthSession
from fastapi.testclient import TestClient


@dataclass
class FakeAuthUseCases:
    refreshed_token: str | None = None
    revoked_token: str | None = None

    def build_authorization_url(
        self,
        *,
        provider: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        return f"https://auth.example/{provider}?redirect_uri={redirect_uri}&state={state}"

    def login_with_oauth_callback(
        self,
        *,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> AuthSession:
        return AuthSession(
            user=AuthenticatedUser(
                id="user-1",
                email="user@example.com",
                nickname="Deal User",
                role="USER",
            ),
            access_token=f"access-{provider}-{code}",
            refresh_token="refresh-1",
        )

    def refresh_session(self, refresh_token: str) -> AuthSession:
        if refresh_token == "bad-refresh":
            raise InvalidRefreshTokenException()
        self.refreshed_token = refresh_token
        return AuthSession(
            user=AuthenticatedUser(
                id="user-1",
                email="user@example.com",
                nickname="Deal User",
                role="USER",
            ),
            access_token="access-2",
            refresh_token="refresh-2",
        )

    def revoke_refresh_token(self, refresh_token: str) -> None:
        self.revoked_token = refresh_token

    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        if access_token != "access-1":
            raise UnauthorizedException()
        return AuthenticatedUser(
            id="user-1",
            email="user@example.com",
            nickname="Deal User",
            role="USER",
        )


def make_client(use_cases: FakeAuthUseCases) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_auth_use_cases] = lambda: use_cases
    return TestClient(app)


def test_build_oauth_authorization_url() -> None:
    client = make_client(FakeAuthUseCases())

    response = client.get(
        "/api/v1/auth/oauth/google/authorize-url",
        params={"redirectUri": "http://localhost/callback", "state": "state-1"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "authorizationUrl": "https://auth.example/google?redirect_uri=http://localhost/callback&state=state-1"
    }


def test_oauth_callback_returns_tokens_and_user() -> None:
    client = make_client(FakeAuthUseCases())

    response = client.post(
        "/api/v1/auth/oauth/google/callback",
        json={"code": "code-1", "redirectUri": "http://localhost/callback"},
    )

    assert response.status_code == 200
    assert response.json()["accessToken"] == "access-google-code-1"
    assert response.json()["refreshToken"] == "refresh-1"
    assert response.json()["tokenType"] == "Bearer"
    assert response.json()["user"]["email"] == "user@example.com"


def test_refresh_rotates_tokens() -> None:
    use_cases = FakeAuthUseCases()
    client = make_client(use_cases)

    response = client.post("/api/v1/auth/token/refresh", json={"refreshToken": "refresh-1"})

    assert response.status_code == 200
    assert response.json()["accessToken"] == "access-2"
    assert response.json()["refreshToken"] == "refresh-2"
    assert use_cases.refreshed_token == "refresh-1"


def test_invalid_refresh_uses_common_error_shape() -> None:
    client = make_client(FakeAuthUseCases())

    response = client.post("/api/v1/auth/token/refresh", json={"refreshToken": "bad-refresh"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


def test_logout_revokes_refresh_token() -> None:
    use_cases = FakeAuthUseCases()
    client = make_client(use_cases)

    response = client.post("/api/v1/auth/logout", json={"refreshToken": "refresh-1"})

    assert response.status_code == 204
    assert response.content == b""
    assert use_cases.revoked_token == "refresh-1"


def test_me_returns_current_user_from_bearer_token() -> None:
    client = make_client(FakeAuthUseCases())

    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer access-1"})

    assert response.status_code == 200
    assert response.json() == {
        "id": "user-1",
        "email": "user@example.com",
        "nickname": "Deal User",
        "role": "USER",
    }


def test_me_without_bearer_token_uses_common_error_shape() -> None:
    client = make_client(FakeAuthUseCases())

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
