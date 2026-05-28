import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getUnreadNotificationCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead
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

describe("notifications api", () => {
  it("fetches unread notification count with bearer token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ count: 3 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getUnreadNotificationCount("access-1")).resolves.toBe(3);

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/notifications/unread-count", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" }
    });
  });

  it("lists notifications with unread filter and cursor", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          {
            id: "notification-1",
            type: "new_deal",
            title: "새 핫딜",
            body: "Galaxy deal",
            targetType: "deal",
            targetId: "deal-1",
            metadata: { productId: "product-1" },
            readAt: null,
            createdAt: "2026-05-29T10:00:00Z"
          }
        ],
        nextCursor: "notification-2"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const page = await listNotifications({
      accessToken: "access-1",
      cursor: "cursor-1",
      unreadOnly: true
    });

    expect(page.items[0].title).toBe("새 핫딜");
    expect(page.nextCursor).toBe("notification-2");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/notifications?limit=20&unreadOnly=true&cursor=cursor-1",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
  });

  it("marks one notification as read", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: "notification-1",
        type: "new_auction",
        title: "새 경매",
        body: "Galaxy auction",
        targetType: "auction",
        targetId: "auction-1",
        metadata: {},
        readAt: "2026-05-29T10:05:00Z",
        createdAt: "2026-05-29T10:00:00Z"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const notification = await markNotificationRead({
      accessToken: "access-1",
      notificationId: "notification-1"
    });

    expect(notification.readAt).toBe("2026-05-29T10:05:00Z");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/notifications/notification-1/read", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "POST"
    });
  });

  it("marks all notifications as read", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ updatedCount: 2 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(markAllNotificationsRead("access-1")).resolves.toBe(2);

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/notifications/read-all", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "POST"
    });
  });

  it("throws notification api errors with stable code", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              code: "UNAUTHORIZED",
              message: "인증이 필요합니다.",
              details: {},
              traceId: "req-1"
            }
          },
          { status: 401 }
        )
      )
    );

    await expect(getUnreadNotificationCount("bad-token")).rejects.toMatchObject({
      code: "UNAUTHORIZED",
      message: "인증이 필요합니다."
    });
  });
});
