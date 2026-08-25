# Тестовые сценарии и фактический прогон

Дата прогона: **2026-08-24**. Среда: macOS + Docker Desktop. Backend, frontend и Compose-сценарии реально выполнены. PASS ставится только автоматизированной, статической или явно указанной live-проверке.

## TC-01 — Получение публичной ленты (positive, integration)

**Related requirement:** FR-01
**Related acceptance criterion:** AC-01
**Preconditions:** TestClient с fake public feed.
**Steps:** 1. Вызвать `/public/news?limit=10`. 2. Проверить status и schema.
**Expected result:** HTTP 200; массив не длиннее limit.
**Actual result:** PASS в полном backend suite; реализован `test_public_news_endpoints`.
**Status:** PASS

## TC-02 — Новость отсутствует (negative, integration)

**Related requirement:** FR-02
**Related acceptance criterion:** AC-02
**Preconditions:** ID 404 отсутствует.
**Steps:** 1. GET `/public/news/404`.
**Expected result:** HTTP 404.
**Actual result:** PASS в полном backend suite; покрыт `test_public_news_endpoints`.
**Status:** PASS

## TC-03 — Верхняя граница MOEX limit (boundary, integration)

**Related requirement:** FR-03
**Related acceptance criterion:** AC-03
**Preconditions:** Fake MOEX service.
**Steps:** 1. GET с `limit=999`. 2. Проверить фактический limit и число items.
**Expected result:** HTTP 200; limit зажат до 20.
**Actual result:** PASS в полном backend suite; покрыт `test_public_moex_limit_is_clamped`.
**Status:** PASS

## TC-04 — MOEX недоступен (negative, unit)

**Related requirement:** FR-03, NFR-03
**Related acceptance criterion:** AC-03
**Preconditions:** HTTP-клиент MOEX выбрасывает ошибку.
**Steps:** 1. Запросить котировки. 2. Проверить fallback contract.
**Expected result:** `fallback=true`, тикеры есть, цены null.
**Actual result:** PASS в полном backend suite; сценарий реализован в `test_moex_service.py`.
**Status:** PASS

## TC-05 — Регистрация, вход, `/me`, logout (positive, integration)

**Related requirement:** FR-04, FR-05, FR-06, FR-07
**Related acceptance criterion:** AC-04, AC-06, AC-07
**Preconditions:** Свободный email, fake repository.
**Steps:** 1. Register. 2. Login. 3. GET `/me`. 4. Выполнить refresh и повторить старый token. 5. Logout.
**Expected result:** Успешные основные ответы; старый token после rotation и сохранённый token после logout отклоняются.
**Actual result:** PASS в полном backend suite; после добавления уникального `jti` rotation/replay покрыты отдельным integration test.
**Status:** PASS

## TC-06 — Дублирующий email (negative, integration)

**Related requirement:** FR-04, NFR-04
**Related acceptance criterion:** AC-05
**Preconditions:** Email уже зарегистрирован.
**Steps:** 1. Повторить регистрацию.
**Expected result:** HTTP 400; второй пользователь не создан.
**Actual result:** PASS в полном backend suite; покрыт `test_register_duplicate_email_returns_400`.
**Status:** PASS

## TC-07 — Граница длины chat message (boundary, API)

**Related requirement:** FR-09, NFR-02
**Related acceptance criterion:** AC-10, AC-11
**Preconditions:** Валидный JWT/permission.
**Steps:** 1. Отправить `""`. 2. Отправить 4000 символов. 3. Отправить 4001 символ.
**Expected result:** 422, успешная передача 4000 символов при доступном обработчике, 422.
**Actual result:** PASS: integration tests отклонили 0/4001 символ и приняли 4000 символов; live API также вернул 422 для пустого и 4001-символьного ввода.
**Status:** PASS

## TC-08 — Недоступный Ollama (negative, integration)

**Related requirement:** FR-09
**Related acceptance criterion:** AC-11
**Preconditions:** Ollama URL недоступен.
**Steps:** 1. POST `/chat/send`.
**Expected result:** HTTP 503 `CHAT_MODEL_UNAVAILABLE`.
**Actual result:** PASS в integration test с dependency override: HTTP 503 и `CHAT_MODEL_UNAVAILABLE`.
**Status:** PASS

## TC-09 — Нормализация тикеров (positive/boundary, API)

**Related requirement:** FR-08
**Related acceptance criterion:** AC-08
**Preconditions:** Валидный JWT и permission.
**Steps:** 1. PATCH с `sber`, ` SBER `. 2. GET profile.
**Expected result:** В БД и ответе один `SBER`.
**Actual result:** PASS в live Compose: `sber` и ` SBER ` сохранены как единственный `SBER`.
**Status:** PASS

## TC-10 — Неизвестный сектор (negative, API)

**Related requirement:** FR-08, NFR-02
**Related acceptance criterion:** AC-09
**Preconditions:** Сохранён исходный профиль.
**Steps:** 1. PATCH с неизвестным сектором. 2. Повторно прочитать профиль.
**Expected result:** HTTP 422; данные не изменены.
**Actual result:** PASS в live Compose: неизвестный сектор отклонён HTTP 422 до обновления профиля.
**Status:** PASS

## TC-11 — Запрет admin endpoint (negative, integration)

**Related requirement:** FR-12
**Related acceptance criterion:** AC-12
**Preconditions:** JWT обычного пользователя.
**Steps:** 1. GET `/admin/users`.
**Expected result:** HTTP 403.
**Actual result:** PASS в полном backend suite; покрыт `test_admin_users_list_forbidden_without_permission`.
**Status:** PASS

## TC-12 — Неизвестная роль (negative, integration)

**Related requirement:** FR-13
**Related acceptance criterion:** AC-12
**Preconditions:** JWT администратора.
**Steps:** 1. PUT roles с `superadmin`.
**Expected result:** HTTP 400; роли не заменены.
**Actual result:** PASS в полном backend suite; integration test проверяет HTTP 400 и неизменность исходных ролей.
**Status:** PASS

## TC-13 — Docker Compose configuration (integration/static)

**Related requirement:** NFR-06
**Related acceptance criterion:** —
**Preconditions:** Docker CLI.
**Steps:** 1. `docker compose config --quiet`. 2. Повторить с production override.
**Expected result:** Обе конфигурации валидны.
**Actual result:** Обе команды завершились с exit code 0; dev-контур собран и четыре сервиса вышли в healthy.
**Status:** PASS

## TC-14 — CI workflow contract (static)

**Related requirement:** NFR-05
**Related acceptance criterion:** —
**Preconditions:** `.github/workflows/ci.yml` существует.
**Steps:** 1. Проверить triggers. 2. Проверить backend/frontend jobs. 3. Убедиться, что secrets не захардкожены.
**Expected result:** push/PR запускают tests/typecheck/build; production secrets отсутствуют.
**Actual result:** Структура и команды проверены статически; локально выполнены те же backend/frontend команды. Реальный GitHub Actions run ещё не выполнялся.
**Status:** PASS

## TC-15 — Персональная лента без GigaChat (integration/unit)

**Related requirement:** FR-14, NFR-03
**Related acceptance criterion:** AC-13
**Preconditions:** Пользователь с профилем; GigaChat отключён; RSS fake содержит материал.
**Steps:** 1. Получить персональную ленту. 2. Проверить rules payload и отсутствие ошибки внешнего AI.
**Expected result:** Возвращён валидный news block, анализ построен rules engine и может быть сохранён в cache/news.
**Actual result:** PASS в полном backend suite; соответствующие ветви покрываются `test_personal_news_rss.py` и unit tests аналитики.
**Status:** PASS

## TC-16 — Сохранение обмена и чтение истории (integration)

**Related requirement:** FR-10, FR-11
**Related acceptance criterion:** AC-10
**Preconditions:** Валидный JWT/permissions; доступные chat repositories и успешный ответ модели.
**Steps:** 1. Отправить корректное сообщение. 2. Вызвать `GET /chat/history`. 3. Проверить принадлежность и порядок user/FinPulse сообщений.
**Expected result:** В default chat текущего пользователя сохранены вопрос и ответ; история не содержит сообщений другого пользователя.
**Actual result:** PASS: integration test отправляет сообщение через `ChatWithLLM`, читает историю и отдельно подтверждает пустую историю другого пользователя.
**Status:** PASS

## Итог

PASS: 16; FAIL: 0; BLOCKED: 0; NOT RUN: 0. Backend: 69 tests passed. Frontend: 9 Vitest tests и 3 Playwright E2E tests passed. Live Compose: регистрация/вход, профиль, Ollama-чат, история, публичные endpoints, PostgreSQL и reverse proxy проверены. Внешние RSS в момент live-проверки отвечали с timeout, поэтому публичная лента корректно вернула пустой массив через предусмотренную деградацию.
