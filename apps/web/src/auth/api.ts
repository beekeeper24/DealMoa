import type { AuthErrorResponse, AuthSession, AuthUser, OAuthProvider } from "./types";

export class AuthApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: AuthErrorResponse["error"]) {
    super(response.message);
    this.name = "AuthApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
}

export async function buildOAuthAuthorizationUrl(request: {
  provider: OAuthProvider;
  redirectUri: string;
  state: string;
}): Promise<string> {
  const params = new URLSearchParams({
    redirectUri: request.redirectUri,
    state: request.state
  });
  const response = await fetch(
    `${getApiBaseUrl()}/auth/oauth/${request.provider}/authorize-url?${params.toString()}`,
    { headers: { Accept: "application/json" } }
  );
  const body = await parseJson(response);
  if (!response.ok) {
    throwAuthError(body);
  }
  return (body as { authorizationUrl: string }).authorizationUrl;
}

export async function loginWithOAuthCallback(request: {
  provider: OAuthProvider;
  code: string;
  redirectUri: string;
}): Promise<AuthSession> {
  return postJson<AuthSession>(
    `/auth/oauth/${request.provider}/callback`,
    {
      code: request.code,
      redirectUri: request.redirectUri
    },
    { includeCredentials: true }
  );
}

export async function refreshAuthSession(): Promise<AuthSession> {
  return postWithoutBody<AuthSession>("/auth/token/refresh", { includeCredentials: true });
}

export async function logout(): Promise<void> {
  await postWithoutBody<void>("/auth/logout", { includeCredentials: true });
}

export async function getCurrentUser(accessToken: string): Promise<AuthUser> {
  const response = await fetch(`${getApiBaseUrl()}/auth/me`, {
    headers: { Accept: "application/json", Authorization: `Bearer ${accessToken}` }
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwAuthError(body);
  }
  return body as AuthUser;
}

async function postJson<T>(
  path: string,
  body: object,
  options: { includeCredentials?: boolean } = {}
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    body: JSON.stringify(body),
    credentials: options.includeCredentials ? "include" : undefined,
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    method: "POST"
  });
  const parsed = await parseJson(response);
  if (!response.ok) {
    throwAuthError(parsed);
  }
  return parsed as T;
}

async function postWithoutBody<T>(
  path: string,
  options: { includeCredentials?: boolean } = {}
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    credentials: options.includeCredentials ? "include" : undefined,
    headers: { Accept: "application/json" },
    method: "POST"
  });
  const parsed = await parseJson(response);
  if (!response.ok) {
    throwAuthError(parsed);
  }
  return parsed as T;
}

async function parseJson(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function throwAuthError(value: unknown): never {
  if (isAuthErrorResponse(value)) {
    throw new AuthApiError(value.error);
  }
  throw new Error("인증 요청에 실패했습니다.");
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isAuthErrorResponse(value: unknown): value is AuthErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as AuthErrorResponse).error.code === "string" &&
    typeof (value as AuthErrorResponse).error.message === "string"
  );
}
