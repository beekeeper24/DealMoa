import type {
  NotificationErrorResponse,
  NotificationItem,
  NotificationListResponse
} from "./types";

export class NotificationApiError extends Error {
  code: string;
  details: unknown;
  traceId: string;

  constructor(response: NotificationErrorResponse["error"]) {
    super(response.message);
    this.name = "NotificationApiError";
    this.code = response.code;
    this.details = response.details;
    this.traceId = response.traceId;
  }
}

export async function getUnreadNotificationCount(accessToken: string): Promise<number> {
  const response = await fetch(`${getApiBaseUrl()}/notifications/unread-count`, {
    headers: authHeaders(accessToken)
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwNotificationError(body);
  }
  return (body as { count: number }).count;
}

export async function listNotifications(request: {
  accessToken: string;
  cursor?: string | null;
  unreadOnly?: boolean;
}): Promise<NotificationListResponse> {
  const params = new URLSearchParams({ limit: "20" });
  if (request.unreadOnly) {
    params.set("unreadOnly", "true");
  }
  if (request.cursor) {
    params.set("cursor", request.cursor);
  }
  const response = await fetch(`${getApiBaseUrl()}/notifications?${params.toString()}`, {
    headers: authHeaders(request.accessToken)
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwNotificationError(body);
  }
  return body as NotificationListResponse;
}

export async function markNotificationRead(request: {
  accessToken: string;
  notificationId: string;
}): Promise<NotificationItem> {
  const response = await fetch(
    `${getApiBaseUrl()}/notifications/${request.notificationId}/read`,
    {
      headers: authHeaders(request.accessToken),
      method: "POST"
    }
  );
  const body = await parseJson(response);
  if (!response.ok) {
    throwNotificationError(body);
  }
  return body as NotificationItem;
}

export async function markAllNotificationsRead(accessToken: string): Promise<number> {
  const response = await fetch(`${getApiBaseUrl()}/notifications/read-all`, {
    headers: authHeaders(accessToken),
    method: "POST"
  });
  const body = await parseJson(response);
  if (!response.ok) {
    throwNotificationError(body);
  }
  return (body as { updatedCount: number }).updatedCount;
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

function throwNotificationError(value: unknown): never {
  if (isNotificationErrorResponse(value)) {
    throw new NotificationApiError(value.error);
  }
  throw new Error("알림 요청에 실패했습니다.");
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}

function isNotificationErrorResponse(value: unknown): value is NotificationErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as NotificationErrorResponse).error.code === "string" &&
    typeof (value as NotificationErrorResponse).error.message === "string"
  );
}
