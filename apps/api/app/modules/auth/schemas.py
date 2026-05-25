from pydantic import BaseModel, Field


class AuthorizationUrlResponse(BaseModel):
    authorization_url: str = Field(alias="authorizationUrl")


class OAuthCallbackRequest(BaseModel):
    code: str = Field(min_length=1)
    redirect_uri: str = Field(alias="redirectUri", min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(alias="refreshToken", min_length=1)


class UserResponse(BaseModel):
    id: str
    email: str
    nickname: str | None
    role: str


class AuthSessionResponse(BaseModel):
    user: UserResponse
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = Field(alias="tokenType")
