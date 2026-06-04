export type AdminReportStatus = "open" | "resolved" | "dismissed";
export type AdminReportReviewStatus = "resolved" | "dismissed";
export type AdminReportTargetType = "deal" | "auction";
export type OfferStatus = "pending" | "active" | "verified" | "rejected" | "blocked" | "closed";

export type AdminReportTarget = {
  targetType: AdminReportTargetType;
  targetId: string;
  title: string;
  status: string;
  seller: string | null;
  sourceUrl: string;
};

export type AdminReport = {
  id: string;
  userId: string;
  targetType: AdminReportTargetType;
  targetId: string;
  reasonCode: string;
  description: string | null;
  status: AdminReportStatus;
  reviewedByUserId: string | null;
  resolutionNote: string | null;
  resolvedAt: string | null;
  createdAt: string;
  updatedAt: string;
  target: AdminReportTarget | null;
};

export type AdminReportListResponse = {
  items: AdminReport[];
  nextCursor: string | null;
};

export type AdminReportReviewRequest = {
  accessToken: string;
  reportId: string;
  resolutionNote?: string;
  status: AdminReportReviewStatus;
  targetStatus?: OfferStatus | "";
};

export type AdminReportErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};

export type AdminCrawlerRunLog = {
  id: string;
  taskName: string;
  status: string;
  scanned: number;
  fetched: number;
  accepted: number;
  created: number;
  duplicates: number;
  skipped: number;
  skipReasons: Record<string, number>;
  errorType: string | null;
  errorMessage: string | null;
  startedAt: string;
  finishedAt: string;
  createdAt: string;
};

export type AdminCrawlerRunLogListResponse = {
  items: AdminCrawlerRunLog[];
  nextCursor: string | null;
};

export type AdminCrawlerTaskName = "crawl_hot_deals_mock" | "crawl_live_urls";

export type AdminCrawlerRunTriggerResponse = {
  taskName: AdminCrawlerTaskName;
  celeryTaskId: string;
};
