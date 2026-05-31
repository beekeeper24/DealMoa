import { afterEach, describe, expect, it, vi } from "vitest";

import {
  SearchApiError,
  searchAuctions,
  searchDeals,
  searchProducts,
  searchWithAi
} from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("search api client", () => {
  it("requests product search with query, limit, and cursor", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ items: [], nextCursor: "cursor-2" }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://api.test/api/v1");

    const result = await searchProducts({ query: "galaxy", limit: 10, cursor: "cursor-1" });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/api/v1/search/products?q=galaxy&limit=10&cursor=cursor-1",
      { headers: { Accept: "application/json" } }
    );
    expect(result.nextCursor).toBe("cursor-2");
  });

  it("requests deal and auction search endpoints", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(new Response(JSON.stringify({ items: [], nextCursor: null }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }))
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "/api/v1");

    await searchDeals({ query: "launch" });
    await searchAuctions({ query: "sealed" });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/v1/search/deals?q=launch&limit=20",
      { headers: { Accept: "application/json" } }
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/search/auctions?q=sealed&limit=20",
      { headers: { Accept: "application/json" } }
    );
  });

  it("requests AI search with a structured body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          intent: {
            query: "galaxy 100만원 이하",
            normalizedQuery: "galaxy 100만원 이하",
            targetTypes: ["deals"],
            filters: { maxPrice: 1000000 }
          },
          summary: "핫딜 중심으로 1개 후보를 찾았습니다.",
          products: { items: [], nextCursor: null },
          deals: { items: [], nextCursor: null },
          auctions: { items: [], nextCursor: null }
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      )
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "/api/v1");

    const result = await searchWithAi({ query: "galaxy 100만원 이하", limit: 5 });

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/ai/search", {
      body: JSON.stringify({ limit: 5, query: "galaxy 100만원 이하" }),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
    expect(result.intent.filters.maxPrice).toBe(1000000);
  });

  it("throws a typed error when the api returns the common error shape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "SEARCH_UNAVAILABLE",
              message: "검색 서비스를 사용할 수 없습니다.",
              details: {},
              traceId: "req_1"
            }
          }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(searchProducts({ query: "galaxy" })).rejects.toMatchObject({
      name: "SearchApiError",
      code: "SEARCH_UNAVAILABLE",
      message: "검색 서비스를 사용할 수 없습니다."
    } satisfies Partial<SearchApiError>);
  });
});
