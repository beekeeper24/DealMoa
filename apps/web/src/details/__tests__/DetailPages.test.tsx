// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { AuctionDetailPage } from "../AuctionDetailPage";
import { DealDetailPage } from "../DealDetailPage";
import { ProductDetailPage } from "../ProductDetailPage";

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

function authError() {
  return {
    error: {
      code: "INVALID_REFRESH_TOKEN",
      message: "로그인이 필요합니다.",
      details: {},
      traceId: "req-1"
    }
  };
}

const productFixture = {
  id: "product-1",
  name: "Galaxy S26 Ultra",
  brand: "Samsung",
  modelName: "SM-S260",
  category: "smartphone",
  specs: { storage: "256GB", color: "black" },
  createdAt: "2026-05-25T00:00:00Z",
  updatedAt: "2026-05-25T00:00:00Z"
};

const dealFixture = {
  id: "deal-1",
  productId: "product-1",
  title: "Galaxy S26 launch deal",
  sourceUrl: "https://example.com/deals/galaxy-s26",
  seller: "Example Store",
  originalPrice: 1400000,
  salePrice: 1090000,
  currency: "KRW",
  status: "active",
  startedAt: null,
  endedAt: null,
  createdAt: "2026-05-25T00:00:00Z",
  updatedAt: "2026-05-25T00:00:00Z"
};

const auctionFixture = {
  id: "auction-1",
  productId: "product-1",
  title: "Galaxy S26 sealed auction",
  sourceUrl: "https://example.com/auctions/galaxy-s26",
  seller: "Auction House",
  currentPrice: 720000,
  bidCount: 3,
  currency: "KRW",
  status: "active",
  endsAt: null,
  createdAt: "2026-05-25T00:00:00Z",
  updatedAt: "2026-05-25T00:00:00Z"
};

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

function renderWithAuthProvider(ui: React.ReactElement) {
  return render(<AuthSessionProvider>{ui}</AuthSessionProvider>);
}

describe("detail pages", () => {
  it("loads a product detail page with linked deals and auctions", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authError(), { status: 401 });
      }
      if (url === "/api/v1/products/product-1") {
        return jsonResponse(productFixture);
      }
      if (url === "/api/v1/products/product-1/deals?limit=10") {
        return jsonResponse({ items: [dealFixture], nextCursor: null });
      }
      if (url === "/api/v1/products/product-1/auctions?limit=10") {
        return jsonResponse({ items: [auctionFixture], nextCursor: null });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider(<ProductDetailPage productId="product-1" />);

    expect(await screen.findByRole("heading", { name: "Galaxy S26 Ultra" })).toBeInTheDocument();
    expect(screen.getByText("Samsung · SM-S260 · smartphone")).toBeInTheDocument();
    expect(screen.getByText("storage: 256GB")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Galaxy S26 launch deal" })).toHaveAttribute(
      "href",
      "/deals/deal-1"
    );
    expect(screen.getByRole("link", { name: "Galaxy S26 sealed auction" })).toHaveAttribute(
      "href",
      "/auctions/auction-1"
    );
  });

  it("submits an authenticated deal report", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession());
      }
      if (url === "/api/v1/deals/deal-1") {
        return jsonResponse(dealFixture);
      }
      if (url === "/api/v1/products/product-1") {
        return jsonResponse(productFixture);
      }
      if (url === "/api/v1/reports/deals/deal-1" && init?.method === "POST") {
        return jsonResponse({
          id: "report-1",
          userId: "user-1",
          targetType: "deal",
          targetId: "deal-1",
          reasonCode: "wrong_price",
          description: "가격이 다릅니다.",
          status: "open",
          reviewedByUserId: null,
          resolutionNote: null,
          resolvedAt: null,
          createdAt: "2026-05-31T00:00:00Z",
          updatedAt: "2026-05-31T00:00:00Z"
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider(<DealDetailPage dealId="deal-1" />);

    await screen.findByRole("heading", { name: "Galaxy S26 launch deal" });
    await screen.findByText("user@example.com");
    await user.selectOptions(screen.getByLabelText("신고 사유"), "wrong_price");
    await user.type(screen.getByLabelText("신고 설명"), "가격이 다릅니다.");
    await user.click(screen.getByRole("button", { name: "신고 제출" }));

    expect(await screen.findByText("신고가 접수되었습니다.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/reports/deals/deal-1", {
      body: JSON.stringify({ reasonCode: "wrong_price", description: "가격이 다릅니다." }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
  });

  it("places an authenticated auction bid and refreshes the local current price", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession());
      }
      if (url === "/api/v1/auctions/auction-1") {
        return jsonResponse(auctionFixture);
      }
      if (url === "/api/v1/products/product-1") {
        return jsonResponse(productFixture);
      }
      if (url === "/api/v1/auctions/auction-1/bids" && init?.method === "POST") {
        return jsonResponse({
          id: "bid-1",
          auctionId: "auction-1",
          userId: "user-1",
          amount: 730000,
          createdAt: "2026-05-31T00:00:00Z"
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider(<AuctionDetailPage auctionId="auction-1" />);

    await screen.findByRole("heading", { name: "Galaxy S26 sealed auction" });
    const bidPanel = screen.getByRole("form", { name: "경매 입찰" });
    expect(within(bidPanel).getByText("현재가 ₩720,000")).toBeInTheDocument();

    await user.clear(within(bidPanel).getByLabelText("입찰 금액"));
    await user.type(within(bidPanel).getByLabelText("입찰 금액"), "730000");
    await user.click(within(bidPanel).getByRole("button", { name: "입찰하기" }));

    expect(await within(bidPanel).findByText("입찰이 접수되었습니다.")).toBeInTheDocument();
    expect(within(bidPanel).getByText("현재가 ₩730,000")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/auctions/auction-1/bids", {
      body: JSON.stringify({ amount: 730000 }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
  });
});
