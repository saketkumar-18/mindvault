/**
 * Captures MindVault UI screenshots for the README.
 *
 * Requires a running backend (mock providers) serving the built frontend at
 * MINDVAULT_E2E_URL, and a fresh MV_HOME so the first-run wizard appears.
 *
 * Usage:
 *   MINDVAULT_E2E_URL=http://127.0.0.1:8010 npx playwright test e2e/screenshots.spec.ts
 *
 * Output: docs/screenshots/*.png
 */
import { test, expect } from "@playwright/test";

const OUT_DIR = "docs/screenshots";

test("capture screenshots", async ({ page }) => {
  await page.goto("/");

  // 1. First-run wizard
  await expect(page.getByRole("heading", { name: /Welcome to MindVault/i })).toBeVisible();
  await page.screenshot({ path: `${OUT_DIR}/welcome.png`, fullPage: true });

  // Complete the wizard
  for (let step = 0; step < 5; step++) {
    await page.getByRole("button", { name: /Next/i }).click();
  }
  await page.getByRole("button", { name: /Start using MindVault/i }).click();
  await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible();

  // 2. Dashboard
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT_DIR}/dashboard.png`, fullPage: true });

  // Upload a document
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await page.getByRole("button", { name: /Upload Documents/i }).click();
  await page.setInputFiles('input[type="file"]', {
    name: "zero-trust-guide.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "Zero Trust Architecture\n\nZero trust assumes that no user or device should automatically be trusted, even inside the network perimeter. Access is granted per request based on identity, device health and context.\n\nKey principles: verify explicitly, use least privilege, assume breach. Continuous authentication and micro-segmentation are core implementation patterns.",
      "utf-8",
    ),
  });
  await expect(page.getByText("zero-trust-guide.txt")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("indexed").first()).toBeVisible({ timeout: 30_000 });

  // 3. Documents
  await page.screenshot({ path: `${OUT_DIR}/documents.png`, fullPage: true });

  // 4. Knowledge bases (create one)
  await page.getByRole("link", { name: "Knowledge Bases", exact: true }).click();
  await page.getByRole("button", { name: /Create Knowledge Base/i }).first().click();
  const kbDialog = page.getByRole("dialog", { name: /Create Knowledge Base/i });
  await kbDialog.locator("input").first().fill("Security Notes");
  await kbDialog.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByText("Security Notes")).toBeVisible();
  await page.screenshot({ path: `${OUT_DIR}/knowledge-bases.png`, fullPage: true });

  // 5. Chat with a grounded answer
  await page.getByRole("link", { name: "Chat", exact: true }).click();
  await page.getByPlaceholder(/Ask about your documents/i).fill("What is the core assumption of zero trust?");
  await page.getByRole("button", { name: /Send/i }).click();
  await expect(page.getByText(/Based on the provided documents/i)).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText(/Sources/i)).toBeVisible({ timeout: 15_000 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT_DIR}/chat.png`, fullPage: true });

  // 6. Search
  await page.getByRole("link", { name: "Search", exact: true }).click();
  await page.getByPlaceholder(/Search your documents semantically/i).fill("zero trust");
  await page.getByRole("button", { name: /Search/i }).click();
  await expect(page.getByText("zero-trust-guide.txt")).toBeVisible({ timeout: 15_000 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT_DIR}/search.png`, fullPage: true });

  // 7. Settings
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page.getByRole("heading", { name: /Settings/i }).waitFor();
  await page.screenshot({ path: `${OUT_DIR}/settings.png`, fullPage: true });

  // 8. Study
  await page.getByRole("link", { name: "Study", exact: true }).click();
  await page.getByRole("button", { name: /Generate Study Material/i }).waitFor();
  await page.screenshot({ path: `${OUT_DIR}/study.png`, fullPage: true });
});
