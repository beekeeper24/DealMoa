// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  clearAuthSession,
  createOAuthState,
  verifyAndConsumeOAuthState
} from "../session";

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

  it("clears legacy auth sessions without persisting access tokens", () => {
    sessionStorage.setItem(
      "dealmoa.authSession",
      JSON.stringify({ accessToken: "legacy-access-token" })
    );
    clearAuthSession();

    expect(sessionStorage.getItem("dealmoa.authSession")).toBeNull();
  });
});
