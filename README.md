# FinPulse — AI-ассистент для российского фондового рынка

FinPulse — full-stack приложение, которое собирает финансовые новости, выделяет ключевые факты и объясняет их возможное влияние на российский рынок. Пользователь получает публичную новостную ленту, котировки ликвидных бумаг, персональные материалы и чат с AI-ассистентом.

Приложение объединяет обработку финансовых данных, LLM-интеграции, API и пользовательский интерфейс. FinPulse не является инвестиционной рекомендацией и не использует реальные средства пользователей.

## Что реализовано

- публичная лента новостей из RSS-источников Банка России, Московской биржи, Интерфакса и Коммерсанта;
- извлечение текста статьи и структурированный анализ новости: краткое содержание, факты, вывод, риски и индикатор влияния;
- GigaChat для анализа публичных новостей с автоматическим переходом на rules-based обработку при недоступности API;
- локальный чат-ассистент на Ollama с учётом истории диалога и профиля пользователя;
- персонализация по интересующим бумагам, секторам, горизонту и уровню риска;
- котировки выборки ликвидных бумаг через MOEX ISS с fallback-ответом при недоступности источника;
- регистрация, JWT-аутентификация, обновление токенов, роли и права доступа;
- хранение пользователей, профилей, новостей и истории чатов в PostgreSQL;
- административный раздел для управления пользователями;
- адаптивный React-интерфейс и macOS-оболочка на Tauri;
- unit-, integration- и e2e-тесты ключевых сценариев.

## Как обрабатывается новость

```text
RSS-источник
    ↓
загрузка анонса и доступного текста статьи
    ↓
GigaChat → структурированный JSON
    ↓ при ошибке или отключённом LLM
rules-based анализ
    ↓
PostgreSQL → FastAPI → React-интерфейс
```

LLM не обучается внутри проекта: FinPulse интегрирует готовые модели через API и локальный Ollama. Основная инженерная задача — подготовка контекста, проверка структуры ответа, обработка ошибок и безопасный fallback.

## Инженерные решения

- Функциональные и нефункциональные требования, сценарии использования и критерии приёмки связаны с тестовыми сценариями в матрице трассируемости.
- Клиент-серверная архитектура, REST API и модель данных PostgreSQL описаны в технической документации.
- React/FastAPI/PostgreSQL/Ollama-контур запускается через Docker Compose.
- В документации зафиксированы известные ограничения и границы текущей реализации.

## Технологии

| Слой | Технологии |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy |
| AI / NLP | GigaChat API, Ollama, prompt engineering, rules-based fallback |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Данные | PostgreSQL, RSS, MOEX ISS |
| Инфраструктура | Docker Compose, Nginx |
| Приложения | Tauri |
| Тестирование | pytest, Vitest, Testing Library, Playwright |

## Структура проекта

```text
backend/         FastAPI, бизнес-логика, интеграции и тесты
frontend/        React-приложение и frontend-тесты
docs/            требования, архитектура, API, данные, тестирование и CI/CD
docker-compose.yml
```

## Быстрый запуск

Требования: Docker Desktop и Docker Compose.

```bash
git clone https://github.com/dstrelnikova/finpulse.git
cd finpulse
cp .env.example .env
docker compose up -d --build
```

Перед первым запуском замените `POSTGRES_PASSWORD` и `SECRET_KEY` в `.env` уникальными локальными значениями. Пример намеренно содержит только placeholders и не является production-конфигурацией.

При первом запуске Ollama загружает модель из переменной `OLLAMA_MODEL`, поэтому старт может занять несколько минут.

После запуска доступны:

- веб-приложение: `http://localhost:3000`;
- Swagger API: `http://localhost:3000/api/docs`;
- backend напрямую: `http://localhost:8000`;
- liveness: `http://localhost:8000/healthz`;
- readiness: `http://localhost:8000/readyz`.

Проверить состояние контейнеров и остановить проект:

```bash
docker compose ps
docker compose down
```

## Настройка AI

Чат работает через локальный Ollama. Основные параметры задаются в `.env`:

```env
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_MAX_CONCURRENCY=1
OLLAMA_CHAT_TIMEOUT_SEC=180
```

Публичная лента может работать без внешнего LLM через rules-based анализ. Для подключения GigaChat:

```env
NEWS_USE_LLM=true
NEWS_LLM_FOR_PUBLIC_RSS=true
GIGACHAT_AUTH_KEY=<Authorization key>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
```

Секреты нельзя добавлять в Git. Файл `.env` исключён через `.gitignore`; в репозитории хранится только безопасный пример `.env.example`.

## Тесты

Backend-тесты внутри запущенного контейнера:

```bash
docker compose exec backend pytest
```

Frontend-проверки локально:

```bash
cd frontend
npm ci
npm run check
```

E2E-тесты:

```bash
cd frontend
npx playwright install
npm run test:e2e
```

## Документация

- [System Context](docs/context.md)
- [Requirements](docs/requirements.md)
- [Use Cases](docs/use-cases.md)
- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Data Model](docs/data-model.md)
- [Technical Specification](docs/specification.md)
- [Acceptance Criteria](docs/acceptance-criteria.md)
- [Test Cases](docs/test-cases.md)
- [Traceability Matrix](docs/traceability-matrix.md)
- [CI/CD](docs/ci-cd.md)

Документы разделяют фактическое состояние **AS-IS**, целевое поведение **TARGET** и известные расхождения **GAP**. Связь требований с критериями и проверками показана в матрице трассируемости.

## CI

Workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) запускается для pull request и push в `main`. Независимые jobs проверяют backend (`pip check`, `compileall`, flake8, pytest, `pip-audit`), frontend (`npm audit`, TypeScript, Vitest, production build) и изолированные Playwright e2e-сценарии. Production-секреты pipeline не требуются; автоматический deployment не настроен.

## Дополнительный вариант запуска

Исходный код macOS-оболочки на Tauri находится в `frontend/src-tauri/`. Для разработки используйте `npm run tauri:dev`, для сборки — `npm run tauri:build`; требуются Rust и системные зависимости Tauri.

## Развёртывание и готовность к релизу

FinPulse — работающий локальный MVP, а не развёрнутый production-сервис. Репозиторий содержит воспроизводимый Docker Compose-контур: сервисы собираются из исходного кода, конфигурация и секреты передаются через переменные окружения, а зависимости контролируются health checks.

Для production-подобного запуска предусмотрен отдельный Compose override: наружу публикуется только Nginx на порту `80`, а PostgreSQL, backend и Ollama остаются во внутренней сети Docker.

```bash
cp .env.prod.example .env.prod
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

В GitHub Actions настроены автоматические проверки backend, frontend и браузерных сценариев для push и pull request. Автоматический deployment, управление production-секретами и публикация в облако пока не реализованы.

Для production-релиза потребуются домен и TLS, безопасное хранилище секретов, версионированные миграции БД, мониторинг и логирование, а также подтверждённый pipeline доставки. Эти пункты намеренно не выдаются за уже реализованные возможности.

## Ограничения и развитие

- качество анализа зависит от доступности и полноты исходной статьи;
- rules-based fallback проще LLM-анализа и предназначен для устойчивой деградации сервиса;
- список бумаг для экрана MOEX ограничен выборкой ликвидных тикеров MVP;
- ответы AI требуют проверки и не должны использоваться как единственное основание для инвестиционных решений;
- access и refresh JWT хранятся в `localStorage`; для публичного production-контура следует отдельно оценить переход на HttpOnly cookies, CSP и XSS-hardening;
- схема БД создаётся через SQLAlchemy `create_all`; версионированные миграции пока отсутствуют;
- следующие шаги: миграции, production deployment pipeline, мониторинг интеграций, расширение покрытия API-тестами и развитие источников и уведомлений.

Проект находится на стадии работающего full-stack MVP.
