from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.exceptions import InvalidRefreshTokenException, UnauthorizedException
from app.modules.auth.models import OAuthAccount, RefreshToken, User
from app.modules.auth.oauth import OAuthClient
from app.modules.auth.repository import AuthRepository
from app.modules.auth.tokens import AuthTokenService


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str
    nickname: str | None
    role: str


@dataclass(frozen=True)
class AuthSession:
    user: AuthenticatedUser
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class AuthUseCases:
    def __init__(
        self,
        *,
        repository: AuthRepository,
        oauth_client: OAuthClient,
        token_service: AuthTokenService,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.oauth_client = oauth_client
        self.token_service = token_service
        self.now = now or (lambda: datetime.now(UTC))

    def build_authorization_url(
        self,
        *,
        provider: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        return self.oauth_client.build_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state,
        )

    def login_with_oauth_callback(
        self,
        *,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> AuthSession:
        profile = self.oauth_client.exchange_code_for_profile(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri,
        )
        oauth_account = self.repository.get_oauth_account(
            provider=profile.provider,
            provider_user_id=profile.provider_user_id,
        )
        if oauth_account is not None:
            user = oauth_account.user
        else:
            existing_user = self.repository.get_user_by_email(profile.email)
            if existing_user is None:
                user = self.repository.create_user(
                    User(
                        email=profile.email,
                        nickname=profile.nickname,
                        role="USER",
                        created_at=self.now(),
                        updated_at=self.now(),
                    )
                )
            else:
                user = existing_user
            self.repository.create_oauth_account(
                OAuthAccount(
                    user_id=user.id,
                    provider=profile.provider,
                    provider_user_id=profile.provider_user_id,
                    email=profile.email,
                    created_at=self.now(),
                    updated_at=self.now(),
                )
            )
        return self._issue_session(user)

    def refresh_session(self, refresh_token: str) -> AuthSession:
        token_hash = self.token_service.hash_refresh_token(refresh_token)
        stored_token = self.repository.get_refresh_token_by_hash(token_hash)
        if (
            stored_token is None
            or stored_token.revoked_at is not None
            or self._aware_utc(stored_token.expires_at) <= self.now()
        ):
            raise InvalidRefreshTokenException()
        user = stored_token.user
        stored_token.revoked_at = self.now()
        stored_token.updated_at = self.now()
        return self._issue_session(user)

    def revoke_refresh_token(self, refresh_token: str) -> None:
        token_hash = self.token_service.hash_refresh_token(refresh_token)
        stored_token = self.repository.get_refresh_token_by_hash(token_hash)
        if stored_token is None or stored_token.revoked_at is not None:
            raise InvalidRefreshTokenException()
        stored_token.revoked_at = self.now()
        stored_token.updated_at = self.now()

    def get_current_user(self, access_token: str) -> AuthenticatedUser:
        user_id = self.token_service.verify_access_token(access_token)
        user = self.repository.get_user(user_id)
        if user is None:
            raise UnauthorizedException()
        return self._user_response(user)

    def _issue_session(self, user: User) -> AuthSession:
        access_token = self.token_service.create_access_token(user.id)
        refresh_token = self.token_service.create_refresh_token()
        self.repository.create_refresh_token(
            RefreshToken(
                user_id=user.id,
                token_hash=self.token_service.hash_refresh_token(refresh_token),
                expires_at=self.token_service.refresh_token_expires_at(),
                revoked_at=None,
                created_at=self.now(),
                updated_at=self.now(),
            )
        )
        return AuthSession(
            user=self._user_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def _user_response(self, user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            role=user.role,
        )

    def _aware_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
