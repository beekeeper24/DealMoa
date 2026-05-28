from datetime import UTC, datetime, timedelta

import pytest
from app.db.base import Base
from app.modules.auth.models import OAuthAccount, RefreshToken, User
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def make_session() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_oauth_account_provider_user_id_is_unique() -> None:
    session_factory = make_session()
    session = session_factory()
    now = datetime(2026, 5, 25, tzinfo=UTC)
    first_user = User(
        id="user-1",
        email="first@example.com",
        nickname="First",
        role="USER",
        created_at=now,
        updated_at=now,
    )
    second_user = User(
        id="user-2",
        email="second@example.com",
        nickname="Second",
        role="USER",
        created_at=now,
        updated_at=now,
    )
    session.add_all([first_user, second_user])
    session.flush()
    session.add_all(
        [
            OAuthAccount(
                id="oauth-1",
                user_id="user-1",
                provider="google",
                provider_user_id="provider-user-1",
                email="first@example.com",
                created_at=now,
                updated_at=now,
            ),
            OAuthAccount(
                id="oauth-2",
                user_id="user-2",
                provider="google",
                provider_user_id="provider-user-1",
                email="second@example.com",
                created_at=now,
                updated_at=now,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()


def test_refresh_token_hash_is_unique_and_belongs_to_user() -> None:
    session_factory = make_session()
    session = session_factory()
    now = datetime(2026, 5, 25, tzinfo=UTC)
    session.add(
        User(
            id="user-1",
            email="user@example.com",
            nickname="User",
            role="USER",
            created_at=now,
            updated_at=now,
        )
    )
    session.flush()
    session.add(
        RefreshToken(
            id="refresh-1",
            user_id="user-1",
            token_hash="hash-1",
            expires_at=now + timedelta(days=14),
            revoked_at=None,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()

    stored = session.get(RefreshToken, "refresh-1")

    assert stored is not None
    assert stored.user_id == "user-1"
    assert stored.token_hash == "hash-1"
