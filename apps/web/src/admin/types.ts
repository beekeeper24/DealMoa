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

export type AdminDiscussionStatus = "visible" | "hidden";
export type AdminDiscussionModerationAction = "hide" | "restore";
export type AdminDiscussionRiskLevel = "low" | "medium" | "high";

export type AdminDiscussionComment = {
  id: string;
  productId: string;
  userId: string;
  userNickname: string;
  body: string;
  status: AdminDiscussionStatus;
  riskScore: number;
  riskLevel: AdminDiscussionRiskLevel;
  riskReasons: string[];
  moderatedByUserId: string | null;
  moderationNote: string | null;
  moderatedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type AdminDiscussionListResponse = {
  items: AdminDiscussionComment[];
  nextCursor: string | null;
};

export type AdminDiscussionModerationRequest = {
  accessToken: string;
  action: AdminDiscussionModerationAction;
  commentId: string;
  moderationNote?: string;
};

export type AdminVerifiedReviewStatus = "pending_review" | "approved" | "rejected" | "hidden";
export type AdminVerifiedReviewModerationAction = "approve" | "reject" | "hide" | "restore";
export type AdminVerifiedReviewRiskLevel = "low" | "medium" | "high";

export type AdminVerifiedReview = {
  id: string;
  productId: string;
  userId: string;
  rating: number;
  title: string;
  body: string;
  proofType: string;
  proofReference: string | null;
  status: AdminVerifiedReviewStatus;
  aiDecision: string | null;
  aiReason: string | null;
  aiReviewedAt: string | null;
  riskScore: number;
  riskLevel: AdminVerifiedReviewRiskLevel;
  riskReasons: string[];
  reviewedByUserId: string | null;
  resolutionNote: string | null;
  resolvedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type AdminVerifiedReviewListResponse = {
  items: AdminVerifiedReview[];
  nextCursor: string | null;
};

export type AdminVerifiedReviewModerationRequest = {
  accessToken: string;
  action: AdminVerifiedReviewModerationAction;
  reviewId: string;
  resolutionNote?: string;
};
