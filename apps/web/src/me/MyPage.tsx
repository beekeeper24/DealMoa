"use client";

import Link from "next/link";
import React, { ReactNode, useEffect, useState } from "react";

import { AuthStatus } from "../auth/AuthStatus";
import { useAuthSession } from "../auth/useAuthSession";
import { listMySubmissions, SubmissionApiError } from "../submissions/api";
import type { Submission, SubmissionStatus } from "../submissions/types";

const statusLabels: Record<SubmissionStatus, string> = {
  approved: "승인됨",
  pending_review: "검토 대기",
  rejected: "거절됨"
};

export function MyPage() {
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;
  const [items, setItems] = useState<Submission[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void fetchSubmissions({ append: false, cursor: null, token: accessToken });
  }, [accessToken]);

  async function fetchSubmissions(request: {
    append: boolean;
    cursor: string | null;
    token: string;
  }) {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const page = await listMySubmissions({
        accessToken: request.token,
        cursor: request.cursor
      });
      setItems((current) => (request.append ? [...current, ...page.items] : page.items));
      setNextCursor(page.nextCursor);
    } catch (error) {
      setItems((current) => (request.append ? current : []));
      setNextCursor(null);
      setErrorMessage(
        error instanceof SubmissionApiError
          ? error.message
          : "내 제보 이력을 불러오지 못했습니다."
      );
    } finally {
      setIsLoading(false);
    }
  }

  if (authSession.status === "loading") {
    return <MyPageShell>로그인 상태 확인 중</MyPageShell>;
  }

  if (authSession.status === "anonymous") {
    return <MyPageShell>로그인 후 내 활동을 확인할 수 있습니다.</MyPageShell>;
  }

  return (
    <MyPageShell>
      <section className="mx-auto max-w-6xl px-5 py-8">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">내 활동</h1>
            <p className="mt-2 text-sm leading-6 text-black/65">제보 처리 상태</p>
          </div>
          <Link
            className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
            href="/submit"
          >
            제보하기
          </Link>
        </div>

        {errorMessage ? (
          <p className="mt-6 rounded-md border border-deal/30 bg-white px-4 py-3 text-sm font-semibold text-deal">
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-6 space-y-3">
          {isLoading && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              제보 이력을 불러오는 중
            </p>
          ) : null}
          {!isLoading && !errorMessage && items.length === 0 ? (
            <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
              표시할 제보가 없습니다.
            </p>
          ) : null}
          {items.map((submission) => (
            <SubmissionHistoryCard key={submission.id} submission={submission} />
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
    </MyPageShell>
  );
}

function SubmissionHistoryCard({ submission }: { submission: Submission }) {
  const price =
    submission.offerType === "deal"
      ? submission.salePrice ?? 0
      : submission.currentPrice ?? 0;

  return (
    <article
      aria-label={`${submission.title} 제보 이력`}
      className="rounded-md border border-black/10 bg-white p-4"
    >
      <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
        <div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-signal">
              {submission.offerType === "deal" ? "핫딜" : "경매"}
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {statusLabels[submission.status]}
            </span>
          </div>
          <h2 className="mt-3 text-lg font-bold">{submission.title}</h2>
          <p className="mt-1 text-sm text-black/65">
            {submission.productName} · {submission.seller ?? "판매처 미상"}
          </p>
          <p className="mt-3 text-sm font-semibold text-deal">{formatCurrency(price)}</p>
          <p className="mt-3 text-sm text-black/70">{submission.aiReason}</p>
          {submission.resolutionNote ? (
            <p className="mt-2 text-sm font-semibold text-ink">{submission.resolutionNote}</p>
          ) : null}
        </div>

        <div className="flex flex-col items-start gap-2 lg:items-end">
          <p className="text-xs font-semibold text-black/50">
            {formatDate(submission.createdAt)}
          </p>
          <a
            className="text-sm font-semibold text-signal underline-offset-4 hover:underline"
            href={submission.sourceUrl}
            rel="noreferrer"
            target="_blank"
          >
            원문 열기
          </a>
          {submission.publishedProductId ? (
            <Link
              className="text-sm font-semibold text-signal underline-offset-4 hover:underline"
              href={`/products/${submission.publishedProductId}`}
            >
              발행 상품
            </Link>
          ) : null}
          {submission.publishedOfferId && submission.publishedOfferType ? (
            <Link
              className="text-sm font-semibold text-signal underline-offset-4 hover:underline"
              href={
                submission.publishedOfferType === "deal"
                  ? `/deals/${submission.publishedOfferId}`
                  : `/auctions/${submission.publishedOfferId}`
              }
            >
              {submission.publishedOfferType === "deal" ? "발행 핫딜" : "발행 경매"}
            </Link>
          ) : null}
        </div>
      </div>
    </article>
  );
}

function MyPageShell({ children }: { children: ReactNode }) {
  const isTextOnly = typeof children === "string";
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/">
            <div className="text-xl font-bold">DealMoa</div>
            <p className="text-xs font-semibold text-signal">마이페이지</p>
          </Link>
          <AuthStatus />
        </div>
      </header>
      {isTextOnly ? (
        <section className="mx-auto max-w-6xl px-5 py-8">
          <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium"
  }).format(new Date(value));
}
