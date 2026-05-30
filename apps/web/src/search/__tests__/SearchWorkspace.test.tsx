// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { renderToString } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
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

function mockAuthErrorResponse(): Response {
  return new Response(
    JSON.stringify({
      error: {
        code: "INVALID_REFRESH_TOKEN",
        message: "로그인이 필요합니다.",
        details: {},
        traceId: "req_1"
      }
    }),
    { status: 401, headers: { "Content-Type": "application/json" } }
  );
}

const authSessionResponse = {
  user: {
    id: "user-1",
    email: "user@example.com",
    nickname: "Deal User",
    role: "USER"
  },
  accessToken: "access-1",
  tokenType: "Bearer"
};

function installFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>
) {
  const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    return Promise.resolve(handler(url, init));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function failUnexpectedFetch(url: string): never {
  throw new Error(`Unexpected fetch: ${url}`);
}

function renderWithAuthProvider(ui: React.ReactElement) {
  return render(<AuthSessionProvider>{ui}</AuthSessionProvider>);
}

describe("SearchWorkspace", () => {
  it("server-renders auth-dependent header controls in a neutral state", () => {
    const markup = renderToString(
      <AuthSessionProvider>
        <SearchWorkspace />
      </AuthSessionProvider>
    );

    expect(markup).toContain("인증 상태 확인 중");
    expect(markup).not.toContain("Google 로그인");
    expect(markup).not.toContain("알림");
  });

  it("renders the search shell and empty state before searching", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return mockAuthErrorResponse();
      }
      return failUnexpectedFetch(url);
    });

    renderWithAuthProvider(<SearchWorkspace />);

    expect(screen.getByRole("searchbox", { name: "검색어" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "검색" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Google 로그인" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /알림/ })).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "상품" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("검색어를 입력하면 상품 결과부터 확인합니다.")).toBeInTheDocument();
  });

  it("searches products and renders result rows", async () => {
    const user = userEvent.setup();
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return mockAuthErrorResponse();
      }
      if (url === "/api/v1/search/products?q=galaxy&limit=20") {
        return mockSearchResponse({
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
        });
      }
      return failUnexpectedFetch(url);
    });
    renderWithAuthProvider(<SearchWorkspace />);

    await screen.findByRole("button", { name: "Google 로그인" });
    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));

    expect(await screen.findByText("Galaxy S26 Ultra")).toBeInTheDocument();
    expect(screen.getByText("Samsung · SM-S260")).toBeInTheDocument();
    expect(screen.getByText("score 2.40")).toBeInTheDocument();
  });

  it("switches tabs and searches deals with the current query", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return mockAuthErrorResponse();
      }
      if (url === "/api/v1/search/deals?q=galaxy&limit=20") {
        return mockSearchResponse({
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
        });
      }
      return failUnexpectedFetch(url);
    });
    renderWithAuthProvider(<SearchWorkspace />);

    await screen.findByRole("button", { name: "Google 로그인" });
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
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return mockAuthErrorResponse();
      }
      if (url === "/api/v1/search/products?q=galaxy&limit=20") {
        return new Response(
          JSON.stringify({
            error: {
              code: "SEARCH_UNAVAILABLE",
              message: "검색 서비스를 사용할 수 없습니다.",
              details: {},
              traceId: "req_1"
            }
          }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        );
      }
      return failUnexpectedFetch(url);
    });
    renderWithAuthProvider(<SearchWorkspace />);

    await screen.findByRole("button", { name: "Google 로그인" });
    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));

    expect(await screen.findByText("검색 서비스를 사용할 수 없습니다.")).toBeInTheDocument();
  });

  it("loads the next page with nextCursor", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return mockAuthErrorResponse();
      }
      if (url === "/api/v1/search/products?q=galaxy&limit=20") {
        return mockSearchResponse({
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
        });
      }
      if (url === "/api/v1/search/products?q=galaxy&limit=20&cursor=cursor-2") {
        return mockSearchResponse({
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
        });
      }
      return failUnexpectedFetch(url);
    });
    renderWithAuthProvider(<SearchWorkspace />);

    await screen.findByRole("button", { name: "Google 로그인" });
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
    const fetchMock = installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return mockSearchResponse(authSessionResponse);
      }
      if (url === "/api/v1/notifications/unread-count") {
        return mockSearchResponse({ count: 0 });
      }
      if (url === "/api/v1/search/products?q=galaxy&limit=20") {
        return mockSearchResponse({
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
        });
      }
      if (url === "/api/v1/me/favorites/products/product-1") {
        return new Response(JSON.stringify({ id: "favorite-1", productId: "product-1" }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      }
      return failUnexpectedFetch(url);
    });
    renderWithAuthProvider(<SearchWorkspace />);

    await screen.findByText("user@example.com");
    await user.type(screen.getByRole("searchbox", { name: "검색어" }), "galaxy");
    await user.click(screen.getByRole("button", { name: "검색" }));
    await user.click(await screen.findByRole("button", { name: "찜하기" }));

    expect(fetchMock).toHaveBeenLastCalledWith("/api/v1/me/favorites/products/product-1", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "PUT"
    });
  });
});
