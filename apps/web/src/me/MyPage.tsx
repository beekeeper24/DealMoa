"use client";

import Link from "next/link";
import React, { ReactNode, useEffect, useState } from "react";

import { AuthStatus } from "../auth/AuthStatus";
import { useAuthSession } from "../auth/useAuthSession";
import { listMySubmissions, listMyVerifiedReviews, MyPageApiError } from "./api";
import type { Submission, SubmissionStatus, VerifiedReview } from "./types";

const statusLabels: Record<SubmissionStatus, string> = {
  approved: "승인됨",
  pending_review: "검토 대기",
  rejected: "거절됨"
};

export function MyPage() {
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;
  const [submissionItems, setSubmissionItems] = useState<Submission[]>([]);
  const [submissionNextCursor, setSubmissionNextCursor] = useState<string | null>(null);
  const [isLoadingSubmissions, setIsLoadingSubmissions] = useState(false);
  const [submissionErrorMessage, setSubmissionErrorMessage] = useState<string | null>(null);
  const [reviewItems, setReviewItems] = useState<VerifiedReview[]>([]);
  const [reviewNextCursor, setReviewNextCursor] = useState<string | null>(null);
  const [isLoadingReviews, setIsLoadingReviews] = useState(false);
  const [reviewErrorMessage, setReviewErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      return;
    }
    void fetchSubmissions({ append: false, cursor: null, token: accessToken });
    void fetchVerifiedReviews({ append: false, cursor: null, token: accessToken });
  }, [accessToken]);

  async function fetchSubmissions(request: {
    append: boolean;
    cursor: string | null;
    token: string;
  }) {
    setIsLoadingSubmissions(true);
    setSubmissionErrorMessage(null);
    try {
      const page = await listMySubmissions({
        accessToken: request.token,
        cursor: request.cursor
      });
      setSubmissionItems((current) =>
        request.append ? [...current, ...page.items] : page.items
      );
      setSubmissionNextCursor(page.nextCursor);
    } catch (error) {
      setSubmissionItems((current) => (request.append ? current : []));
      setSubmissionNextCursor(null);
      setSubmissionErrorMessage(
        error instanceof MyPageApiError
          ? error.message
          : "내 제보 이력을 불러오지 못했습니다."
      );
    } finally {
      setIsLoadingSubmissions(false);
    }
  }

  async function fetchVerifiedReviews(request: {
    append: boolean;
    cursor: string | null;
    token: string;
  }) {
    setIsLoadingReviews(true);
    setReviewErrorMessage(null);
    try {
      const page = await listMyVerifiedReviews({
        accessToken: request.token,
        cursor: request.cursor
      });
      setReviewItems((current) => (request.append ? [...current, ...page.items] : page.items));
      setReviewNextCursor(page.nextCursor);
    } catch (error) {
      setReviewItems((current) => (request.append ? current : []));
      setReviewNextCursor(null);
      setReviewErrorMessage(
        error instanceof MyPageApiError
          ? error.message
          : "내 인증 후기 이력을 불러오지 못했습니다."
      );
    } finally {
      setIsLoadingReviews(false);
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
            <p className="mt-2 text-sm leading-6 text-black/65">
              제보와 인증 후기 처리 상태
            </p>
          </div>
          <Link
            className="rounded border border-black/15 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal"
            href="/submit"
          >
            제보하기
          </Link>
        </div>

        <section className="mt-6">
          <h2 className="text-xl font-bold">제보 이력</h2>
          {submissionErrorMessage ? (
            <p className="mt-3 rounded-md border border-deal/30 bg-white px-4 py-3 text-sm font-semibold text-deal">
              {submissionErrorMessage}
            </p>
          ) : null}
          <div className="mt-3 space-y-3">
            {isLoadingSubmissions && submissionItems.length === 0 ? (
              <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
                제보 이력을 불러오는 중
              </p>
            ) : null}
            {!isLoadingSubmissions &&
            !submissionErrorMessage &&
            submissionItems.length === 0 ? (
              <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
                표시할 제보가 없습니다.
              </p>
            ) : null}
            {submissionItems.map((submission) => (
              <SubmissionHistoryCard key={submission.id} submission={submission} />
            ))}
          </div>

          {submissionNextCursor ? (
            <button
              className="mt-4 rounded border border-black/15 bg-white px-4 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoadingSubmissions}
              onClick={() =>
                accessToken
                  ? void fetchSubmissions({
                      append: true,
                      cursor: submissionNextCursor,
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

        <section className="mt-10">
          <h2 className="text-xl font-bold">인증 후기 이력</h2>
          {reviewErrorMessage ? (
            <p className="mt-3 rounded-md border border-deal/30 bg-white px-4 py-3 text-sm font-semibold text-deal">
              {reviewErrorMessage}
            </p>
          ) : null}
          <div className="mt-3 space-y-3">
            {isLoadingReviews && reviewItems.length === 0 ? (
              <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
                인증 후기 이력을 불러오는 중
              </p>
            ) : null}
            {!isLoadingReviews && !reviewErrorMessage && reviewItems.length === 0 ? (
              <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
                표시할 인증 후기가 없습니다.
              </p>
            ) : null}
            {reviewItems.map((review) => (
              <VerifiedReviewHistoryCard key={review.id} review={review} />
            ))}
          </div>

          {reviewNextCursor ? (
            <button
              className="mt-4 rounded border border-black/15 bg-white px-4 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isLoadingReviews}
              onClick={() =>
                accessToken
                  ? void fetchVerifiedReviews({
                      append: true,
                      cursor: reviewNextCursor,
                      token: accessToken
                    })
                  : undefined
              }
              type="button"
            >
              인증 후기 더보기
            </button>
          ) : null}
        </section>
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
          <h3 className="mt-3 text-lg font-bold">{submission.title}</h3>
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

function VerifiedReviewHistoryCard({ review }: { review: VerifiedReview }) {
  return (
    <article
      aria-label={`${review.title} 인증 후기 이력`}
      className="rounded-md border border-black/10 bg-white p-4"
    >
      <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
        <div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold text-signal">
              인증 후기
            </span>
            <span className="rounded bg-paper px-2 py-1 text-xs font-semibold">
              {statusLabels[review.status]}
            </span>
          </div>
          <h3 className="mt-3 text-lg font-bold">{review.title}</h3>
          <p className="mt-1 text-sm font-semibold text-deal">{formatStars(review.rating)}</p>
          <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-black/75">
            {review.body}
          </p>
          {review.aiReason ? (
            <p className="mt-3 text-sm text-black/70">{review.aiReason}</p>
          ) : null}
          {review.resolutionNote ? (
            <p className="mt-2 text-sm font-semibold text-ink">{review.resolutionNote}</p>
          ) : null}
        </div>

        <div className="flex flex-col items-start gap-2 lg:items-end">
          <p className="text-xs font-semibold text-black/50">{formatDate(review.createdAt)}</p>
          <Link
            className="text-sm font-semibold text-signal underline-offset-4 hover:underline"
            href={`/products/${review.productId}`}
          >
            상품 보기
          </Link>
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

function formatStars(rating: number) {
  const filled = Math.max(0, Math.min(5, rating));
  return `${"★".repeat(filled)}${"☆".repeat(5 - filled)}`;
}
