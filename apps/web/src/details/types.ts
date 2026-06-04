export type ProductDetail = {
  id: string;
  name: string;
  brand: string | null;
  modelName: string | null;
  category: string | null;
  specs: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
};

export type DealDetail = {
  id: string;
  productId: string;
  title: string;
  sourceUrl: string;
  seller: string | null;
  originalPrice: number | null;
  salePrice: number;
  currency: string;
  status: string;
  startedAt: string | null;
  endedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type AuctionDetail = {
  id: string;
  productId: string;
  title: string;
  sourceUrl: string;
  seller: string | null;
  currentPrice: number;
  bidCount: number;
  currency: string;
  status: string;
  endsAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type DetailListResponse<T> = {
  items: T[];
  nextCursor: string | null;
};

export type AuctionBid = {
  id: string;
  auctionId: string;
  userId: string;
  amount: number;
  createdAt: string;
};

export type PriceHistorySnapshot = {
  id: string;
  productId: string;
  sourceType: "auction" | "deal";
  sourceId: string;
  price: number;
  currency: string;
  observedAt: string;
  createdAt: string;
};

export type VerifiedReview = {
  id: string;
  productId: string;
  userId: string;
  rating: number;
  title: string;
  body: string;
  proofType: string;
  proofReference: string | null;
  status: "approved" | "pending_review" | "rejected" | "hidden";
  aiDecision: string | null;
  aiReason: string | null;
  aiReviewedAt: string | null;
  reviewedByUserId: string | null;
  resolutionNote: string | null;
  resolvedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type PublicVerifiedReview = Pick<
  VerifiedReview,
  "body" | "createdAt" | "id" | "productId" | "rating" | "title" | "updatedAt"
>;

export type DiscussionComment = {
  id: string;
  productId: string;
  userId: string;
  userNickname: string;
  body: string;
  status: "visible" | "hidden";
  moderatedByUserId: string | null;
  moderationNote: string | null;
  moderatedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type PublicDiscussionComment = Pick<
  DiscussionComment,
  "body" | "createdAt" | "id" | "productId" | "updatedAt" | "userNickname"
>;

export type PurchaseRecommendation = "buy" | "watch" | "avoid";

export type PurchaseCheckEvidence = {
  type: string;
  label: string;
  value: string;
  sourceType?: string;
  sourceId?: string;
};

export type ProductPurchaseCheck = {
  productId: string;
  recommendation: PurchaseRecommendation;
  confidence: number;
  summary: string;
  evidence: PurchaseCheckEvidence[];
};

export type Report = {
  id: string;
  userId: string;
  targetType: "deal" | "auction";
  targetId: string;
  reasonCode: string;
  description: string | null;
  status: "open" | "resolved" | "dismissed";
  reviewedByUserId: string | null;
  resolutionNote: string | null;
  resolvedAt: string | null;
  createdAt: string;
  updatedAt: string;
};

export type DetailErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};
