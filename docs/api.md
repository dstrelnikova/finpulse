# REST API FinPulse

Backend публикует OpenAPI 3 через FastAPI. При прямом development-доступе Swagger UI расположен на `http://localhost:8000/docs`, OpenAPI JSON — `/openapi.json`; через Nginx — `http://localhost:3000/api/docs` и `/api/openapi.json`. Префикс `/api` удаляется proxy и не является частью backend route.

Формат по умолчанию — JSON. Защищённые методы принимают `Authorization: Bearer <access_token>`. Ошибки FastAPI имеют вид `{"detail": ...}`; ошибки валидации — HTTP 422 со списком нарушений.

## Карта endpoint'ов AS-IS

| Method | URL | Доступ | Назначение |
|---|---|---|---|
| GET | `/`, `/healthz`, `/readyz` | Public | Метаданные и health/readiness |
| POST | `/auth/register` | Public | Регистрация |
| POST | `/auth/login`, `/auth/refresh` | Public | Выдача/обновление JWT |
| POST | `/auth/logout` | JWT | Отзыв сохранённого refresh token |
| GET | `/me` | JWT | ID, email, роли и permissions |
| GET/PATCH | `/profile` | JWT + permission | Чтение/частичное изменение профиля |
| GET | `/meta/options` | Public | Справочники профиля |
| GET | `/public/news` | Public | Публичная лента |
| GET | `/public/news/{news_id}` | Public | Новость по ID |
| GET | `/public/news/slug/{slug}` | Public | Новость по slug |
| GET | `/public/moex/imoex/quotes` | Public | Выборка котировок |
| GET | `/news/feed`, `/news/{news_id}` | JWT + `news:list` | Персональная лента/элемент |
| POST | `/chat/send` | JWT + `chat:use` | Сообщение в Ollama |
| GET/DELETE | `/chat/history` | JWT + permission | История/очистка default chat |
| GET | `/chat` | JWT + `chat:use` | Default chat session |
| GET | `/admin/users` | JWT + `admin_users:list` | Фильтры и пагинация пользователей |
| PUT | `/admin/users/{user_id}/roles` | JWT + `admin_users:assign_role` | Замена ролей |

`/robots.txt` и `/sitemap.xml` возвращают text/XML и исключены из OpenAPI.

## Ключевые контракты

### Регистрация — `POST /auth/register`

Body:

```json
{"name":"Darya","email":"darya@example.com","password":"123456"}
```

`name`: 2–50 символов; email валиден; password минимум 6 символов. Успех AS-IS: HTTP 200 и `UserOut` без password. Дублирующий email: 400. Невалидный body: 422. Rate limit: 429.

### Вход/refresh — `POST /auth/login`, `POST /auth/refresh`

Login body содержит email и password; ответ 200:

```json
{"access_token":"...","refresh_token":"...","token_type":"bearer"}
```

Неверные credentials — 401. Refresh принимает `{"refresh_token":"..."}`, проверяет наличие в БД, expiry, подпись и `type=refresh`, ротирует пару; ошибка — 401.

### Публичные новости — `GET /public/news`

Query: `limit` default 50, эффективный диапазон 1–100. Значение вне диапазона AS-IS не даёт 422, а приводится к ближайшей границе. Ответ 200 — массив:

```json
[{"id":1,"slug":"...","title":"...","source":"...","url":"https://...","summary":"...","bullets":["..."],"conclusion":"...","risks":["..."],"indicator":{"impact":"neutral","confidence":"medium","rationale":["..."]},"asof":"2026-08-24"}]
```

Холодный старт может быть медленным из-за внешних источников. Пустой результат — HTTP 200 `[]`. Принудительное обновление не выставлено в публичный API: его запускает внутренний scheduler. `GET /public/news/{int}` и `/slug/{str}` возвращают `NewsBlockOut` либо 404.

### Котировки — `GET /public/moex/imoex/quotes`

Query `limit` default 12, вручную ограничивается 1–20. Ответ 200 содержит `index`, `source`, UTC `fetched_at`, `fallback`, `items`. Недоступность MOEX — не HTTP-ошибка: `fallback=true`, тикеры сохранены, цены `null`.

### Профиль — `PATCH /profile`

Все поля optional: `market` допускает только `RU` и фактически игнорируется при update; `investment_horizon`, `experience_level`, `risk_level` — enum; `tickers` проверяются regex, trim/uppercase/deduplicate; `sectors` — справочник, lowercase/deduplicate. Успех 200 `UserOut`; без/неверный JWT — 401; без permission — 403; неверные значения — 422.

### Чат — `POST /chat/send`

```json
{"message":"Что влияет на банковский сектор?","chat_id":null}
```

`message`: 1–4000 символов. `chat_id` optional, но AS-IS игнорируется: используется default chat. Успех 200 `{"answer":"...","chat_id":1}`. Ошибки: 401, 403, 422; недоступность/неприемлемый ответ Ollama преобразуется в 503 `CHAT_MODEL_UNAVAILABLE`.

`GET /chat/history?limit=50` принимает 1–200 и возвращает сообщения; `DELETE /chat/history` возвращает `{"ok":true,"deleted":N}`.

### Администрирование

`GET /admin/users`: `q` 1–200, `role` до 64, `sort_by=created_at|email|role`, `sort_dir=asc|desc`, `page>=1`, `page_size=1..100`. Ответ: `items`, `total`, `page`, `page_size`.

`PUT /admin/users/{user_id}/roles` принимает `{"roles":["user"]}` (непустой массив). Успех 200; неизвестный пользователь/роль — 400; недостаток permission — 403.

## Swagger/OpenAPI review

Response models заданы для основных ресурсных endpoint'ов. Метаданные приложения и chat endpoint дополнены. GAP: часть простых dict-ответов (`/me`, logout, set roles, health) не имеет отдельного response model; ручной clamp публичных limit не отражает фактические границы в OpenAPI. Это не мешает текущему поведению, но снижает полноту машинного контракта.
