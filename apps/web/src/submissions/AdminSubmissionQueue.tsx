"use client";

import Link from "next/link";
import React, { FormEvent, ReactNode, useEffect, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";

import {
  listAdminSubmissions,
  listSubmissionProductMatches,
  reviewSubmission,
  SubmissionApiError
} from "./api";
import type { ProductMatch, Submission, SubmissionReviewAction, SubmissionStatus } from "./types";

const statuses: Array<{ key: SubmissionStatus; label: string }> = [
  { key: "pending_review", label: "검토 대기" },
  { key: "approved", label: "승인" },
  { key: "rejected", label: "거절" }
];

export function AdminSubmissionQueue() {
  const authSession = useAuthSession();
  const [activeStatus, setActiveStatus] = useState<SubmissionStatus>("pending_review");
  const [items, setItems] = useState<Submission[]>([]);
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
    void fetchSubmissions({ append: false, cursor: null, status: activeStatus, token: accessToken });
  }, [accessToken, activeStatus]);

  async function fetchSubmissions(request: {
    append: boolean;
    cursor: string | null;
    status: SubmissionStatus;
    token: string;
  }) {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const page = await listAdminSubmissions({
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
        error instanceof SubmissionApiError
          ? error.message
          : "관리자 제보 목록을 불러오지 못했습니다."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleReview(request: {
    action: SubmissionReviewAction;
    resolutionNote: string;
    submissionId: string;
    targetProductId?: string;
  }) {
    if (!accessToken) {
      return;
    }
    const reviewed = await reviewSubmission({ accessToken, ...request });
    setItems((current) => {
      if (reviewed.status !== activeStatus) {
        return current.filter((item) => item.id !== reviewed.id);
      }
      return current.map((item) => (item.id === reviewed.id ? reviewed : item));
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
            <h1 className="text-3xl font-bold">제보 검토</h1>
            <p className="mt-2 text-sm leading-6 text-black/65">
              AI mock 검토 결과를 확인하고 승인할 때만 상품과 딜/경매로 발행합니다.
            </p>
          </div>
          <Link
            className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
            href="/admin"
          >
            신고 검토
          </Link>
        </div>

        <div aria-label="제보 상태" className="mt-6 flex gap-2" role="tablist">
          {statuses.map((status) => (
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
              제보 목록을 불러오는 중
            </p>
          ) : null}
          {!isLoading && !errorMessage && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              표시할 제보가 없습니다.
            </p>
          ) : null}
          {items.map((submission) => (
            <SubmissionCard
              accessToken={accessToken}
              key={submission.id}
              onReview={handleReview}
              submission={submission}
            />
          ))}
        </div>
        {nextCursor ? (
          <button
            className="mt-4 rounded border border-black/15 bg-white px-4 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            onClick={() =>
              accessToken
                ? void fetchSubmissions({
                    append: true,
                    cursor: nextCursor,
                    status: activeStatus,
                    token: accessToken
                  })
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

function SubmissionCard({
  accessToken,
  onReview,
  submission
}: {
  accessToken?: string;
  onReview: (request: {
    action: SubmissionReviewAction;
    resolutionNote: string;
    submissionId: string;
    targetProductId?: string;
  }) => Promise<void>;
  submission: Submission;
}) {
  const [action, setAction] = useState<SubmissionReviewAction>("approve");
  const [resolutionNote, setResolutionNote] = useState("");
  const [matches, setMatches] = useState<ProductMatch[]>([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingMatches, setIsLoadingMatches] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken || submission.status !== "pending_review") {
      return;
    }
    const token = accessToken;
    let isCurrent = true;

    async function fetchMatches() {
      setIsLoadingMatches(true);
      try {
        const page = await listSubmissionProductMatches({
          accessToken: token,
          submissionId: submission.id
        });
        if (isCurrent) {
          setMatches(page.items);
          setSelectedProductId(page.items[0]?.productId ?? "");
        }
      } catch {
        if (isCurrent) {
          setMatches([]);
          setSelectedProductId("");
        }
      } finally {
        if (isCurrent) {
          setIsLoadingMatches(false);
        }
      }
    }

    void fetchMatches();
    return () => {
      isCurrent = false;
    };
  }, [accessToken, submission.id, submission.status]);

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    try {
      await onReview({
        action,
        resolutionNote,
        submissionId: submission.id,
        targetProductId: action === "approve" ? selectedProductId || undefined : undefined
      });
    } catch (error) {
      setErrorMessage(
        error instanceof SubmissionApiError ? error.message : "제보 처리 저장에 실패했습니다."
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <article
      aria-label={`${submission.title} 제보`}
      className="rounded-md border border-black/10 bg-white p-4"
    >
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-signal">
              {submission.offerType === "deal" ? "핫딜" : "경매"}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {submission.status}
            </span>
          </div>
          <h2 className="mt-3 text-lg font-bold">{submission.title}</h2>
          <p className="mt-1 text-sm text-black/65">
            {submission.productName} · {submission.seller ?? "판매처 미상"}
          </p>
          <p className="mt-3 text-sm font-semibold text-deal">
            {submission.offerType === "deal"
              ? formatCurrency(submission.salePrice ?? 0)
              : formatCurrency(submission.currentPrice ?? 0)}
          </p>
          <p className="mt-3 text-sm text-black/70">{submission.aiReason}</p>
          <a
            className="mt-3 inline-block text-sm font-semibold text-signal underline-offset-4 hover:underline"
            href={submission.sourceUrl}
            rel="noreferrer"
            target="_blank"
          >
            원문 열기
          </a>
        </div>

        {submission.status === "pending_review" ? (
          <form className="grid gap-3" onSubmit={submitReview}>
            <section className="rounded border border-black/10 bg-paper p-3">
              <h3 className="text-sm font-bold">상품 매칭 후보</h3>
              {isLoadingMatches ? (
                <p className="mt-2 text-xs text-black/60">후보 조회 중</p>
              ) : null}
              {!isLoadingMatches && matches.length === 0 ? (
                <p className="mt-2 text-xs text-black/60">추천할 기존 상품이 없습니다.</p>
              ) : null}
              {matches.length > 0 ? (
                <div className="mt-2 grid gap-2">
                  <label className="flex items-start gap-2 text-sm">
                    <input
                      checked={selectedProductId === ""}
                      className="mt-1"
                      name={`product-match-${submission.id}`}
                      onChange={() => setSelectedProductId("")}
                      type="radio"
                    />
                    <span>
                      <span className="font-semibold">새 상품으로 발행</span>
                    </span>
                  </label>
                  {matches.map((match) => (
                    <label className="flex items-start gap-2 text-sm" key={match.productId}>
                      <input
                        checked={selectedProductId === match.productId}
                        className="mt-1"
                        name={`product-match-${submission.id}`}
                        onChange={() => setSelectedProductId(match.productId)}
                        type="radio"
                      />
                      <span>
                        <span className="font-semibold">{match.name}</span>
                        <span className="ml-2 text-xs text-signal">점수 {match.score}</span>
                        <span className="block text-xs text-black/55">
                          {[match.brand, match.modelName, match.category].filter(Boolean).join(" · ")}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              ) : null}
            </section>
            <label className="grid gap-1 text-sm font-semibold">
              처리
              <select
                className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
                onChange={(event) => setAction(event.target.value as SubmissionReviewAction)}
                value={action}
              >
                <option value="approve">승인</option>
                <option value="reject">거절</option>
              </select>
            </label>
            <label className="grid gap-1 text-sm font-semibold">
              처리 메모
              <textarea
                className="min-h-20 rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
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
              {isSaving ? "저장 중" : "제보 처리"}
            </button>
          </form>
        ) : null}
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

function formatCurrency(value: number) {
  return new Intl.NumberFormat("ko-KR", {
    currency: "KRW",
    maximumFractionDigits: 0,
    style: "currency"
  }).format(value);
}
