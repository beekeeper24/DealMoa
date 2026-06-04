"use client";

import Link from "next/link";
import React, { ReactNode, useEffect, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";

import { AdminReportApiError, listAdminCrawlerRunLogs, triggerAdminCrawlerRun } from "./api";
import type { AdminCrawlerRunLog, AdminCrawlerTaskName } from "./types";

export function AdminCrawlerRunLogPage() {
  const authSession = useAuthSession();
  const [items, setItems] = useState<AdminCrawlerRunLog[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [triggeringTask, setTriggeringTask] = useState<AdminCrawlerTaskName | null>(null);
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const isAdmin = authSession.session?.user.role === "ADMIN";
  const accessToken =
    authSession.status === "authenticated" && isAdmin ? authSession.accessToken : undefined;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void fetchRunLogs({ append: false, cursor: null, token: accessToken });
  }, [accessToken]);

  async function fetchRunLogs(request: {
    append: boolean;
    cursor: string | null;
    token: string;
  }) {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const page = await listAdminCrawlerRunLogs({
        accessToken: request.token,
        cursor: request.cursor
      });
      setItems((current) => (request.append ? [...current, ...page.items] : page.items));
      setNextCursor(page.nextCursor);
    } catch (error) {
      setItems((current) => (request.append ? current : []));
      setNextCursor(null);
      setErrorMessage(
        error instanceof AdminReportApiError
          ? error.message
          : "크롤러 실행 로그를 불러오지 못했습니다."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function triggerCrawlerRun(taskName: AdminCrawlerTaskName) {
    if (!accessToken) {
      return;
    }
    setTriggeringTask(taskName);
    setTriggerMessage(null);
    setErrorMessage(null);
    try {
      const result = await triggerAdminCrawlerRun({
        accessToken,
        taskName
      });
      setTriggerMessage(`요청됨 ${result.celeryTaskId}`);
      await fetchRunLogs({ append: false, cursor: null, token: accessToken });
    } catch (error) {
      setErrorMessage(
        error instanceof AdminReportApiError
          ? error.message
          : "크롤러 실행 요청에 실패했습니다."
      );
    } finally {
      setTriggeringTask(null);
    }
  }

  if (authSession.status === "loading") {
    return <AdminShell>관리자 세션 확인 중</AdminShell>;
  }
  if (authSession.status === "anonymous") {
    return <AdminShell>관리자 로그인이 필요합니다.</AdminShell>;
  }
  if (!isAdmin) {
    return <AdminShell danger>관리자 권한이 필요합니다.</AdminShell>;
  }

  return (
    <AdminShell>
      <section className="mx-auto max-w-6xl px-5 py-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">크롤러 실행 로그</h1>
            <p className="mt-2 text-sm leading-6 text-black/65">
              worker가 완료한 crawler task의 요약을 확인하고 허용된 작업을 수동 실행합니다.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={triggeringTask !== null}
              onClick={() => void triggerCrawlerRun("crawl_hot_deals_mock")}
              type="button"
            >
              {triggeringTask === "crawl_hot_deals_mock" ? "요청 중" : "Mock 크롤러 실행"}
            </button>
            <button
              className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={triggeringTask !== null}
              onClick={() => void triggerCrawlerRun("crawl_live_urls")}
              type="button"
            >
              {triggeringTask === "crawl_live_urls" ? "요청 중" : "Live 크롤러 실행"}
            </button>
            <Link
              className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
              href="/admin"
            >
              신고 검토
            </Link>
            <Link
              className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
              href="/admin/submissions"
            >
              제보 검토
            </Link>
          </div>
        </div>

        {triggerMessage ? (
          <p className="mt-6 rounded-md border border-signal/30 bg-white px-4 py-3 text-sm font-semibold text-signal">
            {triggerMessage}
          </p>
        ) : null}

        {errorMessage ? (
          <p
            className={`rounded-md border border-deal/30 bg-white px-4 py-3 text-sm font-semibold text-deal ${
              triggerMessage ? "mt-3" : "mt-6"
            }`}
          >
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-6 space-y-3">
          {isLoading && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              크롤러 실행 로그를 불러오는 중
            </p>
          ) : null}

          {!isLoading && !errorMessage && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              표시할 실행 로그가 없습니다.
            </p>
          ) : null}

          {items.map((item) => (
            <CrawlerRunLogCard item={item} key={item.id} />
          ))}
        </div>

        {nextCursor ? (
          <button
            className="mt-4 rounded border border-black/15 bg-white px-4 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            onClick={() =>
              accessToken
                ? void fetchRunLogs({ append: true, cursor: nextCursor, token: accessToken })
                : undefined
            }
            type="button"
          >
            더보기
          </button>
        ) : null}
      </section>
    </AdminShell>
  );
}

function CrawlerRunLogCard({ item }: { item: AdminCrawlerRunLog }) {
  const skipReasonEntries = Object.entries(item.skipReasons);
  return (
    <article
      aria-label={`${item.taskName} 실행 로그`}
      className="rounded-md border border-black/10 bg-white p-4"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-signal">
              {item.status}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {formatDateTime(item.createdAt)}
            </span>
          </div>
          <h2 className="mt-3 text-lg font-bold">{item.taskName}</h2>
          <p className="mt-2 text-sm text-black/65">
            시작 {formatDateTime(item.startedAt)} · 종료 {formatDateTime(item.finishedAt)}
          </p>
        </div>
        <div className="grid gap-2 text-sm lg:min-w-96">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            <Metric label="scanned" value={item.scanned} />
            <Metric label="fetched" value={item.fetched} />
            <Metric label="accepted" value={item.accepted} />
            <Metric label="created" value={item.created} />
            <Metric label="duplicates" value={item.duplicates} />
            <Metric label="skipped" value={item.skipped} />
          </div>
          {skipReasonEntries.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {skipReasonEntries.map(([reason, count]) => (
                <span className="rounded bg-paper px-2 py-1 text-xs font-semibold" key={reason}>
                  {reason} {count}
                </span>
              ))}
            </div>
          ) : null}
          {item.errorType || item.errorMessage ? (
            <div className="rounded border border-deal/30 bg-paper px-3 py-2">
              {item.errorType ? (
                <p className="text-xs font-bold text-deal">{item.errorType}</p>
              ) : null}
              {item.errorMessage ? (
                <p className="mt-1 text-xs leading-5 text-black/70">{item.errorMessage}</p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <span className="rounded border border-black/10 bg-paper px-2 py-1 text-xs font-semibold">
      {label} {value}
    </span>
  );
}

function AdminShell({ children, danger = false }: { children: ReactNode; danger?: boolean }) {
  const isTextOnly = typeof children === "string";
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div>
            <div className="text-xl font-bold">DealMoa</div>
            <p className="text-xs font-semibold text-signal">관리자 콘솔</p>
          </div>
          <Link
            className="rounded border border-black/15 px-3 py-1.5 text-sm font-semibold transition hover:border-signal hover:text-signal"
            href="/"
          >
            검색으로 돌아가기
          </Link>
        </div>
      </header>
      {isTextOnly ? (
        <section className="mx-auto max-w-6xl px-5 py-8">
          <p
            className={`rounded-md border bg-white px-4 py-6 text-sm ${
              danger ? "border-deal/30 font-semibold text-deal" : "border-black/10 text-black/65"
            }`}
          >
            {children}
          </p>
        </section>
      ) : (
        children
      )}
    </main>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
