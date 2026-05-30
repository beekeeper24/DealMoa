import { expect, test } from "@playwright/test";

test("searches products from the browser", async ({ page }) => {
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
  await page.route("**/api/v1/notifications/unread-count", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ count: 0 })
    });
  });
  await page.route("**/api/v1/search/products?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "product-1",
            name: "Galaxy S26 Ultra",
            brand: "Samsung",
            modelName: "SM-S260",
            category: "smartphone",
            specsText: "storage 256GB 색상 블랙",
            createdAt: "2026-05-25T00:00:00Z",
            updatedAt: "2026-05-25T00:00:00Z",
            score: 2.4
          }
        ],
        nextCursor: null
      })
    });
  });
  await page.route("**/api/v1/me/favorites/products/product-1", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer access-1");
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: "favorite-1",
        productId: "product-1",
        createdAt: "2026-05-28T00:00:00Z"
      })
    });
  });

  await page.goto("/");
  await page.getByRole("searchbox", { name: "검색어" }).fill("galaxy");
  await page.getByRole("button", { name: "검색", exact: true }).click();

  await expect(page.getByText("Galaxy S26 Ultra")).toBeVisible();
  await expect(page.getByText("Samsung · SM-S260")).toBeVisible();
  await expect(page.getByText("score 2.40")).toBeVisible();
  await page.getByRole("button", { name: "찜하기" }).click();
  await expect(page.getByRole("button", { name: "찜 해제" })).toBeVisible();
});
