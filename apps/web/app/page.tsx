import { getProductTabs } from "@/app-label";

export default function Home() {
  const tabs = getProductTabs();

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-5 py-4">
          <div className="text-xl font-bold">DealMoa</div>
          <div className="flex flex-1 items-center rounded-md border border-black/15 bg-paper px-3 py-2">
            <input
              aria-label="검색어"
              className="w-full bg-transparent text-sm outline-none"
              placeholder="상품명, 브랜드, 모델명으로 검색"
            />
            <button className="rounded bg-ink px-3 py-1.5 text-sm font-semibold text-white">검색</button>
          </div>
          <button className="rounded border border-signal px-3 py-1.5 text-sm font-semibold text-signal">
            AI 검색
          </button>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-6 px-5 py-8 lg:grid-cols-[1fr_320px]">
        <div>
          <p className="text-sm font-semibold text-signal">검색 중심 커머스</p>
          <h1 className="mt-2 text-3xl font-bold">핫딜과 경매를 상품 기준으로 모아봅니다.</h1>
          <div className="mt-6 flex gap-2">
            {tabs.map((tab) => (
              <span key={tab} className="rounded border border-black/10 bg-white px-3 py-2 text-sm">
                {tab}
              </span>
            ))}
          </div>
        </div>
        <aside className="rounded-md border border-black/10 bg-white p-4">
          <h2 className="text-base font-bold">오늘의 골격</h2>
          <p className="mt-2 text-sm leading-6 text-black/65">
            첫 PR은 검색, 랭킹, OAuth 구현 전에 모노레포 런타임과 품질 검사 흐름을 고정합니다.
          </p>
        </aside>
      </section>
    </main>
  );
}
