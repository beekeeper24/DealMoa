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

const adminSession = {
  user: {
    id: "admin-1",
    email: "admin@example.com",
    nickname: "Deal Admin",
    role: "ADMIN"
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

test("authenticated user submits a deal candidate", async ({ page }) => {
  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(userSession)
    });
  });
  await page.route("**/api/v1/submissions", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer access-1");
    expect(route.request().postDataJSON()).toMatchObject({
      offerType: "deal",
      productName: "Galaxy S26",
      salePrice: 1090000,
      sourceUrl: "https://example.com/deals/galaxy-s26"
    });
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify(submissionFixture())
    });
  });

  await page.goto("/submit");

  await expect(page.getByRole("heading", { name: "핫딜/경매 제보" })).toBeVisible();
  await page.getByLabel("원문 URL").fill("https://example.com/deals/galaxy-s26");
  await page.getByLabel("상품명").fill("Galaxy S26");
  await page.getByLabel("제보 제목").fill("Galaxy S26 launch deal");
  await page.getByLabel("판매처").fill("Example Store");
  await page.getByLabel("정가").fill("1400000");
  await page.getByLabel("핫딜가").fill("1090000");
  await page.getByRole("button", { name: "제보 제출" }).click();

  await expect(page.getByText("제보가 접수되었습니다. 상태: pending_review")).toBeVisible();
});

test("admin approves a pending submission", async ({ page }) => {
  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(adminSession)
    });
  });
  await page.route("**/api/v1/admin/submissions?status=pending_review&limit=20", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [submissionFixture()], nextCursor: null })
    });
  });
  await page.route("**/api/v1/admin/submissions/submission-1", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer access-1");
    expect(route.request().postDataJSON()).toEqual({
      action: "approve",
      resolutionNote: "승인"
    });
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(
        submissionFixture({
          status: "approved",
          reviewedByUserId: "admin-1",
          resolutionNote: "승인",
          resolvedAt: "2026-05-31T14:40:00Z",
          publishedProductId: "product-1",
          publishedOfferType: "deal",
          publishedOfferId: "deal-1"
        })
      )
    });
  });

  await page.goto("/admin/submissions");

  await expect(page.getByRole("heading", { name: "제보 검토" })).toBeVisible();
  await expect(page.getByText("Galaxy S26 launch deal")).toBeVisible();

  await page.getByLabel("처리 메모").fill("승인");
  await page.getByRole("button", { name: "제보 처리" }).click();

  await expect(page.getByText("표시할 제보가 없습니다.")).toBeVisible();
});
