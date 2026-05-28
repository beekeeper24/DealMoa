// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SearchWorkspace } from "../SearchWorkspace";

afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.unstubAllGlobals();
});

function mockSearchResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" }
  });
}

describe("SearchWorkspace", () => {
  it("renders the search shell and empty state before searching", () => {
    render(<SearchWorkspace />);

    expect(screen.getByRole("searchbox", { name: "검색어" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "검색" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Google 로그인" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /알림/ })).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "상품" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("검색어를 입력하면 상품 결과부터 확인합니다.")).toBeInTheDocument();
  });

  it("searches products and renders result rows", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockSearchResponse({
          items: [
            {
              id: "product-1",
              name: "Galaxy S26 Ultra",
              brand: "Samsung",
              modelName: "SM-S260",
              category: "smartphone",
              specsText: "storage 256GB",
              createdAt: "2026-05-25T00:00:00Z",
              updatedAt: "2026-05-25T00:00:00Z",
              score: 2.4
            }
          ],
          nextCursor: null
        })
      )
    );
    render(<SearchWorkspace />);

    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));

    expect(await screen.findByText("Galaxy S26 Ultra")).toBeInTheDocument();
    expect(screen.getByText("Samsung · SM-S260")).toBeInTheDocument();
    expect(screen.getByText("score 2.40")).toBeInTheDocument();
  });

  it("switches tabs and searches deals with the current query", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      mockSearchResponse({
        items: [
          {
            id: "deal-1",
            productId: "product-1",
            title: "Galaxy S26 launch deal",
            sourceUrl: "https://example.com/deals/galaxy-s26",
            seller: "Example Store",
            originalPrice: null,
            salePrice: 1090000,
            currency: "KRW",
            status: "active",
            startedAt: null,
            endedAt: null,
            createdAt: "2026-05-25T00:00:00Z",
            updatedAt: "2026-05-25T00:00:00Z",
            score: 1.1
          }
        ],
        nextCursor: null
      })
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<SearchWorkspace />);

    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("tab", { name: "핫딜" }));

    expect(await screen.findByText("Galaxy S26 launch deal")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/search/deals?q=galaxy&limit=20",
      expect.any(Object)
    );
  });

  it("shows api error messages", async () => {
    const user = userEvent.setup();
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
    render(<SearchWorkspace />);

    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));

    expect(await screen.findByText("검색 서비스를 사용할 수 없습니다.")).toBeInTheDocument();
  });

  it("loads the next page with nextCursor", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        mockSearchResponse({
          items: [
            {
              id: "product-1",
              name: "Galaxy S26",
              brand: "Samsung",
              modelName: "SM-S260",
              category: "smartphone",
              specsText: null,
              createdAt: "2026-05-25T00:00:00Z",
              updatedAt: "2026-05-25T00:00:00Z",
              score: 2
            }
          ],
          nextCursor: "cursor-2"
        })
      )
      .mockResolvedValueOnce(
        mockSearchResponse({
          items: [
            {
              id: "product-2",
              name: "Galaxy S25",
              brand: "Samsung",
              modelName: "SM-S250",
              category: "smartphone",
              specsText: null,
              createdAt: "2026-05-24T00:00:00Z",
              updatedAt: "2026-05-24T00:00:00Z",
              score: 1.5
            }
          ],
          nextCursor: null
        })
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<SearchWorkspace />);

    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));
    const results = await screen.findByRole("list", { name: "검색 결과" });
    await user.click(screen.getByRole("button", { name: "더보기" }));

    expect(within(results).getByText("Galaxy S26")).toBeInTheDocument();
    expect(await within(results).findByText("Galaxy S25")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/search/products?q=galaxy&limit=20&cursor=cursor-2",
      expect.any(Object)
    );
  });

  it("sends favorite requests from logged-in search results", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem(
      "dealmoa.authSession",
      JSON.stringify({
        user: {
          id: "user-1",
          email: "user@example.com",
          nickname: "Deal User",
          role: "USER"
        },
        accessToken: "access-1",
        tokenType: "Bearer"
      })
    );
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(mockSearchResponse({ count: 0 }))
      .mockResolvedValueOnce(
        mockSearchResponse({
          items: [
            {
              id: "product-1",
              name: "Galaxy S26",
              brand: "Samsung",
              modelName: "SM-S260",
              category: "smartphone",
              specsText: null,
              createdAt: "2026-05-25T00:00:00Z",
              updatedAt: "2026-05-25T00:00:00Z",
              score: 2
            }
          ],
          nextCursor: null
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "favorite-1", productId: "product-1" }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<SearchWorkspace />);

    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));
    await user.click(await screen.findByRole("button", { name: "찜하기" }));

    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/me/favorites/products/product-1", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "PUT"
    });
  });
});
