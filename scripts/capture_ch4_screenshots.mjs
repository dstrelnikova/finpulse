import playwright from "../frontend/node_modules/playwright/index.js";

const { chromium } = playwright;

const BASE_URL = "http://127.0.0.1:3000";
const OUT_DIR = "report_assets/screenshots_ch4";

const accessToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJyZXBvcnQuZmlucHVsc2UuZGVtb0BnbWFpbC5jb20iLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc4NTE4Mjc2fQ.U7_vbtuBq_p8-Buzo_DWBZPrkQxQvcfbc3WsL8ZIiao";
const refreshToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZW1haWwiOiJyZXBvcnQuZmlucHVsc2UuZGVtb0BnbWFpbC5jb20iLCJ0eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3OTEyMjE3Nn0.UDW2D-LpHOtCpX-mcHD2VIayJRnPBVZXPJcgeFOoEk0";

const newsSlug = "фондовые-индексы-атр-не-показали-единой-динамики-2cafee8a";

const viewports = {
  desktop: { width: 1440, height: 1000 },
  mobile: { width: 390, height: 844 },
};

async function makePage(browser, viewport, authenticated = false) {
  const context = await browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    locale: "ru-RU",
  });

  if (authenticated) {
    await context.addInitScript(
      ({ accessToken, refreshToken }) => {
        localStorage.setItem("accessToken", accessToken);
        localStorage.setItem("refreshToken", refreshToken);
      },
      { accessToken, refreshToken },
    );
  }

  const page = await context.newPage();
  return { context, page };
}

async function capture(browser, name, path, viewportName, opts = {}) {
  const { context, page } = await makePage(browser, viewports[viewportName], opts.authenticated);
  await page.goto(`${BASE_URL}${path}`, { waitUntil: "networkidle", timeout: 120000 });

  if (opts.after) {
    await opts.after(page);
  }

  await page.screenshot({
    path: `${OUT_DIR}/${name}.png`,
    fullPage: opts.fullPage ?? true,
  });
  await context.close();
}

async function main() {
  const browser = await chromium.launch();

  await capture(browser, "4_1_1_landing_desktop", "/", "desktop");
  await capture(browser, "4_1_2_landing_mobile", "/", "mobile");
  await capture(browser, "4_1_3_register_desktop", "/register", "desktop");
  await capture(browser, "4_1_4_login_desktop", "/login", "desktop");

  await capture(browser, "4_1_5_public_news_desktop", "/news/public", "desktop", {
    after: async (page) => {
      await page.getByText("Публичная лента новостей").waitFor({ timeout: 120000 });
      await page.getByText("Материалов").waitFor({ timeout: 120000 });
    },
  });
  await capture(browser, "4_1_6_public_news_mobile", "/news/public", "mobile", {
    after: async (page) => {
      await page.getByText("Публичная лента новостей").waitFor({ timeout: 120000 });
    },
  });
  await capture(browser, "4_1_7_news_filters_desktop", "/news/public", "desktop", {
    after: async (page) => {
      await page.getByRole("button", { name: /Негатив/ }).click();
      await page.waitForTimeout(500);
    },
  });
  await capture(browser, "4_1_8_news_item_desktop", `/news/public/${newsSlug}`, "desktop", {
    after: async (page) => {
      await page.getByText("Вернуться к ленте").waitFor({ timeout: 120000 });
      await page.waitForTimeout(800);
    },
  });
  await capture(browser, "4_1_9_news_item_mobile", `/news/public/${newsSlug}`, "mobile", {
    after: async (page) => {
      await page.getByText("Вернуться к ленте").waitFor({ timeout: 120000 });
      await page.waitForTimeout(800);
    },
  });

  await capture(browser, "4_1_10_chat_desktop", "/chat", "desktop", {
    authenticated: true,
    after: async (page) => {
      await page.getByText("Личный чат").waitFor({ timeout: 120000 });
      await page.waitForTimeout(1000);
    },
  });
  await capture(browser, "4_1_11_chat_mobile", "/chat", "mobile", {
    authenticated: true,
    after: async (page) => {
      await page.getByText("Личный чат").waitFor({ timeout: 120000 });
      await page.waitForTimeout(1000);
    },
  });
  await capture(browser, "4_1_12_profile_desktop", "/profile", "desktop", {
    authenticated: true,
    after: async (page) => {
      await page.getByText("Дарья Стрельникова").waitFor({ timeout: 120000 });
      await page.waitForTimeout(500);
    },
  });
  await capture(browser, "4_1_13_profile_mobile", "/profile", "mobile", {
    authenticated: true,
    after: async (page) => {
      await page.getByText("Дарья Стрельникова").waitFor({ timeout: 120000 });
      await page.waitForTimeout(500);
    },
  });
  await capture(browser, "4_1_14_moex_desktop", "/market/moex", "desktop", {
    after: async (page) => {
      await page.getByText("MOEX").first().waitFor({ timeout: 120000 });
      await page.waitForTimeout(1500);
    },
  });
  await capture(browser, "4_1_15_moex_mobile", "/market/moex", "mobile", {
    after: async (page) => {
      await page.getByText("MOEX").first().waitFor({ timeout: 120000 });
      await page.waitForTimeout(1500);
    },
  });

  await capture(browser, "4_2_1_login_wrong_credentials", "/login", "desktop", {
    after: async (page) => {
      await page.getByLabel("Почта").fill("wrong@example.com");
      await page.getByLabel("Пароль").fill("WrongPass123!");
      await page.getByRole("button", { name: "Войти" }).click();
      await page.getByText("Incorrect email or password").waitFor({ timeout: 120000 });
    },
  });
  await capture(browser, "4_2_2_register_password_mismatch", "/register", "desktop", {
    after: async (page) => {
      await page.getByLabel("Имя").fill("Тестовый пользователь");
      await page.getByLabel("Почта").fill("new.demo.user@gmail.com");
      await page.getByLabel("Пароль").fill("ReportPass123!");
      await page.getByLabel("Подтвердите пароль").fill("OtherPass123!");
      await page.getByRole("button", { name: "Зарегистрироваться" }).click();
      await page.getByText("Пароли не совпадают").waitFor({ timeout: 120000 });
    },
  });
  await capture(browser, "4_2_3_protected_route_redirect", "/profile", "desktop", {
    after: async (page) => {
      await page.getByText("Войти").waitFor({ timeout: 120000 });
      await page.waitForTimeout(500);
    },
  });
  await capture(browser, "4_2_4_chat_empty_disabled", "/chat", "desktop", {
    authenticated: true,
    after: async (page) => {
      await page.getByText("Личный чат").waitFor({ timeout: 120000 });
      await page.waitForTimeout(500);
    },
  });

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
