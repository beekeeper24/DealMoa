"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";
import { FavoriteButton } from "../favorites/FavoriteButton";

import { DetailApiError, getDeal, getProduct } from "./api";
import { DetailShell, formatCurrency, statusLabel } from "./DetailShell";
import { OfferReportForm } from "./OfferReportForm";
import type { DealDetail, ProductDetail } from "./types";

type DealDetailState = {
  deal: DealDetail;
  product: ProductDetail;
};

export function DealDetailPage({ dealId }: { dealId: string }) {
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;
  const [state, setState] = useState<DealDetailState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;

    async function loadDeal() {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const deal = await getDeal(dealId);
        const product = await getProduct(deal.productId);
        if (isCurrent) {
          setState({ deal, product });
        }
      } catch (error) {
        if (isCurrent) {
          setErrorMessage(
            error instanceof DetailApiError ? error.message : "핫딜 상세를 불러오지 못했습니다."
          );
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false);
        }
      }
    }

    void loadDeal();
    return () => {
      isCurrent = false;
    };
  }, [dealId]);

  return (
    <DetailShell>
      <section className="mx-auto max-w-6xl px-5 py-8">
        {isLoading ? <DetailMessage>핫딜 상세를 불러오는 중</DetailMessage> : null}
        {errorMessage ? <DetailError>{errorMessage}</DetailError> : null}
        {state ? (
          <article className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <div>
              <div className="flex flex-col gap-4 border-b border-black/10 pb-6 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-signal">핫딜</p>
                  <h1 className="mt-2 text-3xl font-bold">{state.deal.title}</h1>
                  <p className="mt-2 text-sm text-black/65">
                    {state.deal.seller ?? "판매처 미상"} · {statusLabel(state.deal.status)}
                  </p>
                </div>
                <FavoriteButton
                  accessToken={accessToken}
                  targetId={state.deal.id}
                  targetType="deals"
                />
              </div>

              <section className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="rounded-md border border-black/10 bg-white p-4">
                  <h2 className="text-base font-bold">가격</h2>
                  <p className="mt-3 text-2xl font-bold text-deal">
                    {formatCurrency(state.deal.salePrice, state.deal.currency)}
                  </p>
                  {state.deal.originalPrice !== null ? (
                    <p className="mt-1 text-sm text-black/55 line-through">
                      {formatCurrency(state.deal.originalPrice, state.deal.currency)}
                    </p>
                  ) : null}
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
                href={state.deal.sourceUrl}
                rel="noreferrer"
                target="_blank"
              >
                외부 딜 보기
              </a>
            </div>

            <aside className="space-y-4">
              <OfferReportForm
                accessToken={accessToken}
                targetId={state.deal.id}
                targetType="deal"
              />
            </aside>
          </article>
        ) : null}
      </section>
    </DetailShell>
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
