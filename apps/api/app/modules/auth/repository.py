from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import OAuthAccount, RefreshToken, User


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.scalar(statement)

    def create_user(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def get_oauth_account(
        self,
        *,
        provider: str,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        statement = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        return self.session.scalar(statement)

    def create_oauth_account(self, oauth_account: OAuthAccount) -> OAuthAccount:
        self.session.add(oauth_account)
        self.session.flush()
        return oauth_account

    def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.session.add(refresh_token)
        self.session.flush()
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.session.scalar(statement)
