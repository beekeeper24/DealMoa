import { describe, expect, it } from "vitest";

import { getProductTabs } from "../app-label";

describe("getProductTabs", () => {
  it("returns the first search result tabs in product-centered order", () => {
    expect(getProductTabs()).toEqual(["상품", "핫딜", "경매"]);
  });
});
