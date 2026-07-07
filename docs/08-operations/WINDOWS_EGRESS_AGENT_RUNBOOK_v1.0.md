# Маяк Авито — Windows Egress Agent Runbook

**Версия:** 1.0
**Статус:** APPROVED documentation baseline
**Дата:** 2026-07-07
**Основание:** Architecture Baseline v1.0, Security and Privacy Model v1.0, Common Contract Package v1.0, Error and Idempotency Policy v1.0, Data Model v1.0, Environment Isolation Policy v1.0, Environment Matrix v1.0, Observability and Alerting v1.0, Backup and Recovery v1.0, Deployment and Release Runbook v1.0, MODULE_REGISTRY.md, OPEN_DECISIONS.md. Product target model v0.1 and architecture map v0.1 are used only as DRAFT context where explicitly marked.
**Не является:** Windows-agent implementation, tunnel/VPN/proxy selection, installer, service definition, scheduled task, firewall rule, port allocation, credential format, route creation, provider-access permission, runtime configuration или разрешением запускать agent.

---

## 1. Назначение

Документ фиксирует безопасную операционную границу будущего Windows Egress Agent.

Agent является заменяемой transport dependency модуля **Egress Routing**. Он может предоставлять контролируемый outbound path для разрешённых parser requests, но не становится владельцем Beacon, account, listing state, scheduler, queue, notification, business decision или primary project data.

Runbook предотвращает следующие подмены:

- домашний Windows-компьютер считается production environment только потому, что он доступен;
- alive process считается готовым route;
- route failure превращается в «объявлений нет»;
- lease превращается в передачу agent чужого authoritative state;
- неизвестный результат transport request повторяется вслепую;
- видимый Windows service, proxy, VPN, browser session, certificate или credential считается project-owned;
- DRAFT transport assumptions становятся implementation decisions без отдельного approval.

## 2. Source-of-truth hierarchy

1. Public GitHub `main` and approved governance state.
2. Approved architecture, security, contracts, data, quality and operations documents.
3. Этот Windows Egress Agent Runbook.
4. Future approved Egress Routing module playbook.
5. Future approved environment/agent/route record.
6. Exact execution task and accepted release identity.
7. Runtime evidence конкретного agent/route operation.

Local Windows state, running process, installed application, open port, certificate store entry, browser profile, VPN/proxy configuration or operator statement не переопределяют approved ownership and route semantics.

## 3. Approved boundary and DRAFT context

### 3.1. Approved boundary

Approved documents establish:

- **Egress Routing** owns routes, agents, leases, heartbeat, health and quarantine semantics;
- `route_id` and `agent_id` are semantic identifiers, not IP address or hostname aliases;
- route/agent is an isolated dependency;
- route failure must remain explicit and must not become clean parser success;
- lease does not transfer ownership of Beacon, account, listing or secrets;
- Windows agent does not store the primary project database;
- foreign resources remain prohibited;
- exact route technology, lease duration, health thresholds and switching policy remain unselected.

### 3.2. DRAFT context not promoted automatically

Product target model v0.1 describes a home Windows computer, an outbound protected connection and future replaceable route types. Architecture map v0.1 mentions a separate Windows agent process.

This Run 8 baseline accepts only the safe documentation boundary:

- Windows agent is a separately identified Egress Routing dependency;
- public inbound exposure is prohibited by default;
- connectivity, authentication and request transport require separate approved design;
- agent remains replaceable;
- exact home/server/provider topology is not selected;
- no DRAFT route type, tunnel or host becomes provisioned by this document.

## 4. Ownership and authority

**Owning module:** Egress Routing.

Egress Routing alone authorizes mutations of:

- Agent registration state;
- Route registration state;
- Agent-to-route association;
- Lease state;
- Route health state;
- Restriction/quarantine state;
- Route-selection decision evidence.

Windows agent may report observations and execute a valid bounded transport assignment. It must not:

- create or modify Beacon configuration;
- choose tariff/entitlement behavior;
- schedule scans;
- calculate baseline/diff;
- interpret listings as business state;
- create notification events;
- mutate account, identity, role or audit ownership;
- decide route fallback policy;
- accept itself into production;
- write directly to another module’s authoritative state.

Admin/support may request protected route operations only through future approved Egress Routing contracts. Direct database/file/service edits are prohibited.

## 5. Conceptual records

This runbook uses the approved conceptual records without selecting storage or wire format:

| Record | Meaning |
|---|---|
| `EgressAgent` | Registered logical agent identity and lifecycle |
| `EgressRoute` | Logical route identity and declared capability boundary |
| `AgentRegistration` | Approved relation between agent identity, environment and trust evidence |
| `AgentHeartbeat` | Time-bounded observation, not business success |
| `RouteLease` | Bounded authorization to use one route for one declared scope |
| `RouteHealthState` | Authoritative Egress Routing classification derived from approved evidence |
| `RouteRestriction` | Explicit restriction, quarantine or suspension record |
| `RouteSelectionDecision` | Evidence explaining why a route was selected/rejected |
| `TransportRequestReference` | Safe request identity and scope without hidden payload leakage |
| `TransportOutcome` | Explicit sent/not-sent/success/rejection/failure/ambiguous outcome |
| `ReconciliationRecord` | Evidence resolving unknown or interrupted effect |

No table, registry, database or file format is selected.

## 6. Agent identity and mandatory registration record

Before any agent may become runtime-eligible, an approved record must contain:

| Field | Requirement |
|---|---|
| `agent_id` | Stable logical identity; not hostname/IP alone |
| `agent_record_version` | Explicit semantic version |
| `environment_id` | Approved environment identity/class |
| `owner` | Accountable project owner, not inferred Windows user |
| `host_scope` | Approved logical host boundary without unnecessary private details |
| `purpose` | Exact allowed and prohibited use |
| `source_release` | Exact accepted agent release identity when implementation exists |
| `route_capabilities` | Explicit approved capability classes, not guessed provider support |
| `trust_status` | Registration/verification state |
| `credential_reference` | Secret reference/class only; no secret value |
| `connectivity_boundary` | Approved direction, peers and exposure model |
| `filesystem_boundary` | Dedicated project-owned paths after approval |
| `runtime_boundary` | Dedicated project-owned process/service/task after approval |
| `network_boundary` | Explicit no-public-inbound default and separately approved exceptions |
| `privacy_boundary` | Allowed request/evidence data and prohibited data |
| `observability_boundary` | Heartbeat, health and safe diagnostics semantics |
| `update_boundary` | Approved release/update/rollback process or `NOT_APPROVED` |
| `recovery_boundary` | Re-registration/revocation/reconciliation behavior |
| `approval_reference` | Approved document/task/decision revision |
| `evidence_freshness` | Date/revision and invalidation conditions |

Missing mandatory field means the agent remains `REGISTRATION_BLOCKED`.

## 7. Agent lifecycle

| State | Meaning |
|---|---|
| `PROPOSED` | Agent concept/record drafted; runtime forbidden |
| `REGISTRATION_BLOCKED` | Required ownership, trust, environment or secret gate absent |
| `REGISTERED` | Logical identity accepted; connectivity/use still separately gated |
| `CONNECTIVITY_PENDING` | Trust exists; approved connection not established/proven |
| `ONLINE_UNREADY` | Agent is reachable/alive but cannot accept approved work |
| `READY` | All current readiness gates for declared capability pass |
| `LEASED` | Agent has at least one valid bounded route lease |
| `DEGRADED` | Limited capability or dependency issue; affected work restricted |
| `QUARANTINED` | New work prohibited pending review/reconciliation |
| `SUSPENDED` | Administrative/security stop; no work accepted |
| `RECONCILIATION_REQUIRED` | Agent/route/request state is ambiguous |
| `RETIRED` | No new work; revocation and evidence obligations remain |

`ONLINE_UNREADY` and `READY` are distinct. A process, heartbeat or established connection alone does not make an agent ready.

## 8. Connectivity and exposure boundary

### 8.1. Default direction

Future Windows agent connectivity must be initiated through an approved outbound-only model by default. The Windows host must not expose a new public inbound listener merely to support the agent.

Any exception requires a separate security, environment and network decision before implementation.

### 8.2. Unselected technology

This document does not choose:

- VPN technology;
- tunnel technology;
- message broker;
- long polling, WebSocket, HTTP/2, QUIC or other transport;
- proxy protocol;
- local bind address or port;
- relay/server endpoint;
- certificate authority or mutual-authentication mechanism;
- firewall/NAT configuration;
- Windows service, scheduled task or user-session process.

### 8.3. Required future properties

Any proposed connectivity design must prove:

- authenticated peer identities;
- confidentiality and integrity in transit;
- replay resistance;
- bounded session lifetime and revocation;
- no public unauthenticated inbound exposure;
- least privilege;
- explicit allowed control/data message classes;
- payload size/time/resource limits;
- safe reconnect and duplicate handling;
- no secret in command line, logs or ordinary reports;
- no reuse of foreign VPN/proxy/service credentials;
- exact environment and release identity;
- reconciliation after connection interruption.

## 9. Secret and trust boundary

Agent credentials, keys, tokens, certificates or enrollment material:

- are never stored in Git;
- are never emitted in ordinary logs/reports;
- are never passed through shell history or process arguments;
- are never copied from foreign applications, browser profiles, VPNs or proxy tools;
- require protected delivery, rotation, revocation and audit after mechanism selection;
- are scoped to agent/route/environment purpose;
- do not grant access to primary database, queue, customer secrets or unrelated server functions.

Registration success must be based on verified evidence, not possession of a hostname, IP address, Windows username or shared secret copied from another system.

## 10. Route and capability model

An agent may expose only explicitly approved route capability classes. Capability is not inferred from host network access.

Future capability record must state:

- route identity;
- supported destination scope based on current reference policy;
- request method/operation classes;
- size/time/concurrency bounds;
- cookie/session handling policy if separately approved;
- redirect and DNS behavior after design approval;
- external restrictions and unsupported cases;
- health/lease dependencies;
- privacy and evidence limits;
- release compatibility.

The agent does not decide whether a Beacon is entitled to a route. Entitlement and route-selection decisions remain server-side in their owning modules/contracts.

## 11. Route lease semantics

A lease is a bounded authorization, not ownership transfer.

Mandatory future lease fields/semantics:

| Field | Requirement |
|---|---|
| `lease_id` | Stable identity |
| `lease_version` | Explicit semantic version |
| `route_id` | One approved logical route |
| `agent_id` | One approved agent |
| `requester` | Authorized logical requester/module |
| `purpose_scope` | Exact approved work class |
| `environment_id` | Exact environment |
| `source_revision` | Relevant release/contract identity |
| `issued_at` / validity | Defined under approved time policy; exact duration unselected |
| `state` | Explicit lifecycle |
| `idempotency_context` | Replay/fingerprint semantics |
| `restriction_snapshot` | Applicable quarantine/restriction state |
| `correlation_id` | Safe cross-operation evidence |

Lease must not contain raw account secrets, customer credentials, provider credentials or unnecessary personal data.

### 11.1. Lease lifecycle

| State | Meaning |
|---|---|
| `REQUESTED` | Request exists; agent use not authorized |
| `REJECTED` | Preconditions failed; no effect |
| `GRANTED` | Bounded lease accepted but work not necessarily dispatched |
| `DISPATCHED` | Approved work reference sent |
| `IN_USE` | Agent reports bounded processing |
| `COMPLETED` | Transport outcome terminal and accepted by Egress Routing contract |
| `EXPIRED` | Validity ended; new work prohibited |
| `REVOKED` | Explicit protected cancellation |
| `AMBIGUOUS` | Dispatch/effect unknown; reconcile before reuse/retry |
| `FAILED` | Defined terminal failure |

Exact persisted state names and lease duration are not selected.

## 12. Heartbeat, liveness and readiness

### 12.1. Heartbeat

Heartbeat is time-bounded evidence that an agent can report within its control boundary. It does not prove:

- route usability;
- destination availability;
- credential validity;
- correct source release;
- request success;
- parser success;
- business success;
- production readiness.

### 12.2. Readiness

Agent readiness must fail/degrade explicitly when:

- agent/environment/release identity is wrong or unknown;
- trust/session is expired, revoked or unverified;
- required configuration/secret reference is unavailable;
- active quarantine/restriction blocks the capability;
- route capability is unsupported or evidence-stale;
- resource bounds are exceeded;
- required reconciliation is incomplete;
- clock/time evidence is unreliable where validity depends on it;
- ownership/isolation cannot be proven.

### 12.3. Unselected thresholds

Heartbeat interval, timeout, readiness window, missed-heartbeat count, resource thresholds and alert thresholds are not selected. They require separate evidence-based approval.

## 13. Transport request lifecycle

A future request must distinguish:

```text
accepted by server contract
→ route selected
→ lease granted
→ dispatch attempted
→ agent received or receipt unknown
→ outbound request not sent | sent
→ explicit usable response | explicit rejection | unavailable | malformed | restricted | ambiguous
→ server-side adapter/parser processing
→ owning module accepts business outcome
```

Agent transport success is not parser success. Parser success is not scan/business success.

### 13.1. Mandatory outcome classes

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

Exact wire codes are not selected.

### 13.2. False-success prohibition

None of the following may be converted into a clean empty listing result:

- agent unavailable;
- route unavailable;
- expired/revoked lease;
- destination timeout;
- blocked/CAPTCHA/access restriction;
- malformed/incomplete response;
- connection interruption;
- unknown dispatch/send state;
- stale capability/reference evidence.

## 14. Idempotency and reconciliation

Every effectful/retryable control or transport request needs stable idempotency identity and normalized fingerprint.

Rules:

- same key/same request/terminal outcome returns original outcome reference;
- same key/different fingerprint is rejected;
- pending or unknown outcome remains pending/reconciliation-required;
- dispatch or outbound send is never repeated blindly after ambiguous interruption;
- lease replay does not silently extend validity or duplicate work;
- agent restart does not erase server-owned authoritative state;
- per-request outcomes remain explicit in partial batches;
- reconciliation uses approved safe evidence and does not inspect secrets or foreign data.

The exact idempotency store, TTL, retry delay, backoff and circuit breaker remain open.

## 15. Data minimization and request boundary

Agent receives only the minimum data required for the approved transport operation.

Prohibited by default:

- primary database access;
- queue/scheduler ownership;
- full account or Beacon records;
- entitlement state beyond a safe authorization result/reference;
- notification history;
- unnecessary personal data;
- raw integration/admin credentials;
- foreign-host configuration or application data;
- arbitrary command/script execution payloads;
- unrestricted filesystem paths;
- shell command templates built from external values.

External URLs, headers, cookies and payloads remain untrusted data. Their exact safe handling requires provider/reference and adapter contracts before implementation.

## 16. Windows host isolation

A future Windows host/agent record must prove dedicated project boundaries before runtime:

- approved host/environment ownership;
- dedicated project-owned filesystem path;
- dedicated runtime identity and least privilege;
- no reuse of personal/foreign service credentials;
- no reading browser passwords, cookies or unrelated profiles;
- no dependency on unrelated VPN/proxy/security software configuration;
- no public inbound listener by default;
- explicit update/restart behavior;
- safe local diagnostic and log boundary;
- protected secret delivery and revocation;
- no primary database, scheduler, durable queue or authoritative business state;
- cleanup/retirement and evidence obligations.

This document does not select Windows version/edition, account type, service manager, package/installer format or host hardware.

## 17. Quarantine and restrictions

A route/agent may enter quarantine for evidence such as:

- repeated access restriction or provider rejection;
- identity/release/configuration mismatch;
- trust/credential concern;
- unexpected destination/capability behavior;
- malformed or unsafe response pattern;
- missing/stale heartbeat or readiness evidence;
- resource/capacity concern under future approved thresholds;
- secret/privacy/redaction violation;
- duplicate/ambiguous dispatch behavior;
- foreign-resource dependency;
- unexplained clock/time inconsistency;
- failed update/rollback/reconciliation.

Quarantine semantics:

- no new affected leases/work;
- in-flight work becomes explicit cancelled/failed/ambiguous according to evidence;
- quarantine does not delete history;
- removal requires authorized review and evidence;
- automatic unquarantine is prohibited unless separately specified and proven;
- quarantine does not authorize route switching by the agent itself.

## 18. Fallback and route switching

Agent does not select fallback route independently.

Future Egress Routing policy must define:

- allowed route classes and priority;
- entitlement/Beacon/environment scope;
- failure categories permitting switch;
- categories requiring stop/quarantine instead;
- retry and reconciliation order;
- impact on cookies/session/request identity;
- rate/restriction safety;
- audit and reason codes;
- no duplicate external request/effect;
- whether current reference evidence permits each route behavior.

Route switching cannot convert unknown or restricted provider behavior into success. Exact switching policy remains unselected.

## 19. Observability and safe evidence

Minimum future route/agent observability semantics:

- safe `agent_id`, `route_id`, lease/request/correlation references;
- environment and source release;
- lifecycle/readiness/quarantine state;
- heartbeat freshness and provenance;
- declared capability state;
- dispatch/send/outcome classes;
- succeeded/failed/pending/ambiguous counts;
- retry/reconciliation state;
- safe reason codes;
- resource observations only after approved thresholds/collection scope;
- secret/redaction and foreign-resource checks.

Logs/metrics/traces must not contain raw credentials, private keys, tokens, cookies, browser profiles, full private payloads, shell history, process arguments or unnecessary personal data.

A green process indicator, connected tunnel or heartbeat does not prove route/business health.

## 20. Audit requirements

Protected audit is required for future:

- agent registration, approval, suspension, retirement;
- credential/trust issuance, rotation, revocation reference;
- route creation/association after approval;
- lease policy and restriction changes;
- quarantine and unquarantine;
- protected manual route selection/override;
- release/update/rollback actions;
- security/privacy incidents;
- administrative fallback changes.

Audit contains safe identities, actor authorization, reason, before/after semantic state, environment/revision, correlation and outcome. Raw secret material is excluded.

## 21. Update, release and rollback boundary

Agent implementation/update remains forbidden until separate product-code approval and an accepted release package.

Future update plan must identify:

- exact source/release/artifact identity;
- Windows environment and agent identity;
- compatibility with server Egress Routing contracts;
- configuration identity without secrets;
- update mechanism and privilege boundary;
- connection/lease behavior during update;
- rollback/roll-forward boundary;
- backup/recovery relevance for local non-authoritative state;
- post-update liveness/readiness/capability checks;
- failure/reconciliation states;
- no foreign service/task/firewall/port reuse.

Rollback is not a destructive reset and must not lose server-owned lease/request evidence.

## 22. Registration, retirement and revocation

Future registration must be explicit, authorized, auditable and idempotent.

Future retirement requires:

- no new leases;
- active lease/request inventory;
- reconciliation of ambiguous work;
- credential/trust revocation;
- route association update;
- safe local state cleanup after evidence preservation;
- no deletion of server authoritative history;
- final environment/secret/foreign-resource checks;
- accepted report.

Lost/decommissioned host cannot remain `READY` merely because the last heartbeat was once valid.

## 23. Required future fixtures and scenarios

Before implementation, module/task quality scope must include at least:

- valid registration and readiness;
- duplicate registration replay;
- registration fingerprint mismatch;
- wrong environment or release;
- missing/revoked/expired trust reference;
- heartbeat present but readiness failed;
- missed/stale heartbeat;
- valid lease and completion;
- expired/revoked lease;
- duplicate lease/request replay;
- dispatch before receipt interruption;
- interruption after possible receipt/send;
- explicit provider rejection;
- destination unavailable;
- access restriction/CAPTCHA/rate condition;
- malformed/incomplete response;
- no false empty result;
- partial batch;
- quarantine and protected unquarantine;
- fallback prohibited/allowed branch;
- agent restart/update/rollback;
- retirement with active/ambiguous work;
- cross-account/Beacon isolation;
- secret/redaction checks;
- foreign-resource and public-inbound exposure checks;
- fake agent/route dependency for parser/orchestration testing.

No executable fixture, test, agent or route is created by this Run 8 document.

## 24. Failure and stop conditions

Stop before mutation/work when:

- agent/route/environment/release identity is wrong or unknown;
- registration/trust/secret gate is absent;
- public inbound exposure or network boundary is unapproved;
- lease is missing, expired, revoked, mismatched or ambiguous;
- route capability/reference evidence is unsupported or stale;
- quarantine/suspension applies;
- ownership/isolation cannot be proven;
- foreign resource or credential would be used;
- request requires arbitrary command execution;
- safe idempotency/reconciliation is absent;
- required observability/evidence cannot be produced.

During/after work:

- partial outcomes are reported per request;
- unknown effect becomes `RECONCILIATION_REQUIRED`;
- validation failure blocks acceptance;
- secret exposure triggers protected stop/review;
- false-success conversion is prohibited;
- corrective action targets the first proven wrong object/value/action;
- failure does not authorize destructive reset, force operation, blind retry or unapproved fallback.

## 25. Evidence package

A future agent/route task report must contain:

1. task/iteration ID;
2. agent/route/environment identities;
3. source release and contract versions;
4. registration/trust state without secrets;
5. allowed scope and exclusions;
6. before/after lifecycle/readiness/quarantine state;
7. lease/request identities and fingerprints safely represented;
8. action classes actually performed;
9. dispatch/send/outcome inventory;
10. failed/pending/ambiguous/reconciliation inventory;
11. heartbeat/health evidence with freshness semantics;
12. ownership/isolation/privacy/redaction checks;
13. public-inbound and foreign-resource statements;
14. credential/secret exposure statement;
15. update/rollback/retirement state when applicable;
16. GitHub/repository/Git/SSH/Windows/server configuration mutation statement;
17. exact final marker;
18. independent acceptance result when required.

Raw credentials, private host details not needed for the gate, provider private payloads and personal data are excluded.

## 26. Relationship to future module playbooks

Run 8 is an operations baseline, not the Run 17 Egress Routing module playbook.

Run 17 must still define:

- module public commands, queries and events;
- authoritative record semantics and contract versions;
- route-selection policy boundaries;
- dependency interfaces and fake route/agent;
- module-specific fixtures/test vectors;
- acceptance matrix rows;
- roadmap tasks;
- handoff/report format;
- append-only module history.

Run 15 Avito Parser Adapter and Run 16 Scan Orchestration may depend only on approved Egress Routing contracts/fakes, not on Windows-agent internals.

## 27. Open decisions

This baseline does not choose:

- Windows version/edition or hardware;
- home, office, hosted or other physical placement;
- runtime language/framework;
- installer/package/update technology;
- Windows service, scheduled task or interactive process;
- transport/tunnel/VPN/proxy protocol;
- relay/server endpoint;
- local/server ports or bind addresses;
- firewall/NAT/DNS rules;
- authentication, certificate or enrollment mechanism;
- secret-management product and rotation schedule;
- heartbeat/lease/readiness/quarantine thresholds;
- concurrency, timeout, payload-size and resource limits;
- retry/backoff/circuit breaker;
- cookie/session handling;
- route priority/switching policy;
- Avito-specific allowed request behavior;
- monitoring stack, alert channels or on-call owner;
- local log retention;
- production eligibility;
- provider/legal acceptability of a route.

## 28. Explicit prohibitions

This document does not authorize:

- creating or configuring a Windows agent;
- installing software or packages;
- creating Windows users, services, scheduled tasks or processes;
- opening inbound listeners or ports;
- changing firewall, NAT, DNS, proxy, VPN or routing configuration;
- creating tunnel/relay/server endpoint;
- registering an agent or route in runtime;
- issuing credentials, tokens, keys or certificates;
- reading browser profiles, cookies, credentials or foreign application data;
- sending Avito/provider requests;
- storing primary database, scheduler, queue or customer secrets on Windows host;
- creating product-code, scripts, executable tests, CI/CD, database, migration, container, deploy or runtime configuration;
- declaring Windows route, environment or production ready.

## 29. Acceptance criteria

Windows Egress Agent Runbook is accepted when:

- Egress Routing ownership and agent non-ownership boundaries are explicit;
- agent/route/lease/request identities and lifecycle semantics are documented;
- outbound-only/no-public-inbound default is explicit without selecting transport;
- heartbeat, liveness, readiness, quarantine and outcome semantics are separated;
- route failure/restriction/ambiguity cannot become clean parser/business success;
- idempotency, reconciliation, fallback and retirement boundaries are explicit;
- Windows host, secret, privacy and foreign-resource isolation is preserved;
- exact technologies, ports, credentials, thresholds, switching policy and provider behavior remain open;
- no agent, route, tunnel, service, port, credential, request, code or runtime artifact is created;
- OD-001–OD-014 remain open.

## 30. Версионная история

| Версия | Дата | Изменение |
|---|---|---|
| 1.0 | 2026-07-07 | First technology-neutral Windows Egress Agent operational baseline without agent implementation, tunnel/port/credential selection or runtime changes. |
