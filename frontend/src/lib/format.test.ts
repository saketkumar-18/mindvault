import { describe, it, expect } from "vitest";
import { formatBytes, formatDate, truncate } from "./format";
import { t } from "./i18n";

describe("formatBytes", () => {
  it("handles bytes", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(512)).toBe("512 B");
  });

  it("handles KB/MB/GB", () => {
    expect(formatBytes(1024)).toBe("1.0 KB");
    expect(formatBytes(1024 * 1024)).toBe("1.0 MB");
    expect(formatBytes(1024 * 1024 * 1024)).toBe("1.0 GB");
  });
});

describe("formatDate", () => {
  it("returns em dash for missing dates", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("formats valid dates", () => {
    const d = formatDate("2026-01-02T00:00:00Z");
    expect(d).not.toBe("—");
    expect(d).toMatch(/2026/);
  });
});

describe("truncate", () => {
  it("keeps short text", () => {
    expect(truncate("short")).toBe("short");
  });

  it("truncates long text", () => {
    const result = truncate("x".repeat(300), 100);
    expect(result).toHaveLength(101); // 100 chars + ellipsis
    expect(result.endsWith("…")).toBe(true);
  });
});

describe("i18n", () => {
  it("resolves translation keys", () => {
    expect(t("app.name")).toBe("MindVault");
    expect(t("nav.dashboard")).toBe("Dashboard");
  });

  it("interpolates params", () => {
    expect(t("documents.uploading", { done: "1", total: "3" })).toBe("Uploading 1/3…");
  });

  it("falls back to the key", () => {
    expect(t("missing.key" as never)).toBe("missing.key");
  });
});
