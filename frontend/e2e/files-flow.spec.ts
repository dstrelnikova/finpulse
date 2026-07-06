import { expect, test } from "@playwright/test";

test("files list and upload error state", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("accessToken", "acc");
    localStorage.setItem("refreshToken", "ref");
  });

  await page.route("**/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 2,
        email: "pro@x.com",
        roles: ["pro"],
        permissions: ["chat:use", "chat:attach_files"],
      }),
    });
  });

  await page.route("**/chat", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{ id: 7, title: "Main", topic: null, is_default: true }]),
      });
      return;
    }
    await route.continue();
  });

  await page.route("**/files/by-chat/7", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
  });

  await page.route("**/files/init-upload", async (route) => {
    await route.fulfill({
      status: 413,
      contentType: "application/json",
      body: JSON.stringify({ detail: "FILE_TOO_LARGE" }),
    });
  });

  await page.goto("/files?chatId=7");
  await expect(page.getByText("Файлов нет")).toBeVisible();

  await page.getByRole("button", { name: "Загрузить" }).click();
  await page.setInputFiles('input[type="file"]', {
    name: "huge.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("x".repeat(1024)),
  });

  await expect(page.getByText("Файл слишком большой")).toBeVisible();
});
