# Runtime Topology and Environment Record Candidate

Version: 1.0
Status: RF-04_ACTIVE_FIFTH_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE
Date: 2026-07-23
Module: 14-runtime-foundation-and-autonomous-integration
Roadmap step: RF-04
Technical-ID: RF-04-05-RUNTIME-TOPOLOGY-AND-ENVIRONMENT-RECORD-CANDIDATE-20260723
Source branch: main
Source base SHA: 39f65b3f2de9668be188aec6f16b777d04f23135
RF-04-01 accepted chain head: 2edfbb96c7438dae6bb6f3890cfe007d4467b6ca
RF-04-02 accepted chain head: 710f965a66488f99b4c3cc9cf9f44bef54c7434a
RF-04-03 accepted SHA: 37785e2cde19b80ba69edd23d07d6b38949dc0cb
RF-04-04 accepted SHA: 39f65b3f2de9668be188aec6f16b777d04f23135
Runtime mutation: none
Environment allocation: CANDIDATE_UNRESERVED
Production verdict: NOT_CLAIMED
Final target: READY_FOR_OPERATOR_ACCEPTANCE

## 1. Authority and scope

GitHub `main` is the sole source of truth. RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`, RF-04-02 through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`, RF-04-03 at `37785e2cde19b80ba69edd23d07d6b38949dc0cb`, and RF-04-04 at `39f65b3f2de9668be188aec6f16b777d04f23135`.

This artifact is documentation/design-only. No server allocation or mutation was performed; no current port is selected or reserved. No container, network, volume, database, user, directory or secret exists by authority of this artifact. The runtime host is the existing project server. A new server is neither required nor authorized. RF-04 defines topology; RF-05 verifies and records the actual existing-server environment; RF-08 implements Docker/Compose; RF-09 implements PostgreSQL/Alembic; RF-27 deploys the accepted SHA. RF-04 remains active, RF-05 remains not started, and no `PRODUCTION_READY` claim is made.

## 2. Accepted topology invariants

The accepted future topology uses Docker Engine and the Docker Compose plugin. The acceptance Compose project is `avito-mayak-acceptance`; the reserved future/default project name is `avito-mayak`.

- Mandatory services are `mayak-api`, `mayak-worker`, `mayak-scheduler`, and `mayak-postgres`.
- Optional one-shot/profile services are `mayak-migrate`, `mayak-backup`, `mayak-restore-check`, `mayak-windows-egress-simulator`, and `mayak-provider-fake`.
- API, worker and scheduler are separate processes using one application image with different commands.
- PostgreSQL 18 is authoritative; there is no Redis, Celery, RabbitMQ, Kafka or external broker.
- Kubernetes and Swarm are outside scope. There is no external Docker network or volume and no `container_name`.
- API is localhost-only; PostgreSQL has no host-published port.
- Provider profiles are disabled by default. There is no public ingress, DNS, TLS, Nginx or firewall mutation.
- Direct foreign-module mutation and production personal data are forbidden.
- Runtime success is never based only on process existence.
- Global Docker prune is forbidden.

## 3. Current repository implementation state

This is an exact tracked-tree observation at source base `39f65b3f2de9668be188aec6f16b777d04f23135`; design documents are not runtime implementation.

| exact path | state | evidence basis | interpretation | future RF owner |
|---|---|---|---|---|
| `Dockerfile` | ABSENT | expected-base tree lookup | no image build file | RF-08 |
| `.dockerignore` | ABSENT | expected-base tree lookup | no container build exclusion file | RF-08 |
| `compose.yaml` | ABSENT | expected-base tree lookup | no Compose implementation | RF-08 |
| `docker-compose.yml` | ABSENT | expected-base tree lookup | no legacy Compose implementation | RF-08 |
| `src/mayak/runtime/` | ABSENT | expected-base tree lookup | no runtime package implementation | RF-23 |
| `.github/workflows/` | ABSENT | expected-base tree lookup | no CI workflow implementation | RF-07 |
| `alembic.ini` | ABSENT | expected-base tree lookup | no migration configuration | RF-09 |
| `alembic/` | ABSENT | expected-base tree lookup | no Alembic implementation | RF-09 |
| `migrations/` | ABSENT | expected-base tree lookup | no alternate migration implementation | RF-09 |
| `docker/` | ABSENT | expected-base tree lookup | no Docker support directory | RF-08 |
| `infra/` | PRESENT | expected-base tree lookup; only `infra/README.md` is tracked | documentation only, not runtime infrastructure | RF-05/RF-08 |
| `deploy/` | ABSENT | expected-base tree lookup | no deployment implementation | RF-27 |

## 4. Environment-record status vocabulary

| status | allowed meaning | forbidden inference | transition owner |
|---|---|---|---|
| `FIXED_ACCEPTED_DECISION` | accepted design invariant | actual host observation or allocation | RF-04 acceptance |
| `OBSERVED_READ_ONLY` | verified read-only fact in an authorized environment | permission to mutate or reserve | RF-05/RF-27 |
| `CANDIDATE_UNRESERVED` | proposed value for deterministic future selection | allocated, free, or present resource | RF-05 |
| `PENDING_RF05_VERIFICATION` | requires existing-server verification | current host fact | RF-05 |
| `PENDING_FUTURE_RF_IMPLEMENTATION` | deferred implementation value or contract | implemented runtime behavior | owning future RF |
| `PROVIDER_DISABLED_CONTINUE` | optional provider remains disabled and core may continue | provider call, credential validity, or success | RF-18/RF-19/RF-23 |
| `BLOCKED_FOREIGN_COLLISION` | candidate conflicts with ambiguous foreign ownership | authority to reuse or delete foreign state | RF-05 |
| `NOT_APPLICABLE` | field or check does not apply | successful verification | owning future RF |
| `NOT_PRODUCTION_READY` | production verdict remains blocked | production approval | RF-29/RF-30 |

## 5. Existing-server and filesystem boundary

No path below is created by this task. Every actual state is `PENDING_RF05_VERIFICATION`.

| boundary | purpose | candidate ownership | candidate mode policy | role | actual state | collision action | implementation/proof owner |
|---|---|---|---|---|---|---|---|
| `/opt/avito-mayak` | source checkout | project Git source | repository policy | immutable source | `PENDING_RF05_VERIFICATION` | do not reuse foreign path; record alternative | RF-05/RF-27 |
| `/opt/avito-mayak-worktrees` | clean worktrees | project task isolation | owner-only access | mutable task workspace | `PENDING_RF05_VERIFICATION` | stop or record safe project-owned alternative | RF-05 |
| `/opt/avito-mayak-runtime` | releases and current pointer | project runtime | owner-only, releases immutable | mutable pointer, immutable releases | `PENDING_RF05_VERIFICATION` | safe project-owned alternative | RF-05/RF-27 |
| `/etc/avito-mayak` | non-secret configuration | project operator | least privilege | mutable deployment config | `PENDING_RF05_VERIFICATION` | safe project-owned alternative | RF-05/RF-25 |
| `/etc/avito-mayak/secrets` | secret references/files | project operator | `0400` or `0600`, least privilege | mutable secret boundary | `PENDING_RF05_VERIFICATION` | stop; never reuse foreign secrets | RF-05/RF-25 |
| `/var/lib/avito-mayak` | persistent data boundary | project runtime | database owner only | mutable durable data | `PENDING_RF05_VERIFICATION` | safe project-owned alternative | RF-05/RF-09 |
| `/var/backups/avito-mayak` | backup artifacts | project operations | least privilege | mutable backup store | `PENDING_RF05_VERIFICATION` | safe project-owned alternative | RF-05/RF-26 |

The source checkout remains source, not mutable runtime data. Worktrees are task-isolated. Runtime releases are immutable per SHA. Configuration, secrets, data and backups remain outside Git where applicable. No foreign path is reused; a conflict requires a safe project-owned alternative recorded by RF-05.

## 6. Release and source-identity model

The immutable release candidate layout is `/opt/avito-mayak-runtime/releases/<full-git-sha>/`, with candidate current pointer `/opt/avito-mayak-runtime/current`. Pointer update is future deployment scope, never this task. Release identity includes full Git SHA, `uv.lock` identity, image digest, environment ID, migration revision, build timestamp and process kind. API, worker and scheduler use the same application image digest.

Mutable configuration, secrets, DB data and backups stay outside the immutable release. No package install or mutable source checkout occurs at container startup. Image/source mismatch causes not-ready/deploy failure. Rollback means selecting an accepted previous immutable release only after schema compatibility proof. Git history is never reset or rebased.

Required future OCI/project labels are `org.opencontainers.image.revision`, `org.opencontainers.image.source`, `com.avito-mayak.project-owned=true`, `com.avito-mayak.environment-id`, `com.avito-mayak.process-kind`, and `com.avito-mayak.compose-project`.

## 7. Compose project and service topology

Logical project-owned network key is `mayak-internal`; logical named volume key is `postgres-data`. Compose-generated resource names remain project-scoped. Optional services are disabled by profile/default unless an exact future task enables them; live provider service/profile is not enabled by default.

| service | class | image source | command responsibility | attached network | durable storage | secret access class | host-published port | startup dependency | restart policy candidate | implementation owner | proof owner |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `mayak-postgres` | mandatory database | PostgreSQL 18 image, later pinned by digest | PostgreSQL server | `mayak-internal` | `postgres-data` | DB bootstrap/migration references | none | none | unless-stopped | RF-08/RF-09 | RF-25/RF-26 |
| `mayak-migrate` | mandatory one-shot | project application image | explicit Alembic migration command | `mayak-internal` | none | migration credentials | none | healthy `mayak-postgres` | no restart | RF-08/RF-09 | RF-09 |
| `mayak-api` | mandatory process | one project application image | FastAPI/Uvicorn API | `mayak-internal` | none | application core references | future `127.0.0.1:<selected-18080-18099>:8000` | migration success and DB ready | unless-stopped | RF-23 | RF-24/RF-26 |
| `mayak-worker` | mandatory process | one project application image | durable work claims/handlers | `mayak-internal` | none | application core/provider references | none | migration success and DB ready | unless-stopped | RF-23 | RF-24/RF-26 |
| `mayak-scheduler` | mandatory process | one project application image | due schedule discovery | `mayak-internal` | none | application core references | none | migration success and DB ready | unless-stopped | RF-23 | RF-24/RF-26 |
| `mayak-backup` | optional/profile one-shot | project operations image | project-owned PostgreSQL backup | `mayak-internal` | backup root | backup/DB references | none | healthy DB | no restart | RF-26 | RF-26 |
| `mayak-restore-check` | optional/profile one-shot | project operations image | isolated restore verification | `mayak-internal` | isolated project-owned target | backup/DB references | none | backup artifact and healthy DB | no restart | RF-26 | RF-26 |
| `mayak-windows-egress-simulator` | optional/profile | project application/test image | synthetic egress agent simulation | `mayak-internal` | none | synthetic references only | none | core test profile | no restart | RF-16/RF-24 | RF-24 |
| `mayak-provider-fake` | optional/profile | project application/test image | fake provider responses | `mayak-internal` | none | synthetic references only | none | core test profile | no restart | RF-18/RF-19/RF-24 | RF-24 |

`mayak-postgres` uses PostgreSQL 18, pinned later by digest. `mayak-migrate` is one-shot and uses migration credentials. API, worker and scheduler use one application image. API internal port is `8000`; its future host mapping shape is `127.0.0.1:<selected-18080-18099>:8000`. PostgreSQL internal port is `5432` and has no host mapping. No service uses `container_name`.

## 8. Network and localhost port allocation

The API host bind is exactly `127.0.0.1`; candidate host range is exactly `18080–18099`. There is no public bind: no `0.0.0.0`, no `[::]`, and no public interface. PostgreSQL is never published to the host. Operator browser access is through localhost or an SSH tunnel. Only the project-owned Compose bridge is used: no foreign or external Docker network and no automatic connection to a foreign proxy/network. Provider outbound is disabled by configuration by default.

RF-05 must allocate deterministically: (1) inspect TCP listeners for `127.0.0.1:18080–18099`; (2) inspect Docker published ports without inspecting foreign content; (3) inspect the accepted environment record; (4) select the numerically lowest unoccupied port; (5) verify bind race immediately before reservation; (6) record exact port, timestamp, environment ID and owner; (7) if occupied before reservation, repeat from step 1; (8) if all 20 ports are occupied, return `STOP_SCOPE_REQUIRED`; (9) do not kill or modify an existing listener; (10) candidate port in this artifact remains `PENDING_RF05_VERIFICATION`. No specific current port is claimed free, selected or reserved.

## 9. Persistent data, volumes and backup boundary

PostgreSQL data uses project-owned named-volume logical key `postgres-data`; there is no external or foreign volume and no bind to a foreign DB directory. Application authoritative state is PostgreSQL, with no SQLite authoritative state. Raw provider payload is not persisted by default, and configuration and secret values are not in the DB by default. Backups use `/var/backups/avito-mayak` and are project-owned. Acceptance retention is 7 days, RPO is 24 hours and RTO is 2 hours. Restore-check uses an isolated project-owned target. Cleanup touches only project-owned backup paths/resources. No backup or volume is created by this task.

## 10. Startup, migration and dependency ordering

Future deployment order is exact: 1) verify project/foreign resource isolation; 2) verify immutable source SHA and lock identity; 3) load non-secret configuration references; 4) verify mandatory secret-file presence without values; 5) create/start project-owned PostgreSQL; 6) wait for PostgreSQL health; 7) run explicit one-shot `mayak-migrate`; 8) verify one Alembic head and current revision; 9) start API, worker and scheduler; 10) verify process liveness; 11) verify process-specific readiness; 12) execute synthetic smoke; 13) record environment evidence.

API, worker and scheduler never auto-migrate. Provider calls do not occur during startup. Missing provider credentials do not block core startup. DB/schema mismatch is `NOT_READY`; `depends_on` alone is not readiness proof; migration success is checked independently. Scheduler and worker correctness do not depend on singleton status. Graceful shutdown preserves durable work, and restart resumes from PostgreSQL.

## 11. Liveness, readiness, version and diagnostics

Unless an already accepted exact contract conflicts (in which case `STOP_SCOPE_REQUIRED`), the canonical API routes are below. Liveness means process alive only; readiness means eligible for core business processing. Version exposes source SHA, image digest/reference, environment ID, process kind, migration revision and lock identity. Diagnostics are redacted; provider-disabled status is safe to expose. Provider response is not proof of human read. API readiness does not assert worker/scheduler liveness; those processes require future process-local health commands/checks. Exact commands are RF-08/RF-26 scope. Mandatory DB/schema failure makes the affected process not ready; optional telemetry failure cannot reverse committed business state.

| path | purpose | allowed checks | status semantics | safe fields | forbidden fields | implementation owner | proof owner |
|---|---|---|---|---|---|---|---|
| `GET /health/live` | process liveness | process-local loop/server | alive only; never readiness | process kind, state | secrets, DB detail, provider payload | RF-23/RF-26 | RF-26 |
| `GET /health/ready` | core readiness | typed config, DB/schema and process-local dependencies | ready/not-ready; optional provider may be degraded | redacted dependency classes, provider disabled state | credentials, tokens, personal data | RF-23/RF-26 | RF-24/RF-26 |
| `GET /version` | source/build identity | static immutable release identity | identity response | SHA, image digest/reference, environment ID, process kind, migration revision, lock identity | secret values, cookies, private keys | RF-08/RF-23 | RF-25/RF-26 |
| `GET /diagnostics` | safe operational evidence | redacted dependency/readiness summary | diagnostic success does not imply business success | redacted status, correlation, safe versions, provider state | raw provider payloads, production data, tokens, cookies, private keys | RF-23/RF-26 | RF-25/RF-26 |

## 12. Configuration and secret interface boundary

This section defines interface/topology only, not a complete settings schema. The full configuration/secrets schema is a later RF-04 artifact; implementation belongs to RF-05/RF-06/RF-23. Pydantic Settings is mandatory. Only safe defaults may be in Git; a future `.env.example` may contain names/placeholders only, while real values remain outside Git. Secret files are mounted read-only under `/run/secrets/<secret-name>`; the host secret boundary is `/etc/avito-mayak/secrets`, with mode `0400` or `0600` and least-privilege ownership.

No secret appears in a command line, image, labels, logs or reports. Migration and application DB credentials are separate. Optional provider credentials produce disabled adapter state; missing mandatory core secrets produce `NOT_READY`. Safe acceptance secrets may be generated only by an exact future task. Secret values are never printed. No real secret value is invented here.

## 13. Provider-disabled and outbound-traffic boundary

Live Avito, Telegram, MAX and payment calls are disabled by default. Fake/synthetic providers are allowed. Missing optional credentials yield `PROVIDER_DISABLED_CONTINUE`; core readiness may remain ready, while provider-specific readiness is `BLOCKED_CREDENTIAL` or `DISABLED`. Enablement requires an exact profile, credential reference, accepted operator step and safe diagnostics. There is no startup probe to a live provider and no foreign proxy fallback. Route failure is not parser success; an ambiguous provider effect is reconciliation-first. Provider acceptance is not human reading. No outbound provider traffic occurs by authority of this artifact.

## 14. Observability and retention boundary

Logs are structured JSON to stdout/stderr with timestamp, environment ID, source SHA, process kind, module, operation, correlation ID, run/work/attempt ID where applicable, result class, latency, readiness state and migration revision. Mandatory redaction applies. There is no third-party analytics, marketing pixel or required external telemetry backend. An OpenTelemetry boundary is allowed; telemetry failure cannot alter business commit semantics. Acceptance log retention target is 7 days; synthetic DB records maximum 14 days; test artifacts 30 days; safe provider evidence metadata 30 days; backup artifacts 7 days; sessions maximum 24 hours. Rotation is project-local. No global Docker daemon mutation is performed by default. Exact retention implementation belongs to RF-26.

## 15. Isolation, ownership and collision rules

Every future created resource must have project ownership evidence. Compose labels are primary Docker ownership evidence, with exact environment ID and source SHA as additional evidence. Foreign containers, networks, volumes, databases, listeners and paths cannot be reused. No foreign object content is inspected beyond safe collision metadata. There is no global Docker prune, automatic deletion of unknown resources, or Nginx/firewall/DNS/TLS mutation.

Ambiguous ownership is `STOP_FOREIGN_RESOURCE`. For a conflicting preferred filesystem path, RF-05 selects the nearest safe project-owned alternative and records it. For a conflicting localhost port, RF-05 chooses the next free port. A conflicting Compose project label/name with ambiguous ownership is `STOP_FOREIGN_RESOURCE`. Cleanup targets only exact environment ID/project labels. Destructive action requires a backup/rollback gate. Environment destroy removes only project-owned containers, networks, volumes, secrets and temporary backups; source checkout and task worktrees are not deleted by runtime destroy.

## 16. Environment record candidate matrix

This candidate does not allocate resources. The future deployed SHA replaces the artifact source SHA in the actual RF-05/RF-27 record. RF-05 may adjust only collision-sensitive candidate values using deterministic rules. No owner question is required.

| field | candidate value | status vocabulary value | verification method | mutation owner | proof owner | foreign-collision action |
|---|---|---|---|---|---|---|
| `environment_id` | `avito-mayak-acceptance-local-01` | `CANDIDATE_UNRESERVED` | RF-05 record check | RF-05 | RF-27 | choose safe ID or stop |
| `environment_class` | `SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME` | `FIXED_ACCEPTED_DECISION` | document comparison | RF-04 | RF-29 | stop scope |
| `host_identity` | `REDACTED_PENDING` | `PENDING_RF05_VERIFICATION` | authorized metadata only | RF-05 | RF-27 | do not disclose; record safe identity |
| `host_os` | `PENDING_RF05_VERIFICATION` | `PENDING_RF05_VERIFICATION` | authorized read-only metadata | RF-05 | RF-27 | record alternative evidence |
| `source_repository` | `MaksimUnimax/AVITO_Mayak` | `FIXED_ACCEPTED_DECISION` | Git remote metadata | RF-05 | RF-27 | stop foreign source |
| `source_sha` | `39f65b3f2de9668be188aec6f16b777d04f23135` (artifact source only) | `OBSERVED_READ_ONLY` | Git object and release labels | RF-27 | RF-27 | require accepted SHA |
| `lock_identity` | current `uv.lock` Git blob `a73b275f72e8376aeb6747484d6c16ceb59820c0`, runtime proof pending RF-06 | `PENDING_FUTURE_RF_IMPLEMENTATION` | Git blob then image proof | RF-06 | RF-27 | reject mismatch |
| `python_target` | `CPython 3.14.x standard GIL` | `FIXED_ACCEPTED_DECISION` | image/runtime proof | RF-06 | RF-25 | reject mismatch |
| `uv_target` | `PENDING_RF06_EXACT_PIN` | `PENDING_FUTURE_RF_IMPLEMENTATION` | lock/toolchain proof | RF-06 | RF-27 | reject mismatch |
| `source_path` | `/opt/avito-mayak` | `PENDING_RF05_VERIFICATION` | path ownership metadata | RF-05 | RF-27 | safe alternative or stop |
| `worktree_root` | `/opt/avito-mayak-worktrees` | `PENDING_RF05_VERIFICATION` | path ownership metadata | RF-05 | RF-27 | safe alternative or stop |
| `runtime_root` | `/opt/avito-mayak-runtime` | `PENDING_RF05_VERIFICATION` | path ownership metadata | RF-05 | RF-27 | safe alternative or stop |
| `configuration_root` | `/etc/avito-mayak` | `PENDING_RF05_VERIFICATION` | path ownership metadata | RF-05 | RF-25 | safe alternative or stop |
| `secret_root` | `/etc/avito-mayak/secrets` | `PENDING_RF05_VERIFICATION` | metadata only, no values | RF-05 | RF-25 | stop; do not reuse |
| `persistent_data_root` | `/var/lib/avito-mayak` | `PENDING_RF05_VERIFICATION` | path/volume ownership metadata | RF-05 | RF-09 | safe alternative or stop |
| `backup_root` | `/var/backups/avito-mayak` | `PENDING_RF05_VERIFICATION` | path ownership metadata | RF-05 | RF-26 | safe alternative or stop |
| `compose_project` | `avito-mayak-acceptance` | `CANDIDATE_UNRESERVED` | Compose label/name metadata | RF-08 | RF-27 | `STOP_FOREIGN_RESOURCE` |
| `compose_network` | `mayak-internal` (logical key) | `CANDIDATE_UNRESERVED` | project label metadata | RF-08 | RF-27 | `STOP_FOREIGN_RESOURCE` |
| `postgres_volume` | `postgres-data` (logical key) | `CANDIDATE_UNRESERVED` | project label metadata | RF-08/RF-09 | RF-27 | `STOP_FOREIGN_RESOURCE` |
| `api_bind_address` | `127.0.0.1` | `FIXED_ACCEPTED_DECISION` | Compose config inspection | RF-08 | RF-25 | reject public bind |
| `api_host_port` | `PENDING_RF05_LOWEST_FREE_18080_18099` | `PENDING_RF05_VERIFICATION` | deterministic listener/port check | RF-05 | RF-27 | choose next free port |
| `postgres_host_port` | `NONE` | `FIXED_ACCEPTED_DECISION` | Compose config inspection | RF-08 | RF-25 | reject published DB |
| `service_identity` | `avito-mayak` | `CANDIDATE_UNRESERVED` | project labels/source identity | RF-08 | RF-27 | stop ambiguous collision |
| `production_verdict` | `NOT_PRODUCTION_READY` | `NOT_PRODUCTION_READY` | acceptance evidence review | RF-29/RF-30 | RF-30 | no production transition |

## 17. Failure and recovery matrix

| # | scenario | detection | authoritative/candidate state | readiness/deploy effect | corrective/reconciliation action | rollback action | safe evidence | forbidden response | future RF proof owner |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | expected Git base changed | fetch/compare | base mismatch | reject deployment | stop; ChatGPT rereads current GitHub main and reissues the task on the verified base | none | SHAs only | publish stale base | RF-05/RF-27 |
| 2 | preferred source/runtime/config path is foreign | ownership metadata | blocked candidate | deployment blocked | select safe project-owned alternative | preserve foreign path | redacted path ownership | reuse or delete | RF-05 |
| 3 | preferred secret path is foreign | ownership metadata | blocked candidate | not ready | select project-owned secret boundary | keep foreign secrets | modes/owner class only | read or reuse values | RF-05/RF-25 |
| 4 | preferred data path is foreign | volume/path labels | blocked candidate | not ready | isolate project data | no DB mutation | ownership metadata | bind foreign DB | RF-05/RF-09 |
| 5 | preferred backup path is foreign | path ownership | blocked candidate | backup gate blocked | select safe backup root | retain foreign backups | metadata only | overwrite | RF-05/RF-26 |
| 6 | Compose project name has ambiguous foreign resources | labels/name | `BLOCKED_FOREIGN_COLLISION` | stop | choose exact safe project or stop | no cleanup | labels/name | prune/delete | RF-05/RF-08 |
| 7 | project network name/label collision | labels | blocked candidate | stop | safe project-scoped network | no foreign mutation | labels | attach/relabel | RF-08 |
| 8 | project volume name/label collision | labels | blocked candidate | stop | safe project-owned volume | no foreign mutation | labels | attach/delete | RF-08/RF-09 |
| 9 | all localhost ports `18080–18099` occupied | listener check | candidate unresolved | `STOP_SCOPE_REQUIRED` | escalate scope | none | port metadata | kill listener | RF-05 |
| 10 | selected port becomes occupied before reservation | bind-race check | candidate invalid | retry allocation | repeat deterministic algorithm | none | timestamp/port | kill listener | RF-05 |
| 11 | API configured to public bind | config inspection | invalid topology | deployment rejected | set localhost-only config | revert unaccepted config | redacted config class | expose public port | RF-08/RF-25 |
| 12 | PostgreSQL host port is published | Compose inspection | invalid topology | deployment rejected | remove mapping | preserve DB data | Compose metadata | expose DB | RF-08/RF-09 |
| 13 | Docker/Compose unavailable at RF-05/RF-08 | command/version check | implementation pending | blocked | install/use only exact future task | none | version/error class | mutate globally | RF-05/RF-08 |
| 14 | source SHA and image revision mismatch | label/version check | identity mismatch | not ready/deploy failure | rebuild/select matching image | select accepted prior release | SHA/digest | run mismatch | RF-08/RF-27 |
| 15 | lock identity mismatch | lock/image check | identity mismatch | not ready | rebuild with accepted lock | select compatible release | hash identity | install at startup | RF-06/RF-08 |
| 16 | migration revision mismatch | Alembic head check | schema incompatible | `NOT_READY` | explicit compatible migration | rollback only after proof | revision metadata | auto-migrate in app | RF-09 |
| 17 | mandatory core secret missing | file presence check | core config incomplete | `NOT_READY` | exact future secret provisioning | no secret fabrication | presence/mode only | print/generate ad hoc | RF-05/RF-25 |
| 18 | optional provider credential missing | provider profile check | provider disabled | `PROVIDER_DISABLED_CONTINUE` | continue core; enable only accepted profile | keep disabled | disabled class | block core/live call | RF-18/RF-19 |
| 19 | service process alive but readiness failed | endpoint/process-local check | process not eligible | not accepted | diagnose dependency/readiness and stop new work | restart after evidence | redacted status | accept process existence | RF-23/RF-26 |
| 20 | foreign resource mutation would be required | ownership gate | foreign boundary | `STOP_FOREIGN_RESOURCE` | stop and obtain safe project-owned alternative | no mutation | ownership metadata | kill/relabel/alter | RF-05/RF-27 |

## 18. Roadmap ownership, acceptance checklist and final state

Ownership is exact: RF-05 verifies the actual existing-server environment and records safe directory/identity/allocation; RF-06 owns Python/uv/lock/settings dependency proof; RF-07 owns CI topology validation; RF-08 owns Dockerfile, Compose, image, network, volume, labels and health-check implementation; RF-09 owns PostgreSQL, roles, migrations and schema readiness; RF-10–RF-22 own domain runtime services/adapters; RF-23 owns application/API/worker/scheduler wiring; RF-24 owns synthetic E2E; RF-25 owns security/least-privilege/secret verification; RF-26 owns observability, retention, backup, restore and recovery; RF-27 owns actual existing-server deployment and environment-record update; RF-28 owns deployed regression/failure drills; RF-29 owns the operator acceptance pack; RF-30 owns final evidence handoff. All implementation and proof gaps have an owner.

Acceptance checklist: exactly 7 filesystem boundaries, exactly 9 service rows, exactly 4 endpoint rows, exactly 24 environment-record rows and exactly 20 failure/recovery rows are present. All candidate values are unreserved or pending where required; no actual host allocation, current port selection/free-port claim, runtime/config/secrets/Compose/DB implementation, provider call or credentials exposure occurred. No public API bind, PostgreSQL host mapping, external network/volume, `container_name`, broker, SQLite authoritative path, auto-migration or live provider enablement is authorized.

RF-04-01 is accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`; RF-04-02 through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`; RF-04-03 at `37785e2cde19b80ba69edd23d07d6b38949dc0cb`; RF-04-04 at `39f65b3f2de9668be188aec6f16b777d04f23135`. This is the RF-04 fifth artifact. RF-04 remains active and not closed; RF-05 remains not started; `PRODUCTION_READY` is not claimed. Final target is `READY_FOR_OPERATOR_ACCEPTANCE`.

RF04_RUNTIME_TOPOLOGY_AND_ENVIRONMENT_RECORD_CANDIDATE_REPOSITORY_CONTENT_COMPLETE — PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE

RF04_RUNTIME_TOPOLOGY_AND_ENVIRONMENT_RECORD_CANDIDATE_PUBLISHED
