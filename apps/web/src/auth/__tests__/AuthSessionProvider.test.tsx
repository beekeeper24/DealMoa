// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider, useAuthSession } from "../useAuthSession";

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.unstubAllGlobals();
});

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

function SessionReader({ label }: { label: string }) {
  const authSession = useAuthSession();
  return (
    <div>
      {label}: {authSession.status}
      {authSession.session ? ` ${authSession.session.user.email}` : ""}
    </div>
  );
}

describe("AuthSessionProvider", () => {
  it("shares one refresh-cookie hydration across multiple consumers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(authSessionResponse));
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthSessionProvider>
        <SessionReader label="header" />
        <SessionReader label="sidebar" />
      </AuthSessionProvider>
    );

    expect(await screen.findByText("header: authenticated user@example.com")).toBeInTheDocument();
    expect(screen.getByText("sidebar: authenticated user@example.com")).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/auth/token/refresh", {
      credentials: "include",
      headers: { Accept: "application/json" },
      method: "POST"
    });
  });

  it("throws a clear error when the session hook is used outside the provider", () => {
    expect(() => render(<SessionReader label="orphan" />)).toThrow(
      "useAuthSession must be used within AuthSessionProvider"
    );
  });
});
