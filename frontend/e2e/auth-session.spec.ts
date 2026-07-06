import { expect, test } from "@playwright/test";

test("login, guarded route and logout", async ({ page }) => {
  await page.route("**/me", async (route) => {
    const auth = route.request().headers()["authorization"];
    if (!auth) {
      await route.fulfill({ status: 401, body: "{}" });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 1, email: "u@x.com", roles: ["user"], permissions: ["profile:read_own"] }),
    });
  });

  await page.route("**/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "acc", refresh_token: "ref", token_type: "bearer" }),
    });
  });

  await page.route("**/auth/logout", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ detail: "Logged out" }) });
  });

  await page.route("**/profile", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          name: "U",
          email: "u@x.com",
          market: "RU",
          investment_horizon: null,
          experience_level: null,
          risk_level: null,
          tickers: [],
          sectors: [],
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/login");
  await page.locator('input[autocomplete="email"]').fill("u@x.com");
  await page.locator('input[autocomplete="current-password"]').fill("123456");
  await page.getByRole("button", { name: "Войти" }).click();

  await expect(page).toHaveURL(/\/profile/);
  await expect(page.getByText("Личный кабинет")).toBeVisible();

  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page.getByRole("link", { name: "Войти" })).toBeVisible();
});
