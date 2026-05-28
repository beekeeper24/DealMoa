// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthStatus } from "../AuthStatus";
import { getStoredAuthSession, saveAuthSession } from "../session";

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("AuthStatus", () => {
  it("renders oauth provider login buttons", () => {
    render(<AuthStatus />);

    expect(screen.getByRole("button", { name: "Google 로그인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kakao 로그인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Naver 로그인" })).toBeInTheDocument();
  });

  it("requests an authorization url and navigates on provider click", async () => {
    const user = userEvent.setup();
    const navigate = vi.fn();
    vi.spyOn(crypto, "randomUUID").mockReturnValue("state-1");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ authorizationUrl: "https://accounts.example/oauth" }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthStatus navigate={navigate} origin="http://localhost:3000" />);

    await user.click(screen.getByRole("button", { name: "Google 로그인" }));

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("https://accounts.example/oauth"));
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/oauth/google/authorize-url?redirectUri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback%2Fgoogle&state=state-1",
      { headers: { Accept: "application/json" } }
    );
  });

  it("shows stored session and clears it on logout", async () => {
    const user = userEvent.setup();
    saveAuthSession({
      user: {
        id: "user-1",
        email: "user@example.com",
        nickname: "Deal User",
        role: "USER"
      },
      accessToken: "access-token",
      tokenType: "Bearer"
    });
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthStatus />);

    expect(screen.getByText("user@example.com")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "로그아웃" }));

    await waitFor(() => expect(getStoredAuthSession()).toBeNull());
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/auth/logout", {
      credentials: "include",
      headers: { Accept: "application/json" },
      method: "POST"
    });
    expect(screen.getByRole("button", { name: "Google 로그인" })).toBeInTheDocument();
  });
});
