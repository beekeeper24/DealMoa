import type {
  AuctionSearchItem,
  DealSearchItem,
  ProductSearchItem,
  SearchErrorResponse,
  SearchResponse,
  SearchTab
} from "./types";

export type SearchRequest = {
  query: string;
  limit?: number;
  cursor?: string | null;
};

export class SearchApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: SearchErrorResponse["error"]) {
    super(response.message);
    this.name = "SearchApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
}

export async function searchProducts(
  request: SearchRequest
): Promise<SearchResponse<ProductSearchItem>> {
  return search("products", request);
}

export async function searchDeals(
  request: SearchRequest
): Promise<SearchResponse<DealSearchItem>> {
  return search("deals", request);
}

export async function searchAuctions(
  request: SearchRequest
): Promise<SearchResponse<AuctionSearchItem>> {
  return search("auctions", request);
}

async function search<T>(
  tab: SearchTab,
  { query, limit = 20, cursor }: SearchRequest
): Promise<SearchResponse<T>> {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit)
  });
  if (cursor) {
    params.set("cursor", cursor);
  }

  const response = await fetch(`${getApiBaseUrl()}/search/${tab}?${params.toString()}`, {
    headers: { Accept: "application/json" }
  });
  const body = await response.json();

  if (!response.ok) {
    if (isSearchErrorResponse(body)) {
      throw new SearchApiError(body.error);
    }
    throw new Error("검색 요청에 실패했습니다.");
  }

  return body as SearchResponse<T>;
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isSearchErrorResponse(value: unknown): value is SearchErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as SearchErrorResponse).error.code === "string" &&
    typeof (value as SearchErrorResponse).error.message === "string"
  );
}
