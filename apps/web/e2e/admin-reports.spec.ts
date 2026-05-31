import { expect, test } from "@playwright/test";

test("admin resolves a report with a target status change", async ({ page }) => {
  const authSession = {
    user: {
      id: "admin-1",
      email: "admin@example.com",
      nickname: "Deal Admin",
      role: "ADMIN"
    },
    accessToken: "access-1",
    tokenType: "Bearer"
  };

  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(authSession)
    });
  });
  await page.route("**/api/v1/admin/reports?status=open&limit=20", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        items: [
          {
            id: "report-1",
            userId: "user-1",
            targetType: "deal",
            targetId: "deal-1",
            reasonCode: "fraud",
            description: "외부 링크가 수상합니다.",
            status: "open",
            reviewedByUserId: null,
            resolutionNote: null,
            resolvedAt: null,
            createdAt: "2026-05-31T00:00:00Z",
            updatedAt: "2026-05-31T00:00:00Z",
            target: {
              targetType: "deal",
              targetId: "deal-1",
              title: "Galaxy S26 launch deal",
              status: "active",
              seller: "Example Store",
              sourceUrl: "https://example.com/deals/galaxy"
            }
          }
        ],
        nextCursor: null
      })
    });
  });
  await page.route("**/api/v1/admin/reports/report-1", async (route) => {
    expect(route.request().headers().authorization).toBe("Bearer access-1");
    expect(route.request().postDataJSON()).toEqual({
      status: "resolved",
      resolutionNote: "차단 처리",
      targetStatus: "rejected"
    });
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: "report-1",
        userId: "user-1",
        targetType: "deal",
        targetId: "deal-1",
        reasonCode: "fraud",
        description: "외부 링크가 수상합니다.",
        status: "resolved",
        reviewedByUserId: "admin-1",
        resolutionNote: "차단 처리",
        resolvedAt: "2026-05-31T00:05:00Z",
        createdAt: "2026-05-31T00:00:00Z",
        updatedAt: "2026-05-31T00:05:00Z",
        target: {
          targetType: "deal",
          targetId: "deal-1",
          title: "Galaxy S26 launch deal",
          status: "rejected",
          seller: "Example Store",
          sourceUrl: "https://example.com/deals/galaxy"
        }
      })
    });
  });

  await page.goto("/admin");

  await expect(page.getByRole("heading", { name: "신고 검토" })).toBeVisible();
  await expect(page.getByText("Galaxy S26 launch deal")).toBeVisible();

  await page.getByLabel("대상 상태").selectOption("rejected");
  await page.getByLabel("처리 메모").fill("차단 처리");
  await page.getByRole("button", { name: "처리 저장" }).click();

  await expect(page.getByText("표시할 신고가 없습니다.")).toBeVisible();
});
