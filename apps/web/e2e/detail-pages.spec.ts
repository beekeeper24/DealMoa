import { expect, test } from "@playwright/test";

const product = {
  id: "product-1",
  name: "Galaxy S26 Ultra",
  brand: "Samsung",
  modelName: "SM-S260",
  category: "smartphone",
  specs: { storage: "256GB", color: "black" },
  createdAt: "2026-05-25T00:00:00Z",
  updatedAt: "2026-05-25T00:00:00Z"
};

const auction = {
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

test("opens product detail from product search results", async ({ page }) => {
  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      status: 401,
      body: JSON.stringify({
        error: {
          code: "INVALID_REFRESH_TOKEN",
          message: "로그인이 필요합니다.",
          details: {},
          traceId: "req-1"
        }
      })
    });
  });
  await page.route("**/api/v1/search/products?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: product.id,
            name: product.name,
            brand: product.brand,
            modelName: product.modelName,
            category: product.category,
            specsText: "storage 256GB 색상 블랙",
            createdAt: product.createdAt,
            updatedAt: product.updatedAt,
            score: 2.4
          }
        ],
        nextCursor: null
      })
    });
  });
  await page.route("**/api/v1/products/product-1", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(product) });
  });
  await page.route("**/api/v1/products/product-1/deals?**", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify({ items: [], nextCursor: null }) });
  });
  await page.route("**/api/v1/products/product-1/auctions?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [auction], nextCursor: null })
    });
  });
  await page.route("**/api/v1/products/product-1/price-history?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "price-1",
            productId: "product-1",
            sourceType: "auction",
            sourceId: "auction-1",
            price: 720000,
            currency: "KRW",
            observedAt: "2026-06-01T00:00:00Z",
            createdAt: "2026-06-01T00:00:00Z"
          }
        ],
        nextCursor: null
      })
    });
  });
  await page.route("**/api/v1/products/product-1/verified-reviews?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "review-1",
            productId: "product-1",
            userId: "user-1",
            rating: 5,
            title: "실구매 기준 만족",
            body: "배송과 제품 상태 모두 좋았습니다.",
            proofType: "receipt",
            proofReference: "order-123",
            status: "approved",
            aiDecision: "needs_admin_review",
            aiReason: "mock review passed: receipt proof requires admin approval",
            aiReviewedAt: "2026-06-01T00:00:00Z",
            reviewedByUserId: "admin-1",
            resolutionNote: "영수증 확인",
            resolvedAt: "2026-06-01T00:05:00Z",
            createdAt: "2026-06-01T00:00:00Z",
            updatedAt: "2026-06-01T00:05:00Z"
          }
        ],
        nextCursor: null
      })
    });
  });

  await page.goto("/");
  await page.getByRole("searchbox", { name: "검색어" }).fill("galaxy");
  await page.getByRole("button", { name: "검색", exact: true }).click();
  await page.getByRole("link", { name: "Galaxy S26 Ultra" }).click();

  await expect(page).toHaveURL(/\/products\/product-1$/);
  await expect(page.getByRole("heading", { name: "Galaxy S26 Ultra" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Galaxy S26 sealed auction" })).toBeVisible();
  await expect(page.getByText("가격 이력")).toBeVisible();
  await expect(page.getByText("실구매 기준 만족")).toBeVisible();
});

test("places an auction bid from the auction detail page", async ({ page }) => {
  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        user: {
          id: "user-1",
          email: "user@example.com",
          nickname: "Deal User",
          role: "USER"
        },
        accessToken: "access-1",
        tokenType: "Bearer"
      })
    });
  });
  await page.route("**/api/v1/auctions/auction-1", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(auction) });
  });
  await page.route("**/api/v1/products/product-1", async (route) => {
    await route.fulfill({ contentType: "application/json", body: JSON.stringify(product) });
  });
  await page.route("**/api/v1/auctions/auction-1/bids", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer access-1");
    expect(route.request().postDataJSON()).toEqual({ amount: 730000 });
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: "bid-1",
        auctionId: "auction-1",
        userId: "user-1",
        amount: 730000,
        createdAt: "2026-05-31T00:00:00Z"
      })
    });
  });

  await page.goto("/auctions/auction-1");
  const bidForm = page.getByRole("form", { name: "경매 입찰" });
  await expect(page.getByRole("heading", { name: "Galaxy S26 sealed auction" })).toBeVisible();
  await expect(bidForm.getByText("현재가 ₩720,000")).toBeVisible();

  await bidForm.getByLabel("입찰 금액").fill("730000");
  await bidForm.getByRole("button", { name: "입찰하기" }).click();

  await expect(bidForm.getByText("입찰이 접수되었습니다.")).toBeVisible();
  await expect(bidForm.getByText("현재가 ₩730,000")).toBeVisible();
});
