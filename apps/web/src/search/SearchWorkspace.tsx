"use client";

import Link from "next/link";
import React, { FormEvent, useMemo, useState } from "react";

import {
  SearchApiError,
  searchAuctions,
  searchDeals,
  searchProducts
} from "./api";
import type {
  AuctionSearchItem,
  DealSearchItem,
  ProductSearchItem,
  SearchItemByTab,
  SearchResponse,
  SearchTab
} from "./types";
import { AuthStatus } from "../auth/AuthStatus";
import { useAuthSession } from "../auth/useAuthSession";
import { FavoriteButton } from "../favorites/FavoriteButton";
import { NotificationCenter } from "../notifications/NotificationCenter";

type SearchState = {
  items: SearchItemByTab[SearchTab][];
  nextCursor: string | null;
  hasSearched: boolean;
};

const tabs: { key: SearchTab; label: string }[] = [
  { key: "products", label: "상품" },
  { key: "deals", label: "핫딜" },
  { key: "auctions", label: "경매" }
];

const initialSearchState: SearchState = {
  items: [],
  nextCursor: null,
  hasSearched: false
};

export function SearchWorkspace() {
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState<SearchTab>("products");
  const [results, setResults] = useState<Record<SearchTab, SearchState>>({
    products: initialSearchState,
    deals: initialSearchState,
    auctions: initialSearchState
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const authSession = useAuthSession();
  const accessToken =
    authSession.status === "authenticated" ? authSession.accessToken : undefined;

  const activeState = results[activeTab];
  const trimmedQuery = query.trim();
  const resultCountLabel = useMemo(() => {
    if (!activeState.hasSearched) {
      return "검색 전";
    }
    return `${activeState.items.length}개 결과`;
  }, [activeState.hasSearched, activeState.items.length]);

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runSearch(activeTab, { append: false });
  }

  async function selectTab(nextTab: SearchTab) {
    setActiveTab(nextTab);
    setErrorMessage(null);
    if (trimmedQuery && !results[nextTab].hasSearched) {
      await runSearch(nextTab, { append: false });
    }
  }

  async function loadMore() {
    await runSearch(activeTab, { append: true });
  }

  async function runSearch(tab: SearchTab, { append }: { append: boolean }) {
    if (!trimmedQuery || isLoading) {
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const page = await fetchSearchPage(tab, {
        query: trimmedQuery,
        cursor: append ? results[tab].nextCursor : null
      });
      setResults((current) => ({
        ...current,
        [tab]: {
          items: append ? [...current[tab].items, ...page.items] : page.items,
          nextCursor: page.nextCursor,
          hasSearched: true
        }
      }));
    } catch (error) {
      setErrorMessage(
        error instanceof SearchApiError ? error.message : "검색 요청에 실패했습니다."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-4 lg:flex-row lg:items-center">
          <div>
            <div className="text-xl font-bold">DealMoa</div>
            <p className="text-xs font-semibold text-signal">검색 중심 커머스</p>
          </div>
          <form
            className="flex flex-1 items-center rounded-md border border-black/15 bg-paper px-3 py-2 focus-within:border-signal"
            onSubmit={submitSearch}
          >
            <input
              aria-label="검색어"
              className="w-full bg-transparent text-sm outline-none"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="상품명, 브랜드, 모델명으로 검색"
              type="search"
              value={query}
            />
            <button
              className="min-w-16 rounded bg-ink px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-black disabled:cursor-not-allowed disabled:bg-black/40"
              disabled={isLoading || !trimmedQuery}
              type="submit"
            >
              {isLoading ? "검색 중" : "검색"}
            </button>
          </form>
          <button
            className="rounded border border-signal px-3 py-1.5 text-sm font-semibold text-signal transition hover:bg-signal hover:text-white"
            type="button"
          >
            AI 검색
          </button>
          {authSession.session?.user.role === "ADMIN" ? (
            <Link
              className="rounded border border-black/15 bg-white px-3 py-1.5 text-sm font-semibold transition hover:border-signal hover:text-signal"
              href="/admin"
            >
              관리자
            </Link>
          ) : null}
          <NotificationCenter accessToken={accessToken} />
          <AuthStatus />
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-6 px-5 py-8 lg:grid-cols-[1fr_300px]">
        <div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold">검색 결과</h1>
              <p className="mt-2 text-sm leading-6 text-black/65">
                상품 기준으로 핫딜과 경매를 나눠 확인합니다.
              </p>
            </div>
            <p className="text-sm font-semibold text-signal">{resultCountLabel}</p>
          </div>

          <div aria-label="검색 결과 유형" className="mt-6 flex gap-2" role="tablist">
            {tabs.map((tab) => (
              <button
                aria-selected={activeTab === tab.key}
                className="rounded border border-black/10 bg-white px-3 py-2 text-sm font-semibold transition hover:border-signal aria-selected:border-signal aria-selected:bg-signal aria-selected:text-white"
                key={tab.key}
                onClick={() => void selectTab(tab.key)}
                role="tab"
                type="button"
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-6">
            {errorMessage ? (
              <p className="rounded-md border border-deal/30 bg-white px-4 py-3 text-sm font-semibold text-deal">
                {errorMessage}
              </p>
            ) : null}

            <SearchResults accessToken={accessToken} state={activeState} tab={activeTab} />

            {activeState.nextCursor ? (
              <button
                className="mt-4 rounded border border-black/15 bg-white px-4 py-2 text-sm font-semibold transition hover:border-signal hover:text-signal disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isLoading}
                onClick={() => void loadMore()}
                type="button"
              >
                더보기
              </button>
            ) : null}
          </div>
        </div>

        <aside className="border-l border-black/10 pl-5">
          <h2 className="text-base font-bold">검색 기준</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div>
              <dt className="font-semibold text-signal">상품</dt>
              <dd className="mt-1 text-black/65">상품명, 브랜드, 모델명, 카테고리, 스펙</dd>
            </div>
            <div>
              <dt className="font-semibold text-signal">핫딜</dt>
              <dd className="mt-1 text-black/65">딜 제목, 판매처, 가격, 상태</dd>
            </div>
            <div>
              <dt className="font-semibold text-signal">경매</dt>
              <dd className="mt-1 text-black/65">경매 제목, 판매처, 현재가, 입찰 수</dd>
            </div>
          </dl>
        </aside>
      </section>
    </main>
  );
}

async function fetchSearchPage(
  tab: SearchTab,
  request: { query: string; cursor: string | null }
): Promise<SearchResponse<SearchItemByTab[SearchTab]>> {
  if (tab === "products") {
    return searchProducts(request);
  }
  if (tab === "deals") {
    return searchDeals(request);
  }
  return searchAuctions(request);
}

function SearchResults({
  accessToken,
  state,
  tab
}: {
  accessToken?: string;
  state: SearchState;
  tab: SearchTab;
}) {
  if (!state.hasSearched) {
    return (
      <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
        검색어를 입력하면 상품 결과부터 확인합니다.
      </p>
    );
  }

  if (state.items.length === 0) {
    return (
      <p className="rounded-md border border-black/10 bg-white px-4 py-6 text-sm text-black/65">
        검색 결과가 없습니다.
      </p>
    );
  }

  return (
    <ul aria-label="검색 결과" className="space-y-3" role="list">
      {state.items.map((item) => (
        <li
          className="rounded-md border border-black/10 bg-white p-4 transition hover:border-signal"
          key={`${tab}-${item.id}`}
        >
          {tab === "products" ? (
            <ProductResult accessToken={accessToken} item={item as ProductSearchItem} />
          ) : tab === "deals" ? (
            <DealResult accessToken={accessToken} item={item as DealSearchItem} />
          ) : (
            <AuctionResult accessToken={accessToken} item={item as AuctionSearchItem} />
          )}
        </li>
      ))}
    </ul>
  );
}

function ProductResult({ accessToken, item }: { accessToken?: string; item: ProductSearchItem }) {
  return (
    <article>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-bold">
            <Link className="transition hover:text-signal" href={`/products/${item.id}`}>
              {item.name}
            </Link>
          </h3>
          <p className="mt-1 text-sm text-black/65">
            {[item.brand, item.modelName].filter(Boolean).join(" · ")}
          </p>
        </div>
        <div className="flex items-start gap-2">
          <Score value={item.score} />
          <FavoriteButton
            accessToken={accessToken}
            targetId={item.id}
            targetType="products"
          />
        </div>
      </div>
      {item.specsText ? <p className="mt-3 text-sm text-black/60">{item.specsText}</p> : null}
    </article>
  );
}

function DealResult({ accessToken, item }: { accessToken?: string; item: DealSearchItem }) {
  return (
    <article>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-bold">
            <Link className="transition hover:text-signal" href={`/deals/${item.id}`}>
              {item.title}
            </Link>
          </h3>
          <p className="mt-1 text-sm text-black/65">{item.seller ?? "판매처 미상"}</p>
        </div>
        <div className="flex items-start gap-2">
          <Score value={item.score} />
          <FavoriteButton accessToken={accessToken} targetId={item.id} targetType="deals" />
        </div>
      </div>
      <p className="mt-3 text-sm font-semibold text-deal">
        {formatCurrency(item.salePrice, item.currency)}
      </p>
    </article>
  );
}

function AuctionResult({ accessToken, item }: { accessToken?: string; item: AuctionSearchItem }) {
  return (
    <article>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-bold">
            <Link className="transition hover:text-signal" href={`/auctions/${item.id}`}>
              {item.title}
            </Link>
          </h3>
          <p className="mt-1 text-sm text-black/65">{item.seller ?? "판매처 미상"}</p>
        </div>
        <div className="flex items-start gap-2">
          <Score value={item.score} />
          <FavoriteButton
            accessToken={accessToken}
            targetId={item.id}
            targetType="auctions"
          />
        </div>
      </div>
      <p className="mt-3 text-sm font-semibold text-deal">
        {formatCurrency(item.currentPrice, item.currency)} · 입찰 {item.bidCount}회
        {typeof item.uniqueBidderCount === "number" ? ` · 참여 ${item.uniqueBidderCount}명` : ""}
      </p>
    </article>
  );
}

function Score({ value }: { value: number }) {
  return <span className="shrink-0 text-xs font-semibold text-signal">score {value.toFixed(2)}</span>;
}

function formatCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: 0
  }).format(value);
}
