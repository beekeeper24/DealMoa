import type {
  AdminCrawlerRunLogListResponse,
  AdminCrawlerRunTriggerResponse,
  AdminCrawlerTaskName,
  AdminDiscussionComment,
  AdminDiscussionListResponse,
  AdminDiscussionModerationRequest,
  AdminDiscussionStatus,
  AdminReport,
  AdminReportErrorResponse,
  AdminReportListResponse,
  AdminReportReviewRequest,
  AdminReportStatus,
  AdminVerifiedReview,
  AdminVerifiedReviewListResponse,
  AdminVerifiedReviewModerationRequest,
  AdminVerifiedReviewStatus
} from "./types";

export class AdminReportApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: AdminReportErrorResponse["error"]) {
    super(response.message);
    this.name = "AdminReportApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
}

export async function listAdminReports(request: {
  accessToken: string;
  cursor?: string | null;
  status: AdminReportStatus;
}): Promise<AdminReportListResponse> {
  const params = new URLSearchParams({
    status: request.status,
    limit: "20"
  });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  const response = await fetch(`${getApiBaseUrl()}/admin/reports?${params.toString()}`, {
    headers: authHeaders(request.accessToken)
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(body);
  }
  return body as AdminReportListResponse;
}

export async function listAdminCrawlerRunLogs(request: {
  accessToken: string;
  cursor?: string | null;
}): Promise<AdminCrawlerRunLogListResponse> {
  const params = new URLSearchParams({ limit: "20" });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  const response = await fetch(`${getApiBaseUrl()}/admin/crawler-runs?${params.toString()}`, {
    headers: authHeaders(request.accessToken)
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(body);
  }
  return body as AdminCrawlerRunLogListResponse;
}

export async function triggerAdminCrawlerRun(request: {
  accessToken: string;
  taskName: AdminCrawlerTaskName;
}): Promise<AdminCrawlerRunTriggerResponse> {
  const response = await fetch(`${getApiBaseUrl()}/admin/crawler-runs/trigger`, {
    body: JSON.stringify({ taskName: request.taskName }),
    headers: {
      ...authHeaders(request.accessToken),
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(body);
  }
  return body as AdminCrawlerRunTriggerResponse;
}

export async function listAdminDiscussions(request: {
  accessToken: string;
  cursor?: string | null;
  status: AdminDiscussionStatus;
}): Promise<AdminDiscussionListResponse> {
  const params = new URLSearchParams({
    status: request.status,
    limit: "20"
  });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  const response = await fetch(`${getApiBaseUrl()}/admin/discussions?${params.toString()}`, {
    headers: authHeaders(request.accessToken)
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(body);
  }
  return body as AdminDiscussionListResponse;
}

export async function moderateAdminDiscussion(
  request: AdminDiscussionModerationRequest
): Promise<AdminDiscussionComment> {
  const body: {
    action: AdminDiscussionModerationRequest["action"];
    moderationNote?: string;
  } = {
    action: request.action
  };
  const moderationNote = request.moderationNote?.trim();
  if (moderationNote) {
    body.moderationNote = moderationNote;
  }

  const response = await fetch(`${getApiBaseUrl()}/admin/discussions/${request.commentId}`, {
    body: JSON.stringify(body),
    headers: {
      ...authHeaders(request.accessToken),
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
  const parsed = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(parsed);
  }
  return parsed as AdminDiscussionComment;
}

export async function listAdminVerifiedReviews(request: {
  accessToken: string;
  cursor?: string | null;
  status: AdminVerifiedReviewStatus;
}): Promise<AdminVerifiedReviewListResponse> {
  const params = new URLSearchParams({
    status: request.status,
    limit: "20"
  });
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  const response = await fetch(`${getApiBaseUrl()}/admin/verified-reviews?${params.toString()}`, {
    headers: authHeaders(request.accessToken)
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(body);
  }
  return body as AdminVerifiedReviewListResponse;
}

export async function moderateAdminVerifiedReview(
  request: AdminVerifiedReviewModerationRequest
): Promise<AdminVerifiedReview> {
  const body: {
    action: AdminVerifiedReviewModerationRequest["action"];
    resolutionNote?: string;
  } = {
    action: request.action
  };
  const resolutionNote = request.resolutionNote?.trim();
  if (resolutionNote) {
    body.resolutionNote = resolutionNote;
  }

  const response = await fetch(`${getApiBaseUrl()}/admin/verified-reviews/${request.reviewId}`, {
    body: JSON.stringify(body),
    headers: {
      ...authHeaders(request.accessToken),
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
  const parsed = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(parsed);
  }
  return parsed as AdminVerifiedReview;
}

export async function reviewAdminReport(
  request: AdminReportReviewRequest
): Promise<AdminReport> {
  const body: {
    resolutionNote?: string;
    status: AdminReportReviewRequest["status"];
    targetStatus?: Exclude<AdminReportReviewRequest["targetStatus"], "">;
  } = {
    status: request.status
  };
  const resolutionNote = request.resolutionNote?.trim();
  if (resolutionNote) {
    body.resolutionNote = resolutionNote;
  }
  if (request.targetStatus) {
    body.targetStatus = request.targetStatus;
  }

  const response = await fetch(`${getApiBaseUrl()}/admin/reports/${request.reportId}`, {
    body: JSON.stringify(body),
    headers: {
      ...authHeaders(request.accessToken),
      "Content-Type": "application/json"
    },
    method: "PATCH"
  });
  const parsed = await parseJson(response);
  if (!response.ok) {
    throwAdminReportError(parsed);
  }
  return parsed as AdminReport;
}

function authHeaders(accessToken: string): HeadersInit {
  return { Accept: "application/json", Authorization: `Bearer ${accessToken}` };
}

async function parseJson(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function throwAdminReportError(value: unknown): never {
  if (isAdminReportErrorResponse(value)) {
    throw new AdminReportApiError(value.error);
  }
  throw new Error("관리자 신고 요청에 실패했습니다.");
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isAdminReportErrorResponse(value: unknown): value is AdminReportErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as AdminReportErrorResponse).error.code === "string" &&
    typeof (value as AdminReportErrorResponse).error.message === "string"
  );
}
