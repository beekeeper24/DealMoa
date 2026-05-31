import type {
  ProductMatchListResponse,
  Submission,
  SubmissionCreateInput,
  SubmissionErrorResponse,
  SubmissionListResponse,
  SubmissionReviewAction,
  SubmissionStatus
} from "./types";

export class SubmissionApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: SubmissionErrorResponse["error"]) {
    super(response.message);
    this.name = "SubmissionApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
}

export async function createSubmission(request: {
  accessToken: string;
  input: SubmissionCreateInput;
}): Promise<Submission> {
  return requestJson<Submission>("/submissions", {
    accessToken: request.accessToken,
    body: createSubmissionBody(request.input),
    method: "POST"
  });
}

export async function listMySubmissions(request: {
  accessToken: string;
  cursor?: string | null;
}): Promise<SubmissionListResponse> {
  const params = new URLSearchParams({ limit: "20" });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  return requestJson<SubmissionListResponse>(`/me/submissions?${params.toString()}`, {
    accessToken: request.accessToken
  });
}

export async function listAdminSubmissions(request: {
  accessToken: string;
  cursor?: string | null;
  status: SubmissionStatus;
}): Promise<SubmissionListResponse> {
  const params = new URLSearchParams({ status: request.status, limit: "20" });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  return requestJson<SubmissionListResponse>(`/admin/submissions?${params.toString()}`, {
    accessToken: request.accessToken
  });
}

export async function listSubmissionProductMatches(request: {
  accessToken: string;
  submissionId: string;
}): Promise<ProductMatchListResponse> {
  return requestJson<ProductMatchListResponse>(
    `/admin/submissions/${request.submissionId}/product-matches?limit=5`,
    {
      accessToken: request.accessToken
    }
  );
}

export async function reviewSubmission(request: {
  accessToken: string;
  action: SubmissionReviewAction;
  resolutionNote: string;
  submissionId: string;
  targetProductId?: string;
}): Promise<Submission> {
  const body: {
    action: SubmissionReviewAction;
    resolutionNote?: string;
    targetProductId?: string;
  } = {
    action: request.action
  };
  const note = request.resolutionNote.trim();
  if (note) {
    body.resolutionNote = note;
  }
  if (request.targetProductId) {
    body.targetProductId = request.targetProductId;
  }
  return requestJson<Submission>(`/admin/submissions/${request.submissionId}`, {
    accessToken: request.accessToken,
    body,
    method: "PATCH"
  });
}

function createSubmissionBody(input: SubmissionCreateInput) {
  const body: Record<string, string | number | null> = {
    brand: blankToNull(input.brand),
    category: blankToNull(input.category),
    currency: "KRW",
    description: blankToNull(input.description),
    modelName: blankToNull(input.modelName),
    offerType: input.offerType,
    originalPrice: numberOrNull(input.originalPrice),
    productName: input.productName.trim(),
    seller: blankToNull(input.seller),
    sourceUrl: input.sourceUrl.trim(),
    title: input.title.trim()
  };
  if (input.offerType === "deal") {
    body.salePrice = numberOrNull(input.salePrice);
    body.currentPrice = null;
  } else {
    body.salePrice = null;
    body.currentPrice = numberOrNull(input.currentPrice);
  }
  return body;
}

function blankToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function numberOrNull(value: string): number | null {
  const trimmed = value.trim();
  return trimmed ? Number(trimmed) : null;
}

async function requestJson<T>(
  path: string,
  options: {
    accessToken: string;
    body?: unknown;
    method?: "GET" | "PATCH" | "POST";
  }
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    Authorization: `Bearer ${options.accessToken}`
  };
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
    if (isSubmissionErrorResponse(body)) {
      throw new SubmissionApiError(body.error);
    }
    throw new Error("제보 요청에 실패했습니다.");
  }
  return body as T;
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isSubmissionErrorResponse(value: unknown): value is SubmissionErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as SubmissionErrorResponse).error.code === "string" &&
    typeof (value as SubmissionErrorResponse).error.message === "string"
  );
}
