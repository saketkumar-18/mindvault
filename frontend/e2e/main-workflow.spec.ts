import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the main MindVault workflow.
 *
 * Requires a running backend (with MV_LLM_PROVIDER=mock for determinism)
 * and the built frontend served at MINDVAULT_E2E_URL (default preview server).
 */
test("main workflow: upload, index, search, chat, citations, delete", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/MindVault/);

  // Complete the first-run wizard if it appears (shared backend across specs).
  const wizardVisible = await page
    .getByRole("heading", { name: /Welcome to MindVault/i })
    .waitFor({ state: "visible", timeout: 8000 })
    .then(() => true)
    .catch(() => false);
  if (wizardVisible) {
    for (let step = 0; step < 6; step++) {
      const startBtn = page.getByRole("button", { name: /Start using MindVault/i });
      if (await startBtn.isVisible().catch(() => false)) {
        await startBtn.click();
        break;
      }
      const nextBtn = page.getByRole("button", { name: /Next/i });
      if (!(await nextBtn.isVisible().catch(() => false))) break;
      await nextBtn.click();
      await page.waitForTimeout(120);
    }
  }

  // Dashboard loads after setup
  await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible({ timeout: 20_000 });

  // Navigate to Documents (sidebar link)
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Documents/i })).toBeVisible();

  // Open the upload dropzone
  await page.getByRole("button", { name: /Upload Documents/i }).click();

  // Upload a document (unique content per run to avoid duplicate detection)
  const marker = `mindvault-e2e-${Date.now()}`;
  const filename = `${marker}.txt`;
  await page.setInputFiles('input[type="file"]', {
    name: filename,
    mimeType: "text/plain",
    buffer: Buffer.from("MindVault E2E test. Zero trust architecture assumes no device is trusted.", "utf-8"),
  });

  // Wait for the document row to appear with "indexed" status
  await expect(page.getByText(marker)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("indexed").first()).toBeVisible({ timeout: 30_000 });

  // Chat (sidebar link)
  await page.getByRole("link", { name: "Chat", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Chat/i })).toBeVisible();
  await page.getByPlaceholder(/Ask about your documents/i).fill("What is zero trust?");
  await page.getByRole("button", { name: /Send/i }).click();

  // Streaming response appears
  await expect(page.getByText(/Based on the provided documents/i)).toBeVisible({ timeout: 60_000 });

  // Sources appear (citations)
  await expect(page.getByText(/Sources/i)).toBeVisible({ timeout: 15_000 });

  // Cleanup: delete the document
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await page.getByTitle(/Delete/i).first().click();
  await page.getByRole("button", { name: /Delete/i }).last().click();
  await expect(page.getByText(marker)).toHaveCount(0);
});
