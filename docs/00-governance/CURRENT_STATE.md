# Маяк Авито — текущее состояние проекта

**Версия снимка:** 1.1
**Статус:** APPROVED snapshot
**Дата снимка:** 2026-07-06

## Фаза

`A0.7 — Technical Baseline evidence collection`

Documentation Bootstrap принят. Product-code, физическая схема БД, миграции, выбранный технологический стек, CI/CD, сервисы проекта, внешние API-ключи и deploy-конфигурация по-прежнему не созданы.

## Принятый documentation baseline

- Репозиторий: `MaksimUnimax/AVITO_Mayak`.
- Рабочая ветка: `main`.
- Принятый remote commit: `b4b14dc6262581b10f45d02e9472c93e3cee6b31`.
- Bootstrap parent commit: `e8587107fd6cd3675b3e69f1ce75ffa0c846cc3c`.
- В документационном baseline ровно 49 файлов.
- 48 исходных файлов совпали с переданным ChatGPT буквальным текстом по SHA-256.
- Единственное расхождение было в исторической записи `WL-0001`: SSH URL ошибочно содержал `/` вместо `:` после `github.com`.
- Ошибка не была переписана. Append-only prefix сохранён, а корректировка добавлена отдельной записью `WL-0002`.
- Рабочее дерево после final audit было чистым.
- Отдельный SSH deploy key и dedicated GitHub known_hosts существуют только для `MaksimUnimax/AVITO_Mayak`.

## Принятые источники и правила

- `docs/01-product/MAYAK_AVITO_TARGET_MODEL_v0.1.md` — целевая модель продукта, статус `DRAFT`.
- `docs/02-architecture/MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md` — архитектурная карта, статус `DRAFT`.
- `docs/00-governance/CHATGPT_PROJECT_LEADERSHIP_RULES_v1.1.md` — обязательные правила руководства разработкой.
- `docs/00-governance/DOCUMENTATION_GOVERNANCE.md` — обязательное правило буквальной передачи документов CLI-исполнителю.
- `docs/00-governance/PROJECT_ENTRYPOINT.md` — обязательный протокол восстановления контекста.

## Активная задача

`TASK-001 — Доказательная инвентаризация технической среды`.

Задача имеет режим `proof_only`. Она не выбирает технологический стек и не создаёт код. Она собирает только проверяемые факты о сервере и доступных инструментах, необходимых ChatGPT для проектирования Technical Baseline.

## Что ещё не существует и не должно предполагаться существующим

- утверждённый технический baseline;
- выбранный язык, framework, package manager, application layout или queue technology;
- машиночитаемые DTO, JSON Schema, OpenAPI или event contracts;
- физическая модель БД, миграции и migration policy;
- security/privacy model;
- test strategy, fixtures, acceptance matrix или regression policy;
- operations/deployment runbooks;
- принятые автономные module playbook-документы;
- product-code, tests, CI, Dockerfile, database, queue, бот, parser, веб-интерфейс или production deploy.

## Следующий безопасный шаг

Получить и проверить отчёт `TASK-001`.

Только ChatGPT после проверки доказательств определяет выбранный technical baseline и пишет полный буквальный текст следующего документационного пакета. CLI-исполнитель не выбирает следующий шаг, стек или содержание документов.
