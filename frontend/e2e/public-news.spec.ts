import { expect, test } from "@playwright/test";

test("public news feed renders and filters real response contract", async ({ page }) => {
  await page.route("**/api/public/news**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: 1,
          slug: "market-growth",
          title: "Индекс МосБиржи завершил день ростом",
          source: "Test RSS",
          url: "https://example.com/market-growth",
          summary: "Российский рынок показал положительную динамику.",
          bullets: ["Индекс вырос по итогам торгов"],
          conclusion: "Сигнал умеренно позитивен для широкого рынка.",
          market_meaning: "Рост поддерживает краткосрочные ожидания участников рынка.",
          affected_segments: ["индекс МосБиржи"],
          risks: ["Движение может оказаться краткосрочным"],
          indicator: {
            impact: "positive",
            confidence: "high",
            importance: "high",
            rationale: ["Рост индекса отражает преобладание спроса"],
          },
          asof: "2026-08-24",
        },
      ]),
    });
  });

  await page.goto("/news/public");

  await expect(page.getByRole("heading", { name: "Публичная лента новостей" })).toBeVisible();
  await expect(page.getByText("Индекс МосБиржи завершил день ростом")).toBeVisible();
  await expect(page.getByText("Позитив", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Негатив/ }).click();
  await expect(page.getByText("По выбранному фильтру пока нет новостей.")).toBeVisible();
});
