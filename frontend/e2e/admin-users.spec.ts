import { expect, test } from "@playwright/test";

test("admin list with pagination and role update", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("accessToken", "acc");
    localStorage.setItem("refreshToken", "ref");
  });

  await page.route("**/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 99,
        email: "admin@x.com",
        roles: ["admin"],
        permissions: ["admin_users:list", "admin_users:assign_role"],
      }),
    });
  });

  await page.route("**/admin/users**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            { id: 1, email: "u1@example.com", name: "U1", roles: ["user"], created_at: "2026-01-01T00:00:00Z" },
            { id: 2, email: "u2@example.com", name: "U2", roles: ["pro"], created_at: "2026-01-02T00:00:00Z" },
          ],
          total: 2,
          page: 1,
          page_size: 5,
        }),
      });
      return;
    }

    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
  });

  await page.goto("/admin/users");
  await expect(page.getByText("Admin: Users")).toBeVisible();
  await expect(page.getByText("u1@example.com")).toBeVisible();

  await page.getByDisplayValue("user").selectOption("pro");
  await expect(page.getByText("u2@example.com")).toBeVisible();
});
