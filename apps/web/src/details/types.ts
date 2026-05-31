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
