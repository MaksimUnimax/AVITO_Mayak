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

## Governance capture update — 2026-07-08 — EB-11 admin tariff-management semantic gate

`ADR-0015` captures the EB-11 Admin tariff-management semantic gate.

Exact semantic contracts/tests for EB-11 are now allowed.

This update does not open Admin UI, Web Cabinet UI/runtime, Identity role runtime, exact role taxonomy, role changing implementation, persistence, migrations, billing runtime, provider/payment runtime, direct Admin/Web writes to Entitlements state or direct table writes.

Future tariff values/defaults remain blocked unless separately approved.

Audit retention/storage remains blocked by `OD-013`.

For current planning after `ADR-0015`:

| Item | Status after ADR-0015 | Notes |
|---|---|---|
| EB-11 admin tariff-management semantic gate | CLOSED_BY_ADR_0015 | EB-11 may proceed only for deterministic semantic Admin tariff-management boundary contracts/tests. |
| Admin UI | BLOCKED | Not authorized by ADR-0015. |
| Web Cabinet UI/runtime | BLOCKED | Not authorized by ADR-0015. |
| Identity role runtime and exact role taxonomy | BLOCKED | Not authorized by ADR-0015. |
| Role changing implementation | BLOCKED | Not authorized by ADR-0015. |
| Persistence/migrations | BLOCKED | Not authorized by ADR-0015. |
| Billing runtime | BLOCKED | Not authorized by ADR-0015. |
| Provider/payment runtime | BLOCKED | Not authorized by ADR-0015. |
| Direct Admin/Web writes to Entitlements state | BLOCKED | Not authorized by ADR-0015. |
| Direct table writes | BLOCKED | Not authorized by ADR-0015. |
| Future tariff values/defaults | BLOCKED | Not authorized by ADR-0015 unless separately approved. |
| Audit retention/storage | BLOCKED | Remains blocked by `OD-013`. |
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

---

## Governance capture update — 2026-07-08 — EB-08 official provider evidence capture

`ADR-0013` captures official provider evidence for EB-08 planning/reference only.

This update closes the official evidence blocker for provider-reference planning only. It does not open runtime provider adapter, provider SDK/API/webhooks, payment account setup, invoice/receipt/tax implementation, refunds automation, recurring billing, payment reconciliation/refunds for EB-09, persistence/migrations, Admin UI, Web Cabinet runtime or secrets/tokens.

For current planning after `ADR-0013`:

| Item | Status after ADR-0013 | Notes |
|---|---|---|
| Official provider evidence blocker | CLOSED_BY_ADR_0013 | EB-08 planning/reference may use the captured official provider references. |
| Runtime provider adapter | BLOCKED | Still requires a separate exact provider-specific task. |
| Provider SDK/API/webhooks | BLOCKED | Not authorized by ADR-0013. |
| Payment account setup | BLOCKED | Not authorized by ADR-0013. |
| Invoice/receipt/tax runtime | BLOCKED | Not authorized by ADR-0013. |
| Refunds automation | BLOCKED | Manual refunds only remain the current policy. |
| Recurring billing | BLOCKED | Recurring billing remains not implemented. |
| Payment reconciliation/refunds for EB-09 | BLOCKED | Remains a later exact task boundary. |
| Persistence/migrations | BLOCKED | Not authorized by ADR-0013. |
| Admin UI/Web Cabinet runtime | BLOCKED | Not authorized by ADR-0013. |
| OD-010 | OPEN | Country-wide availability remains unresolved. |
| OD-011 | OPEN | Minimum monitoring frequency safety remains unresolved. |
| OD-013 | OPEN | Billing, audit and personal-data retention remains unresolved. |
## Governance capture update — 2026-07-08 — EB-09 reconciliation/refunds gate

`ADR-0014` captures the EB-09 reconciliation/refund semantic gate.

Exact semantic contracts/tests for EB-09 are now allowed.

This update does not open runtime reconciliation, provider refund API calls, automatic refunds, recurring billing, chargeback automation, webhook processing, persistence, migrations, Admin UI, Web Cabinet runtime, provider-derived entitlement grant or raw provider payload as entitlement authority.

For current planning after `ADR-0014`:

| Item | Status after ADR-0014 | Notes |
|---|---|---|
| EB-09 reconciliation/refund semantic gate | CLOSED_BY_ADR_0014 | EB-09 may proceed only for deterministic semantic reconciliation/refunds contracts/tests. |
| Runtime reconciliation | BLOCKED | Not authorized by ADR-0014. |
| Provider refund API calls | BLOCKED | Not authorized by ADR-0014. |
| Automatic refunds | BLOCKED | Not authorized by ADR-0014. |
| Recurring billing | BLOCKED | Not authorized by ADR-0014. |
| Chargeback automation | BLOCKED | Not authorized by ADR-0014. |
| Webhook processing | BLOCKED | Not authorized by ADR-0014. |
| Persistence/migrations | BLOCKED | Not authorized by ADR-0014. |
| Admin UI/Web Cabinet runtime | BLOCKED | Not authorized by ADR-0014. |
| Provider-derived entitlement grant | BLOCKED | Not authorized by ADR-0014. |
| Raw provider payload as entitlement authority | BLOCKED | Not authorized by ADR-0014. |
| OD-010 | OPEN | Country-wide availability remains unresolved. |
| OD-011 | OPEN | Minimum monitoring frequency safety remains unresolved. |
| OD-013 | OPEN | Billing, audit and personal-data retention remains unresolved. |

## Beacon Management captured decisions

The following open-decision areas have owner decisions captured for Beacon Management governance use by `ADR-0016 — 2026-07-09 — Beacon Management owner decisions for BM-01`:

- `OD-003` / `OD-011`: Free and Basic interval rules are captured for Beacon Management semantic use; scheduler/runtime implementation remains gated.
- `OD-004`: paid-access expiry consequences for Beacons are captured for Beacon Management semantic use; notifications, runtime downgrade and automatic activation remain gated.
- `OD-009`: supported editable filters are bounded by Parser Adapter / Filter Catalog evidence; Parser/Filter implementation and exact UI remain gated.
- `OD-010`: country-wide policy is captured for Free and Basic activation semantics; Parser/runtime/UI remain gated.
- `OD-013`: History / Archive / delete / permanent delete semantics are captured for Beacon Management semantic use; physical deletion, retention jobs, privacy/legal retention and DB implementation remain gated.

These captured decisions are not product-code authorization and do not implement runtime behavior. Other open decisions remain unresolved unless separately captured by append-only decision record.
## Governance capture update — 2026-07-09 — APA-01 parser owner decisions

`ADR-0017` captures owner decisions for `05-avito-parser-adapter` before Parser Adapter contracts, synthetic fixtures, tests or later implementation may use listing-card field-family policy, raw-retention policy, newest-sort handoff or lost-anchor handoff semantics.

This update does not authorize live Avito calls, endpoint probing, source URL live validation, HTML/JSON parser runtime, provider clients, cookies/sessions/proxy/CAPTCHA tooling, browser automation, real Avito fixtures, raw provider payload retention, listing detail enrichment runtime, phone extraction runtime, persistence, migrations, database schema, Scan runtime, Egress runtime, Notification runtime, Filter Catalog implementation, Admin/Web/Telegram/MAX UI, Docker, CI/CD, deploy, runtime services, credentials, secrets or tokens.

For current planning after `ADR-0017`:

| Item | Status after ADR-0017 | Notes |
|---|---|---|
| APA-01 owner Parser decision capture | CLOSED_BY_ADR_0017 | Owner decisions are captured for Parser Adapter governance use. |
| APA-02 semantic request/outcome contracts | ALLOWED_AFTER_EXACT_TASK | Only semantic contracts and synthetic fixture identifiers are allowed. |
| Reference parser authority | OBSERVATION_ONLY | `AVITO-PRIMARY-PARSER-001` is technical evidence only, not product model or official API proof. |
| Live Avito calls | BLOCKED | No provider traffic, endpoint probing or live source URL validation is authorized. |
| Internal endpoint `/web/1/js/items` | OBSERVATION_ONLY | Not stable contract, not official consumer-search API and not production permission. |
| Listing-card field families | EVIDENCE_GATED_OPTIONAL_CANDIDATES | Phone, seller, rating and full description are desired if technically and safely obtainable, but not mandatory globally. |
| Free listing-card convenience | OWNER_POLICY_CAPTURED | Free is not intentionally deprived of convenience fields; monetization is primarily active Beacon count, interval and geography. |
| Phone value extraction | BLOCKED | Requires separate phone-enrichment proof gate and exact task. |
| Listing detail enrichment | BLOCKED | Requires separate evidence gate and exact task. |
| Category-specific characteristics | FILTER_CATALOG_BOUNDARY | Parser may return evidence-bound candidates only; Filter Catalog owns supported/editable definitions. |
| Newest-sort / ordering handoff | SEMANTIC_INPUT_CAPTURED | Parser may later return observed order and sort evidence; Scan owns baseline/newness. |
| Lost-anchor behavior | FUTURE_SCAN_POLICY_INPUT | Top 3 latest fresh listings after lost anchors are not confirmed new; Scan owns recovery. |
| Raw provider payload retention | BLOCKED_BY_DEFAULT | Only safe fingerprints/counts/profile IDs/redacted evidence/synthetic samples are allowed without OD-013/evidence gate. |
| Clean empty result | PROOF_REQUIRED | Empty is clean only under future approved compatibility profile proof. |
| Live pagination | BLOCKED | Only semantic page/batch/partial placeholders are allowed before evidence/access gate. |
| OD-009 | OPEN_WITH_PARSER_INPUT | Supported editable filters remain Filter Catalog / evidence-bound; not closed globally. |
| OD-010 | OPEN_WITH_PARSER_INPUT | Country-wide support remains entitlement/beacon/parser evidence scoped; not closed globally. |
| OD-011 | OPEN_WITH_PARSER_INPUT | Minimum monitoring frequency safety remains open; newest-sort handoff does not close it. |
| OD-013 | OPEN_WITH_PARSER_INPUT | Raw retention and personal-data storage remain open; default raw payload retention is blocked. |
