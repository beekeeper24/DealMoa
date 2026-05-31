"use client";

import Link from "next/link";
import React, { FormEvent, useEffect, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";
import { FavoriteButton } from "../favorites/FavoriteButton";

import { DetailApiError, getAuction, getProduct, placeAuctionBid } from "./api";
import { DetailShell, formatCurrency, statusLabel } from "./DetailShell";
import { OfferReportForm } from "./OfferReportForm";
import type { AuctionDetail, ProductDetail } from "./types";

type AuctionDetailState = {
  auction: AuctionDetail;
  product: ProductDetail;
};

export function AuctionDetailPage({ auctionId }: { auctionId: string }) {
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;
  const [state, setState] = useState<AuctionDetailState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadAuction() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const auction = await getAuction(auctionId);
        const product = await getProduct(auction.productId);
        if (isCurrent) {
          setState({ auction, product });
        }
      } catch (error) {
        if (isCurrent) {
          setErrorMessage(
            error instanceof DetailApiError ? error.message : "경매 상세를 불러오지 못했습니다."
          );
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    void loadAuction();
    return () => {
      isCurrent = false;
    };
  }, [auctionId]);

  return (
    <DetailShell>
      <section className="mx-auto max-w-6xl px-5 py-8">
        {isLoading ? <DetailMessage>경매 상세를 불러오는 중</DetailMessage> : null}
        {errorMessage ? <DetailError>{errorMessage}</DetailError> : null}
        {state ? (
          <article className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <div>
              <div className="flex flex-col gap-4 border-b border-black/10 pb-6 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-signal">경매</p>
                  <h1 className="mt-2 text-3xl font-bold">{state.auction.title}</h1>
                  <p className="mt-2 text-sm text-black/65">
                    {state.auction.seller ?? "판매처 미상"} · {statusLabel(state.auction.status)}
                  </p>
                </div>
                <FavoriteButton
                  accessToken={accessToken}
                  targetId={state.auction.id}
                  targetType="auctions"
                />
              </div>

              <section className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-md border border-black/10 bg-white p-4">
                  <h2 className="text-base font-bold">현재 경매가</h2>
                  <p className="mt-3 text-2xl font-bold text-deal">
                    {formatCurrency(state.auction.currentPrice, state.auction.currency)}
                  </p>
                  <p className="mt-1 text-sm text-black/60">입찰 {state.auction.bidCount}회</p>
                </div>
                <div className="rounded-md border border-black/10 bg-white p-4">
                  <h2 className="text-base font-bold">연결 상품</h2>
                  <Link
                    className="mt-3 block text-sm font-bold transition hover:text-signal"
                    href={`/products/${state.product.id}`}
                  >
                    {state.product.name}
                  </Link>
                  <p className="mt-1 text-sm text-black/60">
                    {[state.product.brand, state.product.modelName].filter(Boolean).join(" · ")}
                  </p>
                </div>
              </section>

              <a
                className="mt-6 inline-flex rounded bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-black"
                href={state.auction.sourceUrl}
                rel="noreferrer"
                target="_blank"
              >
                외부 경매 보기
              </a>
            </div>

            <aside className="space-y-4">
              <AuctionBidForm
                accessToken={accessToken}
                auction={state.auction}
                onAccepted={(amount) =>
                  setState((current) =>
                    current
                      ? {
                          ...current,
                          auction: {
                            ...current.auction,
                            bidCount: current.auction.bidCount + 1,
                            currentPrice: amount
                          }
                        }
                      : current
                  )
                }
              />
              <OfferReportForm
                accessToken={accessToken}
                targetId={state.auction.id}
                targetType="auction"
              />
            </aside>
          </article>
        ) : null}
      </section>
    </DetailShell>
  );
}

function AuctionBidForm({
  accessToken,
  auction,
  onAccepted
}: {
  accessToken?: string;
  auction: AuctionDetail;
  onAccepted: (amount: number) => void;
}) {
  const minimumBid = auction.currentPrice + 1000;
  const [amount, setAmount] = useState(String(minimumBid));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setAmount(String(minimumBid));
  }, [minimumBid]);

  async function submitBid(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken || isSubmitting) {
      return;
    }

    const bidAmount = Number(amount);
    setIsSubmitting(true);
    setMessage(null);
    setErrorMessage(null);
    try {
      const bid = await placeAuctionBid({
        accessToken,
        amount: bidAmount,
        auctionId: auction.id
      });
      onAccepted(bid.amount);
      setMessage("입찰이 접수되었습니다.");
    } catch (error) {
      setErrorMessage(
        error instanceof DetailApiError ? error.message : "입찰 요청에 실패했습니다."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      aria-label="경매 입찰"
      className="rounded-md border border-black/10 bg-white p-4"
      onSubmit={submitBid}
    >
      <h2 className="text-base font-bold">입찰</h2>
      <p className="mt-3 text-sm font-semibold text-deal">
        현재가 {formatCurrency(auction.currentPrice, auction.currency)}
      </p>
      <p className="mt-1 text-xs text-black/60">
        최소 입찰가는 {formatCurrency(minimumBid, auction.currency)}입니다.
      </p>
      <label className="mt-4 grid gap-1 text-sm font-semibold">
        입찰 금액
        <input
          className="rounded border border-black/15 bg-paper px-3 py-2 text-sm font-normal"
          disabled={!accessToken || isSubmitting}
          min={minimumBid}
          onChange={(event) => setAmount(event.target.value)}
          step={1000}
          type="number"
          value={amount}
        />
      </label>
      {!accessToken ? <p className="mt-3 text-sm text-black/60">로그인 후 입찰할 수 있습니다.</p> : null}
      {message ? <p className="mt-3 text-sm font-semibold text-signal">{message}</p> : null}
      {errorMessage ? <p className="mt-3 text-sm font-semibold text-deal">{errorMessage}</p> : null}
      <button
        className="mt-4 rounded bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-black/40"
        disabled={!accessToken || isSubmitting}
        type="submit"
      >
        {isSubmitting ? "입찰 중" : "입찰하기"}
      </button>
    </form>
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
