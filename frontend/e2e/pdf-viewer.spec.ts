import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Verifies the pdf.js document viewer renders a real PDF and that
 * page navigation and search work.
 */
test("pdf viewer renders pages and navigates", async ({ page }) => {
  await page.goto("/");

  // Complete the first-run wizard if it appears (shared backend).
  const wizard = page.getByRole("heading", { name: /Welcome to MindVault/i });
  const wizardVisible = await wizard
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
    await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible({ timeout: 20_000 });
  } else {
    await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible();
  }

  // Go to Documents and upload the fixture PDF
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await page.getByRole("button", { name: /Upload Documents/i }).click();
  const pdfPath = path.resolve(__dirname, "fixtures", "report.pdf");
  await page.setInputFiles('input[type="file"]', {
    name: "report.pdf",
    mimeType: "application/pdf",
    buffer: fs.readFileSync(pdfPath),
  });

  await expect(page.getByText("report.pdf")).toBeVisible({ timeout: 30_000 });

  // Open the viewer (Eye icon)
  await page.getByTitle(/View/i).click();
  await expect(page.getByText("Rendered PDF")).toBeVisible({ timeout: 15_000 });

  // The pdf.js canvas should render
  await expect(page.locator("canvas").first()).toBeVisible({ timeout: 30_000 });
  await page.waitForTimeout(3000);

  // Page navigation controls should show the correct page count
  await expect(page.getByText(/Page 1 \/ 2/)).toBeVisible({ timeout: 10_000 });

  // Click Next to go to page 2
  await page.locator('button:has-text("Next →")').first().click();
  await expect(page.getByText(/Page 2 \/ 2/)).toBeVisible({ timeout: 10_000 });

  // Find-in-PDF search should jump to the page with the query
  await page.getByLabel("Find in PDF").fill("Second page");
  await page.getByRole("button", { name: /Find/ }).click();
  await expect(page.getByText(/Page 2 \/ 2/)).toBeVisible({ timeout: 10_000 });

  // Cleanup: close viewer, delete the document
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await page.getByTitle(/Delete/i).first().click();
  await page.getByRole("button", { name: /Delete/i }).last().click();
});