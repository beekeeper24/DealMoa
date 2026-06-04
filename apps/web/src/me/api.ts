import type { MyPageErrorResponse, SubmissionListResponse, VerifiedReviewListResponse } from "./types";

export class MyPageApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: MyPageErrorResponse["error"]) {
    super(response.message);
    this.name = "MyPageApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
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

export async function listMyVerifiedReviews(request: {
  accessToken: string;
  cursor?: string | null;
}): Promise<VerifiedReviewListResponse> {
  const params = new URLSearchParams({ limit: "20" });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  return requestJson<VerifiedReviewListResponse>(`/me/verified-reviews?${params.toString()}`, {
    accessToken: request.accessToken
  });
}

async function requestJson<T>(
  path: string,
  options: {
    accessToken: string;
  }
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${options.accessToken}`
    }
  });
  const body = await response.json();
  if (!response.ok) {
    if (isMyPageErrorResponse(body)) {
      throw new MyPageApiError(body.error);
    }
    throw new Error("내 활동 이력을 불러오지 못했습니다.");
  }
  return body as T;
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isMyPageErrorResponse(value: unknown): value is MyPageErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as MyPageErrorResponse).error.code === "string" &&
    typeof (value as MyPageErrorResponse).error.message === "string"
  );
}
