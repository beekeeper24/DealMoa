"use client";

import Link from "next/link";
import React, { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";

import { AdminReportApiError, listAdminReports, reviewAdminReport } from "./api";
import type {
  AdminReport,
  AdminReportReviewStatus,
  AdminReportStatus,
  OfferStatus
} from "./types";

const reportStatuses: Array<{ key: AdminReportStatus; label: string }> = [
  { key: "open", label: "미처리" },
  { key: "resolved", label: "처리 완료" },
  { key: "dismissed", label: "기각" }
];

const reviewStatuses: Array<{ key: AdminReportReviewStatus; label: string }> = [
  { key: "resolved", label: "처리 완료" },
  { key: "dismissed", label: "기각" }
];

const targetStatuses: Array<{ key: OfferStatus | ""; label: string }> = [
  { key: "", label: "변경 없음" },
  { key: "pending", label: "pending" },
  { key: "active", label: "active" },
  { key: "verified", label: "verified" },
  { key: "rejected", label: "rejected" },
  { key: "blocked", label: "blocked" },
  { key: "closed", label: "closed" }
];

export function AdminReportQueue() {
  const authSession = useAuthSession();
  const [activeStatus, setActiveStatus] = useState<AdminReportStatus>("open");
  const [items, setItems] = useState<AdminReport[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isAdmin = authSession.session?.user.role === "ADMIN";
  const accessToken =
    authSession.status === "authenticated" && isAdmin ? authSession.accessToken : undefined;

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void fetchReports({ append: false, cursor: null, status: activeStatus, token: accessToken });
  }, [accessToken, activeStatus]);

  const statusLabel = useMemo(
    () => reportStatuses.find((status) => status.key === activeStatus)?.label ?? activeStatus,
    [activeStatus]
  );

  async function fetchReports(request: {
    append: boolean;
    cursor: string | null;
    status: AdminReportStatus;
    token: string;
  }) {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const page = await listAdminReports({
        accessToken: request.token,
        cursor: request.cursor,
        status: request.status
      });
      setItems((current) => (request.append ? [...current, ...page.items] : page.items));
      setNextCursor(page.nextCursor);
    } catch (error) {
      setItems((current) => (request.append ? current : []));
      setNextCursor(null);
      setErrorMessage(
        error instanceof AdminReportApiError
          ? error.message
          : "관리자 신고 목록을 불러오지 못했습니다."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function loadMore() {
    if (!accessToken || !nextCursor || isLoading) {
      return;
    }
    await fetchReports({
      append: true,
      cursor: nextCursor,
      status: activeStatus,
      token: accessToken
    });
  }

  async function handleReview(request: {
    reportId: string;
    resolutionNote: string;
    status: AdminReportReviewStatus;
    targetStatus: OfferStatus | "";
  }) {
    if (!accessToken) {
      return;
    }
    const reviewed = await reviewAdminReport({
      accessToken,
      reportId: request.reportId,
      resolutionNote: request.resolutionNote,
      status: request.status,
      targetStatus: request.targetStatus
    });
    setItems((current) => {
      if (reviewed.status !== activeStatus) {
        return current.filter((item) => item.id !== reviewed.id);
      }
      return current.map((item) => (item.id === reviewed.id ? reviewed : item));
    });
  }

  if (authSession.status === "loading") {
    return (
      <AdminShell>
        <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
          관리자 세션 확인 중
        </p>
      </AdminShell>
    );
  }

  if (authSession.status === "anonymous") {
    return (
      <AdminShell>
        <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
          관리자 로그인이 필요합니다.
        </p>
      </AdminShell>
    );
  }

  if (!isAdmin) {
    return (
      <AdminShell>
        <p className="rounded-md border border-deal/30 bg-white px-4 py-6 text-sm font-semibold text-deal">
          관리자 권한이 필요합니다.
        </p>
      </AdminShell>
    );
  }

  return (
    <AdminShell>
      <section className="mx-auto max-w-6xl px-5 py-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">신고 검토</h1>
            <p className="mt-2 text-sm leading-6 text-black/65">
              신고는 검토 신호입니다. 상태 변경은 명시적인 관리자 결정으로만 반영됩니다.
            </p>
          </div>
          <p className="text-sm font-semibold text-signal">{statusLabel} {items.length}건</p>
        </div>

        <div aria-label="신고 상태" className="mt-6 flex gap-2" role="tablist">
          {reportStatuses.map((status) => (
            <button
              aria-selected={activeStatus === status.key}
              className="rounded border border-black/10 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal aria-selected:border-signal aria-selected:bg-signal aria-selected:text-white"
              key={status.key}
              onClick={() => setActiveStatus(status.key)}
              role="tab"
              type="button"
            >
              {status.label}
            </button>
          ))}
        </div>

        {errorMessage ? (
          <p className="mt-6 rounded-md border border-deal/30 bg-white px-4 py-3 text-sm font-semibold text-deal">
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-6 space-y-3">
          {isLoading && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              신고 목록을 불러오는 중
            </p>
          ) : null}

          {!isLoading && !errorMessage && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              표시할 신고가 없습니다.
            </p>
          ) : null}

          {items.map((report) => (
            <AdminReportCard key={report.id} onReview={handleReview} report={report} />
          ))}
        </div>

        {nextCursor ? (
          <button
            className="mt-4 rounded border border-black/15 bg-white px-4 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            onClick={() => void loadMore()}
            type="button"
          >
            더보기
          </button>
        ) : null}
      </section>
    </AdminShell>
  );
}

function AdminShell({ children }: { children: ReactNode }) {
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
      {children}
    </main>
  );
}

function AdminReportCard({
  onReview,
  report
}: {
  onReview: (request: {
    reportId: string;
    resolutionNote: string;
    status: AdminReportReviewStatus;
    targetStatus: OfferStatus | "";
  }) => Promise<void>;
  report: AdminReport;
}) {
  const [reviewStatus, setReviewStatus] = useState<AdminReportReviewStatus>("resolved");
  const [targetStatus, setTargetStatus] = useState<OfferStatus | "">("");
  const [resolutionNote, setResolutionNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const target = report.target;
  const title = target?.title ?? `${report.targetType} ${report.targetId}`;

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    try {
      await onReview({
        reportId: report.id,
        resolutionNote,
        status: reviewStatus,
        targetStatus
      });
    } catch (error) {
      setErrorMessage(
        error instanceof AdminReportApiError
          ? error.message
          : "신고 처리 저장에 실패했습니다."
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <article
      aria-label={`${title} 신고`}
      className="rounded-md border border-black/10 bg-white p-4 transition hover:border-signal"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-signal">
              {report.targetType === "deal" ? "핫딜" : "경매"}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {target?.status ?? report.status}
            </span>
          </div>
          <h2 className="mt-3 text-lg font-bold">{title}</h2>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-black/65">
            <span>{target?.seller ?? "판매처 미상"}</span>
            <span>신고자 {report.userId}</span>
            <span>{formatDateTime(report.createdAt)}</span>
          </div>
          <p className="mt-3 text-sm font-semibold text-deal">{report.reasonCode}</p>
          {report.description ? (
            <p className="mt-1 text-sm leading-6 text-black/70">{report.description}</p>
          ) : null}
          {target?.sourceUrl ? (
            <a
              className="mt-3 inline-block text-sm font-semibold text-signal underline-offset-4 hover:underline"
              href={target.sourceUrl}
              rel="noreferrer"
              target="_blank"
            >
              원문 열기
            </a>
          ) : null}
        </div>

        <form className="grid min-w-72 gap-3 lg:w-80" onSubmit={submitReview}>
          <label className="grid gap-1 text-sm font-semibold">
            처리 결과
            <select
              className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
              onChange={(event) => setReviewStatus(event.target.value as AdminReportReviewStatus)}
              value={reviewStatus}
            >
              {reviewStatuses.map((status) => (
                <option key={status.key} value={status.key}>
                  {status.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1 text-sm font-semibold">
            대상 상태
            <select
              className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
              onChange={(event) => setTargetStatus(event.target.value as OfferStatus | "")}
              value={targetStatus}
            >
              {targetStatuses.map((status) => (
                <option key={status.key || "unchanged"} value={status.key}>
                  {status.label}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1 text-sm font-semibold">
            처리 메모
            <textarea
              className="min-h-20 resize-y rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
              onChange={(event) => setResolutionNote(event.target.value)}
              value={resolutionNote}
            />
          </label>

          {errorMessage ? <p className="text-sm font-semibold text-deal">{errorMessage}</p> : null}

          <button
            className="rounded bg-ink px-3 py-2 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-black/40"
            disabled={isSaving}
            type="submit"
          >
            {isSaving ? "저장 중" : "처리 저장"}
          </button>
        </form>
      </div>
    </article>
  );
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
