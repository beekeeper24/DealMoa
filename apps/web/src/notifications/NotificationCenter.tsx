"use client";

import React, { useEffect, useRef, useState } from "react";

import {
  getUnreadNotificationCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead
} from "./api";
import type { NotificationItem } from "./types";

type NotificationCenterProps = {
  accessToken?: string;
};

type NotificationFilter = "all" | "unread";

export function NotificationCenter({ accessToken }: NotificationCenterProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [filter, setFilter] = useState<NotificationFilter>("all");
  const [isLoadingCount, setIsLoadingCount] = useState(false);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void refreshUnreadCount(accessToken);
  }, [accessToken]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    function closeOnOutsidePointer(event: PointerEvent) {
      if (
        event.target instanceof Node &&
        rootRef.current &&
        !rootRef.current.contains(event.target)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener("keydown", closeOnEscape);
    document.addEventListener("pointerdown", closeOnOutsidePointer);
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
    };
  }, [isOpen]);

  if (!accessToken) {
    return null;
  }

  const token = accessToken;
  const hasUnread = unreadCount > 0;
  const isInitialListLoading = isLoadingList && notifications.length === 0;
  const emptyMessage =
    filter === "unread" ? "읽지 않은 알림이 없습니다." : "알림이 없습니다.";

  async function refreshUnreadCount(token: string) {
    setIsLoadingCount(true);
    try {
      setUnreadCount(await getUnreadNotificationCount(token));
    } catch {
      setErrorMessage("알림 수를 불러오지 못했습니다.");
    } finally {
      setIsLoadingCount(false);
    }
  }

  async function openNotifications() {
    const nextOpen = !isOpen;
    setIsOpen(nextOpen);
    setErrorMessage(null);
    if (!nextOpen) {
      return;
    }
    await loadNotifications({ append: false, cursor: null, filter });
  }

  async function refreshNotifications() {
    await loadNotifications({ append: false, cursor: null, filter });
  }

  async function selectFilter(nextFilter: NotificationFilter) {
    setFilter(nextFilter);
    setErrorMessage(null);
    await loadNotifications({ append: false, cursor: null, filter: nextFilter });
  }

  async function loadMoreNotifications() {
    if (!nextCursor || isLoadingList) {
      return;
    }
    await loadNotifications({ append: true, cursor: nextCursor, filter });
  }

  async function loadNotifications({
    append,
    cursor,
    filter
  }: {
    append: boolean;
    cursor: string | null;
    filter: NotificationFilter;
  }) {
    if (!append) {
      setNotifications([]);
      setNextCursor(null);
    }
    setIsLoadingList(true);
    try {
      const page = await listNotifications({
        accessToken: token,
        cursor,
        unreadOnly: filter === "unread"
      });
      setNotifications((current) => (append ? [...current, ...page.items] : page.items));
      setNextCursor(page.nextCursor);
    } catch {
      setErrorMessage("알림을 불러오지 못했습니다.");
    } finally {
      setIsLoadingList(false);
    }
  }

  async function handleMarkRead(notificationId: string) {
    setIsSaving(true);
    setErrorMessage(null);
    try {
      const updated = await markNotificationRead({ accessToken: token, notificationId });
      setNotifications((current) =>
        filter === "unread"
          ? current.filter((notification) => notification.id !== notificationId)
          : current.map((notification) =>
              notification.id === notificationId ? updated : notification
            )
      );
      await refreshUnreadCount(token);
    } catch {
      setErrorMessage("읽음 처리에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleReadAll() {
    setIsSaving(true);
    setErrorMessage(null);
    try {
      await markAllNotificationsRead(token);
      await refreshUnreadCount(token);
      await refreshNotifications();
    } catch {
      setErrorMessage("전체 읽음 처리에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  }

  const buttonLabel = unreadCount > 0 ? `알림 ${unreadCount}개` : "알림 없음";

  return (
    <div className="relative" ref={rootRef}>
      <button
        aria-label={buttonLabel}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        className="relative rounded border border-black/15 bg-white px-3 py-1.5 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-wait disabled:opacity-60"
        disabled={isLoadingCount}
        onClick={() => void openNotifications()}
        type="button"
      >
        알림
        {unreadCount > 0 ? (
          <span className="ml-2 inline-flex min-w-5 justify-center rounded bg-deal px-1.5 py-0.5 text-xs text-white">
            {unreadCount}
          </span>
        ) : null}
      </button>

      {isOpen ? (
        <div
          aria-label="알림 목록"
          className="absolute right-0 z-20 mt-2 w-[min(24rem,calc(100vw-2.5rem))] rounded-md border border-black/10 bg-white shadow-lg"
          role="dialog"
        >
          <div className="flex items-center justify-between gap-3 border-b border-black/10 px-4 py-3">
            <div>
              <h2 className="text-sm font-bold">알림</h2>
              <p className="text-xs text-black/55">
                {filter === "unread" ? "읽지 않은 알림" : "최근 받은 알림"}
              </p>
            </div>
            <button
              className="rounded border border-black/15 px-2.5 py-1 text-xs font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSaving || !hasUnread}
              onClick={() => void handleReadAll()}
              type="button"
            >
              {isSaving ? "처리 중" : "모두 읽음"}
            </button>
          </div>

          <div className="flex gap-2 border-b border-black/10 px-4 py-2">
            <button
              aria-pressed={filter === "all"}
              className={filterButtonClass(filter === "all")}
              disabled={isLoadingList && filter === "all"}
              onClick={() => void selectFilter("all")}
              type="button"
            >
              전체
            </button>
            <button
              aria-pressed={filter === "unread"}
              className={filterButtonClass(filter === "unread")}
              disabled={isLoadingList && filter === "unread"}
              onClick={() => void selectFilter("unread")}
              type="button"
            >
              읽지 않음
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto px-2 py-2">
            {isInitialListLoading ? (
              <p className="px-2 py-6 text-sm text-black/60">알림을 불러오는 중입니다.</p>
            ) : notifications.length === 0 ? (
              <p className="px-2 py-6 text-sm text-black/60">{emptyMessage}</p>
            ) : (
              <>
                <ul
                  aria-label={filter === "unread" ? "읽지 않은 알림" : "최근 알림"}
                  className="space-y-2"
                >
                  {notifications.map((notification) => (
                    <li
                      className="rounded border border-black/10 px-3 py-3 transition hover:border-signal"
                      key={notification.id}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-bold">{notification.title}</p>
                          <p className="mt-1 text-sm leading-5 text-black/65">
                            {notification.body}
                          </p>
                          <p className="mt-2 text-xs text-black/45">
                            {formatNotificationTime(notification.createdAt)}
                          </p>
                        </div>
                        {notification.readAt ? (
                          <span className="shrink-0 text-xs font-semibold text-black/40">
                            읽음
                          </span>
                        ) : (
                          <button
                            className="shrink-0 rounded border border-signal px-2 py-1 text-xs font-semibold text-signal transition hover:bg-signal hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={isSaving}
                            onClick={() => void handleMarkRead(notification.id)}
                            type="button"
                          >
                            읽음 처리
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
                {nextCursor ? (
                  <button
                    className="mt-3 w-full rounded border border-black/15 px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-wait disabled:opacity-60"
                    disabled={isLoadingList}
                    onClick={() => void loadMoreNotifications()}
                    type="button"
                  >
                    {isLoadingList ? "불러오는 중" : "더보기"}
                  </button>
                ) : null}
              </>
            )}
          </div>

          {errorMessage ? (
            <p
              aria-live="polite"
              className="border-t border-deal/20 px-4 py-3 text-xs font-semibold text-deal"
            >
              {errorMessage}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function filterButtonClass(isSelected: boolean): string {
  const base =
    "rounded border px-2.5 py-1 text-xs font-semibold transition disabled:cursor-wait disabled:opacity-60";
  if (isSelected) {
    return `${base} border-signal bg-signal text-white`;
  }
  return `${base} border-black/15 text-black/65 hover:border-signal hover:text-signal`;
}

function formatNotificationTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}
