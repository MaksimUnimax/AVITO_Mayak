# Маяк Авито — Egress Routing Module Playbook

**Версия:** 1.0
**Статус:** APPROVED documentation playbook
**Run:** 18 of 24
**Дата:** 2026-07-07
**Модуль:** `07-egress-routing`
**Основание:** Architecture Baseline v1.1, Technical Baseline v1.0, Platform & Contracts Module Playbook v1.0, Avito Parser Adapter Module Playbook v1.0, Scan Orchestration & Listing State Module Playbook v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Security and Privacy Model v1.0, Environment Isolation Policy v1.0, Windows Egress Agent Runbook v1.0, Acceptance Matrix v1.1, Fixture Registry v1.0, current Avito Reference Foundation and OPEN_DECISIONS.md.
**Не является:** Windows/server agent implementation, tunnel/VPN/proxy selection, installer, service or scheduled-task definition, firewall/DNS/certificate/port configuration, credential format, provider-access permission, physical schema, migration, live request, runtime topology or permission to implement.

---

## 1. Назначение

Egress Routing владеет безопасной серверной семантикой выбора и использования заменяемого outbound transport path для разрешённых внешних adapter requests.

Модуль отвечает на вопросы:

- какой логический agent и route зарегистрированы и в каком scope;
- какие capabilities доказаны и актуальны;
- готов ли route к новому bounded assignment;
- почему route выбран, отклонён, ограничен или помещён в quarantine;
- существует ли bounded `RouteLease` для одного purpose/request scope;
- был ли transport assignment dispatch attempted, received, sent, rejected, unavailable, restricted, malformed or ambiguous;
- когда retry запрещён и требуется reconciliation;
- как Windows Egress Agent остаётся replaceable execution dependency без владения business state.

Модуль не определяет Parser success, Scan success, listing state, notification delivery или provider permission.

## 2. Границы и владение

Egress Routing owns semantic mutation authority for:

- logical `EgressAgent` registration and lifecycle;
- logical `EgressRoute` registration and lifecycle;
- agent-to-route association;
- route capability records and compatibility/evidence references;
- agent/route trust, readiness, health and restriction state;
- `RouteLease` lifecycle;
- server-side route-selection decision evidence;
- bounded transport assignment identity and lifecycle;
- explicit dispatch/send/transport outcomes;
- route/agent quarantine, suspension and retirement;
- transport idempotency and reconciliation records;
- safe operational read models and diagnostics.

It does not own:

- Account, identity, role, session or credentials of customers;
- tariff, subscription, entitlement grant or payment state;
- Beacon source URL, configuration, revision or lifecycle;
- Scan intent, work claim, run, observations, baseline, difference or listing state;
- Avito response parsing, normalization or compatibility-profile interpretation;
- NotificationEvent, outbox, delivery attempt or provider delivery state;
- Telegram/MAX provider behavior;
- supported filter catalog;
- Windows/server/network operating-system configuration;
- primary project database ownership by the agent;
- raw secret material;
- raw provider payload retention while OD-013 remains unresolved.

Only Egress Routing may authorize changes to route/agent/lease/transport authoritative state. Other modules use public contracts and never edit Egress tables, files, services or host configuration directly.

## 3. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance.
2. Approved architecture, contracts, data, security, quality and technical baselines.
3. Environment Isolation Policy and Windows Egress Agent Runbook.
4. Accepted Parser Adapter and Scan Orchestration playbooks.
5. This playbook.
6. Current official/primary provider/reference evidence for destination-specific claims.
7. Future approved environment, agent, route and release records.
8. Exact implementation/execution task and accepted evidence.
9. Runtime evidence for one exact route/agent/request operation.

Observed host applications, open ports, processes, tunnels, VPNs, proxies, certificates, browser profiles or network reachability do not create project ownership or an approved route.

## 4. Confirmed decisions

1. Egress Routing is the sole owner of logical route/agent/lease/readiness/health/quarantine/selection/transport state.
2. `route_id`, `agent_id` and `lease_id` are semantic identifiers, not aliases for hostnames, IP addresses, ports, process IDs or Windows usernames.
3. Windows Egress Agent is a replaceable transport executor, not a business-state owner.
4. Agent registration does not prove connectivity, readiness or provider permission.
5. Heartbeat or connected process does not prove route usability, request success, Parser success or business success.
6. A lease is bounded authorization for one declared purpose and scope; it does not transfer ownership of Beacon, account, entitlement, Scan work, listing state or secrets.
7. `ScanWorkClaim` and `RouteLease` are distinct records and authorities.
8. Route selection is server-side, explainable and auditable. Agent, Parser and Scan do not choose fallback independently.
9. Transport success is not Parser success. Parser success is not a committed Scan comparison. Scan success is not notification delivery.
10. `SENT_SUCCESS_RESPONSE` means only that the transport boundary obtained a response under the recorded assignment; Parser must still validate content.
11. Unknown dispatch/send state is reconcile-first and is never blindly retried.
12. Route/agent unavailable, expired/revoked lease, destination timeout, explicit rejection, restriction/CAPTCHA, malformed response, transport failure or ambiguity never becomes clean Parser success or an empty listing set.
13. Public unauthenticated inbound exposure is prohibited by default.
14. Exact transport/tunnel/VPN/proxy technology, topology, host, port and credential mechanism remain unselected.
15. Agent receives only minimum transport data and no primary database access, scheduler ownership, full Beacon/account records or notification history.
16. External URLs, headers, cookies and payloads remain untrusted data and cannot become commands, scripts or arbitrary filesystem/network targets.
17. Quarantine blocks new affected work and does not delete history.
18. Automatic unquarantine is prohibited unless a later explicit policy proves it.
19. Foreign resources do not become project resources by visibility or convenience.
20. Open decisions and provider capability claims receive no fabricated defaults.

## 5. Open decisions and blockers

Run 18 does not resolve:

- `OD-009` — exact supported first-stage Avito filters where route capability may depend on request scope;
- `OD-010` — country-wide/market support conditions;
- `OD-011` — minimum safe monitoring frequency and routing load boundary;
- `OD-013` — retention/deletion of route, lease, request, outcome, audit and diagnostic evidence;
- exact route classes and supported destinations;
- exact Windows/server/home/provider topology;
- exact tunnel, VPN, proxy, relay or direct-connect technology;
- exact connection direction beyond the approved no-public-inbound default;
- exact authentication, certificate, enrollment and secret-delivery mechanism;
- exact Windows version, account type, service manager, installer/package format or host hardware;
- exact server endpoint, bind address, port, firewall, NAT, DNS, TLS or certificate authority;
- exact route capability schema and destination/method mapping;
- exact cookie/session/request-identity policy;
- exact redirect, DNS resolution and header policy;
- exact route selection priority, scoring, fairness or fallback order;
- exact lease duration, renewal, expiry grace or revocation mechanics;
- exact heartbeat interval, timeout, missed-heartbeat count and readiness window;
- exact health/resource thresholds and alert thresholds;
- exact route capacity, concurrency and queueing policy;
- exact retry count, delay, backoff, rate limits and circuit breaker;
- exact cancellation semantics after dispatch;
- exact reconciliation sources and timeout;
- exact persistence schema, indexes and constraints;
- exact audit/log/metric retention and storage;
- exact update, rollback and retirement procedure;
- exact provider permission and access strategy.

Open means blocked. No implementation, test, fixture, route record or operations task may invent these values.

## 6. Authoritative semantic records

These are logical records, not approved tables, ORM classes, files, services or wire schemas.

| Record | Purpose | Required boundary |
|---|---|---|
| `EgressAgent` | Logical agent identity and lifecycle root | not hostname/IP/user alone |
| `AgentRegistration` | Verified ownership/environment/release/trust record | mandatory fields; no secret value |
| `EgressRoute` | Logical route identity and declared purpose/capability scope | no implicit destination support |
| `RouteCapability` | Evidence-bound allowed transport capability | current evidence and explicit unsupported cases |
| `AgentHeartbeat` | Time-bounded liveness observation | not readiness or success |
| `RouteReadinessState` | Current authoritative eligibility classification | derived from approved evidence |
| `RouteHealthState` | Safe health/degradation state | thresholds remain unselected |
| `RouteRestriction` | Restriction, suspension or quarantine record | blocks affected new work |
| `RouteSelectionDecision` | Explainable selected/rejected/no-route decision | server-side and auditable |
| `RouteLease` | Bounded authorization for one route/request purpose | not business-state ownership |
| `TransportAssignment` | Exact bounded work reference delivered to an agent | minimum data only |
| `TransportAttempt` | One dispatch/send attempt under assignment/lease | explicit outcome and correlation |
| `TransportOutcome` | Sent/not-sent/response/rejection/failure/ambiguity fact | not Parser success |
| `TransportReconciliationRecord` | Evidence resolving unknown dispatch/send/result | no blind retry |
| `EgressReadModel` | Rebuildable route/agent/lease projection | not mutation authority |

## 7. Semantic identifiers and scope

- `agent_id` identifies one approved logical execution identity.
- `route_id` identifies one approved logical route/capability boundary.
- `lease_id` identifies one bounded authorization.
- `transport_assignment_id` identifies one bounded assignment.
- `transport_attempt_id` identifies one attempt under an assignment.
- `environment_id` identifies an approved environment class/record.
- `source_release_id` identifies the exact accepted agent/server release where implementation exists.
- `correlation_id` and `causation_id` connect Parser/Scan/Egress evidence.

Identifiers do not reveal or equal private host/IP/port/credential values. Exact encoding remains future task scope.

## 8. Authorization boundary

Protected Egress operations require server-side authorization before mutation or disclosure.

Actor categories may include:

- internal Parser/Scan service identity for route request/lease use;
- protected operator/admin identity for registration, suspension, quarantine or review;
- agent identity for heartbeat, assignment receipt and transport outcome reports;
- reconciliation worker identity after exact task approval.

Rules:

- client UI cannot select a private route directly;
- agent cannot register/approve itself into production;
- possession of hostname/IP/secret does not prove authority;
- Admin/Support cannot bypass Egress public contracts or edit route state directly;
- unauthorized read does not disclose foreign route/agent existence or private diagnostics;
- safe audit records protected mutations without secrets.

## 9. Agent registration record

Before an agent can become runtime-eligible, an approved record must contain or reference:

- stable `agent_id` and record version;
- exact environment identity/class;
- accountable owner;
- approved host scope without unnecessary private details;
- exact purpose and prohibited uses;
- accepted source release identity when implementation exists;
- declared route capability classes;
- trust/registration state;
- credential reference/class only;
- connectivity direction/exposure boundary;
- dedicated filesystem/runtime/network boundaries after approval;
- privacy/data-minimization boundary;
- observability and safe diagnostic boundary;
- update/rollback/retirement status;
- approval and evidence-freshness references.

Missing mandatory evidence yields `REGISTRATION_BLOCKED`. No default registration is inferred from a running process.

## 10. Agent lifecycle

Conceptual lifecycle classes:

- `PROPOSED` — concept/record only; runtime forbidden;
- `REGISTRATION_BLOCKED` — ownership/trust/environment/release/secret gate absent;
- `REGISTERED` — logical identity accepted; connectivity/use still gated;
- `CONNECTIVITY_PENDING` — approved connection not proven;
- `ONLINE_UNREADY` — reachable/alive but not eligible for approved work;
- `READY` — all current readiness gates for declared capability pass;
- `LEASED` — at least one bounded lease exists;
- `DEGRADED` — limited capability or dependency issue;
- `QUARANTINED` — affected new work prohibited;
- `SUSPENDED` — protected stop; no work;
- `RECONCILIATION_REQUIRED` — state/effect ambiguous;
- `RETIRED` — no new work; revocation/evidence obligations remain.

Exact persisted enum names may be adjusted only by a future compatible contract task.

## 11. Route registration and capability

A route record must state or reference:

- `route_id` and semantic version;
- owning `agent_id` or approved execution class;
- environment and release compatibility;
- intended destination/product scope;
- allowed operation/request classes;
- explicit unsupported classes;
- size/time/resource bounds after approval;
- session/cookie policy state: approved, prohibited or blocked;
- redirect/DNS/header behavior after approval;
- current provider/reference evidence;
- health/readiness/quarantine dependencies;
- privacy/redaction restrictions;
- selection-policy compatibility;
- lifecycle and revocation state.

Capability is never inferred from broad network access, successful ping, browser access, one historical response or a foreign proxy/VPN configuration.

## 12. Readiness and heartbeat

### 12.1. Heartbeat

Heartbeat is a time-bounded observation that an agent can report within its control boundary. It does not prove:

- route capability;
- destination availability;
- credential validity;
- correct release;
- request send;
- response usability;
- Parser success;
- Scan success;
- notification success;
- production readiness.

### 12.2. Readiness gate

Readiness must fail, block or degrade explicitly when:

- agent/environment/release identity is wrong or unknown;
- trust/session/credential reference is expired, revoked or unverified;
- mandatory configuration evidence is missing;
- route capability is unsupported or evidence-stale;
- restriction/quarantine blocks the capability;
- approved capacity/resource boundary is exceeded;
- required reconciliation is incomplete;
- clock/time evidence is unreliable where validity depends on it;
- ownership/isolation cannot be proven;
- public exposure or foreign-resource dependency violates policy.

Exact heartbeat/readiness thresholds remain blocked.

## 13. Route selection boundary

Route selection is a server-side Egress Routing decision. It may consider only approved, safe facts:

- requester/module and purpose class;
- exact environment;
- destination/capability class;
- agent/route registration and release compatibility;
- current readiness/health/restriction state;
- current capability/reference evidence;
- lease/capacity eligibility under approved policy;
- safe authorization/entitlement result references where relevant;
- idempotency and prior ambiguous-effect state;
- explicit manual override approved by protected policy.

Selection result must explain selected, rejected, blocked, no-eligible-route, conflict or ambiguous outcome with safe reason codes.

The playbook does not select priority, scoring, round-robin, geographic routing, fallback order or automatic switching. If multiple routes require an unapproved policy, selection is blocked rather than arbitrary.

## 14. Route lease semantics

A `RouteLease` is bounded authorization, not ownership transfer.

Required semantic fields/references:

- `lease_id` and contract/version;
- one `route_id` and one `agent_id`;
- requester module/identity;
- exact purpose and capability scope;
- exact environment and release compatibility;
- parser/scan request correlation where applicable;
- issuance/validity references under approved time policy;
- lifecycle state;
- idempotency key/fingerprint;
- restriction/quarantine snapshot;
- safe correlation/causation references;
- cancellation/reconciliation state.

A lease must not contain raw customer credentials, provider secrets, full Account/Beacon records or unnecessary personal data.

## 15. Lease lifecycle

Conceptual lifecycle:

- `REQUESTED` — request exists; route use not authorized;
- `REJECTED` — preconditions failed; no effect;
- `GRANTED` — bounded lease committed; dispatch not proven;
- `DISPATCHED` — assignment dispatch attempted;
- `IN_USE` — agent reported bounded processing;
- `COMPLETED` — terminal transport outcome accepted;
- `EXPIRED` — validity ended; new dispatch prohibited;
- `REVOKED` — protected cancellation;
- `AMBIGUOUS` — dispatch/effect unknown;
- `RECONCILIATION_REQUIRED` — no repeat until resolved;
- `FAILED` — explicit terminal failure.

Lease replay does not extend validity, create a second lease or duplicate transport work unless a future explicit renewal contract authorizes it.

## 16. Transport assignment lifecycle

Required semantic sequence:

```text
request accepted by Parser/internal caller
→ route-selection decision
→ bounded lease granted
→ transport assignment committed
→ dispatch attempted
→ agent receipt confirmed or unknown
→ outbound request not sent | sent | send unknown
→ explicit transport response/rejection/failure/ambiguity
→ Parser classification and normalization
→ Scan/business module acceptance
```

Each transition preserves exact assignment/attempt/lease/correlation identity. No later stage may be inferred from an earlier one.

## 17. Public input families

Exact Python/wire schemas remain future implementation task scope.

| Input family | Purpose |
|---|---|
| `RegisterEgressAgentCommand` | Create/update protected logical registration under exact evidence |
| `RegisterEgressRouteCommand` | Create/update protected route/capability record |
| `RecordAgentHeartbeatCommand` | Record time-bounded liveness evidence |
| `EvaluateRouteReadinessCommand` | Recompute explicit readiness from approved evidence |
| `RequestRouteLeaseCommand` | Request bounded route authorization for one purpose/request |
| `DispatchTransportAssignmentCommand` | Commit and dispatch one bounded assignment under a valid lease |
| `RecordAssignmentReceiptCommand` | Record received/not-received/unknown state |
| `RecordTransportOutcomeCommand` | Record explicit send/response/failure/ambiguity outcome |
| `ReconcileTransportAttemptCommand` | Resolve unknown dispatch/send/result state |
| `QuarantineRouteCommand` | Protected restriction/quarantine operation |
| `ReleaseRouteQuarantineCommand` | Protected reviewed release; never automatic by default |
| `RevokeRouteLeaseCommand` | Protected cancellation/revocation under effect boundary |
| `GetEgressAgentQuery` | Read authorized safe agent projection |
| `GetEgressRouteQuery` | Read authorized safe route/capability projection |
| `ExplainRouteSelectionQuery` | Explain selected/rejected/blocked decision |
| `GetTransportAttemptQuery` | Read safe assignment/attempt/outcome/reconciliation evidence |

Mutation-capable inputs require mandatory common contract metadata, authorization scope, idempotency key and normalized fingerprint.

## 18. Public output families

| Output family | Meaning |
|---|---|
| `AgentRegistrationOutcome` | registered, blocked, conflict, rejected, suspended or retired |
| `RouteRegistrationOutcome` | registered, blocked, unsupported, conflict or rejected |
| `RouteReadinessOutcome` | ready, online-unready, degraded, quarantined, suspended, stale or blocked |
| `RouteSelectionOutcome` | selected, no eligible route, blocked, restricted, conflict or ambiguous |
| `RouteLeaseOutcome` | granted, replayed, rejected, expired, revoked, conflict or ambiguous |
| `TransportDispatchOutcome` | not dispatched, dispatched, receipt confirmed, receipt unknown or blocked |
| `TransportOutcomeResult` | explicit transport outcome class with safe response/evidence reference |
| `TransportReconciliationOutcome` | resolved-not-sent, resolved-sent, resolved-terminal, remains-ambiguous or manual-review-required |
| `EgressReadResult` | authorized safe route/agent/lease/attempt projection |
| `RouteSelectionExplanation` | safe policy/evidence/reason references without secrets |

Outputs remain framework, persistence, operating-system and provider neutral.

## 19. Mandatory transport outcome classes

At minimum:

- `NOT_DISPATCHED`;
- `DISPATCH_AMBIGUOUS`;
- `RECEIVED_NOT_SENT`;
- `SENT_SUCCESS_RESPONSE`;
- `SENT_EXPLICIT_REJECTION`;
- `DESTINATION_UNAVAILABLE`;
- `RATE_OR_ACCESS_RESTRICTED`;
- `MALFORMED_OR_UNUSABLE_RESPONSE`;
- `TRANSPORT_FAILURE`;
- `RESULT_AMBIGUOUS`;
- `CANCELLED_OR_EXPIRED`.

Exact wire codes and HTTP mappings are not selected.

## 20. False-success prohibition

None of the following may become clean Parser success, clean empty listing result or successful Scan outcome:

- agent unavailable;
- route unavailable;
- registration/readiness evidence missing;
- expired/revoked lease;
- dispatch not attempted;
- receipt unknown;
- outbound send unknown;
- destination timeout;
- explicit provider rejection;
- rate/access restriction;
- CAPTCHA/challenge;
- malformed/incomplete response;
- connection interruption;
- stale capability/reference evidence;
- quarantine/restriction;
- reconciliation incomplete.

A transport response with status/bytes is not content validity. Parser owns response classification.

## 21. Parser Adapter dependency and handoff

Parser Adapter requests transport through Egress public contracts and supplies:

- exact parser request/contract/version;
- purpose: source analysis or scan extraction;
- destination/capability class;
- bounded request method/URL/header/body references after approval;
- `account_id`/`beacon_id`/revision correlation only when required and authorized;
- Parser compatibility/reference profile identity;
- idempotency and request fingerprint;
- safe size/time expectations;
- session/cookie policy reference if separately approved.

Egress returns:

- route/agent/lease/assignment/attempt references;
- dispatch/receipt/send state;
- explicit transport outcome;
- safe response reference/metadata under approved retention policy;
- restriction/quarantine and retry/reconciliation state;
- safe reason/evidence references.

Egress does not parse Avito content, declare fields complete, decide genuine empty, accept normalized listings or choose Parser compatibility profile.

## 22. Scan Orchestration dependency

Scan may preserve safe Egress route/lease/attempt/outcome references as run provenance.

Rules:

- Egress does not create or own `ScanRun` or `ScanWorkClaim`;
- Egress does not schedule scans or choose cadence;
- route lease does not mutate Scan state;
- Egress does not establish baseline/difference/listing events;
- ambiguous transport state is reported and must remain explicit in Scan;
- Egress cannot silently retry because Scan work still exists;
- Scan cancellation does not prove external dispatch cancellation without Egress evidence;
- historical route evidence does not rewrite historical Scan state.

## 23. Windows Egress Agent boundary

A future Windows agent may:

- authenticate as one approved agent identity;
- receive one bounded transport assignment;
- execute only an approved operation class;
- report receipt/send/response/failure evidence;
- send heartbeat and safe diagnostics;
- reject unsupported, expired, revoked, invalid or unsafe assignments.

It must not:

- store primary project database;
- own scheduler, durable queue or Scan work;
- create/modify Beacon configuration;
- calculate baseline/diff or listing state;
- parse provider content into business truth unless separately acting through Parser ownership, which is not selected here;
- create notification events or delivery attempts;
- choose tariff/entitlement behavior;
- select fallback route independently;
- accept itself into production;
- read browser passwords, cookies or unrelated profiles;
- reuse personal/foreign VPN/proxy/service credentials;
- expose a public inbound listener by default;
- execute arbitrary command/script payloads;
- write another module’s authoritative state.

## 24. Connectivity and exposure boundary

Approved boundary:

- no new public unauthenticated inbound listener by default;
- peer identity, confidentiality, integrity, replay resistance, revocation and bounded lifetime must be proven before runtime;
- exact environment and release identity must be known;
- allowed message classes and size/time/resource limits must be explicit;
- reconnect/duplicate behavior must preserve idempotency/reconciliation;
- secrets must not appear in command line, logs, source or reports;
- foreign credentials and services cannot be reused.

Unselected:

- VPN, tunnel, proxy, relay, broker, long polling, WebSocket, HTTP/2, QUIC or other technology;
- local/server bind address or port;
- firewall, NAT, DNS or certificate configuration;
- Windows service, scheduled task or session process;
- server endpoint and topology.

## 25. Secret and trust boundary

Agent/route credentials, keys, tokens, certificates or enrollment material:

- are never stored in Git;
- are never included in playbooks, fixtures or ordinary reports;
- are never passed through shell history or process arguments;
- are never copied from foreign applications, browsers, VPNs or proxy tools;
- require protected delivery, rotation, revocation and audit after mechanism approval;
- are scoped to agent/route/environment purpose;
- do not grant primary database, queue, customer-secret or unrelated server access.

Contracts carry safe `credential_reference`/trust state, never raw material.

## 26. Data minimization and assignment payload

An agent receives only data required for the approved transport operation.

Prohibited by default:

- primary database access;
- full Account or Beacon records;
- tariff/payment state;
- Scan listing history;
- notification history;
- unnecessary personal data;
- raw admin/integration credentials;
- unrestricted filesystem paths;
- arbitrary command/script templates;
- foreign-host configuration/application data;
- secrets or unrelated provider/session data.

External URLs, headers, cookies and payloads remain untrusted. Exact safe handling is blocked until provider/reference, Parser and security contracts approve it.

## 27. Provider/reference boundary

- A route capability claim requires current reference evidence for its exact destination/operation scope.
- Network reachability is not provider permission.
- Observed internal Avito endpoints are not stable contracts.
- Stale/missing/disputed evidence blocks capability or produces explicit unsupported state.
- Route success does not prove provider acceptance or content correctness.
- OD-009, OD-010 and OD-011 remain open and cannot be encoded as route defaults.
- Live provider traffic requires a separate exact task and permission gate.

## 28. Idempotency rules

Idempotency is required for:

- agent/route registration mutation;
- route lease request/renewal/revocation;
- transport assignment dispatch;
- outcome recording where duplicate reports are possible;
- quarantine/release operations;
- reconciliation and protected manual override;
- any retryable external transport command.

Required semantics:

- same key + same semantic request + known terminal outcome returns/references original outcome;
- same key + same request + pending/ambiguous outcome returns pending/reconciliation state;
- same key + different fingerprint returns `IDEMPOTENCY_MISMATCH` with no effect;
- missing required key is rejected before effect;
- lease replay does not extend validity or duplicate assignment;
- dispatch replay does not produce a second external request;
- duplicate agent outcome report does not duplicate state transition;
- exact storage/TTL remains open.

## 29. Commit-point rules

### 29.1. Registration commit

Success means authoritative agent/route registration state exists. It does not mean runtime readiness.

### 29.2. Selection/lease commit

Success means one explainable selection decision and bounded lease are committed. It does not mean dispatch or send.

### 29.3. Assignment commit

Success means one bounded assignment exists under a valid lease. It does not mean agent receipt.

### 29.4. Dispatch/send outcome commit

Success means the exact dispatch/send/transport outcome is committed with idempotency/correlation evidence. `SENT_SUCCESS_RESPONSE` remains transport-only.

### 29.5. Reconciliation commit

Success means unknown effect is resolved or explicitly remains ambiguous. No retry is authorized merely because reconciliation was attempted.

No confirmed outcome/event is emitted before its defined commit point.

## 30. Interruption and reconciliation

### Before lease commit

- no route authorization exists;
- replay may evaluate selection under idempotency rules.

### After lease commit, before assignment/dispatch

- lease may remain granted;
- no external request success;
- expiry/revocation is evaluated explicitly.

### Dispatch/receipt/send unknown

- attempt becomes `DISPATCH_AMBIGUOUS` or `RESULT_AMBIGUOUS`;
- preserve correlation, assignment, lease and agent evidence;
- do not create another dispatch blindly;
- reconcile using approved safe evidence.

### Outcome committed, caller response lost

- replay returns original outcome reference;
- no duplicate dispatch or state transition.

### Agent restart/disconnect

- server-owned authoritative state remains;
- heartbeat/readiness degrades under future approved policy;
- ambiguous in-flight assignments require reconciliation.

Exact reconciliation sources/timeouts remain open.

## 31. Batch and partial operations

- Every assignment/attempt has an explicit outcome.
- Batch result exposes succeeded, failed, pending, restricted and ambiguous counts/references.
- One generic success is prohibited when units differ.
- Retry identifies exact units and preserves previous outcomes.
- A successful unit does not erase a restricted/ambiguous unit.
- Partial transport success is not generic Parser or Scan success.
- Exact batch size/concurrency remains unselected.

## 32. Quarantine and restrictions

Evidence that may require quarantine/restriction includes:

- repeated access restriction/provider rejection;
- identity/release/configuration mismatch;
- trust/credential concern;
- unexpected destination/capability behavior;
- malformed/unsafe response pattern;
- missing/stale heartbeat/readiness evidence;
- resource/capacity concern under approved thresholds;
- secret/privacy/redaction violation;
- duplicate/ambiguous dispatch behavior;
- foreign-resource dependency;
- clock/time inconsistency;
- failed update/rollback/reconciliation.

Quarantine rules:

- no new affected leases/assignments;
- in-flight work becomes explicit cancelled, failed or ambiguous according to evidence;
- history is preserved;
- release requires protected review/evidence;
- automatic unquarantine is forbidden by default;
- quarantine does not authorize agent-side fallback.

## 33. Route switching and fallback

Future route-switching policy must define:

- eligible route classes;
- priority/scoring/fairness;
- requester/environment/destination scope;
- failure categories permitting switch;
- categories requiring stop/quarantine;
- retry/reconciliation order;
- session/cookie/request-identity impact;
- provider restriction/rate safety;
- audit and reason codes;
- duplicate-request prevention;
- current evidence for each behavior.

Until that policy exists:

- agent does not switch route independently;
- Parser/Scan do not choose fallback;
- ambiguous dispatch blocks replacement dispatch;
- restriction/CAPTCHA does not trigger blind switching;
- no arbitrary “first available route” default is accepted.

## 34. Cancellation, expiry and revocation

- Lease expiry prohibits new dispatch.
- Revocation is protected and audited.
- Cancellation before dispatch may terminate assignment under approved commit rules.
- Cancellation after dispatch does not prove external request cancellation.
- Unknown effect becomes reconciliation-required.
- Agent must reject clearly expired/revoked assignment where safe evidence is available.
- Exact grace periods, cancellation protocol and compensation remain open.

## 35. Concurrency and capacity

Required properties:

- one logical lease/assignment identity is not duplicated by concurrent callers;
- state transitions use expected version/conflict detection;
- stale heartbeat/readiness update cannot overwrite a newer protected restriction;
- concurrent quarantine/lease actions cannot silently grant work after restriction;
- capacity reservation cannot be inferred from process-local counters alone if authoritative effect matters;
- exact locking, transaction, lease capacity, fairness and concurrency values remain unselected;
- no external broker/cache is introduced by this playbook.

## 36. Error semantics

Applicable common categories:

- `INVALID_ARGUMENT`;
- `UNAUTHENTICATED`;
- `FORBIDDEN`;
- `NOT_FOUND`;
- `PRECONDITION_FAILED`;
- `CONFLICT`;
- `IDEMPOTENCY_MISMATCH`;
- `RATE_LIMITED`;
- `EXTERNAL_UNAVAILABLE`;
- `EXTERNAL_REJECTED`;
- `EXTERNAL_AMBIGUOUS`;
- `TEMPORARY_FAILURE`;
- `INTERNAL_FAILURE`.

Safe error details may include agent/route/lease/assignment/correlation IDs, lifecycle/outcome class, evidence/reference state and retry/reconciliation class. They exclude credentials, raw keys/tokens/cookies, private host/network details, raw provider payload and foreign-account data.

## 37. Security and privacy

- All protected route/agent operations require server-side authorization and audit.
- Credentials/secrets are references only in ordinary contracts.
- External URL/header/body values never become shell commands.
- Agent assignment cannot contain arbitrary script execution.
- Public unauthenticated inbound exposure is prohibited by default.
- Agent/runtime identity uses least privilege after exact design approval.
- No primary database, queue or unrelated server access is granted to agent.
- Logs/reports exclude raw tokens, private keys, certificates, cookies, browser profiles, shell history, process arguments and unnecessary personal data.
- Foreign host/service configuration is not read or reused.
- Security mechanism/product/cryptographic details remain separate approval scope.

## 38. Observability and safe evidence

Future minimum signals:

- safe `agent_id`, `route_id`, `lease_id`, assignment/attempt/correlation references;
- environment and release identity;
- registration/lifecycle/readiness/health/quarantine state;
- heartbeat freshness/provenance;
- declared capability/reference state;
- route-selection outcome/reason;
- dispatch/receipt/send/outcome class;
- succeeded/failed/pending/restricted/ambiguous counts;
- retry/reconciliation state;
- safe latency/resource observations after approved policy;
- secret/redaction and foreign-resource checks.

A green process, connected tunnel, heartbeat or response byte count does not prove route, Parser or business health.

## 39. Audit requirements

Protected audit is required for future:

- agent registration/approval/suspension/retirement;
- route creation/association/change;
- trust/credential issuance/rotation/revocation references;
- capability/readiness policy changes;
- lease policy and protected revocation;
- quarantine/unquarantine;
- protected manual route selection/override;
- release/update/rollback actions;
- security/privacy incidents;
- fallback/priority policy changes.

Audit records safe actor, authorization, reason, before/after semantic state, environment/revision, correlation and outcome. Raw secret/private infrastructure data is excluded.

## 40. Retention, deletion and read models

OD-013 remains unresolved.

Until accepted policy:

- no retention period is invented;
- no automatic deletion/compaction is implemented;
- quarantine/reconciliation history is not erased;
- read models remain rebuildable and carry provenance/freshness;
- read model never authorizes route use by itself;
- raw response/request retention remains prohibited by default unless separately approved;
- deletion/archival requires an exact policy/task and must preserve audit/legal/security obligations.

## 41. Dependencies and technology

Allowed only after exact implementation gates:

- Platform & Contracts semantic primitives;
- Parser Adapter accepted public contracts;
- Scan Orchestration accepted provenance contracts;
- Windows Egress Agent Runbook boundaries;
- PostgreSQL/SQLAlchemy/Psycopg selected-with-gate for authoritative server-side state;
- Alembic only after physical schema/migration approval;
- HTTPX only where the owning execution boundary and Python compatibility proof apply;
- pytest/pytest-asyncio/RESpx and approved fakes for deterministic tests;
- OpenTelemetry after exact instrumentation task.

Deferred/blocked:

- Windows/server agent implementation;
- transport/tunnel/VPN/proxy/relay technology;
- ports/listeners/firewall/DNS/TLS/certificate configuration;
- credentials/enrollment/secret delivery;
- physical tables/indexes/constraints;
- live provider traffic;
- route priority/fallback/threshold/retry/rate policy;
- cookies/sessions;
- services/deploy/runtime;
- external broker/cache.

## 42. Fake dependencies and test doubles

Future approved fakes may model:

- `AgentRegistry`;
- `RouteRegistry`;
- `RouteCapabilityRepository`;
- `RouteReadinessEvaluator`;
- `RouteSelectionPolicy` with explicit test policy version;
- `RouteLeaseRepository`;
- `TransportAssignmentRepository`;
- `AgentTransportGateway`;
- `TransportOutcomeRepository`;
- `TransportReconciliationGateway`;
- `ReferenceEvidenceReader`;
- `CredentialReferenceVerifier` without secret material;
- `Clock`;
- `IdGenerator`;
- `TransactionBoundary`;
- `SafeDiagnosticSink`.

Fakes use synthetic agents, routes, environments, capabilities, assignments, responses and credentials references only. They do not prove real provider access or production network behavior.

## 43. Required fixtures and test vectors

Canonical applicable fixtures:

- `FX-CONTRACT-VALID-001`;
- `FX-CONTRACT-MISSING-META-001`;
- `FX-AUTH-UNAUTHENTICATED-001`;
- `FX-AUTH-FORBIDDEN-001`;
- `FX-IDEMP-FIRST-001`;
- `FX-IDEMP-REPLAY-SAME-001`;
- `FX-IDEMP-REPLAY-MISMATCH-001`;
- `FX-INTERRUPT-PRECOMMIT-001`;
- `FX-INTERRUPT-UNKNOWN-001`;
- `FX-INTERRUPT-POSTCOMMIT-001`;
- `FX-BATCH-PARTIAL-001`;
- `FX-DATA-READMODEL-STALE-001`;
- `FX-DATA-UNKNOWN-NO-DEFAULT-001`;
- `FX-EXT-SUCCESS-001`;
- `FX-EXT-REJECTED-001`;
- `FX-EXT-UNAVAILABLE-001`;
- `FX-EXT-MALFORMED-001`;
- `FX-EXT-AMBIGUOUS-001`;
- `FX-AVITO-CAPTCHA-001`;
- `FX-ROUTE-FAILURE-001`;
- `FX-SEC-SECRET-REDACTION-001`;
- `FX-SEC-SHELL-INTERPOLATION-001`;
- `FX-REF-CURRENT-001`;
- `FX-REF-STALE-001`;
- `FX-REF-MISSING-001`;
- `FX-REF-UNSUPPORTED-001`.

Module-specific future semantic fixtures:

- `FX-ER-AGENT-REGISTRATION-BLOCKED-001`;
- `FX-ER-REGISTERED-NOT-READY-001`;
- `FX-ER-HEARTBEAT-NOT-READINESS-001`;
- `FX-ER-RELEASE-MISMATCH-BLOCKS-001`;
- `FX-ER-CAPABILITY-UNSUPPORTED-001`;
- `FX-ER-CAPABILITY-EVIDENCE-STALE-001`;
- `FX-ER-NO-POLICY-NO-ARBITRARY-SELECTION-001`;
- `FX-ER-LEASE-GRANTED-001`;
- `FX-ER-LEASE-REPLAY-NO-EXTENSION-001`;
- `FX-ER-LEASE-IDEMPOTENCY-MISMATCH-001`;
- `FX-ER-LEASE-EXPIRED-NO-DISPATCH-001`;
- `FX-ER-LEASE-REVOKED-NO-DISPATCH-001`;
- `FX-ER-DISPATCH-NOT-SENT-001`;
- `FX-ER-DISPATCH-AMBIGUOUS-RECONCILE-001`;
- `FX-ER-RECEIVED-NOT-SENT-001`;
- `FX-ER-SENT-RESPONSE-NOT-PARSER-SUCCESS-001`;
- `FX-ER-EXPLICIT-REJECTION-NOT-EMPTY-001`;
- `FX-ER-CAPTCHA-NOT-EMPTY-001`;
- `FX-ER-MALFORMED-NOT-PARSER-SUCCESS-001`;
- `FX-ER-ROUTE-FAILURE-NOT-PARSER-SUCCESS-001`;
- `FX-ER-QUARANTINE-BLOCKS-NEW-LEASE-001`;
- `FX-ER-NO-AUTO-UNQUARANTINE-001`;
- `FX-ER-NO-AGENT-FALLBACK-001`;
- `FX-ER-AMBIGUOUS-NO-FALLBACK-001`;
- `FX-ER-CROSS-ENVIRONMENT-REJECT-001`;
- `FX-ER-FOREIGN-RESOURCE-REJECT-001`;
- `FX-ER-NO-PUBLIC-INBOUND-001`;
- `FX-ER-NO-PRIMARY-DATABASE-001`;
- `FX-ER-MINIMUM-ASSIGNMENT-PAYLOAD-001`;
- `FX-ER-SECRET-REFERENCE-ONLY-001`;
- `FX-ER-BATCH-PER-ASSIGNMENT-OUTCOME-001`;
- `FX-ER-RECONCILIATION-REMAINS-AMBIGUOUS-001`;
- `FX-ER-OD011-NO-CADENCE-DEFAULT-001`;
- `FX-ER-OD013-RETENTION-BLOCKED-001`.

Run 18 creates no fixture files and executes no tests.

## 44. Acceptance Matrix coverage

Run 18 documentation coverage:

- `AM-DOC-001`–`AM-DOC-003`;
- `AM-ARCH-001`–`AM-ARCH-004`;
- `AM-TECH-004`, `AM-TECH-007`–`AM-TECH-009`;
- `AM-CONTRACT-001`–`AM-CONTRACT-003`;
- `AM-IDEMP-001`–`AM-IDEMP-002`;
- `AM-INTERRUPT-001`–`AM-INTERRUPT-002`;
- `AM-BATCH-001`;
- `AM-DATA-006`–`AM-DATA-007`;
- `AM-SEC-001`–`AM-SEC-003`;
- `AM-EXT-001`–`AM-EXT-004`;
- `AM-AVITO-001`;
- `AM-EGRESS-001`;
- `AM-REF-001`–`AM-REF-004`;
- `AM-MIG-008`–`AM-MIG-009` where applicable;
- all Module Playbook Adoption gates from Acceptance Matrix section 9.

Runtime, network, Windows-agent, secret, provider, database and deployment gates remain future and are not passed by this documentation run.

## 45. Allowed future changes

A later exact task may, after all gates:

- create transport-neutral Egress domain contracts and synthetic tests;
- create module package skeleton inside approved layout;
- implement protected agent/route registration semantics;
- implement deterministic selection under an explicitly approved policy;
- implement bounded leases, assignment/outcome state and reconciliation;
- implement server-side authoritative PostgreSQL state after physical schema/migration approval;
- implement a separately buildable Windows Egress Agent after environment, connectivity, trust, secret and release approval;
- integrate Parser public contracts;
- add safe observability, audit and read models;
- prove false-success prohibition, idempotency and ambiguous-effect handling.

## 46. Forbidden changes

Without new accepted decisions/evidence/tasks, this module must not:

- create Windows/server agent code;
- create Windows service, scheduled task, installer or runtime user;
- choose tunnel, VPN, proxy, relay, broker or connectivity technology;
- open/configure port, listener, firewall, NAT, DNS, TLS or certificate;
- create route, lease, credential, key, token or enrollment material;
- reuse foreign VPN/proxy/service/browser credentials;
- read browser profiles, cookies, private keys, `.env`, shell history or process arguments;
- select route priority, fallback, thresholds, lease duration, heartbeat interval, retries, backoff, rate limits or concurrency values;
- infer provider support or permission from reachability;
- send live Avito/provider requests;
- classify transport response as Parser success;
- convert restriction/failure/ambiguity into no listings;
- retry ambiguous dispatch blindly;
- allow agent/Parser/Scan to choose fallback independently;
- give agent primary database, queue, scheduler or business-state ownership;
- collect/retain raw request/response payloads without approved policy;
- create product-code, dependency file, lockfile, executable test, fixture data file, migration, database, Docker/CI/CD, service, container, deploy or runtime configuration.

## 47. Roadmap of module subtasks

| ID | Subtask | State | Gate |
|---|---|---|---|
| `ER-01` | Transport-neutral agent/route/lease/outcome contracts and synthetic fixtures | `NOT_STARTED` | exact implementation task and Platform primitives |
| `ER-02` | Registration, trust and environment/release model | `BLOCKED` | environment, ownership, credential and release decisions |
| `ER-03` | Route capability/readiness/health model | `BLOCKED` | current provider evidence and threshold policy |
| `ER-04` | Server-side selection and fallback policy | `BLOCKED` | priority/fallback/rate/cadence decisions including OD-011 |
| `ER-05` | Lease, assignment and dispatch lifecycle | `NOT_STARTED` | contract task and durable transaction model |
| `ER-06` | Windows Egress Agent implementation/proof | `BLOCKED` | connectivity, secret, OS/runtime and isolated toolchain approval |
| `ER-07` | Parser integration and false-success proof | `NOT_STARTED` | accepted Parser contracts and synthetic transport fixtures |
| `ER-08` | Idempotency, interruption and reconciliation | `NOT_STARTED` | exact task and evidence sources |
| `ER-09` | Quarantine, observability, audit and retention | `BLOCKED` | thresholds, security process and OD-013 |
| `ER-10` | Full acceptance evidence and handoff | `NOT_STARTED` | applicable subtasks complete |

## 48. Task packet requirements

A future task must include:

- exact paths and parent SHA;
- stable task/iteration ID;
- accepted contract/playbook versions;
- exact agent/route/environment/release identities;
- ownership and authorization scope;
- destination/capability/reference evidence;
- route-selection policy version and blocked defaults;
- lease/assignment/attempt/outcome semantics;
- connectivity/exposure/secret boundaries;
- idempotency, commit points, interruption and reconciliation;
- quarantine/restriction/fallback behavior;
- Parser/Scan dependency boundaries;
- privacy/redaction/retention scope;
- physical schema/migration scope if applicable;
- Windows/toolchain/network proof scope if applicable;
- fixtures and Acceptance Matrix rows;
- no-live-provider requirement unless separately authorized;
- evidence/report format and exact final marker.

During the documentation cycle CLI remains server-sync-only and does not edit this playbook or configure any route/agent/network state.

## 49. Report and handoff

A future implementation/proof report must include:

- task/iteration ID and exact commit SHA;
- changed paths and dependency/lock identity;
- agent/route/environment/release records;
- ownership/trust/connectivity/secret evidence;
- capability/reference identity and freshness;
- readiness/health/quarantine evidence;
- selection decision and policy version;
- lease/assignment/attempt/commit-point evidence;
- dispatch/receipt/send/transport outcome evidence;
- explicit proof that transport success is not Parser success;
- route-failure/restriction/CAPTCHA/malformed/ambiguous no-false-success evidence;
- idempotency/interruption/reconciliation evidence;
- no-agent-fallback and no-blind-retry evidence;
- batch/per-assignment outcome evidence;
- isolation/no-primary-database/no-foreign-resource evidence;
- no-public-inbound and secret-redaction evidence;
- fixtures, Acceptance Matrix rows and exact results;
- database/migration/runtime statement;
- live provider traffic statement (`NONE` unless separately authorized);
- prohibited-artifact check;
- blockers and next safe task;
- exact final marker for independent review.

## 50. Acceptance criteria

The playbook is acceptable only when:

- Egress ownership and non-ownership are explicit;
- semantic route/agent/lease identities are not host/IP/port aliases;
- Windows agent remains replaceable and owns no business state or primary database;
- heartbeat, readiness, route usability, transport response, Parser success, Scan success and notification delivery are distinct;
- route selection/fallback remains server-side and auditable;
- lease is bounded authorization and differs from Scan work claim;
- explicit transport outcome classes are present;
- unknown dispatch/send state is reconcile-first;
- false-success/false-empty conversion is prohibited;
- public unauthenticated inbound exposure is prohibited by default without selecting technology;
- secret/foreign-resource/data-minimization boundaries are explicit;
- quarantine/restriction/history semantics are explicit;
- exact transport technology, ports, credentials, capabilities, priority/fallback, thresholds, retries/rates, sessions and retention are not guessed;
- OD-009, OD-010, OD-011 and OD-013 remain open;
- contracts, fakes, fixtures, matrix rows, roadmap and handoff are present;
- no agent, route, lease, tunnel, proxy, VPN, port, listener, credential, code, dependency, lock, test, fixture file, database, migration, provider request, notification delivery, Docker/CI/CD, deploy/runtime, service or sensitive material is created;
- GitHub publication and exact server synchronization are independently verified.

## 51. Append-only history

Existing entries in this section must never be edited or deleted. Corrections are appended as a new history entry.

### ER-HISTORY-0001 — 2026-07-07 — Initial playbook publication

- Run 18 initial Egress Routing ownership, contracts and roadmap defined.
- Logical agent/route registration, capability/readiness/health/quarantine, bounded lease, selection, assignment/outcome and reconciliation boundaries fixed.
- Transport success, Parser success, Scan success and notification delivery remain distinct.
- Unknown dispatch/send is reconcile-first; route failure/restriction/ambiguity cannot become clean Parser success or no listings.
- Windows Egress Agent remains replaceable, no-public-inbound by default and without primary database/business-state ownership.
- Route technology, topology, ports, credentials, priorities, thresholds, retries, sessions and retention remain unselected.
- OD-009, OD-010, OD-011 and OD-013 remain unresolved; all OD-001–OD-014 remain open.
- No agent, route, lease, tunnel, VPN, proxy, port, listener, credential, product code, database, migration, provider request, notification delivery, runtime or infrastructure artifact created.
- Run acceptance remains pending until the server checkout is synchronized to the exact published SHA and independently verified.
