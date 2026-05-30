// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthStatus } from "../AuthStatus";
import { AuthSessionProvider } from "../useAuthSession";

const authSessionResponse = {
  user: {
    id: "user-1",
    email: "user@example.com",
    nickname: "Deal User",
    role: "USER"
  },
  accessToken: "access-token",
  tokenType: "Bearer"
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function authErrorResponse(code = "INVALID_REFRESH_TOKEN"): Response {
  return jsonResponse(
    {
      error: {
        code,
        message: "로그인이 필요합니다.",
        details: {},
        traceId: "req_1"
      }
    },
    401
  );
}

function renderWithAuthProvider(ui: React.ReactElement) {
  return render(<AuthSessionProvider>{ui}</AuthSessionProvider>);
}

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("AuthStatus", () => {
  it("server-renders a neutral session-checking state", () => {
    const markup = renderToString(
      <AuthSessionProvider>
        <AuthStatus />
      </AuthSessionProvider>
    );

    expect(markup).toContain("인증 상태 확인 중");
    expect(markup).not.toContain("Google 로그인");
  });

  it("renders oauth provider login buttons when refresh cookie is missing", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(authErrorResponse()));

    renderWithAuthProvider(<AuthStatus />);

    expect(await screen.findByRole("button", { name: "Google 로그인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kakao 로그인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Naver 로그인" })).toBeInTheDocument();
  });

  it("requests an authorization url and navigates on provider click", async () => {
    const user = userEvent.setup();
    const navigate = vi.fn();
    vi.spyOn(crypto, "randomUUID").mockReturnValue("state-1");
    const fetchMock = vi.fn().mockImplementation((input: RequestInfo | URL) => {
      const url = input.toString();
      if (url.includes("/auth/token/refresh")) {
        return Promise.resolve(authErrorResponse());
      }
      return Promise.resolve(jsonResponse({ authorizationUrl: "https://accounts.example/oauth" }));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithAuthProvider(<AuthStatus navigate={navigate} origin="http://localhost:3000" />);

    await user.click(await screen.findByRole("button", { name: "Google 로그인" }));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("https://accounts.example/oauth"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/oauth/google/authorize-url?redirectUri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback%2Fgoogle&state=state-1",
      { headers: { Accept: "application/json" } }
    );
  });

  it("recovers the session from the HttpOnly refresh cookie and clears it on logout", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem(
      "dealmoa.authSession",
      JSON.stringify({ accessToken: "legacy-access-token" })
    );
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(authSessionResponse))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    renderWithAuthProvider(<AuthStatus />);

    expect(await screen.findByText("user@example.com")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/v1/auth/token/refresh", {
      credentials: "include",
      headers: { Accept: "application/json" },
      method: "POST"
    });

    await user.click(screen.getByRole("button", { name: "로그아웃" }));

    await waitFor(() => expect(sessionStorage.getItem("dealmoa.authSession")).toBeNull());
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/auth/logout", {
      credentials: "include",
      headers: { Accept: "application/json" },
      method: "POST"
    });
    expect(screen.getByRole("button", { name: "Google 로그인" })).toBeInTheDocument();
  });
});
