import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DetailApiError,
  getAuction,
  getDeal,
  getProduct,
  listProductAuctions,
  listProductDeals,
  placeAuctionBid,
  reportAuction,
  reportDeal
} from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, init: ResponseInit = { status: 200 }): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: { "Content-Type": "application/json" }
  });
}

const productFixture = {
  id: "product-1",
  name: "Galaxy S26 Ultra",
  brand: "Samsung",
  modelName: "SM-S260",
  category: "smartphone",
  specs: { storage: "256GB" },
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

describe("details api", () => {
  it("fetches product detail and product offers", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      if (url === "/api/v1/products/product-1") {
        return Promise.resolve(jsonResponse(productFixture));
      }
      if (url === "/api/v1/products/product-1/deals?limit=10") {
        return Promise.resolve(jsonResponse({ items: [dealFixture], nextCursor: null }));
      }
      if (url === "/api/v1/products/product-1/auctions?limit=10") {
        return Promise.resolve(jsonResponse({ items: [auctionFixture], nextCursor: null }));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getProduct("product-1")).resolves.toMatchObject({ name: "Galaxy S26 Ultra" });
    await expect(listProductDeals("product-1")).resolves.toMatchObject({ items: [dealFixture] });
    await expect(listProductAuctions("product-1")).resolves.toMatchObject({
      items: [auctionFixture]
    });
  });

  it("fetches deal and auction details", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
      if (url === "/api/v1/deals/deal-1") {
        return Promise.resolve(jsonResponse(dealFixture));
      }
      if (url === "/api/v1/auctions/auction-1") {
        return Promise.resolve(jsonResponse(auctionFixture));
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(getDeal("deal-1")).resolves.toMatchObject({ title: "Galaxy S26 launch deal" });
    await expect(getAuction("auction-1")).resolves.toMatchObject({
      title: "Galaxy S26 sealed auction"
    });
  });

  it("places an auction bid with bearer auth", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: "bid-1",
        auctionId: "auction-1",
        userId: "user-1",
        amount: 730000,
        createdAt: "2026-05-31T00:00:00Z"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      placeAuctionBid({ accessToken: "access-1", amount: 730000, auctionId: "auction-1" })
    ).resolves.toMatchObject({ amount: 730000 });
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

  it("submits deal and auction reports with bearer auth", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        jsonResponse({
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
        })
      )
    );
    vi.stubGlobal("fetch", fetchMock);

    await reportDeal({
      accessToken: "access-1",
      dealId: "deal-1",
      description: "가격이 다릅니다.",
      reasonCode: "wrong_price"
    });
    await reportAuction({
      accessToken: "access-1",
      auctionId: "auction-1",
      description: "",
      reasonCode: "fraud"
    });

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/v1/reports/deals/deal-1", {
      body: JSON.stringify({ reasonCode: "wrong_price", description: "가격이 다릅니다." }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/reports/auctions/auction-1", {
      body: JSON.stringify({ reasonCode: "fraud" }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
  });

  it("throws detail api errors with stable code and message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              code: "AUCTION_NOT_FOUND",
              message: "경매를 찾을 수 없습니다.",
              details: { auctionId: "missing" },
              traceId: "req-1"
            }
          },
          { status: 404 }
        )
      )
    );

    const promise = getAuction("missing");

    await expect(promise).rejects.toBeInstanceOf(DetailApiError);
    await expect(promise).rejects.toMatchObject({
      code: "AUCTION_NOT_FOUND",
      message: "경매를 찾을 수 없습니다."
    });
  });
});
