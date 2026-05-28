import type { AuthSession, OAuthProvider } from "./types";

const authSessionKey = "dealmoa.authSession";

function oauthStateKey(provider: OAuthProvider) {
  return `dealmoa.oauthState.${provider}`;
}

export function createOAuthState(provider: OAuthProvider): string {
  const state = crypto.randomUUID();
  sessionStorage.setItem(oauthStateKey(provider), state);
  return state;
}

export function verifyAndConsumeOAuthState(provider: OAuthProvider, state: string): boolean {
  const key = oauthStateKey(provider);
  const storedState = sessionStorage.getItem(key);
  if (storedState !== state) {
    return false;
  }
  sessionStorage.removeItem(key);
  return true;
}

export function saveAuthSession(session: AuthSession): void {
  sessionStorage.setItem(authSessionKey, JSON.stringify(session));
}

export function getStoredAuthSession(): AuthSession | null {
  const value = sessionStorage.getItem(authSessionKey);
  if (!value) {
    return null;
  }

  try {
    const parsed = JSON.parse(value) as unknown;
    if (isAuthSession(parsed)) {
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}

export function clearAuthSession(): void {
  sessionStorage.removeItem(authSessionKey);
}

function isAuthSession(value: unknown): value is AuthSession {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const session = value as AuthSession;
  return (
    typeof session.accessToken === "string" &&
    session.tokenType === "Bearer" &&
    typeof session.user === "object" &&
    session.user !== null &&
    typeof session.user.id === "string" &&
    typeof session.user.email === "string" &&
    typeof session.user.role === "string"
  );
}
