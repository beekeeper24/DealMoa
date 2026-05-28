import { afterEach, describe, expect, it, vi } from "vitest";

import { addFavorite, removeFavorite } from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("favorites api", () => {
  it("adds a favorite with bearer auth", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "favorite-1", productId: "product-1" }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await addFavorite({
      accessToken: "access-1",
      targetId: "product-1",
      targetType: "products"
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/me/favorites/products/product-1", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "PUT"
    });
  });

  it("removes a favorite with bearer auth", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await removeFavorite({
      accessToken: "access-1",
      targetId: "deal-1",
      targetType: "deals"
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/me/favorites/deals/deal-1", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" },
      method: "DELETE"
    });
  });
});
