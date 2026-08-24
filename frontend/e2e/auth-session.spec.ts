import { expect, test } from "@playwright/test";

test("login, guarded route and logout", async ({ page }) => {
  await page.route("**/api/me", async (route) => {
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

  await page.route("**/api/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "acc", refresh_token: "ref", token_type: "bearer" }),
    });
  });

  await page.route("**/api/auth/logout", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ detail: "Logged out" }) });
  });

  await page.route("**/api/profile", async (route) => {
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
  await expect(page.getByRole("link", { name: "Регистрация" })).toBeVisible();

  const email = page.locator('input[autocomplete="email"]');
  const password = page.locator('input[autocomplete="current-password"]');
  const submit = page.getByRole("button", { name: "Войти" });

  await email.fill("u@x.com");
  await password.fill("123456");
  await expect(email).toHaveValue("u@x.com");
  await expect(password).toHaveValue("123456");
  await expect(submit).toBeEnabled();
  await submit.click();

  await expect(page).toHaveURL(/\/profile/);
  await expect(page.getByText("Личный кабинет")).toBeVisible();

  await page.getByRole("button", { name: "Выйти" }).click();
  const logoutDialog = page.getByRole("dialog", { name: "Выйти из FinPulse?" });
  await expect(logoutDialog).toBeVisible();
  await logoutDialog.getByRole("button", { name: "Выйти" }).click();
  await expect(page.getByRole("link", { name: "Войти" })).toBeVisible();
});
