// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { AdminSubmissionQueue } from "../AdminSubmissionQueue";

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

function submissionFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "submission-1",
    userId: "user-1",
    offerType: "deal",
    sourceUrl: "https://example.com/deals/galaxy-s26",
    productName: "Galaxy S26",
    brand: "Samsung",
    modelName: "SM-S260",
    category: "smartphone",
    title: "Galaxy S26 launch deal",
    seller: "Example Store",
    originalPrice: 1400000,
    salePrice: 1090000,
    currentPrice: null,
    currency: "KRW",
    description: "Launch discount",
    status: "pending_review",
    aiDecision: "needs_admin_review",
    aiReason: "mock review passed: admin approval required",
    aiReviewedAt: "2026-05-31T14:30:00Z",
    reviewedByUserId: null,
    resolutionNote: null,
    resolvedAt: null,
    publishedProductId: null,
    publishedOfferType: null,
    publishedOfferId: null,
    createdAt: "2026-05-31T14:30:00Z",
    updatedAt: "2026-05-31T14:30:00Z",
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
      <AdminSubmissionQueue />
    </AuthSessionProvider>
  );
}

describe("AdminSubmissionQueue", () => {
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

  it("loads pending submissions for admins and approves one", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession("ADMIN"));
      }
      if (url === "/api/v1/admin/submissions?status=pending_review&limit=20") {
        return jsonResponse({ items: [submissionFixture()], nextCursor: null });
      }
      if (url === "/api/v1/admin/submissions/submission-1" && init?.method === "PATCH") {
        return jsonResponse(
          submissionFixture({
            status: "approved",
            reviewedByUserId: "admin-1",
            resolutionNote: "승인",
            resolvedAt: "2026-05-31T14:40:00Z",
            publishedProductId: "product-1",
            publishedOfferType: "deal",
            publishedOfferId: "deal-1"
          })
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const card = await screen.findByRole("article", { name: "Galaxy S26 launch deal 제보" });
    expect(within(card).getByText(/Example Store/)).toBeInTheDocument();
    expect(
      within(card).getByText("mock review passed: admin approval required")
    ).toBeInTheDocument();

    await user.type(within(card).getByLabelText("처리 메모"), "승인");
    await user.click(within(card).getByRole("button", { name: "제보 처리" }));

    expect(await screen.findByText("표시할 제보가 없습니다.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/admin/submissions/submission-1", {
      body: JSON.stringify({ action: "approve", resolutionNote: "승인" }),
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
      if (url === "/api/v1/admin/submissions?status=pending_review&limit=20") {
        return jsonResponse({ items: [], nextCursor: null });
      }
      if (url === "/api/v1/admin/submissions?status=approved&limit=20") {
        return jsonResponse({
          items: [
            submissionFixture({
              id: "submission-2",
              status: "approved",
              title: "Galaxy S26 launch deal"
            })
          ],
          nextCursor: "submission-3"
        });
      }
      if (url === "/api/v1/admin/submissions?status=approved&limit=20&cursor=submission-3") {
        return jsonResponse({
          items: [
            submissionFixture({
              id: "submission-3",
              offerType: "auction",
              status: "approved",
              title: "Galaxy S26 sealed auction",
              salePrice: null,
              currentPrice: 720000
            })
          ],
          nextCursor: null
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    await screen.findByText("표시할 제보가 없습니다.");
    await user.click(screen.getByRole("tab", { name: "승인" }));

    expect(await screen.findByText("Galaxy S26 launch deal")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "더보기" }));

    expect(await screen.findByText("Galaxy S26 sealed auction")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/submissions?status=approved&limit=20&cursor=submission-3",
      expect.any(Object)
    );
  });
});
