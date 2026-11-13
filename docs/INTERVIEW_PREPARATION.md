# FinPulse: подготовка к техническому интервью

Используйте только то, что можете объяснить на примерах из кода. Если личный вклад или история решения неизвестны, скажите об этом прямо.

| Вопрос | Короткий ответ | Пример / что проверить |
|---|---|---|
| Почему такая архитектура? | Это модульный монолит: один FastAPI backend с разделением слоёв. | `backend/app/`, `docs/architecture.md`. |
| Как устроен backend? | Routes валидируют запросы; use cases координируют сценарии; repositories работают с БД. | Проследить публичную ленту. |
| Как устроен API? | REST JSON API с FastAPI/Pydantic, JWT и dependency injection. | Открыть `/api/docs`. |
| Как обрабатываются ошибки? | Внешние сервисы имеют fallback; middleware не раскрывает внутренний текст 500. | `middleware.py`, `moex_service.py`. |
| Как используется AI? | GigaChat анализирует новости, Ollama отвечает в чате; есть контролируемая деградация. | `NEWS_USE_LLM`, LLM services. |
| Как ставить задачу агенту? | Дать цель, границы, интерфейсы, acceptance criteria и команды проверки. | Эта сессия: качество без переписывания продукта. |
| Как проверять AI-код? | Читать diff/интерфейсы и запускать tests, type/build/security checks. | `.github/workflows/ci.yml`. |
| Что такое unit-тест? | Изолированная проверка одной единицы логики. | `test_moex_service.py`. |
| Что такое integration-тест? | Проверка взаимодействия частей с controlled dependencies. | `backend/tests/integration/`. |
| Что такое e2e-тест? | Проверка пользовательского сценария в браузере. | `frontend/e2e/public-news.spec.ts`. |
| Как работает Playwright здесь? | Запускает frontend и intercept-ит `/api` через `page.route`. | Не требует БД/ключей, но не заменяет Docker smoke test. |
| Как обеспечивается безопасность? | Env secrets, JWT/RBAC, Pydantic, CORS allow-list и dependency audit. | Не обещать «полную безопасность». |
| Как организован Git workflow? | Отдельная branch, review и CI перед merge. | `chore/portfolio-readiness`; проверить `git status`. |
| Что проверяет CI? | pytest/audit, frontend type/tests/build, browser e2e. | Workflow не деплоит и не использует production secrets. |
| Что такое MCP? | Протокол структурированного вызова внешних инструментов агентом. | Не утверждать, что FinPulse имеет MCP-server: его нет. |
| Когда нужны Skills? | Для повторяемого процесса с полезными правилами, не ради галочки. | Quality gate — подходящий кандидат после установки. |
| Какие ограничения MVP? | Нет migrations, AI зависит от сервисов, e2e mock API. | README и architecture docs. |
| Что улучшить дальше? | Alembic, observability, contract tests, staging smoke test. | Объяснить приоритет и цену. |
