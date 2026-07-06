# FinPulse — AI-ассистент для фондового рынка России

## Краткое описание
FinPulse — веб-продукт с ИИ-ассистентом, который собирает, суммаризирует и интерпретирует новости российского фондового рынка. Цель — помочь трейдерам и инвесторам быстро понять, что происходит на рынке и как события могут повлиять на акции, сектора и индекс.

Ключевая идея: не пересказ новостей, а объяснение их возможного влияния на рынок РФ.

## Проблема, которую решает продукт
Пользователи сталкиваются с:
- **Информационным шумом**: десятки новостей без понимания важности.
- **Недостатком интерпретации под рынок РФ**.
- **Сложностью быстро оценить риски и последствия**.

Потребность в формулировке пользователя:
- «Быстро понять, что сегодня важно и чем это может закончиться для рынка / портфеля».

## Как работает продукт (high-level flow)
1. **Сбор новостей** из заданных источников (API/парсинг).
2. **NLP/AI-обработка** каждой новости:
   - суммаризация,
   - классификация,
   - оценка влияния,
   - генерация комментария,
   - выделение объекта влияния и риска/неопределённости.
3. **Публикация карточек** в ленте и агрегирование «ключевых новостей дня».
4. **Персонализация** ленты по профилю пользователя (интересующие бумаги, горизонт, риск).
5. **Чат-ассистент** отвечает на вопросы в контексте рынка РФ и обработанных новостей.

## Источники данных
- Банк России
- Минфин РФ
- Московская биржа
- Отчёты публичных компаний
- Интерфакс / РБК / ТАСС

## Технологический стек

### Backend
- FastAPI (Python)
- Pydantic
- Uvicorn

### NLP / AI слой
- Python (ML/NLP логика)
- Ollama для закрытого чата
- GigaChat API для публичной ленты:
  - суммаризации,
  - классификации,
  - оценки sentiment/impact,
  - генерации аналитического комментария

### Frontend
- React (SPA)
- TypeScript
- Tailwind CSS

### Хранение данных
- PostgreSQL (пользователи, чат)
  
### Архитектура (MVP)
- Frontend (React + TS + Tailwind)
- Backend API (FastAPI)
- NLP-сервис
- База данных (PostgreSQL)

## Контейнеризация и деплой

## MVP-приложения для Mac и iPhone

Локальный MVP можно запускать как macOS-приложение через Tauri и как iPhone-приложение через Expo React Native. Backend, PostgreSQL, GigaChat и Ollama остаются общими и запускаются локально через Docker Compose.

Подробная инструкция: [docs/mvp-apps.md](docs/mvp-apps.md)

### Локальный запуск MVP

```bash
docker compose up -d --build
```

- Frontend: `http://localhost:3000`
- API через reverse proxy: `http://localhost:3000/api/*`
- Backend внутри Docker-сети: `http://backend:8000`
- Ollama API внутри Docker-сети: `http://ollama:11434`

### Ollama для чата

Закрытый чат FinPulse использует локальную модель Ollama. При запуске `docker compose up -d --build` сервис `ollama-init` проверяет и подтягивает модель из `OLLAMA_MODEL`.

```env
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:1.5b
OLLAMA_MAX_CONCURRENCY=1
OLLAMA_CHAT_TIMEOUT_SEC=180
OLLAMA_CHAT_NUM_PREDICT=700
```

### GigaChat для публичной ленты

FinPulse может использовать GigaChat API как редактора-аналитика поверх RSS-источников: модель получает заголовок, RSS-анонс и доступный текст статьи, возвращает строгий JSON с `summary`, `facts`, `conclusion`, `risks` и `indicator`. Если GigaChat недоступен или ответ невалиден, публичная лента автоматически использует быстрый rules-анализ.

Для включения:

```env
NEWS_USE_LLM=true
NEWS_LLM_FOR_PUBLIC_RSS=true
GIGACHAT_AUTH_KEY=<Authorization key из личного кабинета>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
GIGACHAT_CHAT_MAX_TOKENS=700
GIGACHAT_NEWS_MAX_TOKENS=700
NEWS_PUBLIC_RSS_LLM_LIMIT=5
```

По документации GigaChat токен получается через `POST https://ngw.devices.sberbank.ru:9443/api/v2/oauth` со scope `GIGACHAT_API_PERS`, а генерация идёт через `https://gigachat.devices.sberbank.ru/api/v1/chat/completions`. Для штатной работы с API нужны сертификаты НУЦ Минцифры; проверка TLS управляется параметром `GIGACHAT_VERIFY_SSL`.

### Прод-конфигурация

```bash
cp .env.prod.example .env.prod
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### Health endpoints

- Backend liveness: `GET /healthz`
- Backend readiness: `GET /readyz`
- Frontend/Nginx liveness: `GET /healthz` (на frontend контейнере)
