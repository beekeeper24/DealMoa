// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { MyPage } from "../MyPage";

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

function authSession() {
  return {
    user: {
      id: "user-1",
      email: "user@example.com",
      nickname: "Deal User",
      role: "USER"
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
      <MyPage />
    </AuthSessionProvider>
  );
}

describe("MyPage", () => {
  it("shows login guidance for anonymous users without loading submissions", async () => {
    const fetchMock = installFetch((url) => {
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

    expect(await screen.findByText("로그인 후 내 활동을 확인할 수 있습니다.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/me/submissions"),
      expect.anything()
    );
  });

  it("loads contribution history and paginates through my submissions only", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession());
      }
      if (url === "/api/v1/me/submissions?limit=20") {
        expect(init?.headers).toMatchObject({
          Accept: "application/json",
          Authorization: "Bearer access-1"
        });
        return jsonResponse({
          items: [
            submissionFixture({
              status: "approved",
              resolutionNote: "승인",
              resolvedAt: "2026-05-31T14:40:00Z",
              publishedProductId: "product-1",
              publishedOfferType: "deal",
              publishedOfferId: "deal-1"
            })
          ],
          nextCursor: "submission-2"
        });
      }
      if (url === "/api/v1/me/submissions?limit=20&cursor=submission-2") {
        return jsonResponse({
          items: [
            submissionFixture({
              id: "submission-2",
              offerType: "auction",
              title: "Galaxy S26 sealed auction",
              salePrice: null,
              currentPrice: 720000,
              status: "rejected",
              resolutionNote: "중복 제보"
            })
          ],
          nextCursor: null
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    const dealCard = await screen.findByRole("article", {
      name: "Galaxy S26 launch deal 제보 이력"
    });
    expect(within(dealCard).getByText("승인됨")).toBeInTheDocument();
    expect(within(dealCard).getByText("₩1,090,000")).toBeInTheDocument();
    expect(within(dealCard).getByText("승인")).toBeInTheDocument();
    expect(within(dealCard).getByRole("link", { name: "발행 상품" })).toHaveAttribute(
      "href",
      "/products/product-1"
    );
    expect(within(dealCard).getByRole("link", { name: "발행 핫딜" })).toHaveAttribute(
      "href",
      "/deals/deal-1"
    );

    await user.click(screen.getByRole("button", { name: "더보기" }));

    const auctionCard = await screen.findByRole("article", {
      name: "Galaxy S26 sealed auction 제보 이력"
    });
    expect(within(auctionCard).getByText("거절됨")).toBeInTheDocument();
    expect(within(auctionCard).getByText("₩720,000")).toBeInTheDocument();
    expect(within(auctionCard).getByText("중복 제보")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/admin/submissions"),
      expect.anything()
    );
  });
});
