// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { AdminDiscussionModerationPage } from "../AdminDiscussionModerationPage";

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

function discussionFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "discussion-1",
    productId: "product-1",
    userId: "user-1",
    userNickname: "Deal User",
    body: "이 가격이면 괜찮아 보입니다.",
    status: "visible",
    moderatedByUserId: null,
    moderationNote: null,
    moderatedAt: null,
    createdAt: "2026-06-01T00:00:00Z",
    updatedAt: "2026-06-01T00:00:00Z",
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
      <AdminDiscussionModerationPage />
    </AuthSessionProvider>
  );
}

describe("AdminDiscussionModerationPage", () => {
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

  it("loads visible discussions for admins and hides one", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/discussions?status=visible&limit=20") {
        return jsonResponse({ items: [discussionFixture()], nextCursor: null });
      }
      if (url === "/api/v1/admin/discussions/discussion-1" && init?.method === "PATCH") {
        return jsonResponse(
          discussionFixture({
            status: "hidden",
            moderatedByUserId: "admin-1",
            moderationNote: "욕설 포함",
            moderatedAt: "2026-06-01T00:01:00Z"
          })
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const card = await screen.findByRole("article", { name: "Deal User 댓글" });
    expect(within(card).getByText("product-1")).toBeInTheDocument();
    expect(within(card).getByText("이 가격이면 괜찮아 보입니다.")).toBeInTheDocument();

    await user.type(within(card).getByLabelText("모더레이션 메모"), "욕설 포함");
    await user.click(within(card).getByRole("button", { name: "숨김 처리" }));

    expect(await screen.findByText("표시할 댓글이 없습니다.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/admin/discussions/discussion-1", {
      body: JSON.stringify({ action: "hide", moderationNote: "욕설 포함" }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("switches to hidden discussions, restores one, and paginates", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/discussions?status=visible&limit=20") {
        return jsonResponse({ items: [], nextCursor: null });
      }
      if (url === "/api/v1/admin/discussions?status=hidden&limit=20") {
        return jsonResponse({
          items: [
            discussionFixture({
              id: "discussion-2",
              body: "복구 가능한 댓글입니다.",
              status: "hidden",
              moderationNote: "임시 숨김"
            })
          ],
          nextCursor: "discussion-3"
        });
      }
      if (url === "/api/v1/admin/discussions?status=hidden&limit=20&cursor=discussion-3") {
        return jsonResponse({
          items: [
            discussionFixture({
              id: "discussion-3",
              body: "두 번째 숨김 댓글입니다.",
              status: "hidden"
            })
          ],
          nextCursor: null
        });
      }
      if (url === "/api/v1/admin/discussions/discussion-2" && init?.method === "PATCH") {
        return jsonResponse(
          discussionFixture({
            id: "discussion-2",
            body: "복구 가능한 댓글입니다.",
            status: "visible",
            moderationNote: "문제 없음"
          })
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    await screen.findByText("표시할 댓글이 없습니다.");
    await user.click(screen.getByRole("tab", { name: "숨김 댓글" }));

    const card = await screen.findByRole("article", { name: "Deal User 댓글" });
    expect(within(card).getByText("복구 가능한 댓글입니다.")).toBeInTheDocument();
    expect(within(card).getByText("임시 숨김")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "더보기" }));
    expect(await screen.findByText("두 번째 숨김 댓글입니다.")).toBeInTheDocument();

    await user.type(within(card).getByLabelText("모더레이션 메모"), "문제 없음");
    await user.click(within(card).getByRole("button", { name: "복구" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/discussions?status=hidden&limit=20&cursor=discussion-3",
      expect.any(Object)
    );
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/admin/discussions/discussion-2", {
      body: JSON.stringify({ action: "restore", moderationNote: "문제 없음" }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("shows admin api errors", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/discussions?status=visible&limit=20") {
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
