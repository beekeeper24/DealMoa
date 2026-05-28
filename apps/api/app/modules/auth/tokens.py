import hashlib
import hmac
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.exceptions import TokenExpiredException, UnauthorizedException


class AuthTokenService:
    def __init__(
        self,
        *,
        secret_key: str,
        access_token_expire_minutes: int,
        refresh_token_expire_days: int,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.now = now or (lambda: datetime.now(UTC))

    def create_access_token(self, user_id: str) -> str:
        issued_at = self.now()
        payload: dict[str, Any] = {
            "sub": user_id,
            "iat": int(issued_at.timestamp()),
            "exp": int(
                (
                    issued_at + timedelta(minutes=self.access_token_expire_minutes)
                ).timestamp()
            ),
            "typ": "access",
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_access_token(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
                options={"require": ["sub", "exp", "typ"], "verify_exp": False},
            )
        except InvalidTokenError:
            raise UnauthorizedException() from None

        subject = payload.get("sub")
        if payload.get("typ") != "access" or not isinstance(subject, str):
            raise UnauthorizedException()
        expires_at = payload.get("exp")
        if not isinstance(expires_at, int):
            raise UnauthorizedException()
        if expires_at <= int(self.now().timestamp()):
            raise TokenExpiredException()
        return subject

    def create_refresh_token(self) -> str:
        return secrets.token_urlsafe(48)

    def hash_refresh_token(self, token: str) -> str:
        digest = hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256:{digest}"

    def refresh_token_expires_at(self) -> datetime:
        return self.now() + timedelta(days=self.refresh_token_expire_days)
