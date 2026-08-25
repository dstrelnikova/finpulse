# Техническое задание / Software Specification

Версия: 1.0 · Статус: описание работающего MVP · Язык: русский

## 1. Контекст

FinPulse агрегирует данные российского финансового рынка и приводит новости к структурированному виду. Документ отделяет фактическую реализацию (**AS-IS**) от возможного развития (**TARGET**) и известных расхождений (**GAP**).

## 2. Назначение

Система предназначена для информационного анализа. Она не выполняет торговых операций и не заменяет профессиональную инвестиционную консультацию.

## 3. Цели

Показать пользователю отобранные новости и рыночные данные; автоматизировать первичное выделение фактов/рисков; дать персональный контекст и AI-чат; обеспечить трассируемость требований и проверок.

## 4. Scope

Поставляемый контур: React SPA/Tauri shell, FastAPI, PostgreSQL, RSS/scraping, GigaChat, Ollama, MOEX ISS, JWT/RBAC, Docker Compose, tests и GitHub Actions CI. Полные границы и Out of Scope: [requirements.md](requirements.md#5-scope).

## 5. Actors

Гость, пользователь, администратор и внешние поставщики данных/AI. Матрица возможностей: [requirements.md](requirements.md#4-actors--пользователи).

## 6. Пользовательские сценарии

Приоритетные сценарии UC-01…UC-05: публичная новость; регистрация/вход; профиль; AI-чат; роли администратора. Полные потоки и исключения: [use-cases.md](use-cases.md).

## 7. Функциональные требования

Нормативный набор FR-01…FR-15 находится в [requirements.md](requirements.md#8-функциональные-требования). Ключевые правила: публичная лента и карточка, fallback котировок, JWT lifecycle, валидируемый профиль, persistent default chat, RBAC и персональная лента.

## 8. Нефункциональные требования

NFR-01…NFR-06 определяют externalized configuration, предсказуемую валидацию, graceful degradation, целостность данных, CI-проверки и health/readiness. См. [requirements.md](requirements.md#9-нефункциональные-требования).

## 9. Системные правила

- Рынок профиля — только `RU`.
- Access и refresh JWT имеют разные `type`; refresh token ротируется и отзывается logout.
- Permissions вычисляются из `user_roles → role_permissions`.
- Новость идентифицируется уникальным URL; выдача по slug не гарантирует уникальность на уровне БД.
- Публичный AI-анализ должен деградировать до rules-based результата; чат при недоступности Ollama должен явно вернуть 503.
- API limit публичной ленты и котировок AS-IS зажимается к допустимой границе.

## 10. Архитектурный контекст

Клиент-серверная модульная архитектура, компоненты и sequence flow описаны в [architecture.md](architecture.md). Бизнес-оркестрация выполняется backend use cases; React не обращается напрямую к БД или внешним AI API.

## 11. REST API

JSON REST contract, endpoint inventory, authentication, validation и Swagger: [api.md](api.md). Совместимость проверяется response models и tests; breaking changes требуют обновления требований, AC и test cases.

## 12. Данные

Физические таблицы, PK/FK, ограничения и ER-диаграмма: [data-model.md](data-model.md). PostgreSQL является единственным постоянным хранилищем backend; volume Docker обеспечивает сохранность между restart, но не является backup.

## 13. Интеграции

| Интеграция | Протокол | Назначение | Поведение при ошибке |
|---|---|---|---|
| RSS/web pages | HTTP(S), XML/HTML | Источники новостей | Источник пропускается |
| GigaChat | OAuth + HTTPS JSON | Анализ новости | Rules-based fallback |
| Ollama | HTTP JSON `/api/generate` | Пользовательский чат | HTTP 503 клиенту |
| MOEX ISS | HTTPS JSON | Котировки выборки | `fallback=true` |

Credentials GigaChat задаются окружением и не должны храниться в Git.

## 14. Обработка ошибок

Pydantic/FastAPI возвращает 422 для schema validation; auth — 401/403/429; отсутствующий ресурс — 404; Ollama — 503; readiness БД — 503. Middleware журналирует запросы и преобразует необработанные ошибки, не раскрывая stack trace клиенту. Интеграционные fallback не должны маскировать признак деградации (`fallback` или rules source в payload).

## 15. Ограничения

Качество зависит от полноты источника и модели; нет migration framework, distributed rate limit, deployment pipeline и гарантированного SLA. Полный GAP-list: [requirements.md](requirements.md#11-ограничения-и-gap).

## 16. Acceptance Criteria

Критерии AC-01…AC-13: [acceptance-criteria.md](acceptance-criteria.md). Результаты прогона TC-01…TC-16: [test-cases.md](test-cases.md). Связность контролирует [traceability matrix](traceability-matrix.md).

## 17. Связанные документы

[Requirements](requirements.md) · [Use Cases](use-cases.md) · [Architecture](architecture.md) · [API](api.md) · [Data Model](data-model.md) · [CI/CD](ci-cd.md)
