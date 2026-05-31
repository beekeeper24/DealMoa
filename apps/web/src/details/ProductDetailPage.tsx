"use client";

import Link from "next/link";
import React, { useEffect, useState } from "react";

import { useAuthSession } from "../auth/useAuthSession";
import { FavoriteButton } from "../favorites/FavoriteButton";

import { DetailApiError, getProduct, listProductAuctions, listProductDeals } from "./api";
import { DetailShell, formatCurrency, specsEntries, statusLabel } from "./DetailShell";
import type { AuctionDetail, DealDetail, ProductDetail } from "./types";

type ProductDetailState = {
  auctions: AuctionDetail[];
  deals: DealDetail[];
  product: ProductDetail;
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
        const [product, dealsPage, auctionsPage] = await Promise.all([
          getProduct(productId),
          listProductDeals(productId),
          listProductAuctions(productId)
        ]);
        if (isCurrent) {
          setState({ auctions: auctionsPage.items, deals: dealsPage.items, product });
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
            </aside>
          </article>
        ) : null}
      </section>
    </DetailShell>
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
