import { expect, test } from "@playwright/test";

const userSession = {
  user: {
    id: "user-1",
    email: "user@example.com",
    nickname: "Deal User",
    role: "USER"
  },
  accessToken: "access-1",
  tokenType: "Bearer"
};

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
    status: "approved",
    aiDecision: "needs_admin_review",
    aiReason: "mock review passed: admin approval required",
    aiReviewedAt: "2026-05-31T14:30:00Z",
    reviewedByUserId: "admin-1",
    resolutionNote: "승인",
    resolvedAt: "2026-05-31T14:40:00Z",
    publishedProductId: "product-1",
    publishedOfferType: "deal",
    publishedOfferId: "deal-1",
    createdAt: "2026-05-31T14:30:00Z",
    updatedAt: "2026-05-31T14:40:00Z",
    ...overrides
  };
}

test("authenticated user views own contribution history", async ({ page }) => {
  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(userSession)
    });
  });
  await page.route("**/api/v1/admin/submissions**", async (route) => {
    throw new Error(`My Page must not call admin submissions: ${route.request().url()}`);
  });
  await page.route("**/api/v1/me/submissions?limit=20", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer access-1");
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [submissionFixture()],
        nextCursor: "submission-2"
      })
    });
  });
  await page.route("**/api/v1/me/submissions?limit=20&cursor=submission-2", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          submissionFixture({
            id: "submission-2",
            offerType: "auction",
            title: "Galaxy S26 sealed auction",
            salePrice: null,
            currentPrice: 720000,
            status: "rejected",
            resolutionNote: "중복 제보",
            publishedProductId: null,
            publishedOfferType: null,
            publishedOfferId: null
          })
        ],
        nextCursor: null
      })
    });
  });

  await page.goto("/me");

  await expect(page.getByRole("heading", { name: "내 활동" })).toBeVisible();
  await expect(page.getByRole("article", { name: "Galaxy S26 launch deal 제보 이력" })).toBeVisible();
  await expect(page.getByText("승인됨")).toBeVisible();
  await expect(page.getByRole("link", { name: "발행 상품" })).toHaveAttribute(
    "href",
    "/products/product-1"
  );
  await expect(page.getByRole("link", { name: "발행 핫딜" })).toHaveAttribute(
    "href",
    "/deals/deal-1"
  );

  await page.getByRole("button", { name: "더보기" }).click();

  await expect(page.getByRole("article", { name: "Galaxy S26 sealed auction 제보 이력" })).toBeVisible();
  await expect(page.getByText("거절됨")).toBeVisible();
  await expect(page.getByText("중복 제보")).toBeVisible();
});
