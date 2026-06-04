import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AdminReportApiError,
  listAdminCrawlerRunLogs,
  listAdminReports,
  reviewAdminReport
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

const reportFixture = {
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
};

describe("admin reports api", () => {
  it("lists admin crawler run logs with limit, cursor, and bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          {
            id: "run-1",
            taskName: "crawl_live_urls",
            status: "succeeded",
            scanned: 2,
            fetched: 1,
            accepted: 1,
            created: 1,
            duplicates: 0,
            skipped: 1,
            skipReasons: { host_rate_limited: 1 },
            errorType: null,
            errorMessage: null,
            startedAt: "2026-06-03T01:00:00Z",
            finishedAt: "2026-06-03T01:00:01Z",
            createdAt: "2026-06-03T01:00:01Z"
          }
        ],
        nextCursor: "run-2"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const page = await listAdminCrawlerRunLogs({
      accessToken: "access-1",
      cursor: "cursor-1"
    });

    expect(page.items[0].taskName).toBe("crawl_live_urls");
    expect(page.items[0].skipReasons.host_rate_limited).toBe(1);
    expect(page.items[0].errorType).toBeNull();
    expect(page.nextCursor).toBe("run-2");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/crawler-runs?limit=20&cursor=cursor-1",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
  });

  it("lists admin reports with status, limit, cursor, and bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [reportFixture],
        nextCursor: "report-2"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const page = await listAdminReports({
      accessToken: "access-1",
      cursor: "cursor-1",
      status: "open"
    });

    expect(page.items[0].target?.title).toBe("Galaxy S26 launch deal");
    expect(page.nextCursor).toBe("report-2");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/reports?status=open&limit=20&cursor=cursor-1",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
  });

  it("reviews a report with optional target status", async () => {
    const reviewedReport = {
      ...reportFixture,
      status: "resolved",
      resolutionNote: "차단 처리",
      target: { ...reportFixture.target, status: "blocked" }
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(reviewedReport));
    vi.stubGlobal("fetch", fetchMock);

    const result = await reviewAdminReport({
      accessToken: "access-1",
      reportId: "report-1",
      resolutionNote: "차단 처리",
      status: "resolved",
      targetStatus: "blocked"
    });

    expect(result.status).toBe("resolved");
    expect(result.target?.status).toBe("blocked");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/admin/reports/report-1", {
      body: JSON.stringify({
        status: "resolved",
        resolutionNote: "차단 처리",
        targetStatus: "blocked"
      }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("omits empty optional review fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        ...reportFixture,
        status: "dismissed"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await reviewAdminReport({
      accessToken: "access-1",
      reportId: "report-1",
      resolutionNote: "",
      status: "dismissed",
      targetStatus: ""
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/reports/report-1",
      expect.objectContaining({
        body: JSON.stringify({ status: "dismissed" })
      })
    );
  });

  it("throws admin report api errors with stable code", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(
          jsonResponse(
            {
              error: {
                code: "FORBIDDEN",
                message: "관리자 권한이 필요합니다.",
                details: {},
                traceId: "req-1"
              }
            },
            { status: 403 }
          )
        )
      )
    );

    await expect(
      listAdminReports({ accessToken: "access-1", status: "open" })
    ).rejects.toBeInstanceOf(AdminReportApiError);
    await expect(
      listAdminReports({ accessToken: "access-1", status: "open" })
    ).rejects.toMatchObject({
      code: "FORBIDDEN",
      message: "관리자 권한이 필요합니다."
    });
  });
});
