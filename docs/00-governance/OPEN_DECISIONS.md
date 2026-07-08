# Маяк Авито — открытые решения

**Версия:** 1.0  
**Статус:** APPROVED register of unresolved decisions  
**Источник:** `docs/01-product/MAYAK_AVITO_TARGET_MODEL_v0.1.md`, раздел 21.

Ни один пункт ниже нельзя заполнять предположением в коде, документации, тарифах, UI или тесте. Решение принимается отдельной записью в `DECISION_LOG_APPEND_ONLY.md` и затем переносится в затронутые документы.

| ID | Открытый вопрос | Блокирует/затрагивает |
|---|---|---|
| OD-001 | Период тарифа «Базовый 990 ₽». | payments/subscriptions, UI, billing |
| OD-002 | Цена, названия и лимиты следующих тарифов. | Entitlements & Billing |
| OD-003 | Полный перечень разрешённых интервалов и правила их изменения. | Entitlements, scheduler, Beacon Management |
| OD-004 | Поведение после окончания доступа: какие Маяки остаются активными/приостановленными. | Entitlements, Beacons, notifications |
| OD-005 | Платёжный провайдер, возвраты, рекуррентность и ручные оплаты. | Payments |
| OD-006 | Точная политика входа по телефону+паролю и восстановлению доступа. | Identity & Access, Web Cabinet |
| OD-007 | Требование телефона: когда он обязателен, если вообще обязателен. | Identity & Access |
| OD-008 | Политика слияния двух аккаунтов и возможность отмены. | Identity & Access, audit |
| OD-009 | Точный набор поддерживаемых на первом этапе редактируемых Avito-фильтров по категориям. | Parser, Beacons, Filter Catalog |
| OD-010 | Условия поддержки country-wide выдач в каждом поддерживаемом рынке. | Parser, Entitlements, Beacons |
| OD-011 | Минимальная частота мониторинга, допустимая с точки зрения устойчивости и правил Avito. | Scheduler, routing, tariffs |
| OD-012 | Нужен ли в будущем VK или другие каналы, помимо Telegram/MAX. | Notifications, adapters |
| OD-013 | Сроки хранения истории, логов и персональных данных. | Data model, privacy, operations |
| OD-014 | Состав будущих экранов публичного сайта и глубина аналитики клиента. | Web Cabinet, analytics |

## Governance capture update — 2026-07-08 — OD-001–OD-005

`ADR-0009` captures owner decisions for `03-entitlements-and-billing` and closes `OD-001`, `OD-002`, `OD-003`, `OD-004` and `OD-005` for the first-stage Free/Basic billing policy.

The historical rows above are preserved for append-only traceability. For current planning after `ADR-0009`, the active unresolved decisions from this file are:

| ID | Status after ADR-0009 | Notes |
|---|---|---|
| OD-001 | CLOSED_BY_ADR_0009 | Basic `990 ₽` is for one month. |
| OD-002 | CLOSED_BY_ADR_0009 | Current stage has Free and Basic only; future tariffs must be admin-configurable but are not predeclared now. |
| OD-003 | CLOSED_BY_ADR_0009 | Basic interval starts at 5 minutes with 5-minute step; Free interval starts at 3 hours with 3-hour step and one Beacon limit. |
| OD-004 | CLOSED_BY_ADR_0009 | Expired paid access freezes all Beacons; user chooses and fixes one Free-compliant Beacon manually. |
| OD-005 | CLOSED_BY_ADR_0009 | YooKassa, Telegram Stars and Tinkoff are provider candidates; first stage is manual renewal/manual refunds only, no recurring, no trial/grace/proration, RUB and Telegram Stars. |
| OD-006 | OPEN | Not changed by ADR-0009. |
| OD-007 | OPEN | Not changed by ADR-0009. |
| OD-008 | OPEN | Not changed by ADR-0009. |
| OD-009 | OPEN | Not changed by ADR-0009. |
| OD-010 | OPEN | Country-wide availability remains unresolved. |
| OD-011 | OPEN | Minimum monitoring frequency safety remains unresolved. |
| OD-012 | OPEN | Not changed by ADR-0009. |
| OD-013 | OPEN | Billing, audit and personal-data retention remains unresolved. |
| OD-014 | OPEN | Not changed by ADR-0009. |

---

## Governance capture update — 2026-07-08 — EB-03 precedence gate

`ADR-0010` captures the approved Entitlements & Billing precedence policy needed before EB-03 `Effective entitlement evaluation semantics`.

This update does not close `OD-010`, `OD-011` or `OD-013`.

For current planning after `ADR-0010`:

| Item | Status after ADR-0010 | Notes |
|---|---|---|
| EB-03 precedence blocker | CLOSED_BY_ADR_0010 | EB-03 may proceed only for deterministic semantic evaluator contracts/tests. |
| Payment records/events authority | NON_AUTHORITY_EVIDENCE | Payment records and events never grant access directly. |
| Expired paid access behavior | GOVERNED_BY_ADR_0009_AND_ADR_0010 | Expired paid access yields Free-only/user-choice-required/free-compliance-required semantics without automatic Beacon choice. |
| Manual access precedence | GOVERNED_BY_ADR_0010 | Manual grants have highest precedence only inside explicit account/scope/interval/reason/actor/idempotency/audit boundaries. |
| OD-010 | OPEN | Country-wide availability remains unresolved. |
| OD-011 | OPEN | Minimum monitoring frequency safety remains unresolved. |
| OD-013 | OPEN | Billing, audit and personal-data retention remains unresolved. |

---

## Governance capture update — 2026-07-08 — EB-04 manual access authorization gate

`ADR-0011` captures the approved Entitlements & Billing manual access grant authorization and lifecycle policy needed before EB-04 `Manual access grants`.

This update does not close `OD-010`, `OD-011` or `OD-013`.

For current planning after `ADR-0011`:

| Item | Status after ADR-0011 | Notes |
|---|---|---|
| EB-04 manual access authorization blocker | CLOSED_BY_ADR_0011 | EB-04 may proceed only for deterministic semantic manual access grant contracts/tests. |
| Manual access admin capability | APPROVED_FOR_SEMANTIC_CONTRACTS | `ENTITLEMENTS_MANUAL_ACCESS_ADMIN` is the required server-side capability for create/revoke semantics. |
| Open-ended manual grants | FORBIDDEN_CURRENT_SCOPE | Every manual access grant must include `starts_at` and `ends_at`. |
| Manual access mutation idempotency | GOVERNED_BY_ADR_0011 | Same key + same request replays original outcome; same key + different fingerprint returns `IDEMPOTENCY_MISMATCH`; missing key returns `REJECTED`. |
| Manual access revocation | GOVERNED_BY_ADR_0011 | Revocation requires authorized actor, grant/account target, reason, idempotency key and audit reference; history is not deleted. |
| Admin UI/Web Cabinet runtime | BLOCKED | This decision does not authorize UI/runtime implementation. |
| Database/persistence/migrations | BLOCKED | This decision does not authorize DB-backed manual access state. |
| OD-010 | OPEN | Country-wide availability remains unresolved. |
| OD-011 | OPEN | Minimum monitoring frequency safety remains unresolved. |
| OD-013 | OPEN | Billing, audit and personal-data retention remains unresolved. |

---

## Governance capture update — 2026-07-08 — EB-06 usage counters gate

`ADR-0012` captures the approved Entitlements & Billing usage counters and limit consumption semantic policy needed before EB-06 `Usage counters / limit consumption`.

This update does not close `OD-010`, `OD-011` or `OD-013`.

For current planning after `ADR-0012`:

| Item | Status after ADR-0012 | Notes |
|---|---|---|
| EB-06 usage counter semantics blocker | CLOSED_BY_ADR_0012 | EB-06 may proceed only for deterministic semantic usage-consumption contracts/tests. |
| Approved EB-06 counter families | APPROVED_FOR_SEMANTIC_CONTRACTS | `ACTIVE_BEACON_SLOT` and `SCAN_INTERVAL_WINDOW` only. |
| Scan-count quotas | BLOCKED | Not approved in current EB-06 scope. |
| Notification-count quotas | BLOCKED | Not approved in current EB-06 scope. |
| Payment-related consumption | BLOCKED | Payment/provider evidence must not become usage consumption authority. |
| Active Beacon source facts owner | BEACON_MANAGEMENT | Entitlements may receive only synthetic snapshot/evidence and must not mutate Beacon state. |
| Scan interval source facts owner | SCAN_ORCHESTRATION | Entitlements may receive only synthetic timing evidence and must not schedule or mutate scans. |
| Usage-consumption idempotency | GOVERNED_BY_ADR_0012 | Same key + same request replays/original terminal outcome; same key + different fingerprint returns `IDEMPOTENCY_MISMATCH`; missing key returns `REJECTED`. |
| Usage-consumption commit point | SEMANTIC_ONLY | No persistent commit is implemented in EB-06. Unknown commit state returns `UNAVAILABLE` or `BLOCKED`. |
| Reset/window policy | LIMITED_BY_ADR_0012 | `ACTIVE_BEACON_SLOT` has no reset window; `SCAN_INTERVAL_WINDOW` uses supplied timing evidence; daily/monthly quotas and rolling counters remain blocked. |
| Beacon Management integration | BLOCKED | Requires accepted Beacon Management contract gate. |
| Scan Orchestration integration | BLOCKED | Requires accepted Scan Orchestration contract gate. |
| Notification Delivery integration | BLOCKED | Notification counters remain blocked. |
| Database/persistence/migrations | BLOCKED | This decision does not authorize DB-backed usage counters. |
| OD-010 | OPEN | Country-wide availability remains unresolved. |
| OD-011 | OPEN | Minimum monitoring frequency safety remains unresolved. |
| OD-013 | OPEN | Billing, audit and personal-data retention remains unresolved. |
