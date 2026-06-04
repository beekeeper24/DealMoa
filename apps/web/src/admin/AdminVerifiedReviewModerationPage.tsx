"use client";

import Link from "next/link";
import React, { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";

import { AdminReportApiError, listAdminVerifiedReviews, moderateAdminVerifiedReview } from "./api";
import type {
  AdminVerifiedReview,
  AdminVerifiedReviewModerationAction,
  AdminVerifiedReviewStatus
} from "./types";

const reviewStatuses: Array<{ key: AdminVerifiedReviewStatus; label: string }> = [
  { key: "approved", label: "공개 후기" },
  { key: "hidden", label: "숨김 후기" }
];

export function AdminVerifiedReviewModerationPage() {
  const authSession = useAuthSession();
  const [activeStatus, setActiveStatus] = useState<AdminVerifiedReviewStatus>("approved");
  const [items, setItems] = useState<AdminVerifiedReview[]>([]);
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
    void fetchReviews({
      append: false,
      cursor: null,
      status: activeStatus,
      token: accessToken
    });
  }, [accessToken, activeStatus]);

  const statusLabel = useMemo(
    () => reviewStatuses.find((status) => status.key === activeStatus)?.label ?? activeStatus,
    [activeStatus]
  );

  async function fetchReviews(request: {
    append: boolean;
    cursor: string | null;
    status: AdminVerifiedReviewStatus;
    token: string;
  }) {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const page = await listAdminVerifiedReviews({
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
          : "인증 후기 목록을 불러오지 못했습니다."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function loadMore() {
    if (!accessToken || !nextCursor || isLoading) {
      return;
    }
    await fetchReviews({
      append: true,
      cursor: nextCursor,
      status: activeStatus,
      token: accessToken
    });
  }

  async function handleModeration(request: {
    action: AdminVerifiedReviewModerationAction;
    resolutionNote: string;
    reviewId: string;
  }) {
    if (!accessToken) {
      return;
    }
    const moderated = await moderateAdminVerifiedReview({
      accessToken,
      action: request.action,
      reviewId: request.reviewId,
      resolutionNote: request.resolutionNote
    });
    setItems((current) => {
      if (moderated.status !== activeStatus) {
        return current.filter((item) => item.id !== moderated.id);
      }
      return current.map((item) => (item.id === moderated.id ? moderated : item));
    });
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
            <h1 className="text-3xl font-bold">인증 후기 검수</h1>
            <p className="mt-2 text-sm leading-6 text-black/65">
              자동 공개된 구매 인증 후기를 사후 검수합니다. 공개 증빙 원문은 관리자 화면에서만
              확인합니다.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-signal">
              {statusLabel} {items.length}건
            </p>
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
            <Link
              className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
              href="/admin/discussions"
            >
              토론 검토
            </Link>
            <Link
              className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
              href="/admin/crawler-runs"
            >
              크롤러 로그
            </Link>
          </div>
        </div>

        <div aria-label="인증 후기 상태" className="mt-6 flex gap-2" role="tablist">
          {reviewStatuses.map((status) => (
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
              인증 후기를 불러오는 중
            </p>
          ) : null}

          {!isLoading && !errorMessage && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              표시할 인증 후기가 없습니다.
            </p>
          ) : null}

          {items.map((review) => (
            <VerifiedReviewModerationCard
              key={review.id}
              onModerate={handleModeration}
              review={review}
            />
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

function VerifiedReviewModerationCard({
  onModerate,
  review
}: {
  onModerate: (request: {
    action: AdminVerifiedReviewModerationAction;
    resolutionNote: string;
    reviewId: string;
  }) => Promise<void>;
  review: AdminVerifiedReview;
}) {
  const [resolutionNote, setResolutionNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const action: AdminVerifiedReviewModerationAction =
    review.status === "approved" ? "hide" : "restore";
  const buttonLabel = action === "hide" ? "숨김 처리" : "복구";

  async function submitModeration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    try {
      await onModerate({
        action,
        resolutionNote,
        reviewId: review.id
      });
    } catch (error) {
      setErrorMessage(
        error instanceof AdminReportApiError
          ? error.message
          : "인증 후기 처리 저장에 실패했습니다."
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <article
      aria-label={`${review.title} 인증 후기`}
      className="rounded-md border border-black/10 bg-white p-4 transition hover:border-signal"
    >
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-signal">
              {review.status}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {review.rating}점
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-deal">
              {review.riskLevel}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {review.productId}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {review.userId}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {formatDateTime(review.createdAt)}
            </span>
          </div>
          <h2 className="mt-3 text-lg font-bold">{review.title}</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-black/75">
            {review.body}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {review.proofType}
            </span>
            {review.proofReference ? (
              <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
                {review.proofReference}
              </span>
            ) : null}
            {review.aiDecision ? (
              <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
                {review.aiDecision}
              </span>
            ) : null}
          </div>
          {review.riskReasons.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {review.riskReasons.map((reason) => (
                <span className="rounded bg-paper px-2 py-1 text-xs font-semibold" key={reason}>
                  {reason}
                </span>
              ))}
            </div>
          ) : null}
          {review.aiReason ? (
            <p className="mt-3 rounded border border-black/10 bg-paper px-3 py-2 text-sm text-black/70">
              {review.aiReason}
            </p>
          ) : null}
          {review.resolutionNote ? (
            <p className="mt-3 rounded border border-black/10 bg-paper px-3 py-2 text-sm text-black/70">
              {review.resolutionNote}
            </p>
          ) : null}
        </div>

        <form className="grid content-start gap-3" onSubmit={submitModeration}>
          <label className="grid gap-1 text-sm font-semibold">
            처리 메모
            <textarea
              className="min-h-24 resize-y rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
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
            {isSaving ? "저장 중" : buttonLabel}
          </button>
        </form>
      </div>
    </article>
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
