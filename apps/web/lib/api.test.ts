import { describe, expect, it } from "vitest";

import { buildApiUrl } from "./api";

describe("buildApiUrl", () => {
  it("joins api base and path", () => {
    expect(buildApiUrl("/health")).toContain("/api/v1/health");
  });
});
