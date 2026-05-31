import type {
  AuctionBid,
  AuctionDetail,
  DealDetail,
  DetailErrorResponse,
  DetailListResponse,
  ProductDetail,
  Report
} from "./types";

export class DetailApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: DetailErrorResponse["error"]) {
    super(response.message);
    this.name = "DetailApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
}

export async function getProduct(productId: string): Promise<ProductDetail> {
  return requestJson<ProductDetail>(`/products/${productId}`);
}

export async function listProductDeals(
  productId: string
): Promise<DetailListResponse<DealDetail>> {
  return requestJson<DetailListResponse<DealDetail>>(`/products/${productId}/deals?limit=10`);
}

export async function listProductAuctions(
  productId: string
): Promise<DetailListResponse<AuctionDetail>> {
  return requestJson<DetailListResponse<AuctionDetail>>(`/products/${productId}/auctions?limit=10`);
}

export async function getDeal(dealId: string): Promise<DealDetail> {
  return requestJson<DealDetail>(`/deals/${dealId}`);
}

export async function getAuction(auctionId: string): Promise<AuctionDetail> {
  return requestJson<AuctionDetail>(`/auctions/${auctionId}`);
}

export async function placeAuctionBid(request: {
  accessToken: string;
  amount: number;
  auctionId: string;
}): Promise<AuctionBid> {
  return requestJson<AuctionBid>(`/auctions/${request.auctionId}/bids`, {
    accessToken: request.accessToken,
    body: { amount: request.amount },
    method: "POST"
  });
}

export async function reportDeal(request: {
  accessToken: string;
  dealId: string;
  description: string;
  reasonCode: string;
}): Promise<Report> {
  return requestJson<Report>(`/reports/deals/${request.dealId}`, {
    accessToken: request.accessToken,
    body: reportBody(request),
    method: "POST"
  });
}

export async function reportAuction(request: {
  accessToken: string;
  auctionId: string;
  description: string;
  reasonCode: string;
}): Promise<Report> {
  return requestJson<Report>(`/reports/auctions/${request.auctionId}`, {
    accessToken: request.accessToken,
    body: reportBody(request),
    method: "POST"
  });
}

function reportBody(request: { description: string; reasonCode: string }) {
  const body: { description?: string; reasonCode: string } = {
    reasonCode: request.reasonCode
  };
  const description = request.description.trim();
  if (description) {
    body.description = description;
  }
  return body;
}

async function requestJson<T>(
  path: string,
  options: {
    accessToken?: string;
    body?: unknown;
    method?: "GET" | "POST";
  } = {}
): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.accessToken) {
    headers.Authorization = `Bearer ${options.accessToken}`;
  }
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
    if (isDetailErrorResponse(body)) {
      throw new DetailApiError(body.error);
    }
    throw new Error("상세 정보를 불러오지 못했습니다.");
  }

  return body as T;
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isDetailErrorResponse(value: unknown): value is DetailErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as DetailErrorResponse).error.code === "string" &&
    typeof (value as DetailErrorResponse).error.message === "string"
  );
}
