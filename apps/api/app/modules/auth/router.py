from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import InvalidRefreshTokenException, UnauthorizedException
from app.db.session import get_session
from app.modules.auth.oauth import HttpOAuthClient, OAuthProviderConfig
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    AuthorizationUrlResponse,
    AuthSessionResponse,
    OAuthCallbackRequest,
    UserResponse,
)
from app.modules.auth.tokens import AuthTokenService
from app.modules.auth.use_cases import AuthSession, AuthUseCases

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_use_cases(
    session: Annotated[Session, Depends(get_session)],
) -> AuthUseCases:
    settings = get_settings()
    return AuthUseCases(
        repository=AuthRepository(session),
        oauth_client=HttpOAuthClient(
            {
                "google": OAuthProviderConfig(
                    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                    token_url="https://oauth2.googleapis.com/token",
                    profile_url="https://openidconnect.googleapis.com/v1/userinfo",
                    client_id=settings.oauth_google_client_id,
                    client_secret=settings.oauth_google_client_secret,
                    scope="openid email profile",
                ),
                "kakao": OAuthProviderConfig(
                    authorize_url="https://kauth.kakao.com/oauth/authorize",
                    token_url="https://kauth.kakao.com/oauth/token",
                    profile_url="https://kapi.kakao.com/v2/user/me",
                    client_id=settings.oauth_kakao_client_id,
                    client_secret=settings.oauth_kakao_client_secret,
                    scope="account_email profile_nickname",
                ),
                "naver": OAuthProviderConfig(
                    authorize_url="https://nid.naver.com/oauth2.0/authorize",
                    token_url="https://nid.naver.com/oauth2.0/token",
                    profile_url="https://openapi.naver.com/v1/nid/me",
                    client_id=settings.oauth_naver_client_id,
                    client_secret=settings.oauth_naver_client_secret,
                    scope="",
                ),
            }
        ),
        token_service=AuthTokenService(
            secret_key=settings.jwt_secret_key,
            access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
            refresh_token_expire_days=settings.jwt_refresh_token_expire_days,
        ),
    )


@router.get("/oauth/{provider}/authorize-url", response_model=AuthorizationUrlResponse)
def build_oauth_authorization_url(
    provider: str,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
    redirect_uri: Annotated[str, Query(alias="redirectUri", min_length=1)],
    state: Annotated[str, Query(min_length=1)],
) -> AuthorizationUrlResponse:
    authorization_url = use_cases.build_authorization_url(
        provider=provider,
        redirect_uri=redirect_uri,
        state=state,
    )
    return AuthorizationUrlResponse(authorizationUrl=authorization_url)


@router.post("/oauth/{provider}/callback", response_model=AuthSessionResponse)
def login_with_oauth_callback(
    provider: str,
    request: OAuthCallbackRequest,
    response: Response,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthSessionResponse:
    session = use_cases.login_with_oauth_callback(
        provider=provider,
        code=request.code,
        redirect_uri=request.redirect_uri,
    )
    set_refresh_cookie(response, session.refresh_token)
    return auth_session_response(session)


@router.post("/token/refresh", response_model=AuthSessionResponse)
def refresh_token(
    request: Request,
    response: Response,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> AuthSessionResponse:
    settings = get_settings()
    refresh_token_cookie = request.cookies.get(settings.auth_refresh_cookie_name)
    if refresh_token_cookie is None:
        raise InvalidRefreshTokenException()
    session = use_cases.refresh_session(refresh_token_cookie)
    set_refresh_cookie(response, session.refresh_token)
    return auth_session_response(session)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> Response:
    settings = get_settings()
    refresh_token_cookie = request.cookies.get(settings.auth_refresh_cookie_name)
    if refresh_token_cookie is None:
        raise InvalidRefreshTokenException()
    use_cases.revoke_refresh_token(refresh_token_cookie)
    delete_refresh_cookie(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=UserResponse)
def me(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    use_cases: Annotated[AuthUseCases, Depends(get_auth_use_cases)],
) -> UserResponse:
    if credentials is None:
        raise UnauthorizedException()
    return UserResponse(**use_cases.get_current_user(credentials.credentials).__dict__)


def auth_session_response(session: AuthSession) -> AuthSessionResponse:
    return AuthSessionResponse(
        user=UserResponse(**session.user.__dict__),
        accessToken=session.access_token,
        tokenType=session.token_type,
    )


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        max_age=settings.jwt_refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        path=f"{settings.api_v1_prefix}/auth",
    )


def delete_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        httponly=True,
        secure=settings.auth_refresh_cookie_secure,
        samesite=settings.auth_refresh_cookie_samesite,
        path=f"{settings.api_v1_prefix}/auth",
    )
