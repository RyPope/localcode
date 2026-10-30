// Regenerates the README screenshots from a running instance (default http://localhost:4173).
//   npm run screenshots [-- --base-url http://localhost:4173]
// Use an instance with some solved problems so the progress views have data.
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const flag = process.argv.indexOf("--base-url");
const base = flag > 0 ? process.argv[flag + 1] : "http://localhost:4173";
const out = fileURLToPath(new URL("../../docs/images/", import.meta.url));
const viewport = { width: 1440, height: 900 };

async function shoot(page, name, url, prepare) {
  await page.goto(base + url, { waitUntil: "networkidle" });
  if (prepare) await prepare(page);
  await page.waitForTimeout(400);
  await page.screenshot({ path: `${out}${name}.png` });
  console.log(`docs/images/${name}.png`);
}

const browser = await chromium.launch();
await mkdir(out, { recursive: true });
for (const theme of ["dark", "light"]) {
  const context = await browser.newContext({ viewport, deviceScaleFactor: 1.5, colorScheme: theme });
  await context.addInitScript((t) => localStorage.setItem("localcode.theme", t), theme);
  const page = await context.newPage();
  if (theme === "light") {
    await shoot(page, "workspace-light", "/problems/merge-intervals", async (p) => {
      await p.getByRole("tab", { name: "Solutions" }).click();
      await p.getByRole("button", { name: "Open in editor" }).click();
      await p.getByRole("button", { name: /^Submit/ }).click();
      await p.getByText(/testcases passed · full suite/).waitFor({ timeout: 60_000 });
      await p.getByRole("tab", { name: "Description" }).click();
    });
    await context.close();
    continue;
  }
  await shoot(page, "problems", "/?company=google&window=6m");
  await shoot(page, "company", "/companies/google?window=6m");
  await shoot(page, "workspace", "/problems/two-sum", async (p) => {
    await p.getByRole("tab", { name: "Solutions" }).click();
    await p.getByRole("button", { name: "Open in editor" }).click();
    await p.getByRole("button", { name: /^Submit/ }).click();
    await p.getByText(/testcases passed · full suite/).waitFor({ timeout: 60_000 });
    await p.getByRole("tab", { name: "Description" }).click();
  });
  await shoot(page, "solutions", "/problems/longest-substring-without-repeating-characters", async (p) => {
    await p.getByRole("tab", { name: "Solutions" }).click();
    await p.locator(".prose .katex").first().waitFor();
  });
  await shoot(page, "run-result", "/problems/two-sum", async (p) => {
    await p.getByRole("tab", { name: "Solutions" }).click();
    await p.getByRole("button", { name: "Open in editor" }).click();
    await p.getByRole("button", { name: /^Run/ }).click();
    await p.getByText(/testcases passed$/).waitFor({ timeout: 60_000 });
  });
  await shoot(page, "progress", "/progress");
  await shoot(page, "setup", "/setup");
  await context.close();
}
await browser.close();
