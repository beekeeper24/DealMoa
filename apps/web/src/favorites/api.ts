export type FavoriteTargetType = "products" | "deals" | "auctions";

export type FavoriteRequest = {
  accessToken: string;
  targetId: string;
  targetType: FavoriteTargetType;
};

export class FavoriteApiError extends Error {
  constructor(message = "찜 요청에 실패했습니다.") {
    super(message);
    this.name = "FavoriteApiError";
  }
}

export async function addFavorite(request: FavoriteRequest): Promise<void> {
  await sendFavoriteRequest(request, "PUT");
}

export async function removeFavorite(request: FavoriteRequest): Promise<void> {
  await sendFavoriteRequest(request, "DELETE");
}

async function sendFavoriteRequest(
  request: FavoriteRequest,
  method: "PUT" | "DELETE"
): Promise<void> {
  const response = await fetch(
    `${getApiBaseUrl()}/me/favorites/${request.targetType}/${request.targetId}`,
    {
      headers: { Accept: "application/json", Authorization: `Bearer ${request.accessToken}` },
      method
    }
  );

  if (!response.ok) {
    throw new FavoriteApiError();
  }
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1").replace(/\/$/, "");
}
