# Маяк Авито

**Статус репозитория:** Documentation Baseline. Код продукта ещё не создан.

«Маяк Авито» — сервис мониторинга поисковой выдачи Avito. Клиент создаёт отдельный Маяк из готовой ссылки поиска и получает уведомления о новых объявлениях и новых для этого Маяка парах `listing_id + price`.

## Точка входа

Перед любой работой читать:

1. [`docs/00-governance/PROJECT_ENTRYPOINT.md`](docs/00-governance/PROJECT_ENTRYPOINT.md)
2. [`docs/00-governance/CURRENT_STATE.md`](docs/00-governance/CURRENT_STATE.md)
3. [`docs/00-governance/ROADMAP.md`](docs/00-governance/ROADMAP.md)
4. [`docs/MANIFEST.md`](docs/MANIFEST.md)
5. [`docs/02-architecture/TECHNICAL_BASELINE_v1.0.md`](docs/02-architecture/TECHNICAL_BASELINE_v1.0.md)

## Неподвижные правила

- Владелец продукта задаёт цели, ограничения и принимает продуктовые решения.
- ChatGPT является разработчиком, архитектором и руководителем проекта.
- Codex/CLI используется только как ограниченный технический исполнитель; для текущего документационного цикла — только как server-sync executor после публикации GitHub.
- Public GitHub `main` — источник истины для документов.
- Код и документация не создаются по догадке.
- Shared-host resources не принадлежат проекту только потому, что они видимы.
- External behavior требует current official/primary evidence.

Полные правила: [`docs/00-governance/CHATGPT_PROJECT_LEADERSHIP_RULES_v1.1.md`](docs/00-governance/CHATGPT_PROJECT_LEADERSHIP_RULES_v1.1.md).

## Current approved foundations

- Architecture Baseline v1.1
- Technical Baseline v1.0
- Common Contract Foundation
- Data and Compatibility Foundation
- Quality Foundation with Acceptance Matrix v1.1
- Operations/Environment boundaries
- Avito Reference Foundation
- Telegram Reference Policy v1.0
- MAX Reference Policy v1.0
- Platform & Contracts Module Playbook v1.0

Core stack выбран документально: Python 3.14, uv, FastAPI/Pydantic, HTTPX, PostgreSQL 18, SQLAlchemy/Psycopg/Alembic и утверждённые quality/telemetry tools.

Это не означает, что packages установлены, lockfile создан, база provisioned или product-code разрешён.

## Product documents

- Target model: [`docs/01-product/MAYAK_AVITO_TARGET_MODEL_v0.1.md`](docs/01-product/MAYAK_AVITO_TARGET_MODEL_v0.1.md)
- Architecture map: [`docs/02-architecture/MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md`](docs/02-architecture/MAYAK_AVITO_ARCHITECTURE_MODULE_MAP_v0.1.md)
- Open decisions: [`docs/00-governance/OPEN_DECISIONS.md`](docs/00-governance/OPEN_DECISIONS.md)

## Запрет до отдельного решения владельца

До принятия applicable module playbook, isolated toolchain proof и exact implementation task запрещены:

- product-code;
- `pyproject.toml`, `uv.lock` и dependency installation;
- physical schema, migrations and database provisioning;
- bots, parser and external calls;
- Docker, CI/CD and deploy;
- services, ports, credentials, secrets and production infrastructure.

Run 12 опубликован как documentation-only Platform & Contracts playbook. После синхронизации сервера с точным Run 12 SHA следующий документационный ран — Run 13 of 24, Identity & Access Module Playbook.
