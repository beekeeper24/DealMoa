"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";

import { refreshAuthSession } from "./api";
import { clearAuthSession } from "./session";
import type { AuthSession } from "./types";

export type AuthSessionStatus = "loading" | "authenticated" | "anonymous";

export type AuthSessionSnapshot = {
  accessToken?: string;
  session: AuthSession | null;
  status: AuthSessionStatus;
};

export type UseAuthSessionResult = AuthSessionSnapshot & {
  clear: () => void;
  refresh: () => void;
  save: (session: AuthSession) => void;
};

const loadingSnapshot: AuthSessionSnapshot = {
  accessToken: undefined,
  session: null,
  status: "loading"
};

const AuthSessionContext = createContext<UseAuthSessionResult | null>(null);

export function AuthSessionProvider({ children }: { children: React.ReactNode }) {
  const [snapshot, setSnapshot] = useState<AuthSessionSnapshot>(loadingSnapshot);

  const refresh = useCallback(() => {
    setSnapshot((current) => (current.status === "loading" ? current : loadingSnapshot));
    void hydrateFromRefreshCookie(setSnapshot);
  }, []);

  const save = useCallback((session: AuthSession) => {
    setSnapshot({
      accessToken: session.accessToken,
      session,
      status: "authenticated"
    });
  }, []);

  const clear = useCallback(() => {
    clearAuthSession();
    setSnapshot({
      accessToken: undefined,
      session: null,
      status: "anonymous"
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSnapshot(loadingSnapshot);
    void hydrateFromRefreshCookie((nextSnapshot) => {
      if (!cancelled) {
        setSnapshot(nextSnapshot);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  return React.createElement(
    AuthSessionContext.Provider,
    {
      value: {
        ...snapshot,
        clear,
        refresh,
        save
      }
    },
    children
  );
}

export function useAuthSession(): UseAuthSessionResult {
  const authSession = useContext(AuthSessionContext);
  if (!authSession) {
    throw new Error("useAuthSession must be used within AuthSessionProvider");
  }
  return authSession;
}

async function hydrateFromRefreshCookie(
  setSnapshot: (snapshot: AuthSessionSnapshot) => void
): Promise<void> {
  try {
    const session = await refreshAuthSession();
    clearAuthSession();
    setSnapshot({
      accessToken: session.accessToken,
      session,
      status: "authenticated"
    });
  } catch {
    clearAuthSession();
    setSnapshot({
      accessToken: undefined,
      session: null,
      status: "anonymous"
    });
  }
}
