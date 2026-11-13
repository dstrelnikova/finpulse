# Portfolio readiness report — FinPulse

_Статус: локальная ветка `chore/portfolio-readiness`; это не отчёт о production-деплое._

## A. Выполненные изменения

| Изменение | Зачем |
|---|---|
| Placeholders в development `.env.example` | Не использовать повторяемые credentials как шаблон. |
| `pip-audit` в CI | Проверять известные уязвимости Python-зависимостей. |
| Playwright job в CI | Проверять browser-сценарии в чистой среде. |
| Обновлены `axios` и `vite` в пределах текущих major versions | Устранить подтверждённые high-severity frontend advisories. |
| Расширен `frontend/.dockerignore` для Tauri build artifacts | Не передавать в Docker build context гигабайтные локальные артефакты. |
| Добавлены browser security headers на Nginx | Ограничить clickjacking, MIME sniffing, ненужные browser permissions и embedding. |
| Портфолио и interview docs | Сделать решения и ограничения проверяемыми. |

## B. Результаты тестирования

Перед merge запускать:

```bash
cd backend && pytest
cd frontend && npm run check && npm run test:e2e
```

Наблюдённые результаты текущей сессии:

- `frontend: npm ci && npm run check && npm run build` — PASS: typecheck, 5 unit-тестов, 4 integration-теста и production build.
- `frontend: npm audit --audit-level=high` — PASS: high/critical findings отсутствуют после обновления `axios` и `vite`; остаются 2 moderate findings в `react-router`.
- `frontend: npm run test:e2e` — локальный macOS browser cache не содержал headless-shell. Проверка выполнена в official Playwright Linux/Chromium container: PASS, 3 scenarios.
- `docker compose exec backend pytest` — PASS: 69 tests.
- Docker smoke: `/healthz`, `/readyz`, frontend `/` и `/api/docs` — PASS (HTTP 200 / ready).
- `docker compose build frontend` и перезапуск frontend service — PASS; rebuilt container healthy and returns HTTP 200.
- `docker compose exec backend flake8 app tests` — PASS после исправления 4 превышений длины строк в fallback-ответах чата.
- `black --check` и `isort --check-only` — обнаружили существующий formatting backlog (соответственно 9 и 10 файлов); `mypy app` — 151 errors в 32 файлах. Это не относится к текущему безопасному изменению и требует отдельного согласованного refactoring scope.

YAML подготовлен для GitHub Actions, но до конкретного GitHub run не подтверждает GitHub-hosted результат.

## C. Безопасность

Проверено: `.env` игнорируется, скан публичного кода не выявил типовых key markers, используются CORS allow-list, JWT/RBAC и Pydantic. История `.env*` просмотрена без вывода значений. Исправлено: realistic-looking local DB/JWT values в `.env.example` заменены на placeholders; high-severity frontend dependency findings устранены обновлением `axios` и `vite`.

Остаётся: `npm audit` показывает две moderate React Router advisory, для исправления которых предлагается breaking migration на v7; access/refresh JWT находятся в `localStorage`, что требует отдельного XSS-hardening решения для публичного production-контура; automated audit не заменяет threat modeling; старые локальные `.env` и внешние системы не проверялись; `create_all` вместо migrations — операционный риск. Если в Git history будет найден реальный секрет, нужна ротация; переписывать историю можно только отдельным согласованным действием.

## D. Соответствие вакансии

| Требование | Доказательство | Статус |
|---|---|---|
| MVP/decomposition | requirements, use cases, acceptance, traceability | подтверждено |
| Frontend/UI | React SPA, guards, browser tests | подтверждено |
| Backend/API/БД | FastAPI, SQLAlchemy, PostgreSQL | подтверждено |
| AI/external integrations | RSS, MOEX, GigaChat, Ollama + fallback | подтверждено |
| Automated testing | pytest, Vitest, Playwright | подтверждено |
| CI/CD | checks + e2e; deployment отсутствует | частично подтверждено |
| Security | env hygiene, auth, dependency audits | частично подтверждено |
| AI-assisted workflow | [AI case](AI_ENGINEERING_CASE.md) | подтверждено для этой сессии |
| MCP/Skills | environment supports MCP; product integration absent | частично подтверждено |

## E–G. Демонстрация, ограничения, следующие шаги

Можно показывать ленту и индикаторы, MOEX fallback, auth/RBAC, архитектуру, tests и CI YAML. Обязательно уточнить, что AI не даёт инвестиционных рекомендаций, а e2e используют controlled API responses.

Ограничения: нет migrations, CI ещё не запускался в GitHub из этой ветки, browser e2e используют controlled API responses, нет доказательств production-нагрузки/SLA, полный Docker smoke test зависит от Docker Desktop, сети и Ollama model.

Приоритеты: (1) Alembic migrations, (2) PR workflow и required checks, (3) отдельный план закрытия Black/isort/mypy backlog, (4) structured logging/monitoring интеграций, (5) contract fixtures для RSS/MOEX/GigaChat.
