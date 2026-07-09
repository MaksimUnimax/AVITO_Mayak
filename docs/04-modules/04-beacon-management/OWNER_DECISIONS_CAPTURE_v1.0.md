# Маяк Авито — Beacon Management Owner Decisions Capture v1.0

**Статус:** APPROVED governance capture for BM-01
**Дата:** 2026-07-09
**Модуль:** `04-beacon-management`
**Основание:** `ADR-0016 — 2026-07-09 — Beacon Management owner decisions for BM-01` in `docs/00-governance/DECISION_LOG_APPEND_ONLY.md`.

## 1. Назначение

This document captures owner-provided Beacon Management decisions before they are used by Beacon Management contracts, fixtures, tests, implementation or runtime behavior.

This document is not product-code, parser implementation, Filter Catalog implementation, Scan Orchestration implementation, scheduler runtime, notification flow, UI, database schema, migration, retention job, deploy or runtime configuration.

## 2. Decisions captured

The following decision areas are captured for Beacon Management governance use:

- `OD-003` / `OD-011`: monitoring interval rules for Beacon activation semantics;
- `OD-004`: Beacon consequences after paid access expiry;
- `OD-009`: supported editable filters boundary;
- `OD-010`: country-wide / all-Russia availability;
- `OD-013`: archive, delete, history and permanent delete;
- duplicate source URL policy;
- Beacon naming policy;
- current configuration and revision/storage policy;
- patch-based save and last-write-wins behavior;
- override and effective configuration behavior;
- parser snapshot acceptance safety boundary;
- entitlement re-check boundary;
- Basic active Beacon limit.

## 3. Relation to Entitlements & Billing

Entitlements & Billing is the tariff/access authority.

Beacon Management may consume effective entitlement decisions and semantic outcomes, but it must not duplicate tariff authority as runtime source.

`ADR-0009` captures billing policy. This document captures Beacon Management-specific consequences and boundaries.

## 4. Interval policy

### Free

- active Beacon limit: 1;
- minimum interval: 3 hours;
- allowed step: 3 hours;
- examples: 3, 6, 9, 12 hours and further by 3-hour increments;
- no configured upper limit at this decision level;
- country-wide activation is not allowed.

### Paid / Basic

- active Beacon limit: 5;
- minimum interval: 5 minutes;
- allowed step: 5 minutes;
- examples: 5, 10, 15, 20 minutes and further by 5-minute increments;
- no configured upper limit at this decision level;
- country-wide activation is allowed.

Exact UI mechanics for interval selection remain deferred to future interface decisions.

## 5. Access expiry policy

When paid access ends:

1. Only Free access remains.
2. All active paid Beacons freeze.
3. The user receives a future notification through a future notification/channel module.
4. The user chooses one Beacon that may continue under Free.
5. The chosen Beacon must satisfy Free geography, interval and active-count constraints.
6. The user explicitly starts or resumes the selected Free Beacon.
7. Without user choice and Free compliance, no Beacon is activated automatically.

Beacon Management must not automatically choose the remaining Beacon.

## 6. Supported editable filters policy

Beacon Management does not invent supported editable filters.

A filter/parameter is editable only when it is safely parsed from Avito source URL evidence and accepted as supported by Parser Adapter / Filter Catalog evidence.

Unsupported, uncertain or ambiguous parameters must not be silently changed.

This document does not implement Parser Adapter, Filter Catalog, live Avito validation or UI forms.

## 7. Country-wide policy

Country-wide all-Russia search is allowed for Paid / Basic.

Free cannot activate a country-wide Beacon. If a Free user submits a country-wide source, the system must explicitly indicate that Free does not allow country-wide activation and require city selection. Without city selection, the Free Beacon is not activated.

## 8. History, archive and delete policy

A user may delete a Beacon from the active list.

Ordinary deletion moves the Beacon into user-visible History / Archive, not necessarily immediate physical deletion.

History may include:
- frozen Beacons after paid access expiry;
- user-deleted Beacons removed from the active list;
- archived Beacons.

A user may restore/activate a Beacon from History without re-entering the source URL if current entitlement, current policy and validation allow.

A user may permanently delete a Beacon from History. Permanently deleted Beacons cannot be restored.

Deleted, archived and History Beacons do not count toward active Beacon limits.

This policy is semantic only until persistence, retention and privacy gates are opened.

## 9. Duplicate source URL policy

One account may create multiple Beacons with the same Avito source URL.

Different accounts may also create Beacons with the same Avito source URL.

Source URL is not a unique key. Idempotency must not be based only on source URL.

## 10. Beacon naming policy

A user may provide a Beacon name.

If a user does not provide a name, a default name may be created from recognized title/context. Exact default naming algorithm remains deferred.

Beacon name is presentation metadata. Rename does not change search configuration.

## 11. Current configuration and storage policy

The user-facing target is one current working configuration per Beacon.

When settings change, the new active configuration becomes current.

Old user-facing revision settings must not be stored forever as unbounded clutter.

Already committed scan/audit/history evidence may retain minimal immutable configuration evidence, snapshot or reference only when required to prove the settings used by that committed scan/audit purpose.

Exact physical retention/compaction policy must be decided before persistence, migration or runtime.

This decision clarifies owner intent and must be reconciled with the older immutable revision boundary before any persistence, migration, scan handoff or runtime implementation.

## 12. Save and concurrency policy

Saving Beacon settings is patch-based.

On save, the system reads current authoritative Beacon state and applies only fields present in the current save command.

Different-field concurrent edits may be combined.

Same-field concurrent edits use last-write-wins: the later successful save becomes authoritative.

A stale full-form overwrite is forbidden.

After save, the user sees actual current state reloaded from authoritative storage.

Conflict/blocked outcomes remain allowed when the command cannot be safely applied, including unauthorized actor/account, permanently deleted Beacon, unsupported field, invalid source/snapshot, entitlement denial, missing required confirmation or missing target state.

## 13. Override policy

Effective configuration equals accepted extracted snapshot plus explicit user overrides.

Override wins only for explicitly changed supported fields.

Unsupported or uncertain parameters are not changed silently.

Multivalue approved values must not be silently collapsed.

Exact add/remove/replace UX for multivalue parameters remains deferred.

## 14. Parser snapshot safety boundary

Malformed, incomplete, CAPTCHA-affected, blocked, route-failed or ambiguous parser outcome must not become a clean accepted snapshot.

Exact acceptance thresholds remain future Parser/Filter evidence and test scope.

## 15. Entitlement re-check boundary

Before activation or resume, entitlement is re-checked.

Ambiguous, denied or expired entitlement blocks activation/resume.

Free violations for geography, interval or active count block activation/resume.

Expired paid access enters frozen/history/user-choice flow and does not auto-select a Beacon.

## 16. Explicit non-authorization

This document does not authorize:

- product-code;
- parser implementation;
- live Avito calls;
- source URL live validation;
- Filter Catalog implementation;
- Scan Orchestration runtime;
- scheduler runtime;
- notification sending;
- Telegram/MAX/Web Cabinet UI;
- Admin UI;
- database schema;
- migrations;
- physical delete implementation;
- retention job;
- runtime service;
- Docker/CI/CD/deploy;
- ports/listeners;
- credentials/secrets.

## 17. Next allowed use

After this capture is accepted, later Beacon Management tasks may reference these decisions only within their own exact allowed scope and gates, starting with semantic contracts and synthetic fixtures. Runtime, persistence, Parser, Scan, Filter Catalog, UI and Operations remain separately gated.
