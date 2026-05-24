import { afterEach, describe, expect, it, vi } from "vitest";

import {
  SearchApiError,
  searchAuctions,
  searchDeals,
  searchProducts
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
