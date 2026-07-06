# FinPulse MVP Apps

Локальный MVP состоит из трех клиентских поверхностей и общего backend:

- `frontend/` — существующий React/Vite web-клиент.
- `frontend/src-tauri/` — macOS desktop-приложение FinPulse через Tauri.
- `mobile/` — iPhone-приложение на Expo React Native.
- `backend/` — FastAPI API, PostgreSQL-интеграция, GigaChat и Ollama.

AI-функции остаются только на backend. GigaChat-ключи, параметры Ollama и остальные секреты должны храниться в `.env` для Docker/backend и не должны попадать в web, Tauri или Expo bundle.

## Backend и web

Запуск локальной инфраструктуры:

```bash
docker compose up -d --build
```

После запуска:

- Web: `http://localhost:3000`
- API через frontend/nginx: `http://localhost:3000/api`
- Backend напрямую: `http://localhost:8000`
- Ollama внутри Docker-сети: `http://ollama:11434`

GigaChat работает через backend при включенных env-переменных `NEWS_USE_LLM`, `NEWS_LLM_FOR_PUBLIC_RSS` и заполненном `GIGACHAT_AUTH_KEY`. Чатовая модель Ollama вызывается backend по `OLLAMA_URL`.

## macOS приложение

Tauri настроен внутри `frontend/`, потому что desktop MVP использует существующий React/Vite интерфейс.

Dev-запуск:

```bash
cd frontend
npm run tauri:dev
```

Production-сборка:

```bash
cd frontend
npm run tauri:build
```

Для `tauri:build` на Mac должен быть установлен Rust/Cargo и системные зависимости Tauri. Если Rust отсутствует, web-сборка все равно проверяется через `npm run build`, но `.app` не будет собран до установки Rust.

В dev-режиме Vite слушает `http://localhost:3000` и проксирует `/api` в `http://localhost:8000`.

## iPhone приложение

Expo-приложение находится в `mobile/`.

Перед запуском iPhone должен быть в той же Wi-Fi сети, что и Mac. Узнать IP Mac:

```bash
ipconfig getifaddr en0
```

Создать локальный env-файл в `mobile/.env`:

```env
EXPO_PUBLIC_API_BASE_URL=http://<MAC_LAN_IP>:3000/api
```

Пример:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.10:3000/api
```

На iPhone нельзя использовать `localhost`, потому что для телефона это сам iPhone, а не Mac.

Запуск:

```bash
cd mobile
npm start
```

Либо:

```bash
cd mobile
npm run ios
```

`npm start` подходит для Expo Go на iPhone по QR-коду. `npm run ios` запускает iOS Simulator и требует полный Xcode из App Store. Для локального MVP backend, PostgreSQL, GigaChat-интеграция и Ollama должны быть запущены на Mac через Docker Compose.

## Установка на iPhone как отдельное приложение

Для установки без Expo Go используется EAS internal distribution. Это создает iOS `.ipa` и install-ссылку для конкретных зарегистрированных устройств.

Что потребуется:

- Expo account.
- Apple Developer Program membership для ad hoc/internal iOS distribution.
- iPhone, зарегистрированный в provisioning profile через UDID.

Команды:

```bash
cd mobile
npm run eas:login
```

Затем зарегистрировать iPhone:

```bash
cd mobile
npm run eas:devices
```

EAS покажет QR-код или URL. Открой его на iPhone и установи профиль, чтобы EAS получил UDID устройства.

После регистрации устройства собрать installable iOS build:

```bash
cd mobile
npm run build:ios:preview
```

Во время сборки EAS попросит войти в Apple Developer account и сможет автоматически подготовить signing credentials/provisioning profile. После завершения сборки EAS даст ссылку, по которой приложение можно установить на зарегистрированный iPhone.

Ограничения Apple:

- Ad hoc build установится только на устройства, добавленные в provisioning profile.
- При добавлении нового iPhone нужна новая сборка или re-sign.
- Для обычной публичной установки нужен TestFlight/App Store.

## PWA на iPhone без Apple Developer

Web-клиент поддерживает установку на домашний экран iPhone как PWA: подключены `manifest.webmanifest`,
`apple-touch-icon`, iOS meta-теги и service worker для production-сборки.

Локальный запуск:

```bash
docker compose up -d --build
```

Затем узнать IP Mac:

```bash
ipconfig getifaddr en0
```

На iPhone открыть Safari:

```text
http://<MAC_LAN_IP>:3000
```

Например:

```text
http://192.168.1.10:3000
```

После открытия:

```text
Share -> Add to Home Screen -> Add
```

На домашнем экране появится иконка `FinPulse`. Для полноценной PWA-работы service worker требует HTTPS
или localhost, поэтому в локальной Wi-Fi демонстрации главное преимущество этого режима — быстрый запуск
через Safari и установка иконки без Apple Developer Program.

## Проверки

Web:

```bash
cd frontend
npm run typecheck
npm run build
```

Mobile:

```bash
cd mobile
npm run typecheck
```

## Что остается после MVP

- Поднять backend на HTTPS-сервер для работы вне домашней Wi-Fi сети.
- Настроить EAS Build/TestFlight для iPhone.
- Настроить подпись, иконки и notarization для macOS `.app`.
- Расширить mobile UI: редактирование профиля, фильтры новостей, управление чат-сессиями.
