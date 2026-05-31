import type {
  AdminReport,
  AdminReportErrorResponse,
  AdminReportListResponse,
  AdminReportReviewRequest,
  AdminReportStatus
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
