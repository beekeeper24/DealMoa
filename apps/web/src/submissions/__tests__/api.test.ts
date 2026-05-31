import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createSubmission,
  listAdminSubmissions,
  listMySubmissions,
  reviewSubmission,
  SubmissionApiError
} from "../api";

afterEach(() => {
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, init: ResponseInit = { status: 200 }): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: { "Content-Type": "application/json" }
  });
}

const submissionFixture = {
  id: "submission-1",
  userId: "user-1",
  offerType: "deal",
  sourceUrl: "https://example.com/deals/galaxy-s26",
  productName: "Galaxy S26",
  brand: "Samsung",
  modelName: "SM-S260",
  category: "smartphone",
  title: "Galaxy S26 launch deal",
  seller: "Example Store",
  originalPrice: 1400000,
  salePrice: 1090000,
  currentPrice: null,
  currency: "KRW",
  description: "Launch discount",
  status: "pending_review",
  aiDecision: "needs_admin_review",
  aiReason: "mock review passed: admin approval required",
  aiReviewedAt: "2026-05-31T14:30:00Z",
  reviewedByUserId: null,
  resolutionNote: null,
  resolvedAt: null,
  publishedProductId: null,
  publishedOfferType: null,
  publishedOfferId: null,
  createdAt: "2026-05-31T14:30:00Z",
  updatedAt: "2026-05-31T14:30:00Z"
};

describe("submissions api", () => {
  it("creates a submission with bearer auth and normalized body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(submissionFixture, { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    await createSubmission({
      accessToken: "access-1",
      input: {
        brand: "Samsung",
        category: "smartphone",
        currentPrice: "",
        description: "Launch discount",
        modelName: "SM-S260",
        offerType: "deal",
        originalPrice: "1400000",
        productName: "Galaxy S26",
        salePrice: "1090000",
        seller: "Example Store",
        sourceUrl: "https://example.com/deals/galaxy-s26",
        title: "Galaxy S26 launch deal"
      }
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/submissions");
    expect(JSON.parse(String(init?.body))).toEqual({
      brand: "Samsung",
      category: "smartphone",
      currency: "KRW",
      currentPrice: null,
      description: "Launch discount",
      modelName: "SM-S260",
      offerType: "deal",
      originalPrice: 1400000,
      productName: "Galaxy S26",
      salePrice: 1090000,
      seller: "Example Store",
      sourceUrl: "https://example.com/deals/galaxy-s26",
      title: "Galaxy S26 launch deal"
    });
    expect(init).toMatchObject({
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
  });

  it("lists my and admin submissions", async () => {
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(jsonResponse({ items: [submissionFixture], nextCursor: "submission-2" }))
    );
    vi.stubGlobal("fetch", fetchMock);

    await listMySubmissions({ accessToken: "access-1", cursor: "cursor-1" });
    await listAdminSubmissions({
      accessToken: "access-1",
      cursor: "cursor-2",
      status: "pending_review"
    });

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/api/v1/me/submissions?limit=20&cursor=cursor-1", {
      headers: { Accept: "application/json", Authorization: "Bearer access-1" }
    });
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/admin/submissions?status=pending_review&limit=20&cursor=cursor-2",
      {
        headers: { Accept: "application/json", Authorization: "Bearer access-1" }
      }
    );
  });

  it("reviews a submission", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        ...submissionFixture,
        status: "approved",
        publishedOfferId: "deal-1"
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await reviewSubmission({
      accessToken: "access-1",
      action: "approve",
      resolutionNote: "approved",
      submissionId: "submission-1"
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/v1/admin/submissions/submission-1", {
      body: JSON.stringify({ action: "approve", resolutionNote: "approved" }),
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "PATCH"
    });
  });

  it("throws api errors with stable code", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            error: {
              code: "FORBIDDEN",
              message: "권한이 없습니다.",
              details: {},
              traceId: "req-1"
            }
          },
          { status: 403 }
        )
      )
    );

    await expect(
      listAdminSubmissions({ accessToken: "access-1", status: "pending_review" })
    ).rejects.toBeInstanceOf(SubmissionApiError);
  });
});
