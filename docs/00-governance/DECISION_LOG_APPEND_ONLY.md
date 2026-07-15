# Маяк Авито — журнал решений (append-only)

**Статус:** APPROVED append-only log  
**Правило:** записи не редактируются, не удаляются и не переставляются. Новое решение или корректировка добавляется только новой записью в конец.

---

## ADR-0001 — 2026-07-06 — Стартовая архитектура: modular monolith first

**Статус:** APPROVED  
**Контекст:** проект состоит из 13 логических модулей, но команда и процесс работы нерегулярны; отдельные микросервисы на старте создадут лишнюю операционную нагрузку.

**Решение:**

Стартовать как модульный монолит: один репозиторий, одна основная PostgreSQL-база, явные внутренние границы модулей, отдельные процессы worker/scheduler и отдельный Windows Egress Agent. Это не означает отказ от будущего выделения нагруженных частей.

**Последствие:**

Нельзя создавать отдельные базы и независимые production-deployments модулей без нового доказанного архитектурного решения.

---

## ADR-0002 — 2026-07-06 — Управление проектом и роль CLI

**Статус:** APPROVED  
**Контекст:** для предотвращения архитектурной самодеятельности Codex/CLI нельзя передавать исполнителю принятие решений.

**Решение:**

ChatGPT является разработчиком, архитектором и руководителем проекта. CLI-исполнитель только выполняет точное задание, запускает проверки и возвращает доказательства. Он не выбирает архитектуру, контракт, следующий шаг или содержание документации.

**Последствие:**

Каждая задача CLI должна содержать доказанный baseline, решение ChatGPT, разрешённый и запрещённый scope, проверки и критерии приёмки.

---

## ADR-0003 — 2026-07-06 — Буквальная передача документации CLI-исполнителю

**Статус:** APPROVED  
**Контекст:** документация, написанная CLI «по смыслу», создаёт неотслеживаемые предположения и расхождения.

**Решение:**

Каждый документ или append-only блок передаётся CLI-исполнителю ChatGPT полным точным текстом. CLI создаёт, заменяет или добавляет только этот текст и не вносит самостоятельных дополнений, исправлений или сокращений.

**Последствие:**

При отсутствии полного текста или append-блока CLI обязан остановиться со статусом `STOP_DOCUMENT_TEXT_MISSING`.

---

## ADR-0004 — 2026-07-06 — Исправлять причину на уровень выше симптома

**Статус:** APPROVED  
**Контекст:** локальные патчи скрывают следствия, оставляют неверный source of truth и повторно создают ошибки.

**Решение:**

Перед любым постоянным исправлением ChatGPT обязан проверить механизм симптома, владельца неверного состояния, нарушенный контракт/инвариант и подтверждённую корневую причину на уровень выше симптома. Постоянные костыли запрещены. Временная защита допустима только как явно помеченная `TEMPORARY_MITIGATION` с отдельной задачей на устранение причины.

**Последствие:**

Отчёт об исправлении должен доказывать проверку уровня выше, устранение причины или ограниченной временной защиты, а также тест против повторения класса ошибки.

---

## ADR-0005 — 2026-07-06 — Целевая модель и архитектурная карта сохраняются как DRAFT

**Статус:** APPROVED  
**Контекст:** текущие документы v0.1 фиксируют большую часть продукта, но сами имеют статус черновиков и содержат открытые решения.

**Решение:**

Хранить их в репозитории без тихого переписывания, со статусом `DRAFT`. Они являются обязательной базой для анализа, но не закрывают открытые решения и не заменяют утверждённые контрактные документы.

**Последствие:**

Нельзя выдумывать незакрытые значения — период тарифа, интервалы, платежи, phone-login, retention и другие пункты. Они остаются в `OPEN_DECISIONS.md` до отдельного решения.

## ADR-0006 — 2026-07-06 — Independent remote repository supervision

**Статус:** APPROVED

**Решение:** public GitHub `main` is the factual source of truth. ChatGPT independently reads it before repository-changing decisions and independently verifies commit, diff, final content, append-only integrity, forbidden scope and remote state after CLI reports. CLI verifies its local baseline but does not replace this review. Foreign shared-host resources do not belong to the project.

**Последствие:** handoff, local worktree and CLI report cannot independently close a task; baseline mismatch stops without self-repair; code and deploy remain gated by separate approved documentation.

---

## ADR-0007 — 2026-07-07 — Technical Baseline becomes a separate mandatory Run 10

**Статус:** APPROVED

**Контекст:**

Architecture Baseline v1.0 explicitly left the implementation stack unselected, while the Platform & Contracts README requires an approved Technical Baseline before its module playbook. The existing 23-run route moved directly from provider references to module playbooks and therefore omitted a required gate.

**Решение:**

Expand the documentation cycle from 23 to 24 runs. Insert Technical Baseline as Run 10. Move Telegram and MAX reference policies to Run 11. Move the thirteen module playbooks to Runs 12–24 without combining modules. Final independent documentation audit follows Run 24.

Run 10 consists of the Technology Selection Method, Technical Baseline Evidence, Technical Baseline, and necessary architecture/environment/quality version updates. It is documentation only and creates no implementation or runtime artifacts.

**Последствие:**

Platform & Contracts cannot receive a playbook before Run 10 is accepted and synchronized. Existing references to Runs 11–23 as the module-playbook interval are superseded by the current manifest, roadmap, current state and Acceptance Matrix v1.1. The second documentation agent must resume from Run 11 and use the 24-run route.

---

## ADR-0008 — 2026-07-07 — Core implementation technology baseline

**Статус:** APPROVED

**Контекст:**

The project requires one reproducible core toolchain compatible with the modular-monolith boundaries, PostgreSQL ownership, typed contracts, background work, Windows egress boundary and the mandatory `Duff89/parser_avito` implementation reference. The reference is a local Python application and is not a SaaS architecture or a permission to copy source.

**Решение:**

Select the following core baseline:

- CPython 3.14 supported line, standard GIL build;
- `uv` project management with `pyproject.toml` and committed `uv.lock`, with the exact `uv` version pinned by the first toolchain task;
- FastAPI and Uvicorn for the HTTP application boundary;
- Pydantic v2 and pydantic-settings for external DTO and configuration validation;
- HTTPX as the default HTTP client;
- PostgreSQL 18 supported line;
- SQLAlchemy 2, Psycopg 3 and Alembic for persistence and migration tooling;
- PostgreSQL-backed durable work claims and transactional outbox for the initial worker/scheduler model, without a required external broker;
- pytest, pytest-asyncio, RESpx, Ruff, mypy, import-linter and coverage.py for the initial quality toolchain;
- OpenTelemetry Python API/SDK as the telemetry instrumentation boundary, while exporter/backend selection remains deferred.

Framework and ORM objects are not intermodule contracts. Module-specific and operations-specific dependencies remain deferred to their own evidence and playbooks.

Flet, SQLite, Excel dependencies, VK integration, local TOML as multiuser state, Requests as a second default HTTP client and direct parser-to-notification coupling are not part of the core baseline.

**Последствие:**

The first implementation authorization must be a separate proof/toolchain task that creates exact dependency pins and demonstrates isolated reproducibility. This ADR does not authorize implementation, installation, migration, database creation, external access, deployment or server mutation. A major technology change requires new evidence, compatibility analysis, rollback/roll-forward implications and a new append-only decision.

## ADR-0009 — 2026-07-08 — Entitlements & Billing owner decisions for Free/Basic and first-stage billing policy

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Закрывает:** `OD-001`, `OD-002`, `OD-003`, `OD-004`, `OD-005`.

**Контекст:** Module playbook `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` left tariff period, later tiers, intervals, expiry behavior and payment policy open. The owner supplied explicit product decisions for the first Entitlements & Billing implementation planning stage. These decisions must be captured in governance before they are used in contracts, tests, documentation, code, tariff semantics or later runtime tasks.

**Решение:**

1. `OD-001`: the Basic tariff price `990 ₽` is for one month.
2. `OD-002`: at the current stage there are only two approved product tariff families: `Free` and `Basic`. No additional paid tariffs are introduced now as concrete product defaults. Future tariffs must be possible through Admin capability, but their names, prices and limits are not predeclared by this decision.
3. `OD-003`: Basic allows monitoring intervals starting from 5 minutes with a 5-minute step: 5, 10, 15, 20 and further by the same step. Free allows one Beacon, reduced functionality and monitoring intervals starting from 3 hours with a 3-hour step: 3, 6, 9, 12 hours and further by the same step. Free uses the same entitlement mechanism as a paid tariff, but with stricter limits.
4. `OD-004`: after paid access expires, only Free remains available. All Beacons are frozen. The user receives a message that the tariff has ended. The user must choose one Beacon that will remain under Free, must bring that Beacon into Free requirements and must manually start that Beacon. The system must not automatically choose the remaining Free Beacon.
5. `OD-005`: first-stage payment provider candidates are YooKassa, Telegram Stars and Tinkoff. The first stage uses manual renewal only. Recurring payments are not needed now. Refunds are manual only. Supported monetary/payment units for the first stage are RUB and Telegram Stars. There is no trial, grace period or proration; Free tariff is the alternative to trial/grace. Manual access is required as an Admin capability. Admin capability must eventually allow changing roles, adding new tariffs, editing existing tariffs and manually assigning tariffs/access to accounts.

**Scope boundary:** This decision captures product policy only. It does not authorize payment provider integration, payment account setup, real provider SDK calls, webhook endpoints, invoice/receipt/tax implementation, card data handling, Telegram Stars runtime integration, Tinkoff runtime integration, YooKassa runtime integration, Admin UI implementation, database schema, migrations, billing runtime service, Docker, CI/CD, deploy, runtime configuration, secrets, tokens or payment credentials.

**Consequences:**

- Entitlements & Billing may use `Free` and `Basic` as approved current product policy in later exact semantic-contract tasks.
- Any later provider-specific task still requires current official provider evidence and a separate exact task.
- Payment provider responses remain external evidence and never grant access by themselves.
- Manual access must require verified actor context, authorization, reason, scope, effective interval, idempotency and audit reference.
- `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.
- Persistence, migrations, Admin UI, provider runtime integration, Beacon runtime mutation, scheduler integration and notification sending remain blocked until their own gates are opened.

---

## ADR-0010 — 2026-07-08 — Entitlements precedence policy for effective entitlement evaluation

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-03 `Effective entitlement evaluation semantics` for semantic evaluator contracts/tests only.

**Не открывает:** runtime evaluator, billing runtime service, database persistence, migrations, provider integration, payment SDK/API calls, webhooks, invoice/receipt/tax implementation, Admin UI, Web Cabinet, Beacon runtime mutation, scheduler integration, notification sending, Docker, CI/CD, deploy, secrets, tokens or payment credentials.

**Контекст:** `docs/04-modules/03-entitlements-and-billing/MODULE_PLAYBOOK.md` states that exact precedence among tariff, subscription and manual grants remains a future contract/task detail and must be explicit before implementation. `ADR-0009` approved the first-stage Free/Basic billing policy and confirmed that payment provider responses remain external evidence and never grant access by themselves. EB-02 added semantic contracts and fixtures, but EB-03 effective entitlement evaluation remained blocked until an explicit precedence decision.

**Решение:**

1. `TariffDefinition` defines the baseline tariff policy: approved capability set, limits, scan interval rules, price/period semantics where applicable and explicit future gates.
2. An active `Subscription` selects the currently applicable tariff family for an account. If the paid subscription is active, it selects the paid tariff policy. If paid access is expired or unavailable, evaluation must move to the Free-only requirement state described below.
3. `EntitlementGrant` may add, restrict or qualify individual capabilities only inside its explicit account scope, capability scope and effective interval. It must not silently mutate the selected tariff definition or create a new tariff family.
4. `ManualAccessGrant` has highest precedence only inside its explicit target account, capability/scope, effective interval, reason, actor context, idempotency reference and audit reference. A valid manual grant may override a tariff/subscription denial only for that exact explicit scope and interval. Outside that scope or interval, normal tariff/subscription/grant evaluation applies.
5. `PaymentRecord` and `PaymentEvent` are non-authority evidence. They never grant access directly and never produce an entitlement by themselves. Any future payment-derived access requires a separate server-authorized transition and its own exact task.
6. If paid access is expired, the effective result must represent a Free-only requirement state. All paid Beacons are treated as requiring user action: user-choice-required and free-compliance-required. The system must not automatically choose the remaining Free Beacon.
7. If sources disagree or the evaluator cannot prove a safe deterministic result, the result must be `AMBIGUOUS` or `CONFLICT`; it must not silently allow access.
8. EB-03 semantic evaluator contracts/tests may use the following result statuses only as semantic outcomes: `ALLOWED`, `DENIED`, `BLOCKED`, `EXPIRED`, `AMBIGUOUS`, `UNSUPPORTED`, `USER_CHOICE_REQUIRED`, `FREE_COMPLIANCE_REQUIRED`, `CONFLICT`.

**Evaluation precedence order for EB-03 semantic contracts/tests:**

1. Validate account ownership/scope first. Foreign-account or missing-account-scope inputs must not evaluate to silent allow.
2. Treat payment records/events as evidence only and never as authority.
3. Determine the baseline tariff policy from the active subscription state and approved tariff definitions.
4. If paid access is expired, return the Free-only requirement state instead of choosing a Beacon or mutating Beacon state.
5. Apply valid entitlement grants only within their explicit scope and effective interval.
6. Apply valid manual access grants only within their explicit scope and effective interval, with actor, reason, idempotency and audit reference.
7. If a deterministic safe decision remains impossible, return `AMBIGUOUS` or `CONFLICT`.

**Consequences:**

- EB-03 may proceed only for deterministic semantic evaluator contracts/tests.
- EB-03 must remain transport/provider/framework/ORM neutral.
- EB-03 must not implement database-backed evaluation, repositories, provider adapters, webhooks, runtime services, Beacon mutation, scheduler integration, notification sending or Admin UI.
- `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.
- Usage counters, Beacon integration, provider adapters, reconciliation/refunds, persistence/migrations and Admin tariff management remain gated by their own roadmap steps.

---

## ADR-0011 — 2026-07-08 — Manual access grant authorization and lifecycle policy

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-04 `Manual access grants` for semantic contracts/tests only.

**Не открывает:** runtime Admin UI, Web Cabinet runtime, role runtime service, database persistence, migrations, repositories, direct database edits, provider/payment integration, Beacon mutation, scheduler integration, notification sending, Docker, CI/CD, deploy, runtime configuration, secrets, tokens or payment credentials.

**Контекст:** The module playbook requires exact authorization scope and task before manual access grants. Current source-of-truth already requires actor context, authorization, ownership/scope validation, idempotency, explicit commit point and auditable outcome for entitlement mutations, but exact role taxonomy for entitlement administration remained open. EB-04 needs an approved manual access authorization and lifecycle policy before semantic contracts/tests may be implemented.

**Решение:**

1. Manual access grant creation and revocation may be performed only by a server-side actor with capability `ENTITLEMENTS_MANUAL_ACCESS_ADMIN`.
2. The actor context must include `actor_id`, `actor_category`, `authorization_scope`, `authorization_reference` and `audit_reference`.
3. A manual access grant is valid only for one explicit `target_account_id`, one explicit capability/scope, one explicit effective interval, one required reason, one required idempotency key and one required audit reference.
4. Open-ended manual grants are forbidden for current scope. Every manual access grant must define both `starts_at` and `ends_at`.
5. EB-04 semantic contracts/tests may use only these manual grant lifecycle outcomes: `CREATED`, `REPLAYED`, `REVOKED`, `EXPIRED`, `REJECTED`, `CONFLICT`, `IDEMPOTENCY_MISMATCH`, `UNAUTHORIZED`, `OUT_OF_SCOPE`.
6. Idempotency policy for manual access mutations is:
   - same key plus same request fingerprint plus terminal outcome returns the original outcome;
   - same key plus different request fingerprint returns `IDEMPOTENCY_MISMATCH`;
   - missing idempotency key returns `REJECTED` before any effect.
7. Revocation may be performed only by an actor with capability `ENTITLEMENTS_MANUAL_ACCESS_ADMIN`.
8. Revocation requires target `grant_id`, target `account_id`, reason, idempotency key and audit reference.
9. Revocation must not delete history. It may only produce a semantic revoked outcome in EB-04 contracts/tests.
10. A successful manual grant or revocation event may exist only after an authoritative semantic commit point.
11. UI toggles, chat messages, direct database edits and provider/payment events are not valid manual access grants.

**Consequences:**

- EB-04 may proceed only for deterministic semantic manual access grant contracts/tests.
- EB-04 must remain transport/provider/framework/ORM neutral.
- EB-04 must not implement runtime Admin UI, role runtime service, database-backed mutation, repositories, migrations, direct database edits, provider/payment integration, Beacon mutation, scheduler integration or notification sending.
- `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.
- Admin UI/Web Cabinet runtime remains blocked until its own module gates.
- Payment/provider runtime remains blocked until provider-specific evidence and exact tasks.

---

## ADR-0012 — 2026-07-08 — Usage counters and limit consumption semantic policy

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-06 `Usage counters / limit consumption` for semantic contracts/tests only.

**Не открывает:** runtime counter store, database tables, repositories, migrations, scheduler hooks, notification sending, Beacon mutation, Scan Orchestration mutation, provider/payment consumption, runtime quota decrement, Admin UI, Web Cabinet UI, Docker, CI/CD, deploy, runtime configuration, secrets, tokens or credentials.

**Контекст:** The module playbook keeps usage counters and limit consumption blocked until exact semantics and affected module contracts are approved. EB-02 through EB-05 define tariff, subscription, effective entitlement, manual access and subscription lifecycle semantics, but they do not define usage-consumption ownership, counter families, commit-point semantics, idempotency, reset/window behavior or requester-module boundaries.

**Решение:**

1. EB-06 is opened only for deterministic semantic contracts/tests.
2. Entitlements & Billing owns only semantic usage-consumption policy and decisions.
3. Entitlements & Billing does not own Beacon state, scan execution state, notification delivery state or payment provider state.
4. Current approved EB-06 semantic counter families are:
   - `ACTIVE_BEACON_SLOT`;
   - `SCAN_INTERVAL_WINDOW`.
5. The following are not approved in current EB-06 scope:
   - scan-count quotas;
   - notification-count quotas;
   - payment-related consumption;
   - storage quotas;
   - provider-specific quotas;
   - monetary/payment consumption.
6. `ACTIVE_BEACON_SLOT` semantics:
   - requester module: Beacon Management;
   - source facts owner: Beacon Management;
   - Entitlements receives only synthetic snapshot/evidence for semantic evaluation;
   - Entitlements must not create, freeze, start, stop, delete or choose Beacons;
   - Free may use the accepted current limit of one active Beacon;
   - Basic active Beacon numeric limit remains gated unless already accepted elsewhere in current source-of-truth;
   - unsupported or missing limit returns `UNAVAILABLE` or `BLOCKED`, not `ACCEPTED`.
7. `SCAN_INTERVAL_WINDOW` semantics:
   - requester module: Scan Orchestration;
   - source facts owner: Scan Orchestration;
   - Entitlements receives only synthetic last/next scan timing evidence for semantic evaluation;
   - Entitlements must not schedule scans, run scans, cancel scans or mutate scheduler state;
   - Free uses accepted interval policy: starting at 3 hours, step 3 hours;
   - Basic uses accepted interval policy: starting at 5 minutes, step 5 minutes;
   - `OD-011` minimum monitoring frequency safety remains open and must not be closed by EB-06;
   - if `OD-011` safety is required to decide a case, return `BLOCKED` or `UNAVAILABLE`.
8. EB-06 semantic outcomes are:
   - `ACCEPTED`;
   - `DENIED`;
   - `REPLAYED`;
   - `CONFLICT`;
   - `UNAVAILABLE`;
   - `IDEMPOTENCY_MISMATCH`;
   - `REJECTED`;
   - `BLOCKED`.
9. Idempotency policy:
   - usage-consumption semantic requests require an idempotency key;
   - same key plus same request fingerprint plus terminal outcome returns `REPLAYED` or the original terminal outcome;
   - same key plus different request fingerprint returns `IDEMPOTENCY_MISMATCH`;
   - missing idempotency key returns `REJECTED` before any effect.
10. Commit-point policy:
    - EB-06 may define semantic commit-point terminology only;
    - no actual persistent commit is implemented in EB-06;
    - a successful semantic usage decision may become an event candidate only after the owning requester module reaches its own future approved commit point;
    - unknown commit state returns `UNAVAILABLE` or `BLOCKED`, never silent `ACCEPTED`.
11. Reset/window policy:
    - `ACTIVE_BEACON_SLOT` has no reset window in EB-06 and is evaluated from current source facts snapshot;
    - `SCAN_INTERVAL_WINDOW` is evaluated from current time plus supplied last/next scan evidence;
    - daily/monthly quota reset, rolling counters and notification counters are not approved in EB-06.
12. Conflict handling:
    - conflicting source facts return `CONFLICT`;
    - missing required source facts return `UNAVAILABLE` or `REJECTED`;
    - unsupported counter family returns `BLOCKED`;
    - ambiguous evidence must not return `ACCEPTED`.
13. Remaining open decisions:
    - `OD-010` country-wide availability remains open;
    - `OD-011` minimum monitoring frequency safety remains open;
    - `OD-013` billing, audit and personal-data retention remains open.

**Consequences:**

- EB-06 may proceed only for deterministic semantic usage-consumption contracts/tests.
- EB-06 must remain transport-neutral, provider-neutral, framework-neutral, ORM-neutral and runtime-neutral.
- EB-06 must not implement database schema, migrations, repositories, runtime quota decrement, Beacon mutation, Scan Orchestration mutation, Notification Delivery mutation, payment/provider integration, Admin UI/Web Cabinet UI, Docker/CI/CD/deploy/runtime configuration, secrets, tokens or credentials.
- Beacon Management, Scan Orchestration and Notification Delivery integration remain gated by their own accepted module contracts.
- Provider/payment runtime remains blocked until provider-specific evidence and exact tasks.

## ADR-0013 — 2026-07-08 — Payment provider official evidence capture

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-08 official provider evidence/reference capture for later planning only.

**Не открывает:** runtime provider adapter, provider SDK/API calls, webhooks, payment account setup, invoice/receipt/tax implementation, refunds runtime, recurring billing, provider-derived entitlement grants, database schema, migrations, repositories, persistence, Admin UI, Web Cabinet UI, Beacon mutation, scheduler integration, notification sending, Docker, CI/CD, deploy, runtime configuration, secrets, tokens or payment credentials.

**Контекст:** The module playbook keeps payment-provider work blocked until exact provider-specific scope is approved. The current owner policy remains manual renewal only and manual refunds only, with no recurring payments now. EB-08 needs official provider references captured as governance evidence before later planning can define deterministic semantic boundaries. Provider response remains external evidence and never grants access by itself.

**Решение:**

1. Capture the official YooKassa API reference as provider evidence for future planning only.
2. Capture the official Telegram bot payments documentation for digital goods/services and Telegram Stars as provider evidence for future planning only.
3. Capture the official T-Bank internet acquiring and T-API documentation as provider evidence for future planning only.
4. Treat provider response as non-authority evidence only.
5. Treat raw provider payload as not being entitlement authority.
6. Preserve the current owner policy: manual renewal only and manual refunds only.
7. Preserve the current owner policy that recurring billing is not implemented now.
8. Require any future EB-08 implementation to use an exact provider-specific task before runtime adapter work.
9. Keep `OD-010`, `OD-011` and `OD-013` open.

**Consequences:**

- EB-08 may use these official references for later provider-boundary planning and documentation only.
- This decision does not authorize provider SDK/API calls, webhook endpoints, payment account setup, receipts, invoices, refunds automation, recurring billing, card data handling, database access, migrations, Admin UI, Web Cabinet UI or secrets handling.
- Payment evidence remains external evidence and never grants access by itself.
- Raw provider payload must not become entitlement authority.
- `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.
## ADR-0014 — 2026-07-08 — EB-09 Payment reconciliation and manual refund semantics

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-09 deterministic semantic reconciliation/refunds contracts/tests only.

**Не открывает:** runtime reconciliation engine, provider API calls, provider refund API calls, automatic refunds, recurring billing, chargebacks, webhooks, persistence, migrations, UI, secrets or provider-derived entitlement grants.

**Контекст:** EB-09 opens only for deterministic semantic reconciliation/refund contracts/tests. The module already treats payment provider responses as external evidence only, raw provider payload as non-authority, payment evidence as non-authority for access changes, refunds as manual only and recurring billing as not implemented now. The exact reconciliation/refund semantic state machine needed for EB-09 has now been captured at governance level.

**Решение:**

1. EB-09 is approved only for deterministic semantic reconciliation/refund contracts/tests.
2. Approved reconciliation semantic outcomes are: `RECORDED`, `DUPLICATE`, `REJECTED`, `AMBIGUOUS`, `RECONCILE_REQUIRED`, `CONFIRMED`, `UNRESOLVED`, `MANUAL_REVIEW_REQUIRED`, `REPLAYED`, `IDEMPOTENCY_MISMATCH`, `BLOCKED`.
3. Approved manual refund semantic outcomes are: `MANUAL_REFUND_REVIEW_REQUIRED`, `MANUAL_REFUND_REFERENCED`, `AUTOMATIC_REFUND_BLOCKED`, `PROVIDER_REFUND_API_BLOCKED`, `REFUND_REJECTED`, `REFUND_REPLAYED`, `REFUND_IDEMPOTENCY_MISMATCH`.
4. Duplicate provider event identity or stable idempotency/fingerprint semantics must not create a second semantic effect.
5. Ambiguous or unknown external provider effect must use reconcile-first semantics; blind retry after unknown provider effect is forbidden.
6. Idempotency key is required; missing key is rejected before any semantic effect; same key with the same request fingerprint replays the original terminal semantic outcome; same key with a different request fingerprint returns `IDEMPOTENCY_MISMATCH`.
7. Commit-point terminology in EB-09 is semantic-only and does not implement persistence/runtime commit in this task.
8. Manual renewal only remains the current recurrence policy; recurring billing attempts remain blocked.
9. Refunds are manual only; automatic refunds and provider refund API calls remain blocked.
10. Raw provider payload is not entitlement authority and payment evidence must not create, change or extend access by itself.
11. Any future entitlement/subscription transition requires a separate server-authorized business transition and remains distinct from payment evidence.
12. `OD-010`, `OD-011` and `OD-013` remain open.

## ADR-0015 — 2026-07-08 — EB-11 Admin tariff management semantic boundary

**Статус:** APPROVED

**Модуль:** `03-entitlements-and-billing`

**Открывает gate:** EB-11 deterministic semantic Admin tariff-management boundary contracts/tests only.

**Не открывает:** Admin UI, Web Cabinet UI, Identity role runtime, billing runtime, database schema, migrations, repositories, persistence, provider/payment runtime, secrets or product-code.

**Контекст:** The module playbook and prior governance decisions already separate owner policy, identity authority, admin/support boundary and web presentation boundary. EB-11 needs a deterministic semantic boundary for tariff draft/edit/publish and protected account tariff/manual assignment contracts/tests without authorizing runtime implementation.

**Решение:**

1. Approved semantic capability references for future EB-11 contracts/tests are:
   - `ENTITLEMENTS_TARIFF_ADMIN`;
   - `ENTITLEMENTS_TARIFF_ASSIGN_ADMIN`;
   - `ENTITLEMENTS_MANUAL_ACCESS_ADMIN`.
2. `ENTITLEMENTS_TARIFF_ADMIN` is required for protected tariff draft/edit/publish semantics inside Entitlements.
3. `ENTITLEMENTS_TARIFF_ASSIGN_ADMIN` is required for protected account tariff assignment semantics inside Entitlements.
4. `ENTITLEMENTS_MANUAL_ACCESS_ADMIN` remains the existing approved manual access capability from `ADR-0011`.
5. These capability references are module-level semantic references only. They do not implement Identity roles, do not close exact admin role taxonomy, and do not authorize UI flags, provider usernames, chat titles, local config or client-supplied admin flags.
6. Approved semantic command families are:
   - `CreateTariffDraftCommand`;
   - `EditTariffDraftCommand`;
   - `PublishTariffDefinitionCommand`;
   - `AssignAccountTariffCommand`;
   - `AssignManualAccessCommand`;
   - `RejectAdminTariffCommand`.
7. Approved semantic outcomes are:
   - `DRAFT_CREATED`;
   - `DRAFT_UPDATED`;
   - `PUBLISH_READY`;
   - `PUBLISHED`;
   - `ASSIGNED`;
   - `MANUAL_ACCESS_ASSIGNED`;
   - `REJECTED`;
   - `FORBIDDEN`;
   - `CONFLICT`;
   - `REPLAYED`;
   - `IDEMPOTENCY_MISMATCH`;
   - `BLOCKED`;
   - `UNAVAILABLE`.
8. A tariff draft is not an active tariff, does not change user access, does not change subscription state and does not create payment/provider behavior.
9. A tariff draft must include semantic draft id, actor context, requested fields, reason, idempotency key and audit reference.
10. Future tariff names, prices, limits and defaults may not be invented by code/tests. Only current approved `Free` and `Basic` product values may be used as current published policy where already accepted by prior ADRs.
11. Publishing requires all product fields to be approved and no open-decision blocker relevant to the field.
12. Publishing must be performed by an Entitlements semantic command, not by Admin/Web direct write.
13. Editing an already published tariff must create a new semantic version or be blocked until versioning rules are approved.
14. Direct mutation of historical tariff definitions is blocked, and deleting tariff history is blocked.
15. Protected assignment requires verified actor context, server-side capability reference, target `account_id`, target approved tariff or manual-access scope, reason, idempotency key and audit reference.
16. Assignment to non-approved or draft-only tariff returns `BLOCKED` or `REJECTED`.
17. Assignment cannot be derived from payment provider evidence or UI/client flag and cannot bypass subscription/manual-access semantics already accepted.
18. Assignment does not mutate Beacon, scheduler, notification, provider or UI state, and remains semantic-only until persistence/runtime gates open.
19. Admin/Web must supply verified server-side actor context; UI flags, provider usernames, chat titles, local config and client-supplied admin flags are not authorization.
20. Identity owns role assignment and actor verification; EB-11 does not implement role assignment, role revocation or role-changing and does not close exact admin role taxonomy.
21. Admin & Support and Web Cabinet may request protected tariff/manual assignment actions only through public command envelopes and do not own tariff, subscription, entitlement or payment state.
22. Admin & Support and Web Cabinet must not write Entitlements state directly or write billing tables directly.
23. Every tariff draft/edit/publish/assignment semantic mutation requires an idempotency key; missing idempotency key returns `REJECTED`; same key + same request fingerprint + prior terminal outcome returns `REPLAYED` or original terminal outcome; same key + different request fingerprint returns `IDEMPOTENCY_MISMATCH`.
24. Audit reference is required as a semantic reference only, and audit retention/storage remains blocked by `OD-013`.
25. `OD-010`, `OD-011` and `OD-013` remain open and must not be closed by this decision.

**Последствие:**

EB-11 exact semantic contracts/tests may use this decision and `ADR-0015` as approved input only for deterministic semantic Admin tariff-management boundary contracts/tests. Runtime Admin UI, Web Cabinet UI, Identity role runtime, billing runtime, persistence, migrations, database, provider/payment runtime or actual tariff management service still requires a separate exact task.

## ADR-0016 — 2026-07-09 — Beacon Management owner decisions for BM-01

**Статус:** APPROVED owner decision capture for Beacon Management governance.

**Контекст:** Module `04-beacon-management` playbook v1.0 intentionally left Beacon-specific use of `OD-003`, `OD-004`, `OD-009`, `OD-010`, `OD-011`, `OD-013`, duplicate source URL policy, Beacon naming, revision retention/compaction, patch-based save semantics, lifecycle/history/delete semantics and several activation constraints unresolved. Entitlements & Billing already captured billing policy in `ADR-0009`; this ADR captures Beacon Management-specific owner decisions and boundaries before Beacon Management contracts, fixtures, tests, implementation or runtime may use them.

**Решение:**

### Relation to Entitlements & Billing decisions

Beacon Management must treat Entitlements & Billing as the tariff/access authority. Beacon Management may use captured Free/Basic outcomes semantically, but it must not duplicate tariff authority as runtime source.

`ADR-0009` remains the Entitlements & Billing owner decision capture. This ADR captures Beacon Management consequences and module boundaries.

### OD-003 / OD-011 — allowed monitoring intervals and minimum monitoring frequency

For `Paid / Basic`:
- minimum interval is 5 minutes;
- allowed interval step is 5 minutes: 5, 10, 15, 20 and further by 5-minute increments;
- there is no configured upper limit at this decision level.

For `Free`:
- minimum interval is 3 hours;
- allowed interval step is 3 hours: 3, 6, 9, 12 hours and further by 3-hour increments;
- there is no configured upper limit at this decision level.

User interval-change UI mechanics remain deferred to a future interface decision. Semantic contracts may express allowed/denied interval outcomes, but this decision does not authorize runtime UI flow, scheduler runtime, parser calls, database schema or product implementation.

### OD-004 — behavior after paid access expiry

After paid access ends:
- only `Free` access remains;
- all active paid Beacons become frozen;
- the user receives a future notification through a future notification/channel module;
- the user chooses one Beacon that may remain under Free;
- the chosen Beacon must be brought into Free-compliant state;
- the user explicitly starts/resumes the chosen Free Beacon;
- without user choice and Free compliance, no Beacon is activated automatically.

Beacon Management must not automatically choose a Beacon for the user.

### OD-009 — supported editable filters

Beacon Management does not define a hard-coded first-stage list of supported editable Avito filters by itself.

Beacon Management may support only parameters that are safely parsed from the Avito source URL and accepted as supported by Parser Adapter / Filter Catalog evidence. Parser Adapter / Filter Catalog evidence determines which parameters are actually supported.

Unsupported, uncertain or ambiguous parameters must not be silently changed.

This decision does not authorize Parser Adapter implementation, Filter Catalog implementation, live Avito calls, raw query-string rewriting, UI forms or runtime validation.

### OD-010 — country-wide / all-Russia search

Country-wide search across all Russia is allowed for `Paid / Basic`.

`Free` cannot activate a country-wide Beacon. If a Free user submits an all-Russia source, the system must explicitly indicate that this is unavailable on Free and require the user to choose a city. Without city selection, the Free Beacon is not activated.

### OD-013 — archive, delete, history and permanent delete

A user may delete a Beacon from the active list.

Ordinary deletion moves the Beacon into user-visible History / Archive rather than necessarily physically deleting it immediately.

History includes Beacons that belonged to the user, including:
- frozen Beacons after paid access expiry;
- Beacons removed from the active list;
- archived Beacons.

From History, the user may restore/activate a Beacon without re-entering the source URL if current entitlement, current policy and validation allow.

From History, the user may permanently delete a Beacon. A permanently deleted Beacon cannot be restored.

Deleted, archived and History Beacons do not count toward the active Beacon limit. For Free, only one active Beacon counts toward the Free active limit. While a Free account already has one active Beacon, another active Free Beacon cannot be added.

Exact History UI mechanics remain deferred to a future interface decision.

This decision does not authorize physical database delete implementation, retention job, privacy/legal retention implementation, listing history deletion, ScanRun deletion, notification sending, Admin/Web/Telegram/MAX presentation or database schema.

### Duplicate source URL

One account may create multiple Beacons with the same Avito source URL. A user may need identical source URLs for different intervals, names or settings.

Different accounts may also have identical source URLs.

Source URL is not a unique key. Idempotency must not be based only on source URL.

### Beacon naming

The user may provide a Beacon name.

If the user does not provide a name, a default name may be created from recognized title/context.

The exact default naming algorithm remains deferred to a future interface decision.

Beacon name is presentation metadata. Rename does not change search configuration.

### Configuration changes, current configuration and revision/storage policy

The owner does not want unbounded database clutter from old user-facing revision settings.

Target behavior:
- the user sees one current working Beacon configuration;
- when settings change, the new active configuration becomes current;
- old user-facing revision settings are not stored forever as separate user-visible clutter;
- if downstream scan/audit/history requires proof of settings used by an already committed scan, minimal immutable evidence/snapshot/reference may be retained only for that committed scan/audit purpose.

Exact physical retention and compaction policy must be decided governance-safely before persistence, migrations or runtime implementation.

This decision clarifies the current owner intent and must be reconciled with the earlier immutable revision boundary in the Beacon Management playbook before any persistence, migration, scan handoff or runtime implementation.

### Patch-based save and last-write-wins behavior

Saving Beacon settings is patch-based and last-write-wins.

When a user saves settings, the system reads the current authoritative Beacon state and applies only fields that are actually present in the current save command.

If two clients changed different fields, both changes may be combined.

If two clients changed the same field, the last successful save wins.

The system must not overwrite the entire Beacon from an old stale form.

After save, the user must see the actual current Beacon state reloaded from authoritative storage.

A user-visible conflict is not created merely because Telegram and Web Cabinet edited the same Beacon concurrently. Conflict/blocked outcomes remain allowed when the command cannot be safely applied at all, including permanently deleted target, unauthorized actor/account, unsupported field, invalid source/snapshot, entitlement denial, missing required confirmation or missing target state.

Before physical database/schema gates this is semantic behavior only, not a database implementation.

### Overrides and effective configuration

Effective configuration is the accepted extracted snapshot plus explicit user overrides.

An override wins over snapshot only for an explicitly changed supported field.

Unsupported or uncertain parameters must not be silently changed.

For multivalue parameters, approved values must not be silently collapsed.

Exact add/remove/replace UX for multivalue parameters remains deferred to Filter Catalog / interface evidence.

### Parser snapshot acceptance

Exact acceptance thresholds must be tested later.

Malformed, incomplete, CAPTCHA-affected, blocked, route-failed or ambiguous parser outcome must not become a clean accepted snapshot.

### Entitlement re-check

Before activation or resume, entitlement must be checked again.

If entitlement is ambiguous, denied or expired, the Beacon is not activated.

If Free does not allow geography, interval or active count, the Beacon is not activated.

If paid access ended, affected Beacons enter the frozen/history/user-choice flow described for OD-004.

### Basic active Beacon limit

Basic initially allows 5 active Beacons.

An Admin capability may change limits and tariffs in the future. Admin UI/runtime is not implemented by this decision.

**Границы и запреты:** This ADR does not authorize product-code, parser implementation, live Avito calls, source URL live validation, Filter Catalog implementation, Scan Orchestration runtime, scheduler runtime, notification sending, Telegram/MAX/Web Cabinet UI, Admin UI, database schema, migrations, physical delete implementation, retention job, runtime services, Docker/CI/CD/deploy, ports/listeners, credentials or secrets.

**Последствие:** Beacon Management BM-01 may use these decisions only as governance-captured owner decisions. Later steps may reference them in semantic contracts and synthetic documentation only when their own gates allow it. Runtime, persistence, parser, scan, UI and infrastructure remain separately gated.
## ADR-0017 — 2026-07-09 — Avito Parser Adapter owner decisions for APA-01

**Статус:** APPROVED owner decision capture for Avito Parser Adapter governance.

**Модуль:** `05-avito-parser-adapter`

**Открывает gate:** APA-02 semantic request/outcome contracts and synthetic fixture identifiers only, after an exact task.

**Не открывает:** product-code beyond separately authorized semantic contracts, live Avito calls, endpoint probing, source URL live validation, HTML/JSON parser runtime, HTTPX live client, provider SDK/client, cookies, sessions, proxy/VPN/CAPTCHA tooling, browser automation, real Avito fixtures, raw provider payload retention, listing detail enrichment runtime, phone extraction runtime, database schema, migrations, repositories, persistence, Scan Orchestration runtime, Egress Routing runtime, Notification Delivery runtime, Filter Catalog implementation, Admin UI, Web Cabinet UI, Telegram/MAX UI, Docker, CI/CD, deploy, runtime services, ports/listeners, credentials, secrets or tokens.

**Контекст:** Module `05-avito-parser-adapter` is the external boundary between untrusted Avito/search transport outcomes and internal transport-neutral Mayak contracts. The approved module playbook uses `AVITO-PRIMARY-PARSER-001` as implementation observation only and explicitly rejects automatic inheritance of endpoint stability, local history, phone extraction, unrestricted details/views collection, retry/cookie/proxy choices and production/legal suitability. Owner decisions are required before Parser Adapter contracts, synthetic fixtures, tests or later implementation may use listing-card field-family policy, raw-retention policy, newest-sort handoff or lost-anchor handoff semantics.

**Решение:**

1. Parser Adapter is a Mayak module, not a copy of the reference parser. `AVITO-PRIMARY-PARSER-001` may be used only as technical evidence / observation within its exact commit and scope.
2. Current stage live Avito calls are forbidden. The allowed current scope is semantic contracts, synthetic fixtures, fake response classifications, safe parser outcome models, reference-profile placeholders, negative safety outcomes and no-live-traffic evidence.
3. Forbidden current-stage actions include real requests to Avito, endpoint probing, browser automation, live source URL validation, cookies, sessions, proxy/VPN/CAPTCHA tooling and production parser implementation.
4. The observed internal later-page endpoint `/web/1/js/items` is reference observation only. It is not an official consumer-search API, not a stability guarantee, not legal/access permission and not a production route design.
5. Owner wants a useful listing card that can avoid unnecessary user transitions to Avito when fields are technically and safely obtainable.
6. Free users must not be intentionally deprived of convenient listing-card fields. The primary monetization boundary is active Beacon count, monitoring interval and geography, not hiding phone/seller/rating/description from Free by default.
7. Desired listing-card field families are title, normalized price, source/listing URL, preview/image reference, geography, category, publication/order signal if proven, full description if proven, seller identity/name/profile if proven, seller rating if proven and phone/contact availability if proven.
8. Phone value itself is allowed only after a separate approved phone-enrichment evidence gate. Phone extraction runtime is not authorized by this decision.
9. Listing data must be represented in tiers: Tier 1 search-result fields, Tier 2 listing-detail fields and Tier 3 contact/phone fields.
10. Tier 1 may be described in semantic contracts and synthetic fixtures when exact tasks allow it. Tier 2 remains gated by listing-detail enrichment proof. Tier 3 remains gated by phone-enrichment proof.
11. Phone, seller, seller rating and description are evidence-gated optional candidate field families. They are not globally mandatory parser success criteria.
12. Absence or unavailability of phone, seller, rating or description must not make an otherwise usable search-result listing candidate fail unless a future exact compatibility profile explicitly requires that field for that scope.
13. Parser Adapter must return field-level provenance, quality and warnings. If an active compatibility profile does not prove a field, Parser returns unavailable, unknown or warning semantics rather than inventing a value.
14. Category-specific characteristics are not mandatory in the first parser scope. Parser may return evidence-bound parameter candidates only when they are safely present in source URL or search extraction evidence. Filter Catalog & Builder remains owner of supported filter definitions, editable filter definitions, category-specific option schema and UI-neutral builder semantics.
15. Monitoring new listings should prefer newest-first observed ordering when evidence proves the sort context. Parser Adapter must return observed order, sort-context candidate if proven, publication/order timestamp candidate if proven and warning if sort context is missing, ambiguous, unsupported or unproven.
16. Parser Adapter does not decide baseline, new listing, price-change event, anchor window, lost-anchor recovery or notification creation. Scan Orchestration & Listing State owns those decisions.
17. Future Scan design should use top-window newest-first logic, first successful scan should create baseline without mass-sending old listings, and anchor window size should become future admin-configurable setting rather than a Parser constant.
18. Future lost-anchor behavior: if all anchors are lost, the system must not label top results as confirmed new. It may show the latest 3 fresh listings as “latest fresh listings / state restored” and then store a new anchor window so the same recovery does not repeat those listings as newly found again. This is a Scan handoff policy, not Parser implementation.
19. Raw provider payloads are not stored by default. Full raw HTML, full raw JSON, hidden provider structures, cookies, session values, tokens and unnecessary provider fields must not be retained, logged, added to Git, placed in ordinary reports or used as public contracts without a separate OD-013 / evidence-retention gate.
20. Allowed safe evidence forms are hash/fingerprint, counts, profile ID, retrieval timestamp, field availability, redacted reason code, safe selector/profile version and synthetic sample data that is not a real Avito raw dump.
21. A clean usable empty result is allowed only when a future approved compatibility profile proves that the request was sent through an approved route, the response was explicit and usable, required structure was present and validated, no restriction/CAPTCHA/malformed/incomplete/ambiguous signal exists and evidence is current for that scope.
22. No request sent, route failure, timeout, CAPTCHA, restriction, malformed response, incomplete response, unsupported structure, ambiguous response, stale reference profile or parser uncertainty must not become clean empty success.
23. Live pagination is forbidden now. Pagination may be represented only as semantic page/batch outcomes, synthetic pagination fixtures, per-page outcome models and partial/ambiguous/interrupted placeholders until a future exact evidence/access gate exists.
24. Parser Adapter does not own cookies, sessions, browser profiles, proxy selection, VPN selection, mobile proxy choice, CAPTCHA solving, route fallback, route quarantine, agent health or lease management. Egress Routing owns route selection, lease, assignment, transport outcome, quarantine and fallback policy.
25. Parser Adapter may classify outcomes such as `CAPTCHA_OR_CHALLENGE`, `RATE_OR_ACCESS_RESTRICTED`, `TRANSPORT_UNAVAILABLE`, `TRANSPORT_AMBIGUOUS`, `RESPONSE_RECEIVED_UNCLASSIFIED`, `USABLE_RESPONSE`, `MALFORMED_RESPONSE`, `INCOMPLETE_RESPONSE`, `UNSUPPORTED_STRUCTURE`, `REFERENCE_STALE` and `RESULT_AMBIGUOUS` only as semantic outcomes within approved contracts and fixtures.
26. Owner decisions captured here may be used only by later exact Parser Adapter roadmap tasks. They do not authorize runtime provider traffic, persistence, UI, notifications, Egress runtime, Scan runtime or Filter Catalog implementation.

**Последствие:**

- APA-02 may use these owner decisions only for semantic Parser request/outcome contracts and synthetic fixture identifiers after an exact task.
- APA-08 may later model phone/seller/rating/description as desired evidence-gated optional listing-card field families, not as mandatory runtime extraction.
- APA-09 may later capture ordering/newest-sort evidence and Scan handoff semantics, but Parser must not implement Scan newness, baseline, anchor-window or notification behavior.
- APA-10 remains blocked for live pagination.
- APA-11 remains blocked for raw-retention/storage implementation until OD-013 / evidence policy gates.
- `OD-009`, `OD-010`, `OD-011` and `OD-013` remain open except where this ADR provides Parser-specific governance input for semantic planning.
- Product-code, live Avito calls, provider implementation, persistence, UI and infrastructure remain separately gated.

## ADR-0018 — 2026-07-09 — Scan Orchestration owner decisions for SOLS-01

This governance capture records the owner decisions now frozen in `docs/04-modules/06-scan-orchestration-and-listing-state/OWNER_SCAN_DECISIONS_CAPTURE_v1.0.md` for `06-scan-orchestration-and-listing-state`.

In short: Scan scope stays new-listings-only; price can remain candidate data; price-change tracking and price-pair notification are deferred; newest-first monitoring is required; Parser Adapter owns observed order and sort/publication signals; missing or unproven sort context is blocked/ambiguous rather than false no-new; rolling anchors are compact memory; Scan does not build a full user-visible archive; anchors update after each successful comparison-eligible scan; anchor size is future Admin-configurable; lost anchors differ from window overflow; lost anchors may restore the latest 3 as latest-fresh rather than confirmed-new; window overflow remains future design; external failure, Avito unavailability, CAPTCHA, route failure, parser failure or ambiguity is not no-new and must not erase or advance anchors; one pending recovery scan is kept; one recovery result may be reported after entitlement expiry if failure began while access was active; no-new must not spam every interval by default; one Beacon cannot have parallel active comparison commits; lifecycle and entitlement are re-checked before user-visible commit; paused/archived/deleted/frozen/denied/ambiguous/expired normal state blocks the normal result except one recovery grace case; Scan emits safe facts/status only while Notification Delivery and UI/channel own delivery/rendering; scheduler, worker, DB, parser/provider, Egress, Notification, UI, deploy, secrets and raw payload retention stay gated; older playbook v1.0 price-pair direction is superseded for current owner scope but remains in history; OD-011 and OD-013 remain open and no open decision is closed by assumption.

---

## ADR-0019 — 2026-07-12 — Egress Routing owner decisions for ER-01

**Статус:** APPROVED owner decision capture for Egress Routing governance.

**Модуль:** `07-egress-routing`

**Roadmap step:** `ER-01`

**Technical task:** `ER-01-GOVERNANCE-CAPTURE-20260712-003`

**Открывает gate:** использование зафиксированных owner decisions как input для последующих exact semantic Egress tasks.

**Не открывает:** live Avito access, route runtime, proxy/VPN/tunnel implementation, concrete provider selection, browser automation, browser-extension modification, Windows Agent, native host, installer, cookies/session storage, CAPTCHA solving, persistence, migrations, worker/scheduler runtime, Docker, CI/CD, deployment, ports, firewall, DNS, TLS, secrets or credentials.

**Контекст:** Module 07 playbook intentionally leaves route technology, topology, provider access, fallback order, cookies/session policy, Windows/browser implementation, runtime and live proof gated. The owner supplied explicit direction for the primary Linux/server route candidate, browser-extension evidence boundary, Windows fallback, development owner bridge, browser worker model, Russian residential route, isolated sessions, CAPTCHA handling, policy-based automatic fallback, route authority, minimal assignment, agent database isolation and live proof limits. These decisions must be captured before semantic contracts or fixtures use them.

**Решение:**

1. The primary target route family is Linux/server reference-style egress, but it is not production-proven and requires a separate bounded `proof_only` task before implementation.
2. Owner-provided browser-extension experience is accepted only as evidence that a browser-extension route family can work with Avito; it is not production-scale SaaS proof and does not authorize implementation.
3. A future production-scope Avito extension must keep only necessary Avito interaction/extraction, bounded assignment, safe result return and explicit outcome handling, while excluding self-editing, developer-control and unrelated automation capabilities unless separately proven necessary.
4. Full SaaS on Windows is not selected. Linux remains the preferred SaaS core environment.
5. Windows VM, Windows Egress Agent and Windows Browser Worker are allowed only as future replaceable fallback execution dependencies after exact proof, security and operations gates.
6. A temporary owner-assisted development bridge is allowed only for explicit bounded development/proof use, is not production, is not scalable proof and must remain replaceable.
7. One permanently open browser per Beacon is not the target architecture. A bounded browser worker pool is the preferred future browser fallback model.
8. Russian residential proxy / Russian residential route is allowed as a future route type, but no provider, credential format, protocol, payment contract, priority or production configuration is selected.
9. Cookies/session may be used only through a future project-owned isolated-session policy. Personal browser profiles, passwords, unrelated cookies, private owner sessions by default and secret values in Git/logs/reports are forbidden.
10. CAPTCHA solving and CAPTCHA bypass are forbidden. CAPTCHA, challenge and restriction must become explicit outcomes and may degrade, restrict or quarantine a route; they must not become clean empty results.
11. Automatic fallback is allowed only when policy-based, bounded, explainable and auditable. Blind, random, infinite or CAPTCHA-bypass fallback is forbidden.
12. Runtime route selection belongs only to Egress Routing. Parser, Scan, Beacon and Notification do not choose routes.
13. Agent or browser worker receives only a minimum bounded assignment and no full Account, Beacon, tariff, Scan history, Notification history, global secrets or unrelated personal data.
14. Agent has no direct primary database access and remains a replaceable execution dependency.
15. Live Avito proof is allowed only through a separate owner-approved `proof_only` task with exact route, URL scope, limits, no-secrets/no-raw-retention rules, success/failure criteria and STOP conditions.
16. `OD-009`, `OD-010`, `OD-011` and `OD-013` remain open.
17. Tunnel/proxy/VPN/browser/Windows runtime, database, migrations, services, CI/CD and deployment remain blocked.

**Последствие:**

- ER-02 and later exact semantic steps may use these decisions only within their own approved scope.
- This ADR does not select a concrete route provider or technology implementation.
- This ADR does not authorize live traffic or runtime.
- Transport success remains distinct from Parser success, Scan success and Notification delivery.
- Browser-extension evidence remains proof of route-family feasibility only, not production readiness.
- No open decision is closed by assumption.

---

## ADR-0020 — 2026-07-12 — Notification Delivery owner decisions for ND-01

**Статус:** APPROVED owner decision capture for Notification Delivery semantic planning.

**Модуль:** `08-notification-delivery`

**Roadmap step:** `ND-01`

**Technical task:** `ND-01-GOVERNANCE-CAPTURE-20260712-001`

**Открывает gate:** последующие точные semantic-only задачи модуля 08 после отдельной проверки prerequisites и exact task.

**Не открывает:** source code этим решением, physical database schema, migrations, queue, worker, broker, scheduler, provider adapter, Telegram/MAX bot or API, webhook, Mini App, live delivery, provider calls, message-template catalog, provider credentials, runtime configuration, Docker, CI/CD, deploy, retention/deletion tooling, read/click tracking, quiet hours or digest implementation.

**Контекст:**

Playbook Module 08 v1.0 определил generic Notification Delivery boundary, но оставил открытыми или требующими уточнения текущие product rules для активных notification families, price-change events, no-new status, recovery, multi-channel planning, listing grouping and delivery history. Владелец зафиксировал эти решения до semantic contracts/tests и отдельно сохранил provider/runtime/schema gates закрытыми.

**Решение:**

1. Главный текущий пользовательский notification effect — уведомление о новых объявлениях после committed Scan fact и успешного прохождения eligibility gates.
2. Initial baseline не создаёт user-visible listing notification и не должен отправлять существующие объявления как новые.
3. Price-change notification для старого объявления отключён и отложен. Цена может использоваться как безопасное display field, но изменение цены само по себе не создаёт outbox item.
4. Notification Delivery принимает только committed upstream source facts. Parser-only, Egress-only, raw provider and unapproved callback outcomes не создают notification work.
5. Статус «новых объявлений нет» не отправляется после каждого scan и не отправляется каждые пять минут по умолчанию.
6. Пользователь в будущем может включить status notification «Маяк работает. Новых объявлений нет».
7. Минимальная частота push-уведомления «новых нет» — не чаще одного раза в час.
8. Текущий no-new status должен оставаться доступным в safe read model/status UI независимо от push preference.
9. При начале проблемы Avito, route or parser пользователь получает один понятный status notification; одинаковый статус не повторяется на каждом интервале.
10. Материальное изменение проблемы может создать новый status effect при отдельной approved classification.
11. После восстановления выполняется и сообщается один результат одного recovery scan, а не набор уведомлений за каждый пропущенный интервал.
12. Recovery result с новыми объявлениями сообщает новые объявления.
13. Recovery result без новых объявлений может сообщить восстановление и отсутствие новых объявлений согласно approved recovery-result policy.
14. Если recovery scan завершился lost anchors, результат классифицируется как «последние свежие / состояние восстановлено», а не как confirmed-new.
15. Если внешняя проблема началась при активном доступе, допускается один owed recovery-result после истечения доступа. После этого одного результата снова применяются текущие entitlement rules.
16. Один scan result с несколькими новыми объявлениями является одним generic user-visible notification effect с полным count и всеми безопасными listing-card references.
17. Notification Delivery не обрезает listing references из-за preview limit и не превращает каждое объявление в отдельное generic notification по умолчанию.
18. Pagination, buttons, preview count, carousel-like presentation и final rendering принадлежат Telegram/MAX adapters or Web Cabinet, а не Notification Delivery.
19. Безопасный listing-card boundary может включать title, price, geography, safe listing URL/reference, approved photo/preview reference, Beacon reference and reason label, если эти facts уже предоставлены approved upstream contract.
20. Phone, seller, seller rating and description допустимы только после отдельного Parser/detail/privacy gate. Notification Delivery их не добывает и не требует для доставки.
21. Notification Delivery не хранит raw Avito payload, full HTML/JSON, cookies, tokens, credentials or unapproved private seller data.
22. По умолчанию generic delivery work планируется для всех включённых и подтверждённых каналов пользователя.
23. Пользователь может отключить ненужный канал; disabled or unverified channel не получает delivery work.
24. Telegram Adapter владеет Telegram-specific mapping/rendering/delivery, MAX Adapter владеет MAX-specific mapping/rendering/delivery, Web Cabinet владеет UI/read presentation.
25. Notification Delivery не создаёт Telegram/MAX provider payloads, templates, bots, webhooks, Mini Apps or provider calls.
26. Multi-channel success/failure фиксируется отдельно для каждого channel/attempt. Успех одного канала не стирает failure history другого.
27. Cross-channel priority/fallback values сейчас не выбираются, поскольку текущая default-модель — delivery во все enabled channels.
28. Unknown, ambiguous or interrupted provider send является reconciliation-first state и никогда не повторяется вслепую.
29. Attempt identity and evidence сохраняются; ambiguous send не создаёт автоматически второй attempt с возможным duplicate user-visible effect.
30. Provider HTTP success, Egress transport success, queue success or adapter callback сами по себе не доказывают accepted user-visible delivery.
31. Minimal delivery history требуется для deduplication, support and reconciliation.
32. Minimal history может содержать source event reference, outbox identity, authorized account/Beacon scope, channel class, target reference class, attempt identity, safe outcome/reason class, deduplication key, approved timestamps, safe listing-card references, correlation/causation and reconciliation state.
33. Delivery history не является full listing archive, full chat history or raw provider archive.
34. Retention, deletion, archive and compaction остаются заблокированными `OD-013`.
35. Read, click and open tracking отложены и этим решением не разрешаются.
36. Quiet hours, digest, time batching and grouping over time отложены и этим решением не разрешаются.
37. Exact preference storage, UI, unsubscribe semantics, future-channel defaults, retry/backoff values, provider limits, message templates, physical schema, queue/worker technology and runtime remain gated.
38. Semantic contracts, deterministic synthetic fakes, architecture/static checks and evidence documentation могут создаваться только отдельными exact roadmap tasks.
39. Это решение supersedes playbook v1.0 только в текущем owner product scope, где `ListingPricePairFirstSeen` не является активным user-visible trigger, no-new push configurable and rate-limited, all enabled channels planned by default, and recovery/lost-anchor notification classes explicitly defined.
40. `OD-013` не закрывается. Другие open decisions нельзя закрывать предположениями.

**Последствия:**

- Следующий допустимый шаг после отдельной проверки GitHub и prerequisites — `ND-02` semantic source event intake contracts.
- Каждый дальнейший ND step требует отдельного exact task.
- Runtime delivery, provider adapters, Telegram/MAX implementation, persistence, schema, migrations, queue, worker и deployment остаются blocked.
- Scan остаётся владельцем source facts, baseline, listing state, no-new и recovery facts.
- Parser остаётся владельцем extraction/provider classification.
- Egress Routing остаётся владельцем route/transport state.
- Identity, Entitlements и Beacon Management сохраняют собственную authority.
- Notification Delivery владеет только generic eligibility, outbox, channel plan, attempts, deduplication, reconciliation и safe delivery history semantics.

---

## ADR-0021 — 2026-07-12 — Correct malformed Notification Delivery owner capture

**Статус:** APPROVED append-only correction for ND-01 governance capture.

**Модуль:** `08-notification-delivery`

**Roadmap step:** `ND-01`

**Technical task:** `ND-01-LITERAL-CORRECTION-20260712-002`

**Исправляет:** механические literal, conjunction, Markdown and numbering defects в публикации `ADR-0020` и связанном `docs/04-modules/08-notification-delivery/OWNER_NOTIFICATION_DECISIONS_CAPTURE_v1.0.md`, опубликованные commit `9d1560057680f8d5f53921bb1b5632793e135e6f`.

**Не переписывает:** исторический текст `ADR-0020`; append-only history сохраняется byte-for-byte.

**Не изменяет product decisions:** owner scope, module boundaries, blocked gates and roadmap остаются теми же.

**Решение:**

1. `ADR-0020` остаётся исторической append-only записью и не редактируется.
2. Канонический полный owner capture для последующих Module 08 tasks — исправленный `docs/04-modules/08-notification-delivery/OWNER_NOTIFICATION_DECISIONS_CAPTURE_v1.0.md` из commit этой corrective task.
3. При механическом literal or conjunction расхождении между историческим `ADR-0020` и исправленным module document authoritative является исправленный module document.
4. Исправленный module document восстанавливает закрывающие Markdown fences, numbered lists, backticks around `OD-013` and GitHub `main`, all-enabled-and-verified channel wording, all safe listing references, no-blind-retry semantics and exact ND-02 gate wording.
5. Price-change notification остаётся disabled/deferred.
6. Initial baseline не создаёт user-visible listing notification.
7. No-new push остаётся suppressed/off by default и не может отправляться чаще одного раза в час при включённой preference.
8. Unknown provider send остаётся reconciliation-first and never blindly retried.
9. Provider adapters, Telegram/MAX/Web implementation, database, migrations, queue, worker, runtime, templates, credentials, retention tooling, read/click tracking, quiet hours and digest остаются blocked.
10. `OD-013` и другие open decisions не закрываются.
11. `ND-02` разрешается только после независимого принятия этой correction и новой проверки current GitHub `main`, Module 08 playbook and upstream Scan prerequisites.

**Последствия:**

- Исправленный module document является каноническим owner decision capture для Module 08.
- Эта задача не создаёт product code, contracts, tests, fixtures or runtime.
- Roadmap остаётся на `ND-01` до независимого принятия corrective commit.
