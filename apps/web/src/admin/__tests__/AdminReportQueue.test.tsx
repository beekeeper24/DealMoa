// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { AdminReportQueue } from "../AdminReportQueue";

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

function reportFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "report-1",
    userId: "user-1",
    targetType: "deal",
    targetId: "deal-1",
    reasonCode: "fraud",
    description: "외부 링크가 수상합니다.",
    status: "open",
    reviewedByUserId: null,
    resolutionNote: null,
    resolvedAt: null,
    createdAt: "2026-05-31T00:00:00Z",
    updatedAt: "2026-05-31T00:00:00Z",
    target: {
      targetType: "deal",
      targetId: "deal-1",
      title: "Galaxy S26 launch deal",
      status: "active",
      seller: "Example Store",
      sourceUrl: "https://example.com/deals/galaxy"
    },
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
      <AdminReportQueue />
    </AuthSessionProvider>
  );
}

describe("AdminReportQueue", () => {
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

  it("loads open reports for admins and resolves a report with target status", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/reports?status=open&limit=20") {
        return jsonResponse({ items: [reportFixture()], nextCursor: null });
      }
      if (url === "/api/v1/admin/reports/report-1" && init?.method === "PATCH") {
        return jsonResponse(
          reportFixture({
            status: "resolved",
            resolutionNote: "차단 처리",
            target: {
              targetType: "deal",
              targetId: "deal-1",
              title: "Galaxy S26 launch deal",
              status: "blocked",
              seller: "Example Store",
              sourceUrl: "https://example.com/deals/galaxy"
            }
          })
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const card = await screen.findByRole("article", { name: "Galaxy S26 launch deal 신고" });
    expect(within(card).getByText("Example Store")).toBeInTheDocument();
    expect(within(card).getByText("fraud")).toBeInTheDocument();

    await user.selectOptions(within(card).getByLabelText("처리 결과"), "resolved");
    await user.selectOptions(within(card).getByLabelText("대상 상태"), "blocked");
    await user.type(within(card).getByLabelText("처리 메모"), "차단 처리");
    await user.click(within(card).getByRole("button", { name: "처리 저장" }));

    expect(await screen.findByText("표시할 신고가 없습니다.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/admin/reports/report-1", {
      body: JSON.stringify({
        status: "resolved",
        resolutionNote: "차단 처리",
        targetStatus: "blocked"
      }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("switches status filters and loads the next page", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/reports?status=open&limit=20") {
        return jsonResponse({ items: [], nextCursor: null });
      }
      if (url === "/api/v1/admin/reports?status=resolved&limit=20") {
        return jsonResponse({
          items: [reportFixture({ id: "report-2", status: "resolved" })],
          nextCursor: "report-3"
        });
      }
      if (url === "/api/v1/admin/reports?status=resolved&limit=20&cursor=report-3") {
        return jsonResponse({
          items: [
            reportFixture({
              id: "report-3",
              status: "resolved",
              target: {
                targetType: "auction",
                targetId: "auction-1",
                title: "Galaxy S26 sealed auction",
                status: "closed",
                seller: null,
                sourceUrl: "https://example.com/auctions/galaxy"
              }
            })
          ],
          nextCursor: null
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    await screen.findByText("표시할 신고가 없습니다.");
    await user.click(screen.getByRole("tab", { name: "처리 완료" }));

    expect(await screen.findByText("Galaxy S26 launch deal")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "더보기" }));

    expect(await screen.findByText("Galaxy S26 sealed auction")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/reports?status=resolved&limit=20&cursor=report-3",
      expect.any(Object)
    );
  });

  it("shows admin api errors", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/reports?status=open&limit=20") {
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
