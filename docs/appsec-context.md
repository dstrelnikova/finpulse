# AppSec-контекст FinPulse

FinPulse — финансовое веб-приложение, а не cybersecurity-продукт. Ниже разделены реально наблюдаемые меры (**AS-IS**) и возможные этапы развития (**TARGET**).

## Secure SDLC

Secure SDLC добавляет security-деятельность на протяжении жизненного цикла: угрозы и security requirements при анализе, безопасное проектирование, review/SAST/SCA при разработке, DAST перед выпуском, управление уязвимостями и обновления после выпуска. Для FinPulse это особенно относится к JWT, персональным данным профиля, внешним URL и LLM-интеграциям.

## DevSecOps

DevSecOps автоматизирует повторяемые проверки в pipeline и даёт разработчику раннюю обратную связь. Quality gate может остановить дальнейший этап, если найдена критичная уязвимость или запрещённая зависимость. Автоматизация не заменяет threat modeling и ручной review.

## SAST

Static Application Security Testing анализирует исходный/промежуточный код без запуска приложения: потенциальные injection, небезопасную работу с секретами, ошибочные auth-пути. Подходящий этап — после checkout/install и до quality gate. SAST AS-IS в workflow FinPulse отсутствует.

## DAST

Dynamic Application Security Testing проверяет запущенное приложение через его интерфейсы, например HTTP: security headers, ошибочную авторизацию, инъекции и конфигурацию. В отличие от SAST, DAST видит runtime-поведение, но хуже указывает строку источника. Для FinPulse ему нужен изолированный Compose stand с тестовыми данными.

## SCA / OSA

Software Composition Analysis (Open Source Analysis) сопоставляет зависимости `requirements.txt` и `package-lock.json` с базами уязвимостей и лицензиями. Это актуально, потому что приложение зависит от FastAPI, SQLAlchemy, React, Axios и других open-source пакетов. SCA AS-IS не настроен.

## SBOM

Software Bill of Materials — машиночитаемый перечень компонентов и версий, например CycloneDX/SPDX. Он помогает понять, затрагивает ли опубликованная уязвимость конкретную сборку, и поддерживает аудит цепочки поставки. FinPulse SBOM не генерирует.

## OWASP Top 10

OWASP Top 10 — ориентир по распространённым классам рисков веб-приложений, а не готовый чек-лист соответствия. Для FinPulse релевантны прежде всего broken access control, cryptographic failures, injection, security misconfiguration, vulnerable components и SSRF при загрузке внешних страниц.

## AS-IS security controls

- пароль хешируется; access endpoints используют JWT и RBAC permissions;
- Pydantic валидирует большинство входных данных;
- SQLAlchemy ORM параметризует обычные запросы;
- CORS ограничен известными origins/methods/headers;
- `.env` исключён из Git, production credentials не обнаружены среди tracked files;
- в GitHub включены secret scanning и push protection; на момент проверки открытых secret alerts нет;
- refresh JWT ротируется и отзывается logout;
- auth имеет простой in-memory rate limit;
- контейнер backend запускается непривилегированным `appuser`.

## Gaps и учебный TARGET flow

```text
Requirements / threat model
→ code review
→ build + unit/integration tests
→ SAST + secret scan + SCA
→ container image scan + SBOM
→ isolated deployment
→ DAST
→ quality gate
→ release and vulnerability monitoring
```

Для junior-проекта это обзор терминов, а не заявление о внедрённой DevSecOps-платформе. AS-IS frontend CI запускает `npm audit` с порогом high, backend — `pip check`; GitHub дополнительно выполняет secret scanning и push protection. Две moderate-уязвимости frontend относятся к React Router и требуют отдельно проверяемого обновления до major version 7. Миграции, полноценный SAST/SCA и хеширование refresh tokens можно рассматривать после MVP. Solar appScreener в проект не установлен и не настроен.

Связанные документы: [CI/CD](ci-cd.md), [требования](requirements.md), [архитектура](architecture.md).
