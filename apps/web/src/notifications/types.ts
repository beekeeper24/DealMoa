export type NotificationItem = {
  id: string;
  type: string;
  title: string;
  body: string;
  targetType: string | null;
  targetId: string | null;
  metadata: Record<string, unknown>;
  readAt: string | null;
  createdAt: string;
};

export type NotificationListResponse = {
  items: NotificationItem[];
  nextCursor: string | null;
};

export type NotificationErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};
