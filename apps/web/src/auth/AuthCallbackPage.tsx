"use client";

import React, { useEffect, useState } from "react";

import { loginWithOAuthCallback } from "./api";
import { saveAuthSession, verifyAndConsumeOAuthState } from "./session";
import type { OAuthProvider } from "./types";

type AuthCallbackPageProps = {
  provider: OAuthProvider;
  searchParams?: URLSearchParams;
  navigate?: (url: string) => void;
  origin?: string;
};

export function AuthCallbackPage({
  provider,
  searchParams,
  navigate = defaultNavigate,
  origin
}: AuthCallbackPageProps) {
  const [status, setStatus] = useState("로그인 처리 중입니다.");

  useEffect(() => {
    let cancelled = false;

    async function completeLogin() {
      const params = searchParams ?? new URLSearchParams(window.location.search);
      const code = params.get("code");
      const state = params.get("state");

      if (!code || !state) {
        setStatus("OAuth 응답 정보가 부족합니다.");
        return;
      }

      if (!verifyAndConsumeOAuthState(provider, state)) {
        setStatus("로그인 상태 검증에 실패했습니다.");
        return;
      }

      try {
        const redirectUri = `${origin ?? window.location.origin}/auth/callback/${provider}`;
        const session = await loginWithOAuthCallback({ provider, code, redirectUri });
        if (cancelled) {
          return;
        }
        saveAuthSession(session);
        setStatus("로그인이 완료되었습니다.");
        navigate("/");
      } catch {
        if (!cancelled) {
          setStatus("로그인 처리에 실패했습니다.");
        }
      }
    }

    void completeLogin();

    return () => {
      cancelled = true;
    };
  }, [navigate, origin, provider, searchParams]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper px-5 text-ink">
      <section className="w-full max-w-md rounded-md border border-black/10 bg-white p-6">
        <p className="text-xs font-semibold text-signal">DealMoa Auth</p>
        <h1 className="mt-2 text-2xl font-bold">로그인 콜백</h1>
        <p className="mt-4 text-sm leading-6 text-black/65">{status}</p>
      </section>
    </main>
  );
}

function defaultNavigate(url: string) {
  window.location.replace(url);
}
