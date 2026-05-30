"use client";

import React, { useState } from "react";

import { buildOAuthAuthorizationUrl, logout } from "./api";
import { createOAuthState } from "./session";
import type { OAuthProvider } from "./types";
import { useAuthSession } from "./useAuthSession";

type ProviderOption = {
  provider: OAuthProvider;
  label: string;
};

const providers: ProviderOption[] = [
  { provider: "google", label: "Google" },
  { provider: "kakao", label: "Kakao" },
  { provider: "naver", label: "Naver" }
];

type AuthStatusProps = {
  navigate?: (url: string) => void;
  origin?: string;
};

export function AuthStatus({
  navigate = defaultNavigate,
  origin
}: AuthStatusProps) {
  const authSession = useAuthSession();
  const { session, status } = authSession;
  const [loadingProvider, setLoadingProvider] = useState<OAuthProvider | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function startLogin(provider: OAuthProvider) {
    setLoadingProvider(provider);
    setErrorMessage(null);
    try {
      const state = createOAuthState(provider);
      const redirectUri = `${origin ?? window.location.origin}/auth/callback/${provider}`;
      const authorizationUrl = await buildOAuthAuthorizationUrl({
        provider,
        redirectUri,
        state
      });
      navigate(authorizationUrl);
    } catch {
      setErrorMessage("로그인 요청을 시작하지 못했습니다.");
      setLoadingProvider(null);
    }
  }

  async function handleLogout() {
    if (!session) {
      return;
    }
    setIsLoggingOut(true);
    setErrorMessage(null);
    try {
      await logout();
      authSession.clear();
    } catch {
      setErrorMessage("로그아웃에 실패했습니다.");
    } finally {
      setIsLoggingOut(false);
    }
  }

  if (status === "loading") {
    return (
      <div
        aria-label="인증 상태 확인 중"
        className="flex min-h-14 min-w-40 items-center rounded-md border border-black/10 bg-paper px-3 py-2 text-xs font-semibold text-black/50"
      >
        인증 상태 확인 중
      </div>
    );
  }

  if (session) {
    return (
      <div className="flex flex-col gap-2 rounded-md border border-black/10 bg-paper px-3 py-2 text-sm lg:min-w-64">
        <div>
          <div className="text-xs font-semibold text-signal">로그인됨</div>
          <div className="max-w-56 truncate font-semibold" title={session.user.email}>
            {session.user.email}
          </div>
        </div>
        <button
          className="rounded border border-black/15 bg-white px-3 py-1.5 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoggingOut}
          onClick={() => void handleLogout()}
          type="button"
        >
          {isLoggingOut ? "로그아웃 중" : "로그아웃"}
        </button>
        {errorMessage ? <p className="text-xs font-semibold text-deal">{errorMessage}</p> : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2" aria-label="OAuth 로그인">
        {providers.map(({ provider, label }) => (
          <button
            className="rounded border border-black/15 bg-white px-3 py-1.5 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loadingProvider !== null}
            key={provider}
            onClick={() => void startLogin(provider)}
            type="button"
          >
            {loadingProvider === provider ? `${label} 이동 중` : `${label} 로그인`}
          </button>
        ))}
      </div>
      {errorMessage ? <p className="text-xs font-semibold text-deal">{errorMessage}</p> : null}
    </div>
  );
}

function defaultNavigate(url: string) {
  window.location.assign(url);
}
