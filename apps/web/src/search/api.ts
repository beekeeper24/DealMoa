import type {
  AiSearchResponse,
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

export async function searchWithAi(request: {
  query: string;
  limit?: number;
}): Promise<AiSearchResponse> {
  return requestJson<AiSearchResponse>("/ai/search", {
    body: {
      limit: request.limit ?? 5,
      query: request.query
    },
    method: "POST"
  });
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

  return requestJson<SearchResponse<T>>(`/search/${tab}?${params.toString()}`);
}

async function requestJson<T>(
  path: string,
  options: {
    body?: unknown;
    method?: "GET" | "POST";
  } = {}
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {}),
    headers,
    ...(options.method !== undefined ? { method: options.method } : {})
  });
  const body = await response.json();

  if (!response.ok) {
    if (isSearchErrorResponse(body)) {
      throw new SearchApiError(body.error);
    }
    throw new Error("검색 요청에 실패했습니다.");
  }

  return body as T;
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
