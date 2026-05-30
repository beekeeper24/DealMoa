import type { OAuthProvider } from "./types";

const legacyAuthSessionKey = "dealmoa.authSession";

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

export function clearAuthSession(): void {
  sessionStorage.removeItem(legacyAuthSessionKey);
}
