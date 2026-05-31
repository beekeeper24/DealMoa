"use client";

import Link from "next/link";
import React, { FormEvent, useEffect, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";
import { FavoriteButton } from "../favorites/FavoriteButton";

import {
  createVerifiedReview,
  DetailApiError,
  getProduct,
  listProductAuctions,
  listProductDeals,
  listProductPriceHistory,
  listProductVerifiedReviews
} from "./api";
import { DetailShell, formatCurrency, specsEntries, statusLabel } from "./DetailShell";
import type {
  AuctionDetail,
  DealDetail,
  PriceHistorySnapshot,
  ProductDetail,
  PublicVerifiedReview,
  VerifiedReview
} from "./types";

type ProductDetailState = {
  auctions: AuctionDetail[];
  deals: DealDetail[];
  priceHistory: PriceHistorySnapshot[];
  product: ProductDetail;
  verifiedReviews: PublicVerifiedReview[];
};

export function ProductDetailPage({ productId }: { productId: string }) {
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;
  const [state, setState] = useState<ProductDetailState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadProduct() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const [product, dealsPage, auctionsPage, priceHistoryPage, verifiedReviewsPage] =
          await Promise.all([
            getProduct(productId),
            listProductDeals(productId),
            listProductAuctions(productId),
            listProductPriceHistory(productId),
            listProductVerifiedReviews(productId)
          ]);
        if (isCurrent) {
          setState({
            auctions: auctionsPage.items,
            deals: dealsPage.items,
            priceHistory: priceHistoryPage.items,
            product,
            verifiedReviews: verifiedReviewsPage.items
          });
        }
      } catch (error) {
        if (isCurrent) {
          setErrorMessage(
            error instanceof DetailApiError ? error.message : "상품 상세를 불러오지 못했습니다."
          );
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    void loadProduct();
    return () => {
      isCurrent = false;
    };
  }, [productId]);

  return (
    <DetailShell>
      <section className="mx-auto max-w-6xl px-5 py-8">
        {isLoading ? <DetailMessage>상품 상세를 불러오는 중</DetailMessage> : null}
        {errorMessage ? <DetailError>{errorMessage}</DetailError> : null}
        {state ? (
          <article className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <div>
              <div className="flex flex-col gap-4 border-b border-black/10 pb-6 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h1 className="text-3xl font-bold">{state.product.name}</h1>
                  <p className="mt-2 text-sm text-black/65">
                    {[state.product.brand, state.product.modelName, state.product.category]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
                <FavoriteButton
                  accessToken={accessToken}
                  targetId={state.product.id}
                  targetType="products"
                />
              </div>
              <section className="mt-6">
                <h2 className="text-lg font-bold">스펙</h2>
                {specsEntries(state.product.specs).length > 0 ? (
                  <ul className="mt-3 grid gap-2 text-sm text-black/70">
                    {specsEntries(state.product.specs).map((spec) => (
                      <li className="rounded border border-black/10 bg-white px-3 py-2" key={spec}>
                        {spec}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-black/60">등록된 스펙이 없습니다.</p>
                )}
              </section>
              <PriceHistoryList items={state.priceHistory} />
              <VerifiedReviewList items={state.verifiedReviews} />
            </div>

            <aside className="space-y-4">
              <OfferList
                emptyMessage="등록된 핫딜이 없습니다."
                items={state.deals}
                title="현재 핫딜"
                type="deal"
              />
              <OfferList
                emptyMessage="등록된 경매가 없습니다."
                items={state.auctions}
                title="현재 경매"
                type="auction"
              />
              <VerifiedReviewForm
                accessToken={accessToken}
                onCreated={(review) =>
                  review.status === "approved"
                    ? setState((current) =>
                        current
                          ? {
                              ...current,
                              verifiedReviews: [review, ...current.verifiedReviews]
                            }
                          : current
                      )
                    : undefined
                }
                productId={state.product.id}
              />
            </aside>
          </article>
        ) : null}
      </section>
    </DetailShell>
  );
}

function PriceHistoryList({ items }: { items: PriceHistorySnapshot[] }) {
  return (
    <section className="mt-6">
      <h2 className="text-lg font-bold">가격 이력</h2>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-black/60">기록된 가격 이력이 없습니다.</p>
      ) : null}
      <ul className="mt-3 grid gap-2">
        {items.map((item) => (
          <li className="rounded border border-black/10 bg-white px-3 py-2 text-sm" key={item.id}>
            <div className="flex items-center justify-between gap-3">
              <span className="font-semibold text-deal">
                {formatCurrency(item.price, item.currency)}
              </span>
              <span className="text-xs text-black/55">
                {item.sourceType === "deal" ? "핫딜" : "경매"}
              </span>
            </div>
            <p className="mt-1 text-xs text-black/55">{formatDate(item.observedAt)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function VerifiedReviewList({ items }: { items: PublicVerifiedReview[] }) {
  return (
    <section className="mt-6">
      <h2 className="text-lg font-bold">구매 인증 후기</h2>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-black/60">승인된 구매 인증 후기가 없습니다.</p>
      ) : null}
      <ul className="mt-3 grid gap-3">
        {items.map((item) => (
          <li className="rounded border border-black/10 bg-white p-4" key={item.id}>
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-bold">{item.title}</h3>
              <span className="text-xs font-semibold text-signal">평점 {item.rating}/5</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-black/70">{item.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function VerifiedReviewForm({
  accessToken,
  onCreated,
  productId
}: {
  accessToken?: string;
  onCreated: (review: VerifiedReview) => void;
  productId: string;
}) {
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [proofReference, setProofReference] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    setMessage(null);
    setErrorMessage(null);
    try {
      const review = await createVerifiedReview({
        accessToken,
        body,
        productId,
        proofReference,
        proofType: "receipt",
        rating,
        title
      });
      setMessage("인증 후기가 접수되었습니다. 관리자 승인 후 공개됩니다.");
      setTitle("");
      setBody("");
      setProofReference("");
      setRating(5);
      onCreated(review);
    } catch (error) {
      setErrorMessage(
        error instanceof DetailApiError ? error.message : "인증 후기 접수에 실패했습니다."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      aria-label="구매 인증 후기"
      className="rounded-md border border-black/10 bg-white p-4"
      onSubmit={submitReview}
    >
      <h2 className="text-base font-bold">구매 인증 후기</h2>
      {!accessToken ? (
        <p className="mt-3 text-sm text-black/60">로그인 후 인증 후기를 제출할 수 있습니다.</p>
      ) : null}
      <label className="mt-3 grid gap-1 text-sm font-semibold">
        평점
        <select
          className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
          disabled={!accessToken || isSubmitting}
          onChange={(event) => setRating(Number(event.target.value))}
          value={rating}
        >
          {[5, 4, 3, 2, 1].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>
      <label className="mt-3 grid gap-1 text-sm font-semibold">
        제목
        <input
          className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
          disabled={!accessToken || isSubmitting}
          onChange={(event) => setTitle(event.target.value)}
          value={title}
        />
      </label>
      <label className="mt-3 grid gap-1 text-sm font-semibold">
        후기
        <textarea
          className="min-h-20 rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
          disabled={!accessToken || isSubmitting}
          onChange={(event) => setBody(event.target.value)}
          value={body}
        />
      </label>
      <label className="mt-3 grid gap-1 text-sm font-semibold">
        구매 증빙 번호
        <input
          className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
          disabled={!accessToken || isSubmitting}
          onChange={(event) => setProofReference(event.target.value)}
          value={proofReference}
        />
      </label>
      {message ? <p className="mt-3 text-sm font-semibold text-signal">{message}</p> : null}
      {errorMessage ? <p className="mt-3 text-sm font-semibold text-deal">{errorMessage}</p> : null}
      <button
        className="mt-4 rounded bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-black/40"
        disabled={!accessToken || isSubmitting || !title.trim() || !body.trim()}
        type="submit"
      >
        {isSubmitting ? "접수 중" : "후기 제출"}
      </button>
    </form>
  );
}

function OfferList({
  emptyMessage,
  items,
  title,
  type
}: {
  emptyMessage: string;
  items: Array<AuctionDetail | DealDetail>;
  title: string;
  type: "auction" | "deal";
}) {
  return (
    <section className="rounded-md border border-black/10 bg-white p-4">
      <h2 className="text-base font-bold">{title}</h2>
      {items.length === 0 ? <p className="mt-3 text-sm text-black/60">{emptyMessage}</p> : null}
      <ul className="mt-3 space-y-3">
        {items.map((item) => (
          <li className="border-t border-black/10 pt-3 first:border-t-0 first:pt-0" key={item.id}>
            <Link
              className="text-sm font-bold transition hover:text-signal"
              href={type === "deal" ? `/deals/${item.id}` : `/auctions/${item.id}`}
            >
              {item.title}
            </Link>
            <p className="mt-1 text-xs text-black/60">{item.seller ?? "판매처 미상"}</p>
            <p className="mt-2 text-sm font-semibold text-deal">
              {type === "deal"
                ? formatCurrency((item as DealDetail).salePrice, item.currency)
                : `${formatCurrency((item as AuctionDetail).currentPrice, item.currency)} · 입찰 ${
                    (item as AuctionDetail).bidCount
                  }회`}
            </p>
            <p className="mt-1 text-xs text-black/50">{statusLabel(item.status)}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function DetailMessage({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
      {children}
    </p>
  );
}

function DetailError({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-md border border-deal/30 bg-white px-4 py-6 text-sm font-semibold text-deal">
      {children}
    </p>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
