// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NotificationCenter } from "../NotificationCenter";

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

function notificationFixture(overrides: Record<string, unknown> = {}) {
  return {
    id: "notification-1",
    type: "new_deal",
    title: "관심 상품에 새 핫딜이 등록되었습니다.",
    body: "Galaxy S26 launch deal",
    targetType: "deal",
    targetId: "deal-1",
    metadata: {},
    readAt: null,
    createdAt: "2026-05-29T10:00:00Z",
    ...overrides
  };
}

describe("NotificationCenter", () => {
  it("does not render without an access token", () => {
    render(<NotificationCenter />);

    expect(screen.queryByRole("button", { name: /알림/ })).not.toBeInTheDocument();
  });

  it("loads unread count and opens recent notifications", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ count: 2 }))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: "notification-1",
              type: "new_deal",
              title: "관심 상품에 새 핫딜이 등록되었습니다.",
              body: "Galaxy S26 launch deal",
              targetType: "deal",
              targetId: "deal-1",
              metadata: {},
              readAt: null,
              createdAt: "2026-05-29T10:00:00Z"
            }
          ],
          nextCursor: null
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<NotificationCenter accessToken="access-1" />);

    expect(await screen.findByText("2")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "알림 2개" }));

    expect(await screen.findByText("Galaxy S26 launch deal")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/api/v1/notifications?limit=20", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" }
    });
  });

  it("marks one notification as read and refreshes unread count", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ count: 1 }))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: "notification-1",
              type: "auction_ending_soon",
              title: "관심 경매가 곧 종료됩니다.",
              body: "Galaxy S26 sealed auction",
              targetType: "auction",
              targetId: "auction-1",
              metadata: {},
              readAt: null,
              createdAt: "2026-05-29T10:00:00Z"
            }
          ],
          nextCursor: null
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: "notification-1",
          type: "auction_ending_soon",
          title: "관심 경매가 곧 종료됩니다.",
          body: "Galaxy S26 sealed auction",
          targetType: "auction",
          targetId: "auction-1",
          metadata: {},
          readAt: "2026-05-29T10:05:00Z",
          createdAt: "2026-05-29T10:00:00Z"
        })
      )
      .mockResolvedValueOnce(jsonResponse({ count: 0 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<NotificationCenter accessToken="access-1" />);

    await screen.findByText("1");
    await user.click(screen.getByRole("button", { name: "알림 1개" }));
    await user.click(await screen.findByRole("button", { name: "읽음 처리" }));

    await waitFor(() => expect(screen.queryByText("1")).not.toBeInTheDocument());
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/v1/notifications/notification-1/read", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "POST"
    });
  });

  it("marks all notifications as read", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ count: 2 }))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: "notification-1",
              type: "new_deal",
              title: "새 핫딜",
              body: "Galaxy deal",
              targetType: "deal",
              targetId: "deal-1",
              metadata: {},
              readAt: null,
              createdAt: "2026-05-29T10:00:00Z"
            }
          ],
          nextCursor: null
        })
      )
      .mockResolvedValueOnce(jsonResponse({ updatedCount: 2 }))
      .mockResolvedValueOnce(jsonResponse({ count: 0 }))
      .mockResolvedValueOnce(jsonResponse({ items: [], nextCursor: null }));
    vi.stubGlobal("fetch", fetchMock);

    render(<NotificationCenter accessToken="access-1" />);

    await screen.findByText("2");
    await user.click(screen.getByRole("button", { name: "알림 2개" }));
    await user.click(await screen.findByRole("button", { name: "모두 읽음" }));

    expect(await screen.findByText("알림이 없습니다.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/api/v1/notifications/read-all", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "POST"
    });
  });

  it("filters unread notifications and loads the next cursor page", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ count: 3 }))
      .mockResolvedValueOnce(jsonResponse({ items: [], nextCursor: null }))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [notificationFixture({ id: "notification-1", body: "첫 번째 안 읽은 알림" })],
          nextCursor: "cursor-2"
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          items: [notificationFixture({ id: "notification-2", body: "두 번째 안 읽은 알림" })],
          nextCursor: null
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<NotificationCenter accessToken="access-1" />);

    await screen.findByText("3");
    await user.click(screen.getByRole("button", { name: "알림 3개" }));
    await user.click(await screen.findByRole("button", { name: "읽지 않음" }));

    expect(await screen.findByText("첫 번째 안 읽은 알림")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "더보기" }));

    expect(await screen.findByText("두 번째 안 읽은 알림")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/v1/notifications?limit=20&unreadOnly=true",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "/api/v1/notifications?limit=20&unreadOnly=true&cursor=cursor-2",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
  });

  it("closes the open panel with Escape", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ count: 1 }))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [notificationFixture()],
          nextCursor: null
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<NotificationCenter accessToken="access-1" />);

    await screen.findByText("1");
    await user.click(screen.getByRole("button", { name: "알림 1개" }));
    expect(await screen.findByRole("dialog", { name: "알림 목록" })).toBeInTheDocument();

    await user.keyboard("{Escape}");

    await waitFor(() =>
      expect(screen.queryByRole("dialog", { name: "알림 목록" })).not.toBeInTheDocument()
    );
    expect(screen.getByRole("button", { name: "알림 1개" })).toBeInTheDocument();
  });

  it("closes the open panel when pressing outside", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ count: 1 }))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [notificationFixture()],
          nextCursor: null
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<NotificationCenter accessToken="access-1" />);

    await screen.findByText("1");
    await user.click(screen.getByRole("button", { name: "알림 1개" }));
    expect(await screen.findByRole("dialog", { name: "알림 목록" })).toBeInTheDocument();

    fireEvent.pointerDown(document.body);

    await waitFor(() =>
      expect(screen.queryByRole("dialog", { name: "알림 목록" })).not.toBeInTheDocument()
    );
  });
});
