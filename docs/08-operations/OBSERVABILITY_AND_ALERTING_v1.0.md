# Маяк Авито — Observability and Alerting

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Environment Matrix v1.0, Environment Isolation Policy v1.0, Architecture Baseline v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Migration and Compatibility Policy v1.0, Test Strategy v1.0, Acceptance Matrix v1.0, OPEN_DECISIONS.md.
**Не является:** monitoring-stack selection, dashboard configuration, alert-rule file, pager/on-call process, SLO commitment, incident runbook, runtime configuration или разрешением запускать services.

---

## 1. Назначение

Документ определяет общую семантику operational signals, health/readiness, alert states, redaction and acceptance evidence для будущих environments and modules.

Его цель — не допустить ложную наблюдаемость, при которой running process, HTTP response, empty parser result или отсутствие alert ошибочно считаются доказательством корректной работы.

## 2. Source-of-truth and evidence order

1. Approved public GitHub documentation and exact revision.
2. Approved contracts, data ownership and module playbook.
3. Approved environment record and task packet.
4. Authoritative operational/business evidence produced within allowed scope.
5. Derived metrics, logs, traces, dashboards and alerts.

Derived signal cannot override authoritative state. Dashboard, metric, process list, listener or alert status alone does not prove business success.

## 3. Observability principles

1. Every signal has an owner, environment, source revision and semantic meaning.
2. Liveness, readiness, dependency health and business outcome are distinct.
3. Failure, partial, ambiguous and unsupported states remain visible.
4. External/provider failure never becomes clean empty business result.
5. Unknown effect after possible commit requires reconciliation evidence.
6. Account/Beacon isolation is preserved in signal scope.
7. Secrets and unnecessary personal data are excluded by design.
8. Logs, metrics and traces are not authorization mechanisms.
9. Alert absence is not proof of health.
10. Thresholds and channels require separate approved operational decisions.
11. Foreign shared-host signals and resources are not project observability.
12. Time-sensitive evidence includes timestamp provenance and clock uncertainty when material.

## 4. Signal classes

| Signal class | Purpose | Authoritative limit |
|---|---|---|
| Event | Immutable approved fact after defined commit point | Must not be emitted as confirmed success before commit |
| Audit record | Protected evidence of actor/action/authorization/outcome | Must not contain raw secrets or unnecessary personal content |
| Structured log | Diagnostic/operational statement | Cannot become authoritative business state |
| Metric | Aggregated numeric or categorical observation | Must retain defined source/scope; no hidden semantic change |
| Trace/correlation evidence | Links calls/actions across boundaries | Must not expose credentials or provider private payloads |
| Health signal | Liveness/readiness/dependency status | Does not prove business outcome |
| Alert | Derived notification that an approved condition requires attention | Does not fix state or authorize mutation |
| Reconciliation record | Evidence resolving an ambiguous effect | Required before retry/acceptance where commit is unknown |
| Reference-regression signal | Evidence that external official/primary behavior may have changed | Blocks affected acceptance until reviewed |

Exact implementation technologies are not selected.

## 5. Mandatory signal metadata

A future operational signal must contain or inherit:

| Field | Meaning |
|---|---|
| `signal_name` | Stable semantic name |
| `signal_version` | Explicit semantic version |
| `signal_class` | Class from section 4 |
| `environment_id` | Approved logical environment identity |
| `source_revision` | Exact Git/release/contract identity when applicable |
| `producer` | Logical module, adapter or operations boundary |
| `owner` | Team/module responsible for semantic meaning |
| `observed_at` | Observation time under approved time policy |
| `correlation_id` | Cross-operation reference when applicable |
| `causation_id` | Prior action/signal when applicable |
| `account_scope` | Safe account reference only when necessary |
| `beacon_scope` | Safe Beacon reference only when necessary |
| `outcome_class` | Success/rejection/failure/partial/ambiguous/unsupported as applicable |
| `reason_code` | Stable safe code |
| `privacy_class` | Public, internal, personal-minimized, operational-sensitive or secret-prohibited |
| `evidence_source` | Authoritative record, dependency result or derived computation |
| `freshness` | Current/stale/unknown semantics when material |

Exact wire fields and storage format are not selected.

## 6. Health semantics

### 6.1. Liveness

Liveness answers only whether a component/process can respond within its defined technical boundary.

Liveness does not prove:

- configuration correctness;
- dependency availability;
- authorization correctness;
- current reference compatibility;
- successful scan, notification or payment outcome;
- data integrity;
- production readiness.

### 6.2. Readiness

Readiness means the component may accept its approved work only when all required dependencies and configuration gates for that work are satisfied.

Readiness must fail or degrade explicitly when:

- environment or revision identity is wrong/unknown;
- required project-owned dependency is unavailable;
- secret/configuration is absent without disclosure;
- compatibility/reference gate is stale or blocked;
- required migration/reconciliation is incomplete;
- ownership/isolation cannot be proven.

### 6.3. Dependency health

Dependency health reports the dependency’s observed state, not the business result.

At minimum it distinguishes:

- available and usable;
- available but rejecting;
- unavailable;
- malformed/incompatible;
- rate/restriction condition;
- ambiguous effect;
- unsupported or evidence-stale.

### 6.4. Business outcome

Business outcome is determined only by the owning module and approved contract after the defined commit point.

Examples of prohibited inference:

- parser request failed → “no listings”;
- notification provider timeout → “not delivered” or “delivered” without reconciliation;
- process alive → scan succeeded;
- database reachable → data valid;
- alert absent → service healthy.

## 7. Required observability domains

Future module playbooks and operations tasks assess applicable domains:

| Domain | Minimum observable semantics |
|---|---|
| Environment/revision | environment ID, class, source revision, readiness state |
| Contract processing | contract/version, accepted/rejected/error/ambiguous outcome |
| Authorization | safe actor category, decision and reason without credentials |
| Ownership/isolation | account/Beacon scope mismatch without foreign data disclosure |
| Idempotency | first execution, exact replay, mismatch, pending/reconciliation |
| External dependency | success, rejection, unavailable, malformed, ambiguous, unsupported |
| Scan/parser | run identity, completeness, restriction/warning, no false empty result |
| Notification | event identity, attempt state, provider outcome, reconciliation |
| Egress | route/agent safe identity, lease/health state, quarantine/restriction |
| Data/migration | plan/revision, unit counts, failed/ambiguous inventory, validation state |
| Security/privacy | denied action, redaction violation, verification failure |
| Reference evidence | current/stale/missing/changed/disputed status |
| Backup/recovery | future backup identity, verification and recovery result after Run 7 |
| Release/rollback | future release identity and rollback readiness after Run 7 |

## 8. Logs and diagnostic evidence

Structured logs should use stable reason/outcome codes and safe references.

Logs must not contain:

- raw passwords;
- access/refresh tokens;
- one-time codes;
- private keys;
- cookies or session secrets;
- complete secret-bearing configuration;
- unnecessary full phone/email/private message content;
- unredacted provider payloads outside approved evidence scope;
- foreign application data or infrastructure internals;
- shell history or process arguments containing secrets.

External strings are treated as data and never passed to shell through interpolation.

Debug verbosity cannot bypass privacy, ownership or environment boundaries.

## 9. Metrics semantics

Every metric requires:

- semantic name and version;
- unit/type;
- producer and owner;
- environment and revision scope;
- aggregation/window meaning;
- labels/dimensions with cardinality/privacy review;
- expected zero/absence meaning;
- stale/missing-data behavior;
- alert dependency if any;
- change-control classification.

A zero value must distinguish, where applicable:

- true zero business events;
- no data collected;
- collection failure;
- dependency unavailable;
- unsupported scenario;
- filtered/unauthorized scope.

High-cardinality or personal identifiers must not become unrestricted metric labels.

## 10. Correlation and tracing

Correlation evidence must preserve:

- approved `correlation_id` and `causation_id` semantics;
- module/adapter transitions;
- contract and version boundaries;
- explicit external request/outcome states;
- commit point and reconciliation state when relevant;
- environment and source revision.

Trace completeness is not assumed. Missing span/evidence produces explicit incomplete/unknown state, not success.

Raw provider request/response bodies and secrets are excluded unless a separately approved evidence policy permits a minimized/redacted capture.

## 11. Audit boundary

Audit is required for protected state changes identified by Security and Privacy Model and module playbooks.

Audit records preserve:

- verified actor reference/category;
- authorized action and target scope;
- contract/version;
- before/after semantic state or safe references;
- outcome and reason;
- correlation and time;
- environment/revision;
- reconciliation/rollback reference when applicable.

Audit does not grant permission to perform the action and does not replace owning-module state.

Retention and physical audit storage remain unresolved until separate approval.

## 12. Alert condition classes

An alert condition may be defined only from an approved signal and explicit meaning.

| Class | Example semantic concern | Required response state |
|---|---|---|
| Security/authorization | Repeated verification failure, forbidden access, secret exposure indication | Stop affected path, preserve safe evidence, security review |
| Data integrity/isolation | Cross-account/Beacon scope anomaly, incompatible state | Stop mutation/acceptance, reconcile authoritative state |
| Availability/readiness | Approved component not ready or dependency unavailable | Degraded/blocked state; no false success |
| External dependency | Provider rejection, restriction, malformed or ambiguous outcome | Explicit provider/dependency state; reconcile if effect unknown |
| Delivery | Notification attempt failed/ambiguous/duplicated | Per-attempt state and idempotent reconciliation |
| Migration/compatibility | Wrong revision, plan mismatch, partial/ambiguous unit | Stop and follow migration policy |
| Reference regression | Official/primary evidence stale/changed/disputed | Block affected behavior and review references |
| Capacity/resource | Future project-owned resource approaching approved boundary | No threshold until separately approved |
| Evidence pipeline | Missing/stale/incomplete signals | Mark observability gap; do not infer health |

No current alert rules, thresholds or destinations are created by this document.

## 13. Severity semantics

Conceptual severity classes:

| Severity | Meaning |
|---|---|
| `INFO` | Evidence for awareness; no known degradation |
| `WARNING` | Degraded/at-risk state; bounded impact or evidence gap |
| `ERROR` | Approved function failed or is blocked; action/reconciliation required |
| `CRITICAL` | Confirmed or strongly evidenced security, isolation, data-integrity or widespread availability risk requiring immediate owner attention |

Severity is based on impact and evidence, not log wording. Exact paging, response-time targets and escalation channels remain open.

## 14. Alert lifecycle

Conceptual states:

| State | Meaning |
|---|---|
| `DETECTED` | Condition observed with source evidence |
| `OPEN` | Condition validated as requiring attention |
| `ACKNOWLEDGED` | Authorized owner accepted responsibility |
| `INVESTIGATING` | Evidence collection/reconciliation in progress |
| `MITIGATED` | Immediate impact bounded; root cause may remain |
| `RESOLVED` | Acceptance criteria prove condition no longer active |
| `FALSE_POSITIVE` | Trigger did not represent the stated condition; rule/evidence review required |
| `SUPPRESSED` | Explicit approved bounded suppression with owner/reason/expiry |

Automatic resolution based only on missing data is prohibited. Suppression must not hide security, isolation or unknown-effect conditions without approved reasoning.

## 15. Deduplication and alert idempotency

Alert processing must define:

- stable condition identity;
- environment and scope;
- first/open/updated/resolved event semantics;
- duplicate handling;
- changed-condition fingerprint;
- suppression expiry;
- reconciliation after uncertain delivery;
- no repeated external paging effect without idempotency control.

Exact storage and notification channel are not selected.

## 16. Evidence package for future observability checks

A future observability task/report must include:

1. exact environment and revision;
2. signal/alert semantic version;
3. allowed scope and data sources;
4. expected and actual outcome;
5. safe sample or aggregate evidence;
6. missing/stale/ambiguous inventory;
7. redaction/privacy check;
8. ownership/isolation check;
9. effect on readiness/business acceptance;
10. GitHub/repository/server mutation statement;
11. exact final marker and independent acceptance when required.

A screenshot alone, dashboard color, single log line or “all green” summary is insufficient.

## 17. Quality and fixture requirements

Before implementing signals or alerts, the owning playbook/task must cover:

- valid signal and expected state;
- missing signal;
- stale signal;
- malformed signal;
- duplicate signal/alert;
- wrong environment/revision;
- unauthorized/foreign scope;
- secret/personal-data redaction;
- dependency unavailable/rejected/ambiguous;
- false-success prevention;
- alert open/update/resolve lifecycle;
- suppression expiry;
- reconciliation after uncertain delivery.

Executable fixtures/tests are not created by this Run 6 document.

## 18. Change control

Changing signal meaning, labels, severity, alert condition, health/readiness semantics or redaction is a controlled contract/operations change.

Change packet includes:

- old/new semantic definition;
- reason and evidence;
- affected modules/environments;
- compatibility and dashboard/alert impact;
- privacy/cardinality impact;
- fixture and Acceptance Matrix updates;
- rollout/rollback or explicit blocked state;
- open decisions touched but not closed;
- independent approval.

Renaming a metric/log field while changing meaning under the same version is prohibited.

## 19. Open decisions

This baseline does not choose:

- monitoring/logging/tracing products;
- storage/indexing backend;
- agents/exporters/collectors;
- dashboard system;
- alert engine;
- alert thresholds or evaluation windows;
- SLI/SLO/SLA values;
- on-call team, paging channels or escalation times;
- incident-management tooling;
- time synchronization/format implementation;
- signal retention periods;
- sampling policy;
- cost/capacity budgets;
- provider-specific operational fields;
- production incident or breach workflow.

## 20. Explicit prohibitions

This document does not authorize:

- installing or configuring monitoring software;
- creating dashboards, alert rules or paging integrations;
- opening ports or changing network/ingress;
- creating services, containers, users or credentials;
- reading foreign logs/configuration/process arguments;
- sending production/provider traffic;
- logging secrets or unnecessary personal data;
- creating product-code, CI/CD, migrations, databases or deploy artifacts;
- treating host availability as project ownership;
- declaring production readiness.

## 21. Acceptance criteria

Observability and Alerting baseline is accepted when:

- signal classes and mandatory metadata are defined;
- liveness, readiness, dependency health and business outcome are distinct;
- logs/metrics/traces/audit redaction and ownership boundaries are explicit;
- alert classes, severity semantics and lifecycle are documented without tooling/threshold selection;
- false-success, ambiguity and reconciliation rules align with contracts/data/quality policies;
- environment and reference-regression evidence are integrated;
- no monitoring stack, runtime configuration, alert delivery, credentials or product-code is created;
- open decisions remain open.

## 22. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | First technology-neutral observability/alerting semantic baseline without monitoring stack, thresholds or runtime configuration. |
