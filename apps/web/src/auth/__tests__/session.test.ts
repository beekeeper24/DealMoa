// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearAuthSession,
  createOAuthState,
  getStoredAuthSession,
  saveAuthSession,
  verifyAndConsumeOAuthState
} from "../session";
import type { AuthSession } from "../types";

const authSession: AuthSession = {
  user: {
    id: "user-1",
    email: "user@example.com",
    nickname: "Deal User",
    role: "USER"
  },
  accessToken: "access-token",
  tokenType: "Bearer"
};

afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
});

describe("auth session storage", () => {
  it("creates provider-scoped oauth state and consumes it once", () => {
    vi.spyOn(crypto, "randomUUID").mockReturnValue("state-1");

    const state = createOAuthState("google");

    expect(state).toBe("state-1");
    expect(verifyAndConsumeOAuthState("google", "wrong-state")).toBe(false);
    expect(verifyAndConsumeOAuthState("google", "state-1")).toBe(true);
    expect(verifyAndConsumeOAuthState("google", "state-1")).toBe(false);
  });

  it("stores and clears the auth session", () => {
    saveAuthSession(authSession);

    expect(getStoredAuthSession()).toEqual(authSession);
    expect(sessionStorage.getItem("dealmoa.authSession")).not.toContain("refresh-token");

    clearAuthSession();

    expect(getStoredAuthSession()).toBeNull();
  });

  it("ignores malformed stored session values", () => {
    sessionStorage.setItem("dealmoa.authSession", JSON.stringify({ accessToken: "missing-user" }));

    expect(getStoredAuthSession()).toBeNull();
  });
});
