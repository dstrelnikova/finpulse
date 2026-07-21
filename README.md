# FinPulse — AI-ассистент для российского фондового рынка

FinPulse — учебный full-stack MVP, который собирает финансовые новости, выделяет ключевые факты и объясняет их возможное влияние на российский рынок. Пользователь получает публичную новостную ленту, котировки ликвидных бумаг, персональные материалы и чат с AI-ассистентом.

Проект демонстрирует интеграцию LLM в продукт, обработку финансовых данных, разработку API и пользовательского интерфейса. FinPulse не является инвестиционной рекомендацией и не использует реальные средства пользователей.

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
- адаптивный React-интерфейс, macOS-оболочка на Tauri и мобильный MVP на Expo React Native;
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

## Моя роль

Проект самостоятельно разработан мной: от идеи и архитектуры MVP до реализации backend, frontend, AI-интеграций, Docker-конфигурации, тестов и документации.

В рамках проекта я:

- спроектировала FastAPI API и структуру приложения по слоям;
- реализовала авторизацию, роли, профили, новостную ленту и историю чатов;
- интегрировала Ollama, GigaChat, RSS и MOEX ISS;
- разработала React-интерфейс и клиентскую маршрутизацию;
- настроила PostgreSQL, Docker Compose и Nginx;
- добавила unit-, integration- и e2e-тесты;
- подготовила desktop- и mobile-варианты MVP.

## Технологии

| Слой | Технологии |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy |
| AI / NLP | GigaChat API, Ollama, prompt engineering, rules-based fallback |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Данные | PostgreSQL, RSS, MOEX ISS |
| Инфраструктура | Docker Compose, Nginx |
| Приложения | Tauri, Expo React Native |
| Тестирование | pytest, Vitest, Testing Library, Playwright |

## Структура проекта

```text
backend/         FastAPI, бизнес-логика, интеграции и тесты
frontend/        React-приложение и frontend-тесты
mobile/          мобильный MVP на Expo React Native
docs/            инструкции для macOS- и iPhone-приложений
report_assets/   материалы проектной документации
scripts/         вспомогательные скрипты
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

## Дополнительные варианты запуска

Инструкция по macOS-приложению на Tauri и мобильному MVP на Expo находится в [docs/mvp-apps.md](docs/mvp-apps.md).

Прод-конфигурация запускается отдельным compose-файлом:

```bash
cp .env.prod.example .env.prod
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Ограничения и развитие

- качество анализа зависит от доступности и полноты исходной статьи;
- rules-based fallback проще LLM-анализа и предназначен для устойчивой деградации сервиса;
- список бумаг для экрана MOEX ограничен выборкой ликвидных тикеров MVP;
- ответы AI требуют проверки и не должны использоваться как единственное основание для инвестиционных решений;
- следующие шаги: расширение источников, аналитики по компаниям и секторам, покрытия тестами, CI/CD и системы уведомлений.

Проект находится на стадии работающего full-stack MVP.
