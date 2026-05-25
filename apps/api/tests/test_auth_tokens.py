from datetime import UTC, datetime, timedelta

import pytest
from app.core.exceptions import TokenExpiredException, UnauthorizedException
from app.modules.auth.tokens import AuthTokenService

SECRET = "test-secret-with-at-least-32-bytes"


def test_access_token_round_trips_subject_and_expiry() -> None:
    now = datetime(2026, 5, 25, tzinfo=UTC)
    service = AuthTokenService(
        secret_key=SECRET,
        access_token_expire_minutes=30,
        refresh_token_expire_days=14,
        now=lambda: now,
    )

    token = service.create_access_token("user-1")

    assert service.verify_access_token(token) == "user-1"


def test_expired_access_token_raises_domain_exception() -> None:
    issued_at = datetime(2026, 5, 25, tzinfo=UTC)
    service = AuthTokenService(
        secret_key=SECRET,
        access_token_expire_minutes=30,
        refresh_token_expire_days=14,
        now=lambda: issued_at,
    )
    token = service.create_access_token("user-1")
    expired_service = AuthTokenService(
        secret_key=SECRET,
        access_token_expire_minutes=30,
        refresh_token_expire_days=14,
        now=lambda: issued_at + timedelta(minutes=31),
    )

    with pytest.raises(TokenExpiredException):
        expired_service.verify_access_token(token)


def test_invalid_access_token_raises_unauthorized() -> None:
    service = AuthTokenService(
        secret_key=SECRET,
        access_token_expire_minutes=30,
        refresh_token_expire_days=14,
    )

    with pytest.raises(UnauthorizedException):
        service.verify_access_token("not-a-token")


def test_refresh_token_hash_does_not_store_raw_token() -> None:
    now = datetime(2026, 5, 25, tzinfo=UTC)
    service = AuthTokenService(
        secret_key=SECRET,
        access_token_expire_minutes=30,
        refresh_token_expire_days=14,
        now=lambda: now,
    )

    refresh_token = service.create_refresh_token()
    token_hash = service.hash_refresh_token(refresh_token)

    assert refresh_token != token_hash
    assert service.hash_refresh_token(refresh_token) == token_hash
    assert service.refresh_token_expires_at() == now + timedelta(days=14)
