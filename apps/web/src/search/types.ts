export type SearchTab = "products" | "deals" | "auctions";

export type ProductSearchItem = {
  id: string;
  name: string;
  brand: string | null;
  modelName: string | null;
  category: string | null;
  specsText: string | null;
  createdAt: string;
  updatedAt: string;
  score: number;
};

export type DealSearchItem = {
  id: string;
  productId: string;
  title: string;
  sourceUrl: string;
  seller: string | null;
  originalPrice: number | null;
  salePrice: number;
  currency: string;
  status: string;
  trustScore?: number;
  startedAt: string | null;
  endedAt: string | null;
  createdAt: string;
  updatedAt: string;
  score: number;
};

export type AuctionSearchItem = {
  id: string;
  productId: string;
  title: string;
  sourceUrl: string;
  seller: string | null;
  currentPrice: number;
  bidCount: number;
  uniqueBidderCount?: number;
  favoriteCount?: number;
  viewMomentum?: number;
  currency: string;
  status: string;
  trustScore?: number;
  endsAt: string | null;
  createdAt: string;
  updatedAt: string;
  score: number;
};

export type SearchItemByTab = {
  products: ProductSearchItem;
  deals: DealSearchItem;
  auctions: AuctionSearchItem;
};

export type SearchResponse<T> = {
  items: T[];
  nextCursor: string | null;
};

export type AiSearchIntent = {
  query: string;
  normalizedQuery: string;
  targetTypes: SearchTab[];
  filters: {
    category?: string;
    maxPrice?: number;
  };
};

export type AiSearchResponse = {
  intent: AiSearchIntent;
  summary: string;
  products: SearchResponse<ProductSearchItem>;
  deals: SearchResponse<DealSearchItem>;
  auctions: SearchResponse<AuctionSearchItem>;
};

export type SearchErrorResponse = {
  error: {
    code: string;
    message: string;
    details: unknown;
    traceId: string;
  };
};
