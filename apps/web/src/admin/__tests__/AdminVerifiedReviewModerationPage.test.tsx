// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { AdminVerifiedReviewModerationPage } from "../AdminVerifiedReviewModerationPage";

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

function verifiedReviewFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "review-1",
    productId: "product-1",
    userId: "user-1",
    rating: 5,
    title: "실구매 기준 만족",
    body: "배송과 제품 상태 모두 좋았습니다.",
    proofType: "receipt",
    proofReference: "order-123",
    status: "approved",
    aiDecision: null,
    aiReason: null,
    aiReviewedAt: null,
    riskScore: 100,
    riskLevel: "high",
    riskReasons: ["duplicate_proof_reference", "external_contact"],
    reviewedByUserId: null,
    resolutionNote: null,
    resolvedAt: null,
    createdAt: "2026-06-04T00:00:00Z",
    updatedAt: "2026-06-04T00:00:00Z",
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
      <AdminVerifiedReviewModerationPage />
    </AuthSessionProvider>
  );
}

describe("AdminVerifiedReviewModerationPage", () => {
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

  it("loads approved verified reviews for admins and hides one", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/verified-reviews?status=approved&limit=20") {
        return jsonResponse({
          items: [verifiedReviewFixture()],
          nextCursor: null
        });
      }
      if (url === "/api/v1/admin/verified-reviews/review-1" && init?.method === "PATCH") {
        return jsonResponse(
          verifiedReviewFixture({
            status: "hidden",
            reviewedByUserId: "admin-1",
            resolutionNote: "증빙 불일치",
            resolvedAt: "2026-06-04T00:01:00Z"
          })
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const card = await screen.findByRole("article", { name: "실구매 기준 만족 인증 후기" });
    expect(within(card).getByText("product-1")).toBeInTheDocument();
    expect(within(card).getByText("user-1")).toBeInTheDocument();
    expect(within(card).getByText("5점")).toBeInTheDocument();
    expect(within(card).getByText("배송과 제품 상태 모두 좋았습니다.")).toBeInTheDocument();
    expect(within(card).getByText("receipt")).toBeInTheDocument();
    expect(within(card).getByText("order-123")).toBeInTheDocument();
    expect(within(card).getByText("high")).toBeInTheDocument();
    expect(within(card).getByText("duplicate_proof_reference")).toBeInTheDocument();
    expect(within(card).getByText("external_contact")).toBeInTheDocument();

    await user.type(within(card).getByLabelText("처리 메모"), "증빙 불일치");
    await user.click(within(card).getByRole("button", { name: "숨김 처리" }));

    expect(await screen.findByText("표시할 인증 후기가 없습니다.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/admin/verified-reviews/review-1", {
      body: JSON.stringify({ action: "hide", resolutionNote: "증빙 불일치" }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("switches to hidden verified reviews, restores one, and paginates", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/verified-reviews?status=approved&limit=20") {
        return jsonResponse({ items: [], nextCursor: null });
      }
      if (url === "/api/v1/admin/verified-reviews?status=hidden&limit=20") {
        return jsonResponse({
          items: [
            verifiedReviewFixture({
              id: "review-2",
              title: "숨김 처리된 후기",
              body: "복구 검토 대상입니다.",
              status: "hidden",
              resolutionNote: "관리자 임시 숨김"
            })
          ],
          nextCursor: "review-3"
        });
      }
      if (url === "/api/v1/admin/verified-reviews?status=hidden&limit=20&cursor=review-3") {
        return jsonResponse({
          items: [
            verifiedReviewFixture({
              id: "review-3",
              title: "두 번째 숨김 후기",
              body: "페이지네이션으로 불러온 후기입니다.",
              status: "hidden"
            })
          ],
          nextCursor: null
        });
      }
      if (url === "/api/v1/admin/verified-reviews/review-2" && init?.method === "PATCH") {
        return jsonResponse(
          verifiedReviewFixture({
            id: "review-2",
            title: "숨김 처리된 후기",
            body: "복구 검토 대상입니다.",
            status: "approved",
            resolutionNote: "문제 없음"
          })
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    await screen.findByText("표시할 인증 후기가 없습니다.");
    await user.click(screen.getByRole("tab", { name: "숨김 후기" }));

    const card = await screen.findByRole("article", { name: "숨김 처리된 후기 인증 후기" });
    expect(within(card).getByText("복구 검토 대상입니다.")).toBeInTheDocument();
    expect(within(card).getByText("관리자 임시 숨김")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "더보기" }));
    expect(await screen.findByText("페이지네이션으로 불러온 후기입니다.")).toBeInTheDocument();

    await user.type(within(card).getByLabelText("처리 메모"), "문제 없음");
    await user.click(within(card).getByRole("button", { name: "복구" }));

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/verified-reviews?status=hidden&limit=20&cursor=review-3",
      expect.any(Object)
    );
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/admin/verified-reviews/review-2", {
      body: JSON.stringify({ action: "restore", resolutionNote: "문제 없음" }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("does not render consumer report controls", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/verified-reviews?status=approved&limit=20") {
        return jsonResponse({ items: [verifiedReviewFixture()], nextCursor: null });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    await screen.findByRole("article", { name: "실구매 기준 만족 인증 후기" });
    expect(screen.queryByRole("button", { name: /신고/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/소비자 신고/)).not.toBeInTheDocument();
  });
});
