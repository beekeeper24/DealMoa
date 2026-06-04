// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { AdminCrawlerRunLogPage } from "../AdminCrawlerRunLogPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, init: ResponseInit = { status: 200 }): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: { "Content-Type": "application/json" }
  });
}

function authSession(role: "ADMIN" | "USER" = "ADMIN") {
  return {
    user: {
      id: role === "ADMIN" ? "admin-1" : "user-1",
      email: role === "ADMIN" ? "admin@example.com" : "user@example.com",
      nickname: role === "ADMIN" ? "Admin" : "User",
      role
    },
    accessToken: "access-1",
    tokenType: "Bearer"
  };
}

function crawlerRunFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "run-1",
    taskName: "crawl_live_urls",
    status: "succeeded",
    scanned: 2,
    fetched: 1,
    accepted: 1,
    created: 1,
    duplicates: 0,
    skipped: 1,
    skipReasons: { host_rate_limited: 1 },
    errorType: null,
    errorMessage: null,
    startedAt: "2026-06-03T01:00:00Z",
    finishedAt: "2026-06-03T01:00:01Z",
    createdAt: "2026-06-03T01:00:01Z",
    ...overrides
  };
}

function installFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>
) {
  const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    return Promise.resolve(handler(url, init));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderWithAuthProvider() {
  return render(
    <AuthSessionProvider>
      <AdminCrawlerRunLogPage />
    </AuthSessionProvider>
  );
}

describe("AdminCrawlerRunLogPage", () => {
  it("shows login guidance for anonymous users", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(
          {
            error: {
              code: "INVALID_REFRESH_TOKEN",
              message: "로그인이 필요합니다.",
              details: {},
              traceId: "req-1"
            }
          },
          { status: 401 }
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    expect(await screen.findByText("관리자 로그인이 필요합니다.")).toBeInTheDocument();
  });

  it("blocks authenticated non-admin users", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("USER"));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    expect(await screen.findByText("관리자 권한이 필요합니다.")).toBeInTheDocument();
  });

  it("loads crawler run logs for admins and paginates", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/crawler-runs?limit=20") {
        return jsonResponse({
          items: [crawlerRunFixture()],
          nextCursor: "run-2"
        });
      }
      if (url === "/api/v1/admin/crawler-runs?limit=20&cursor=run-2") {
        return jsonResponse({
          items: [
            crawlerRunFixture({
              id: "run-2",
              taskName: "crawl_hot_deals_mock",
              scanned: 2,
              fetched: 0,
              accepted: 2,
              created: 0,
              duplicates: 2,
              skipped: 0,
              skipReasons: {}
            })
          ],
          nextCursor: null
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const firstCard = await screen.findByRole("article", { name: "crawl_live_urls 실행 로그" });
    expect(within(firstCard).getByText("scanned 2")).toBeInTheDocument();
    expect(within(firstCard).getByText("fetched 1")).toBeInTheDocument();
    expect(within(firstCard).getByText("host_rate_limited 1")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "더보기" }));

    expect(await screen.findByRole("article", { name: "crawl_hot_deals_mock 실행 로그" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/crawler-runs?limit=20&cursor=run-2",
      expect.any(Object)
    );
  });

  it("shows failed crawler run error fields", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/crawler-runs?limit=20") {
        return jsonResponse({
          items: [
            crawlerRunFixture({
              status: "failed",
              errorType: "RuntimeError",
              errorMessage: "crawler fetch failed with raw html [redacted]"
            })
          ],
          nextCursor: null
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const card = await screen.findByRole("article", { name: "crawl_live_urls 실행 로그" });
    expect(within(card).getByText("failed")).toBeInTheDocument();
    expect(within(card).getByText("RuntimeError")).toBeInTheDocument();
    expect(within(card).getByText("crawler fetch failed with raw html [redacted]")).toBeInTheDocument();
  });

  it("shows admin api errors", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/crawler-runs?limit=20") {
        return jsonResponse(
          {
            error: {
              code: "FORBIDDEN",
              message: "관리자 권한이 필요합니다.",
              details: {},
              traceId: "req-1"
            }
          },
          { status: 403 }
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    expect(await screen.findByText("관리자 권한이 필요합니다.")).toBeInTheDocument();
  });
});
