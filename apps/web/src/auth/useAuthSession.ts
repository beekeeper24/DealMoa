"use client";

import { useCallback, useEffect, useState } from "react";

import {
  clearAuthSession,
  getStoredAuthSession,
  saveAuthSession
} from "./session";
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

export function useAuthSession(): UseAuthSessionResult {
  const [snapshot, setSnapshot] = useState<AuthSessionSnapshot>(loadingSnapshot);

  const refresh = useCallback(() => {
    setSnapshot(readStoredSessionSnapshot());
  }, []);

  const save = useCallback((session: AuthSession) => {
    saveAuthSession(session);
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
    refresh();

    function handleStorage(event: StorageEvent) {
      if (event.key === null || event.key === "dealmoa.authSession") {
        refresh();
      }
    }

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [refresh]);

  return {
    ...snapshot,
    clear,
    refresh,
    save
  };
}

function readStoredSessionSnapshot(): AuthSessionSnapshot {
  const session = getStoredAuthSession();
  if (!session) {
    return {
      accessToken: undefined,
      session: null,
      status: "anonymous"
    };
  }

  return {
    accessToken: session.accessToken,
    session,
    status: "authenticated"
  };
}
