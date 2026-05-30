// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthCallbackPage } from "../AuthCallbackPage";
import { createOAuthState } from "../session";

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("AuthCallbackPage", () => {
  it("shows an error when code or state is missing", async () => {
    render(
      <AuthCallbackPage
        navigate={vi.fn()}
        origin="http://localhost:3000"
        provider="google"
        searchParams={new URLSearchParams("code=code-1")}
      />
    );

    expect(await screen.findByText("OAuth 응답 정보가 부족합니다.")).toBeInTheDocument();
  });

  it("rejects mismatched oauth state before calling the api", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthCallbackPage
        navigate={vi.fn()}
        origin="http://localhost:3000"
        provider="google"
        searchParams={new URLSearchParams("code=code-1&state=wrong-state")}
      />
    );

    expect(await screen.findByText("로그인 상태 검증에 실패했습니다.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("exchanges code, stores session, and navigates home", async () => {
    const navigate = vi.fn();
    vi.spyOn(crypto, "randomUUID").mockReturnValue("state-1");
    createOAuthState("google");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            user: {
              id: "user-1",
              email: "user@example.com",
              nickname: "Deal User",
              role: "USER"
            },
            accessToken: "access-token",
            tokenType: "Bearer"
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    render(
      <AuthCallbackPage
        navigate={navigate}
        origin="http://localhost:3000"
        provider="google"
        searchParams={new URLSearchParams("code=code-1&state=state-1")}
      />
    );

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/"));
    expect(sessionStorage.getItem("dealmoa.authSession")).toBeNull();
  });
});
