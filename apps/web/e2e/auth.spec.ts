import { expect, test } from "@playwright/test";

test("logs in through the mocked oauth callback flow", async ({ page }) => {
  let hasRefreshCookie = false;
  const authSession = {
    user: {
      id: "user-1",
      email: "user@example.com",
      nickname: "Deal User",
      role: "USER"
    },
    accessToken: "access-token",
    tokenType: "Bearer"
  };

  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    if (!hasRefreshCookie) {
      await route.fulfill({
        contentType: "application/json",
        status: 401,
        body: JSON.stringify({
          error: {
            code: "INVALID_REFRESH_TOKEN",
            message: "로그인이 필요합니다.",
            details: {},
            traceId: "req_1"
          }
        })
      });
      return;
    }
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(authSession)
    });
  });
  await page.route("**/api/v1/auth/oauth/google/authorize-url?**", async (route) => {
    const requestUrl = new URL(route.request().url());
    const state = requestUrl.searchParams.get("state");
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        authorizationUrl: `/auth/callback/google?code=code-1&state=${state}`
      })
    });
  });
  await page.route("**/api/v1/auth/oauth/google/callback", async (route) => {
    hasRefreshCookie = true;
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(authSession)
    });
  });
  await page.route("**/api/v1/notifications/unread-count", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ count: 0 })
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Google 로그인" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByText("user@example.com")).toBeVisible();
});
