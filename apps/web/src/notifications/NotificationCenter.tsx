"use client";

import React, { useEffect, useState } from "react";

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

export function NotificationCenter({ accessToken }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
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

  if (!accessToken) {
    return null;
  }

  const token = accessToken;

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
    await refreshNotifications();
  }

  async function refreshNotifications() {
    setIsLoadingList(true);
    try {
      const page = await listNotifications({ accessToken: token });
      setNotifications(page.items);
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
        current.map((notification) =>
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
    <div className="relative">
      <button
        aria-label={buttonLabel}
        aria-expanded={isOpen}
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
        <div className="absolute right-0 z-20 mt-2 w-[min(22rem,calc(100vw-2.5rem))] rounded-md border border-black/10 bg-white shadow-lg">
          <div className="flex items-center justify-between gap-3 border-b border-black/10 px-4 py-3">
            <div>
              <h2 className="text-sm font-bold">알림</h2>
              <p className="text-xs text-black/55">최근 받은 알림</p>
            </div>
            <button
              className="rounded border border-black/15 px-2.5 py-1 text-xs font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSaving || notifications.length === 0}
              onClick={() => void handleReadAll()}
              type="button"
            >
              모두 읽음
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto px-2 py-2">
            {isLoadingList ? (
              <p className="px-2 py-6 text-sm text-black/60">알림을 불러오는 중입니다.</p>
            ) : notifications.length === 0 ? (
              <p className="px-2 py-6 text-sm text-black/60">알림이 없습니다.</p>
            ) : (
              <ul aria-label="최근 알림" className="space-y-2">
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
            )}
          </div>

          {errorMessage ? (
            <p className="border-t border-deal/20 px-4 py-3 text-xs font-semibold text-deal">
              {errorMessage}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
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
