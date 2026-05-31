export type SubmissionOfferType = "auction" | "deal";
export type SubmissionStatus = "approved" | "pending_review" | "rejected";
export type SubmissionReviewAction = "approve" | "reject";

export type Submission = {
  id: string;
  userId: string;
  offerType: SubmissionOfferType;
  sourceUrl: string;
  productName: string;
  brand: string | null;
  modelName: string | null;
  category: string | null;
  title: string;
  seller: string | null;
  originalPrice: number | null;
  salePrice: number | null;
  currentPrice: number | null;
  currency: string;
  description: string | null;
  status: SubmissionStatus;
  aiDecision: string | null;
  aiReason: string | null;
  aiReviewedAt: string | null;
  reviewedByUserId: string | null;
  resolutionNote: string | null;
  resolvedAt: string | null;
  publishedProductId: string | null;
  publishedOfferType: SubmissionOfferType | null;
  publishedOfferId: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ProductMatch = {
  productId: string;
  name: string;
  brand: string | null;
  modelName: string | null;
  category: string | null;
  score: number;
  matchedReasons: string[];
};

export type SubmissionCreateInput = {
  brand: string;
  category: string;
  currentPrice: string;
  description: string;
  modelName: string;
  offerType: SubmissionOfferType;
  originalPrice: string;
  productName: string;
  salePrice: string;
  seller: string;
  sourceUrl: string;
  title: string;
};

export type SubmissionListResponse = {
  items: Submission[];
  nextCursor: string | null;
};

export type ProductMatchListResponse = {
  items: ProductMatch[];
};

export type SubmissionErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};
