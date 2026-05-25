from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from app.core.exceptions import InvalidRefreshTokenException, UnsupportedOAuthProviderException
from app.db.base import Base
from app.modules.auth.models import OAuthAccount, RefreshToken, User
from app.modules.auth.oauth import OAuthProfile
from app.modules.auth.repository import AuthRepository
from app.modules.auth.tokens import AuthTokenService
from app.modules.auth.use_cases import AuthUseCases
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

SECRET = "test-secret-with-at-least-32-bytes"


class FakeOAuthClient:
    def __init__(self, profile: OAuthProfile) -> None:
        self.profile = profile

    def build_authorization_url(
        self,
        *,
        provider: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        if provider not in {"google", "kakao", "naver"}:
            raise UnsupportedOAuthProviderException(provider)
        return f"https://auth.example/{provider}?redirect_uri={redirect_uri}&state={state}"

    def exchange_code_for_profile(
        self,
        *,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> OAuthProfile:
        if provider not in {"google", "kakao", "naver"}:
            raise UnsupportedOAuthProviderException(provider)
        return self.profile


def make_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def make_use_cases(session: Session, profile: OAuthProfile) -> AuthUseCases:
    now = datetime(2026, 5, 25, tzinfo=UTC)
    return AuthUseCases(
        repository=AuthRepository(session),
        oauth_client=FakeOAuthClient(profile),
        token_service=AuthTokenService(
            secret_key=SECRET,
            access_token_expire_minutes=30,
            refresh_token_expire_days=14,
            now=lambda: now,
        ),
        now=lambda: now,
    )


def test_oauth_callback_creates_user_oauth_account_and_refresh_token() -> None:
    session = next(make_session())
    use_cases = make_use_cases(
        session,
        OAuthProfile(
            provider="google",
            provider_user_id="google-user-1",
            email="user@example.com",
            nickname="Deal User",
        ),
    )

    auth_session = use_cases.login_with_oauth_callback(
        provider="google",
        code="code-1",
        redirect_uri="http://localhost/callback",
    )
    session.commit()

    users = list(session.scalars(select(User)))
    oauth_accounts = list(session.scalars(select(OAuthAccount)))
    refresh_tokens = list(session.scalars(select(RefreshToken)))
    assert len(users) == 1
    assert users[0].email == "user@example.com"
    assert oauth_accounts[0].user_id == users[0].id
    assert refresh_tokens[0].user_id == users[0].id
    assert refresh_tokens[0].token_hash != auth_session.refresh_token
    assert auth_session.user.id == users[0].id
    assert auth_session.token_type == "Bearer"


def test_oauth_callback_reuses_existing_oauth_account() -> None:
    session = next(make_session())
    profile = OAuthProfile(
        provider="google",
        provider_user_id="google-user-1",
        email="user@example.com",
        nickname="Deal User",
    )
    use_cases = make_use_cases(session, profile)

    first = use_cases.login_with_oauth_callback(
        provider="google",
        code="code-1",
        redirect_uri="http://localhost/callback",
    )
    second = use_cases.login_with_oauth_callback(
        provider="google",
        code="code-2",
        redirect_uri="http://localhost/callback",
    )
    session.commit()

    assert second.user.id == first.user.id
    assert len(list(session.scalars(select(User)))) == 1
    assert len(list(session.scalars(select(OAuthAccount)))) == 1
    assert len(list(session.scalars(select(RefreshToken)))) == 2


def test_oauth_callback_links_same_email_to_existing_user() -> None:
    session = next(make_session())
    first = make_use_cases(
        session,
        OAuthProfile(
            provider="google",
            provider_user_id="google-user-1",
            email="user@example.com",
            nickname="Deal User",
        ),
    ).login_with_oauth_callback(
        provider="google",
        code="code-1",
        redirect_uri="http://localhost/callback",
    )
    second = make_use_cases(
        session,
        OAuthProfile(
            provider="naver",
            provider_user_id="naver-user-1",
            email="user@example.com",
            nickname="Naver User",
        ),
    ).login_with_oauth_callback(
        provider="naver",
        code="code-2",
        redirect_uri="http://localhost/callback",
    )
    session.commit()

    assert second.user.id == first.user.id
    assert len(list(session.scalars(select(User)))) == 1
    assert len(list(session.scalars(select(OAuthAccount)))) == 2


def test_refresh_rotates_token_and_revokes_previous_token() -> None:
    session = next(make_session())
    use_cases = make_use_cases(
        session,
        OAuthProfile(
            provider="google",
            provider_user_id="google-user-1",
            email="user@example.com",
            nickname="Deal User",
        ),
    )
    original = use_cases.login_with_oauth_callback(
        provider="google",
        code="code-1",
        redirect_uri="http://localhost/callback",
    )

    rotated = use_cases.refresh_session(original.refresh_token)
    session.commit()

    refresh_tokens = list(session.scalars(select(RefreshToken).order_by(RefreshToken.created_at)))
    assert rotated.refresh_token != original.refresh_token
    assert refresh_tokens[0].revoked_at is not None
    assert refresh_tokens[1].revoked_at is None


def test_invalid_refresh_token_raises_domain_exception() -> None:
    session = next(make_session())
    use_cases = make_use_cases(
        session,
        OAuthProfile(
            provider="google",
            provider_user_id="google-user-1",
            email="user@example.com",
            nickname="Deal User",
        ),
    )

    with pytest.raises(InvalidRefreshTokenException):
        use_cases.refresh_session("missing-refresh-token")


def test_unsupported_provider_raises_domain_exception() -> None:
    session = next(make_session())
    use_cases = make_use_cases(
        session,
        OAuthProfile(
            provider="google",
            provider_user_id="google-user-1",
            email="user@example.com",
            nickname="Deal User",
        ),
    )

    with pytest.raises(UnsupportedOAuthProviderException):
        use_cases.login_with_oauth_callback(
            provider="github",
            code="code-1",
            redirect_uri="http://localhost/callback",
        )
