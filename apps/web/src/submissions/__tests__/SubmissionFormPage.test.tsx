// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthSessionProvider } from "../../auth/useAuthSession";
import { SubmissionFormPage } from "../SubmissionFormPage";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function jsonResponse(body: unknown, init: ResponseInit = { status: 200 }): Response {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: { "Content-Type": "application/json" }
  });
}

function authSession() {
  return {
    user: {
      id: "user-1",
      email: "user@example.com",
      nickname: "Deal User",
      role: "USER"
    },
    accessToken: "access-1",
    tokenType: "Bearer"
  };
}

function submissionFixture(overrides: Record<string, unknown> = {}) {
  return {
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
    updatedAt: "2026-05-31T14:30:00Z",
    ...overrides
  };
}

function installFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>
) {
  const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    return Promise.resolve(handler(url, init));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function renderWithAuthProvider() {
  return render(
    <AuthSessionProvider>
      <SubmissionFormPage />
    </AuthSessionProvider>
  );
}

describe("SubmissionFormPage", () => {
  it("shows login guidance for anonymous users", async () => {
    installFetch((url) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(
          {
            error: {
              code: "INVALID_REFRESH_TOKEN",
              message: "로그인이 필요합니다.",
              details: {},
              traceId: "req-1"
            }
          },
          { status: 401 }
        );
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    expect(await screen.findByText("로그인 후 제보할 수 있습니다.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "제보 제출" })).toBeDisabled();
  });

  it("submits a deal candidate for authenticated users", async () => {
    const user = userEvent.setup();
    const fetchMock = installFetch((url, init) => {
      if (url === "/api/v1/auth/token/refresh") {
        return jsonResponse(authSession());
      }
      if (url === "/api/v1/submissions" && init?.method === "POST") {
        return jsonResponse(submissionFixture(), { status: 201 });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    renderWithAuthProvider();

    expect(await screen.findByText("user@example.com")).toBeInTheDocument();
    await user.type(screen.getByLabelText("원문 URL"), "https://example.com/deals/galaxy-s26");
    await user.type(screen.getByLabelText("상품명"), "Galaxy S26");
    await user.type(screen.getByLabelText("브랜드"), "Samsung");
    await user.type(screen.getByLabelText("모델명"), "SM-S260");
    await user.type(screen.getByLabelText("카테고리"), "smartphone");
    await user.type(screen.getByLabelText("제보 제목"), "Galaxy S26 launch deal");
    await user.type(screen.getByLabelText("판매처"), "Example Store");
    await user.type(screen.getByLabelText("정가"), "1400000");
    await user.type(screen.getByLabelText("핫딜가"), "1090000");
    await user.type(screen.getByLabelText("설명"), "Launch discount");
    await user.click(screen.getByRole("button", { name: "제보 제출" }));

    expect(await screen.findByText("제보가 접수되었습니다. 상태: pending_review")).toBeInTheDocument();
    const [, request] = fetchMock.mock.calls.at(-1) ?? [];
    expect(fetchMock.mock.calls.at(-1)?.[0]).toBe("/api/v1/submissions");
    expect(JSON.parse(String(request?.body))).toEqual({
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
    expect(request).toMatchObject({
      headers: {
        Accept: "application/json",
        Authorization: "Bearer access-1",
        "Content-Type": "application/json"
      },
      method: "POST"
    });
  });
});
