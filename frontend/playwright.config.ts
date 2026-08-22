import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  // Screenshot capture is manual-only (run with CAPTURE_SCREENSHOTS=1);
  // it needs a fresh DB (wizard visible) and is excluded from CI runs.
  testIgnore: process.env.CAPTURE_SCREENSHOTS === "1" ? [] : ["**/screenshots.spec.ts"],
  timeout: 60_000,
  retries: 0,
  // Specs share one local backend + database, so run them serially.
  workers: 1,
  fullyParallel: false,
  use: {
    baseURL: process.env.MINDVAULT_E2E_URL ?? "http://127.0.0.1:4173",
    headless: true,
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
