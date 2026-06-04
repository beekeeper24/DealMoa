import { afterEach, describe, expect, it, vi } from "vitest";

import { listMySubmissions, listMyVerifiedReviews } from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, init: ResponseInit = { status: 200 }): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: { "Content-Type": "application/json" }
  });
}

describe("me api", () => {
  it("lists my submissions and verified reviews with bearer auth", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() =>
        Promise.resolve(jsonResponse({ items: [], nextCursor: null }))
      );
    vi.stubGlobal("fetch", fetchMock);

    await listMySubmissions({ accessToken: "access-1", cursor: "submission-cursor" });
    await listMyVerifiedReviews({ accessToken: "access-1", cursor: "review-cursor" });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/v1/me/submissions?limit=20&cursor=submission-cursor",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/me/verified-reviews?limit=20&cursor=review-cursor",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
  });
});
