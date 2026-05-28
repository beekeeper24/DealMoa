// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";

import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FavoriteButton } from "../FavoriteButton";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("FavoriteButton", () => {
  it("shows login required state without an access token", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<FavoriteButton targetId="product-1" targetType="products" />);

    await user.click(screen.getByRole("button", { name: "로그인 후 찜" }));

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("toggles favorite state with an access token", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "favorite-1" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <FavoriteButton accessToken="access-1" targetId="product-1" targetType="products" />
    );

    await user.click(screen.getByRole("button", { name: "찜하기" }));
    expect(await screen.findByRole("button", { name: "찜 해제" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "찜 해제" }));
    expect(await screen.findByRole("button", { name: "찜하기" })).toBeInTheDocument();
  });
});
