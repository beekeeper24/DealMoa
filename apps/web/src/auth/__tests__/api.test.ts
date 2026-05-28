import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AuthApiError,
  buildOAuthAuthorizationUrl,
  getCurrentUser,
  loginWithOAuthCallback,
  logout,
  refreshAuthSession
} from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

const authSessionResponse = {
  user: {
    id: "user-1",
    email: "user@example.com",
    nickname: "Deal User",
    role: "USER"
  },
  accessToken: "access-token",
  refreshToken: "refresh-token",
  tokenType: "Bearer"
};

describe("auth api client", () => {
  it("requests provider authorization url", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        authorizationUrl: "https://accounts.example/oauth"
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://api.test/api/v1");

    const authorizationUrl = await buildOAuthAuthorizationUrl({
      provider: "google",
      redirectUri: "http://localhost:3000/auth/callback/google",
      state: "state-1"
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/auth/oauth/google/authorize-url?redirectUri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback%2Fgoogle&state=state-1",
      { headers: { Accept: "application/json" } }
    );
    expect(authorizationUrl).toBe("https://accounts.example/oauth");
  });

  it("exchanges oauth callback code for an auth session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(authSessionResponse));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "/api/v1");

    const session = await loginWithOAuthCallback({
      provider: "kakao",
      code: "code-1",
      redirectUri: "http://localhost:3000/auth/callback/kakao"
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/auth/oauth/kakao/callback", {
      body: JSON.stringify({
        code: "code-1",
        redirectUri: "http://localhost:3000/auth/callback/kakao"
      }),
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      method: "POST"
    });
    expect(session.user.email).toBe("user@example.com");
  });

  it("uses bearer token for current user requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(authSessionResponse.user));
    vi.stubGlobal("fetch", fetchMock);

    const user = await getCurrentUser("access-token");

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/auth/me", {
      headers: { Accept: "application/json", Authorization: "Bearer access-token" }
    });
    expect(user.email).toBe("user@example.com");
  });

  it("refreshes and logs out with refresh token payloads", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(authSessionResponse))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await refreshAuthSession("refresh-token");
    await logout("refresh-token");

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/v1/auth/token/refresh", {
      body: JSON.stringify({ refreshToken: "refresh-token" }),
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      method: "POST"
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/auth/logout", {
      body: JSON.stringify({ refreshToken: "refresh-token" }),
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      method: "POST"
    });
  });

  it("throws typed errors for common api error responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              code: "UNAUTHORIZED",
              message: "로그인이 필요합니다.",
              details: {},
              traceId: "req_1"
            }
          },
          401
        )
      )
    );

    await expect(getCurrentUser("bad-token")).rejects.toMatchObject({
      name: "AuthApiError",
      code: "UNAUTHORIZED",
      message: "로그인이 필요합니다."
    } satisfies Partial<AuthApiError>);
  });
});
