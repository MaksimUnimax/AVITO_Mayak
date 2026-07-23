# Configuration and Secrets Boundary

Version: 1.0
Status: RF-04_ACTIVE_SIXTH_ARTIFACT_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE
Date: 2026-07-23
Module: 14-runtime-foundation-and-autonomous-integration
Roadmap step: RF-04
Technical-ID: RF-04-06-CONFIGURATION-AND-SECRETS-BOUNDARY-20260723
Source branch: main
Source base SHA: 9062d613d64ded16c9758ea33ae7cfe04c267990
RF-04-01 accepted chain head: 2edfbb96c7438dae6bb6f3890cfe007d4467b6ca
RF-04-02 accepted chain head: 710f965a66488f99b4c3cc9cf9f44bef54c7434a
RF-04-03 accepted SHA: 37785e2cde19b80ba69edd23d07d6b38949dc0cb
RF-04-04 accepted SHA: 39f65b3f2de9668be188aec6f16b777d04f23135
RF-04-05 accepted chain head: 9062d613d64ded16c9758ea33ae7cfe04c267990
Runtime mutation: none
Secret creation: none
Provider calls: none
Production verdict: NOT_CLAIMED
Final target: READY_FOR_OPERATOR_ACCEPTANCE

## 1. Authority and scope

GitHub `main` is the sole source of truth. This artifact is design/documentation only: it defines the boundary for subsequent implementation of Pydantic Settings, Compose secrets, API, worker, scheduler, migrations, provider adapters, readiness and deployment. No setting implementation exists by authority of this task; no secret is created, read or validated; no runtime path is created; and no provider call is performed.

Pydantic Settings is the mandatory future implementation. Non-secret configuration and secret material are separate. Secrets remain outside Git. RF-04 remains active; RF-05 has not started. Public production launch is blocked by Module 14, and this artifact makes no `PRODUCTION_READY` claim. This document does not create Python settings, `.env.example`, Docker/Compose, secret files, passwords or keys, and does not select a host port.

## 2. Current repository implementation state

| exact path or class | current state | evidence basis | interpretation | future RF owner |
|---|---|---|---|---|
| `src/mayak/runtime/settings.py` | NOT_PRESENT | tracked-tree inventory | no settings implementation | RF-06 |
| `src/mayak/runtime/config.py` | NOT_PRESENT | tracked-tree inventory | no runtime config implementation | RF-06 |
| `src/mayak/runtime/` | NOT_PRESENT | tracked-tree inventory | runtime package path is not implemented | RF-06/RF-08 |
| `.env` | NOT_TRACKED | tracked-file inventory | no repository dotenv authority | RF-06 |
| `.env.example` | NOT_TRACKED | tracked-file inventory | no dotenv template created | RF-06 |
| `compose.yaml` | NOT_PRESENT | tracked-tree inventory | no Compose implementation | RF-08 |
| `Dockerfile` | NOT_PRESENT | tracked-tree inventory | no image implementation | RF-08 |
| `/run/secrets/` as non-repository runtime path | NOT_OBSERVED_BY_THIS_TASK | design path only; no host inspection | future container secret root | RF-08 |
| `/etc/avito-mayak/secrets/` as non-repository host path | NOT_OBSERVED_BY_THIS_TASK | design path only; no host inspection | future host secret root | RF-05/RF-08 |
| `src/mayak/platform/config.py` | PRESENT | tracked-tree inventory | existing contract primitive, not settings loading | RF-06 |
| `src/mayak/contracts/configuration.py` | PRESENT | tracked-tree inventory | existing framework-neutral contract primitive | RF-06 |
| `src/mayak/platform/redaction.py` | PRESENT | tracked-tree inventory | existing redaction primitive | RF-25 |
| `src/mayak/platform/readiness.py` | PRESENT | tracked-tree inventory | existing readiness primitive | RF-23 |
| `pyproject.toml` | PRESENT, unchanged | tracked-tree inventory and dependency read | declares Pydantic/Pydantic Settings and provider-adjacent libraries | RF-06 |
| `uv.lock` | PRESENT, unchanged | tracked-tree inventory and dependency read | locked dependency evidence | RF-06 |

The current configuration-related source paths are contract primitives only. No current tracked file is a secret value. Filename inventory is not a security scan; secret leakage remains an RF-25 concern.

## 3. Configuration authority and precedence

For a deployed runtime, authority is ordered as follows:

1. accepted immutable build identity;
2. explicit process environment for non-secret external keys;
3. Pydantic Settings secret directory `/run/secrets`;
4. safe code defaults only for values explicitly marked defaultable;
5. no `.env` runtime loading.

For automated tests the order is: explicit in-memory constructor/test fixture values; temporary test-only environment; temporary isolated secrets directory; safe defaults. Command-line secret values are forbidden. Secret values in ordinary environment variables are forbidden for deployed acceptance. `.env` value files outside the test harness are forbidden, and a config file inside an image cannot be a source of real secrets. DB/provider payloads are not configuration authority.

The runtime cannot silently fall back between profiles. Unknown or contradictory `MAYAK_` keys cause validation failure. Configuration is loaded once per process start; there is no per-request environment reread. A process reports only safe config identity, never values.

## 4. Settings object and external-key model

The future implementation has one immutable typed root settings object with nested typed groups named exactly `build`, `runtime`, `api`, `database`, `worker`, `scheduler`, `http`, `session`, `providers`, `observability`, `retention`, and `backup`. External keys have the exact `MAYAK_` prefix and uppercase snake-case form; internal Python fields use lower snake-case. External key names and secret file names are stable deployment contracts.

Structured and test inputs have `extra="forbid"` semantics. The implementation explicitly checks unknown `MAYAK_` environment keys, uses strict types, does not use implicit comma parsing for security-sensitive lists, parses applicable URLs as typed URLs, and stores durations as bounded integer seconds. Monetary settings are not introduced here. Core settings do not contain provider SDK types. The object is immutable after construction. Raw secrets must never occur in `repr`, model dumps, validation errors or diagnostics.

## 5. Runtime profiles and process scope

| profile | purpose | synthetic identity | live providers | public ingress | production data | allowed authority |
|---|---|---|---|---|---|---|
| `test` | unit/contract/integration tests | synthetic-only | no network provider calls | none | no | fixture values, temporary environment and isolated secrets |
| `synthetic_acceptance` | target automatic acceptance profile | permitted | fake providers permitted; live providers disabled | localhost-only | no | accepted non-secret settings and temporary safe acceptance secrets |
| `operator_acceptance` | documented operator acceptance | may be used only for documented acceptance procedure | individual live provider profiles require explicit operator action and credentials; unavailable providers disabled | no public ingress; localhost-only | no | accepted settings plus explicit operator credential action |
| `production` | future separately gated launch | forbidden | no automatic enablement | not approved | not approved | separate future production gate; blocked by Module 14 |

The exact profile selector is `MAYAK_RUNTIME_PROFILE`. A profile is not inferred from secret presence, process kind, image metadata or provider response.

## 6. Canonical non-secret configuration catalog

All rows are non-secret; every `secret?` value is `no`. Values marked candidate are design candidates, not current host observations or selected allocations. All timeout, poll, lease, batch and response values are positive and bounded. Worker lease exceeds worker poll interval. Every provider enabled flag defaults `false`.

| # | external key | group | type | required/default | validation | consumers | secret? | future implementation owner |
|---:|---|---|---|---|---|---|---|---|
| 1 | `MAYAK_ENVIRONMENT_ID` | runtime | string | required | stable nonempty identity | all | no | RF-06 |
| 2 | `MAYAK_RUNTIME_PROFILE` | runtime | enum | required | `test`, `synthetic_acceptance`, `operator_acceptance`, `production` | all | no | RF-06 |
| 3 | `MAYAK_SOURCE_SHA` | build | SHA string | required | accepted commit identity | all | no | RF-06 |
| 4 | `MAYAK_LOCK_IDENTITY` | build | string | required | accepted lock identity | all | no | RF-06 |
| 5 | `MAYAK_IMAGE_DIGEST` | build | digest string | required | immutable image identity | all | no | RF-06 |
| 6 | `MAYAK_PROCESS_KIND` | build | enum | required | exact process kind | one process | no | RF-06 |
| 7 | `MAYAK_LOG_LEVEL` | observability | enum | defaultable | bounded approved level | all | no | RF-06 |
| 8 | `MAYAK_LOG_FORMAT` | observability | enum | default `json` | exactly `json` in baseline | all | no | RF-06 |
| 9 | `MAYAK_API_BIND_HOST` | api | string | default `127.0.0.1` | deployed acceptance rejects any other value | api | no | RF-06/RF-23 |
| 10 | `MAYAK_API_INTERNAL_PORT` | api | integer | default `8000` | positive bounded container port | api | no | RF-06/RF-08 |
| 11 | `MAYAK_API_HOST_PORT` | api | integer/disabled | defaultable | if mapping active, `18080–18099`; no current port selected | Compose/operator | no | RF-05/RF-08 |
| 12 | `MAYAK_DATABASE_HOST` | database | hostname | candidate `mayak-postgres` | internal acceptance only; no external DB | all DB clients | no | RF-06/RF-09 |
| 13 | `MAYAK_DATABASE_PORT` | database | integer | default `5432` | internal network only; no PostgreSQL host port | all DB clients | no | RF-06/RF-09 |
| 14 | `MAYAK_DATABASE_NAME` | database | string | candidate `avito_mayak` | bounded nonempty name | DB clients | no | RF-06/RF-09 |
| 15 | `MAYAK_DATABASE_APPLICATION_USER` | database | string | required | differs from migration user | api/worker/scheduler | no | RF-06/RF-09 |
| 16 | `MAYAK_DATABASE_MIGRATION_USER` | database | string | required | differs from application user | migrate | no | RF-06/RF-09 |
| 17 | `MAYAK_DATABASE_SSLMODE` | database | enum | internal candidate `disable` | public/external DB forbidden | DB clients | no | RF-06/RF-09 |
| 18 | `MAYAK_DATABASE_CONNECT_TIMEOUT_SECONDS` | database | bounded integer | defaultable | positive bounded duration | DB clients | no | RF-06/RF-09 |
| 19 | `MAYAK_WORKER_POLL_INTERVAL_SECONDS` | worker | bounded integer | defaultable | positive; less than lease | worker | no | RF-06/RF-23 |
| 20 | `MAYAK_WORKER_LEASE_SECONDS` | worker | bounded integer | defaultable | positive and greater than poll | worker | no | RF-06/RF-23 |
| 21 | `MAYAK_WORKER_BATCH_SIZE` | worker | bounded integer | defaultable | positive bounded batch | worker | no | RF-06/RF-23 |
| 22 | `MAYAK_SCHEDULER_POLL_INTERVAL_SECONDS` | scheduler | bounded integer | defaultable | positive bounded duration | scheduler | no | RF-06/RF-23 |
| 23 | `MAYAK_OUTBOX_BATCH_SIZE` | worker | bounded integer | defaultable | positive bounded batch | worker/scheduler | no | RF-06/RF-23 |
| 24 | `MAYAK_HTTP_CONNECT_TIMEOUT_SECONDS` | http | bounded integer | defaultable | positive bounded duration | adapters | no | RF-06/RF-10–22 |
| 25 | `MAYAK_HTTP_READ_TIMEOUT_SECONDS` | http | bounded integer | defaultable | positive bounded duration | adapters | no | RF-06/RF-10–22 |
| 26 | `MAYAK_HTTP_WRITE_TIMEOUT_SECONDS` | http | bounded integer | defaultable | positive bounded duration | adapters | no | RF-06/RF-10–22 |
| 27 | `MAYAK_HTTP_POOL_TIMEOUT_SECONDS` | http | bounded integer | defaultable | positive bounded duration | adapters | no | RF-06/RF-10–22 |
| 28 | `MAYAK_HTTP_MAX_RESPONSE_BYTES` | http | bounded integer | required/defaultable | positive bounded size | adapters | no | RF-06/RF-10–22 |
| 29 | `MAYAK_SESSION_MAX_AGE_SECONDS` | session | bounded integer | defaultable | acceptance `<= 86400` | API/Identity | no | RF-06/RF-11/RF-23 |
| 30 | `MAYAK_SYNTHETIC_IDENTITY_ENABLED` | session | boolean | default `false` | production `true` is invalid | Identity | no | RF-06/RF-11/RF-24 |
| 31 | `MAYAK_AVITO_LIVE_ENABLED` | providers | boolean | default `false` | operator gate required | Avito adapter | no | RF-14 |
| 32 | `MAYAK_TELEGRAM_ENABLED` | providers | boolean | default `false` | missing token non-core blocker | Telegram adapter | no | RF-18 |
| 33 | `MAYAK_TELEGRAM_UPDATE_MODE` | providers | enum | default `disabled` | `disabled`, `webhook`, `long_polling_test` | Telegram adapter | no | RF-18 |
| 34 | `MAYAK_MAX_ENABLED` | providers | boolean | default `false` | explicit enable only | MAX adapter | no | RF-19 |
| 35 | `MAYAK_MAX_UPDATE_MODE` | providers | enum | default `disabled` | `disabled`, `webhook`, `long_polling_test` | MAX adapter | no | RF-19 |
| 36 | `MAYAK_YOOKASSA_ENABLED` | providers | boolean | default `false` | explicit enable only | YooKassa adapter | no | RF-12 |
| 37 | `MAYAK_EGRESS_AGENT_ENABLED` | providers | boolean | default `false` | explicit enable only | Egress adapter | no | RF-16 |
| 38 | `MAYAK_OTEL_ENABLED` | observability | boolean | default `false` | telemetry optional | all | no | RF-26 |
| 39 | `MAYAK_OTEL_EXPORTER_ENDPOINT` | observability | typed URL/disabled | defaultable | endpoint only when enabled | telemetry | no | RF-26 |
| 40 | `MAYAK_BACKUP_ROOT` | backup | path | candidate `/var/backups/avito-mayak` | project-owned future path | backup | no | RF-26/RF-27 |
| 41 | `MAYAK_BACKUP_RETENTION_DAYS` | retention | bounded integer | default `7` | positive bounded retention | backup | no | RF-26 |
| 42 | `MAYAK_SECRETS_DIR` | runtime | path | deployed `/run/secrets` | individual file root only | secret loader | no | RF-06/RF-08 |

No 43rd key is defined. Long polling is test/development-only where accepted by the provider module. External telemetry is optional.

## 7. Canonical secret catalog

| # | secret field | secret file name | mandatory class | consumers | enabled-condition | allowed generation | rotation owner | forbidden exposure |
|---:|---|---|---|---|---|---|---|---|
| 1 | `postgres_bootstrap_password` | `mayak_postgres_bootstrap_password` | core provisioning | postgres | bootstrap only | safe acceptance generation | RF-05/RF-09 | Git, logs, env, command line, API |
| 2 | `database_application_password` | `mayak_database_application_password` | core runtime | api/worker/scheduler | core DB runtime | safe acceptance generation | RF-05/RF-09 | Git, logs, env, command line, migration |
| 3 | `database_migration_password` | `mayak_database_migration_password` | core migration | migrate | explicit migration | safe acceptance generation | RF-05/RF-09 | Git, logs, env, normal processes |
| 4 | `session_signing_key` | `mayak_session_signing_key` | API session mandatory | api | API session issuance/validation | safe acceptance generation | RF-05/RF-11 | Git, logs, env, cookies, diagnostics |
| 5 | `telegram_bot_token` | `mayak_telegram_bot_token` | provider optional | Telegram adapter | Telegram enabled | operator-provided only | RF-18/RF-29 | all unrelated processes |
| 6 | `max_bot_token` | `mayak_max_bot_token` | provider optional | MAX adapter | MAX enabled | operator-provided only | RF-19/RF-29 | all unrelated processes |
| 7 | `max_webhook_secret` | `mayak_max_webhook_secret` | provider optional | MAX adapter | MAX webhook enabled | operator-provided only | RF-19/RF-29 | all unrelated processes |
| 8 | `avito_live_credential` | `mayak_avito_live_credential` | provider optional | Avito adapter | Avito live enabled | operator-provided only | RF-14/RF-29 | all unrelated processes |
| 9 | `yookassa_secret_key` | `mayak_yookassa_secret_key` | provider optional | YooKassa adapter | YooKassa enabled | operator-provided only | RF-12/RF-29 | all unrelated processes |
| 10 | `egress_agent_shared_secret` | `mayak_egress_agent_shared_secret` | provider optional | Egress adapter | Egress enabled | operator-provided only | RF-16/RF-29 | all unrelated processes |

The first four are core or process-mandatory according to consumers. Provider and egress secrets are optional while disabled; no provider secret can make core readiness fail while its provider is disabled. Safe acceptance generation is permitted only for the first four and belongs to exact future RF-05/RF-08/RF-09 tasks. Generated values are never printed. There are no literal secret examples. No secret is committed to Git, reused across providers, or automatically enabled by presence. Telegram's token cannot be reused as a generic app/session secret. Application and migration DB passwords are distinct.

The bootstrap password is not mounted into API/worker/scheduler. The migration password is not mounted into normal API/worker/scheduler. The application password is not mounted into migration-only process where avoidable. Missing optional provider credentials produce `PROVIDER_DISABLED_CONTINUE` while disabled.

## 8. Secret files, names and mounts

The host root candidate is `/etc/avito-mayak/secrets`; the container root is `/run/secrets`. Only individual regular files are accepted. Symlinks, directories, devices, FIFOs and sockets are forbidden. Files are mode `0400` or `0600`, have a least-privilege owner, and are read-only bind/Compose secret mounts. Maximum accepted size is 16384 bytes. Empty content after trimming one terminal LF or CRLF is invalid. At most one terminal newline is trimmed; other internal whitespace is preserved. Textual provider secrets are UTF-8. A binary secret format is not introduced in the baseline.

Path and presence may be reported. Size may be reported only as a bounded class, never as an exact content-derived fingerprint. Value, hash, prefix, suffix and length are not logged. A process must not enumerate or read secrets it does not consume. Secret filenames are operational metadata, not values. Wildcard secret mounts, command-line secrets, Compose labels, image layers, immutable release directories, deployed environment variables and `.env` fallback are forbidden.

| process | allowed secret files |
|---|---|
| `mayak-postgres` | `mayak_postgres_bootstrap_password` |
| `mayak-migrate` | `mayak_database_migration_password` |
| `mayak-api` | `mayak_database_application_password`, `mayak_session_signing_key` |
| `mayak-worker` | `mayak_database_application_password`; enabled provider/egress files only |
| `mayak-scheduler` | `mayak_database_application_password` |
| `mayak-backup` | `none` until exact future backup/DB scope is accepted |
| `mayak-restore-check` | `none` until exact future restore-check scope is accepted |

Provider secrets may be mounted only into the process that executes the relevant provider adapter and only when enabled by the exact future implementation.

## 9. Database credential and privilege separation

PostgreSQL bootstrap, migration and application identities are separate. The migration role owns DDL/schema migration; the application role has no DDL authority. API, worker and scheduler use the application role only; the explicit migration process uses the migration role. The bootstrap secret is one-time/provisioning scope. There is no PostgreSQL host port, no foreign DB and no foreign database dependency.

The DSN is assembled in memory and never shown in logs. Diagnostics expose only host class, database name, role class and connection state. Passwords never occur in exception output; SQLAlchemy and Psycopg errors require sanitization. Backup/restore credentials receive an exact future least-privilege design and are not inferred as application authority. Rotation/revocation requires readiness handling and connection-pool restart handling.

## 10. Provider credential and enablement boundaries

| provider | enable key | required secret files | disabled state | missing credential state | live-call gate | ambiguity rule | future RF owner |
|---|---|---|---|---|---|---|---|
| Avito | `MAYAK_AVITO_LIVE_ENABLED` | `mayak_avito_live_credential` | disabled by default | `BLOCKED_CREDENTIAL` only if enabled | explicit operator proof; no startup probe | reconcile-first; no blind replay | RF-14/RF-29 |
| Telegram | `MAYAK_TELEGRAM_ENABLED` | `mayak_telegram_bot_token` | disabled by default | `BLOCKED_CREDENTIAL` only if enabled | explicit provider operation | unknown effect is reconciliation-first | RF-18/RF-29 |
| MAX | `MAYAK_MAX_ENABLED` | `mayak_max_bot_token`, `mayak_max_webhook_secret` when webhook | disabled by default | `BLOCKED_CREDENTIAL` only if enabled | explicit operator action | eligibility/token absence is non-blocking | RF-19/RF-29 |
| YooKassa | `MAYAK_YOOKASSA_ENABLED` | `yookassa_secret_key` | disabled by default | `BLOCKED_CREDENTIAL` only if enabled | explicit payment proof | payment evidence cannot grant entitlement directly | RF-12/RF-29 |
| Windows Egress Agent | `MAYAK_EGRESS_AGENT_ENABLED` | `egress_agent_shared_secret` | disabled by default | `BLOCKED_CREDENTIAL` only if enabled | explicit configured agent | no foreign proxy fallback | RF-16/RF-29 |

Every enabled key defaults false. Missing an optional secret while disabled is `PROVIDER_DISABLED_CONTINUE`; enabling without its credential is provider-specific `BLOCKED_CREDENTIAL` and performs no live call. Core may remain ready when a provider is not mandatory for the current operation. Fake/synthetic providers require no real secret. There is no startup live-provider probe, no automatic enablement from secret presence, and no provider response treated as proof of human read. Telegram is the primary practical channel but a missing token is not a core blocker. Windows host absence is non-blocking. Operator acceptance remains required.

## 11. Sessions, signing material and synthetic identity

`account_id` remains authoritative. There is no phone/password authentication; phone is not mandatory. Automatic account merge is forbidden. The session signing key is mandatory for API session issuance/validation, and acceptance session maximum age is `<= 24 hours`.

Synthetic identity is allowed only in `test`, `synthetic_acceptance` and a documented `operator_acceptance` procedure. It is forbidden in `production`; `MAYAK_SYNTHETIC_IDENTITY_ENABLED=true` in production is a validation failure. Synthetic account IDs are deterministic test fixtures, not production identities. No real provider identifier is embedded in configuration. Session cookie values are never logged.

Signing-key rotation invalidates or explicitly versions prior sessions. Exact key-version implementation is deferred to Identity runtime; silent multi-key fallback is forbidden unless separately accepted. Recovery remains verified provider relinking or an audited Admin procedure.

## 12. Validation, startup and readiness semantics

Syntax, type and profile invariant failures fail startup. A mandatory core secret missing fails startup or leaves the process not-ready before it serves or claims work. An optional provider secret missing while disabled leaves core readiness possible; an enabled provider without its secret is blocked with no live call. DB/schema mismatch and image/source/lock mismatch are not ready. API liveness is not readiness; worker and scheduler have process-local readiness. Scheduler/worker correctness does not rely on a singleton assumption. No process auto-migrates; migration is explicit one-shot. Provider calls do not occur during readiness. Telemetry failure does not change business commit semantics. Safe validation errors contain field name and error class only. Readiness never exposes a secret path beyond approved class/name metadata, and startup never silently switches profile.

| process | mandatory non-secret checks | mandatory secret checks | optional provider checks | startup behavior | readiness behavior | safe diagnostic class |
|---|---|---|---|---|---|---|
| `mayak-postgres` | process/profile/build identity | bootstrap scope if provisioning | none | fail on invalid bootstrap boundary | DB service state only | role class and state |
| `mayak-migrate` | build/profile, DB target, migration command | migration password | none | explicit one-shot; fail closed | schema current or not-ready | revision and role class |
| `mayak-api` | bind, ports, build, profile, schema | application password, session key | provider files only when enabled | fail before serving on core error | DB/schema/build/session checks | identity and redacted status |
| `mayak-worker` | process kind, leases, HTTP bounds, schema | application password | enabled adapter/egress files | fail before claiming work on core error | process-local DB/lease/config state | identity and state class |
| `mayak-scheduler` | process kind, poll bounds, schema | application password | none by default | fail before scheduling on core error | process-local DB/config state | identity and state class |
| `mayak-backup` | backup path/retention and build | none until exact scope | none | explicit operation only | project-owned backup state | path class and result class |
| `mayak-restore-check` | build, isolated target, restore procedure | none until exact scope | none | explicit isolated check only | check state, never production claim | result class |

## 13. Redaction, logs, diagnostics and evidence

Keys matching the secret catalog always redact. Case-insensitive sensitive-name patterns include `password`, `secret`, `token`, `authorization`, `cookie`, `session`, `private_key` and `credential`. Structured nested values are recursively redacted. HTTP Authorization headers and cookies are never logged. Sensitive query parameters are redacted. Provider payloads are not logged raw. Database DSNs and exception messages are sanitized before logging or API response. Validation errors omit rejected values. Secret file contents, hashes and lengths are not logged.

Safe fields include source SHA, environment ID, process kind, migration revision and provider-disabled class. Safe diagnostics cannot return configuration dumps: `/version` contains identity only and `/diagnostics` contains redacted status only. Evidence reports contain names and procedures, never values. Production personal data and third-party analytics/tracking are forbidden.

| evidence item | safe | forbidden |
|---|---|---|
| source SHA | yes | secret-bearing build dump |
| environment ID | yes | personal data |
| process kind | yes | full environment |
| migration revision | yes | DSN |
| provider disabled class | yes | provider payload |
| secret filename | approved metadata | file content |
| secret presence class | approved bounded class | exact value/hash/length |
| redacted validation error class | yes | rejected value |
| sanitized DB connection state | yes | password/DSN |
| `/version` identity | yes | configuration dump |
| `/diagnostics` status | redacted only | token/cookie/header |
| evidence procedure | yes | credential material |
| HTTP method/status class | bounded | Authorization/cookies/payload |
| provider outcome class | bounded | raw provider response |
| retention/deletion result class | yes | personal record content |

## 14. Process and Compose distribution matrix

One application image is used for API, worker and scheduler with different commands and process kinds. Only needed settings and secrets are distributed; there is no all-secrets mount. PostgreSQL receives bootstrap scope only; migrate receives migration scope; API receives session and application DB scope; worker receives application DB and only enabled provider/egress scope; scheduler receives application DB scope and no provider token by default; backup/restore receive a future exact least-privilege scope. Settings load once at process start; baseline has no hot reload.

| process | non-secret groups | secret allowlist | provider configuration | reload model | readiness owner | implementation owner |
|---|---|---|---|---|---|---|
| `mayak-postgres` | build, runtime, database | `mayak_postgres_bootstrap_password` | none | restart/provisioning | RF-09 | RF-08/RF-09 |
| `mayak-migrate` | build, runtime, database | `mayak_database_migration_password` | none | one-shot restart | RF-09 | RF-08/RF-09 |
| `mayak-api` | build, runtime, api, database, session, http, observability | application DB and session key | disabled by default; adapter scope only when enabled | restart | RF-23 | RF-08/RF-23 |
| `mayak-worker` | build, runtime, database, worker, http, providers | application DB plus enabled provider/egress scope | exact enabled adapters only | restart | RF-23 | RF-08/RF-23 |
| `mayak-scheduler` | build, runtime, database, scheduler, observability | application DB | none by default | restart | RF-23 | RF-08/RF-23 |
| `mayak-backup` | build, runtime, database, backup, retention | future exact DB/backup scope | none | explicit restart | RF-26 | RF-08/RF-26 |
| `mayak-restore-check` | build, runtime, database, backup | future exact restore-check scope | none | explicit isolated restart | RF-26 | RF-08/RF-26 |

## 15. Rotation, reload, restart and revocation

Non-secret configuration changes require a controlled process restart. Secret rotation uses atomic file replacement outside Git; permissions and ownership are verified before restart, and partial in-place writes are forbidden. Old/new values are never placed in reports. DB password rotation preserves availability where possible and explicitly restarts connection pools. Session-key rotation follows the explicit version/invalidation procedure. Provider-token rotation disables the provider first when external-effect ambiguity exists. Revocation takes precedence over retries; unknown effect remains reconciliation-first; blind replay after credential rotation is forbidden.

Rollback means restoring a previously accepted external secret/config reference, never rewriting Git history. A failed rotation leaves the provider disabled or the process not-ready. There is no automatic fallback to a stale credential and no runtime secret-reload signal in the baseline. Exact automation belongs to RF-25/RF-27 or the owning provider RF.

## 16. Security, privacy, retention and deletion

Real production personal data is prohibited in automatic and acceptance environments. Synthetic DB records are retained for a maximum of 14 days; logs 7 days; test artifacts 30 days; backups 7 days; sessions at most 24 hours; safe provider evidence metadata 30 days. Raw provider payload is not persisted by default. Git evidence is retained without secrets. Secret values are not backups unless an exact encrypted future procedure is accepted.

This task does not authorize copying `/etc/avito-mayak/secrets` into backup artifacts. Environment destruction removes only project-owned secret files after exact ownership proof and a destructive gate. Source checkouts and worktrees are not runtime secret stores. Plaintext secrets in the database, unnecessary personal identifiers in config, marketing pixels and third-party analytics are forbidden. Privacy/legal production decisions remain a future launch gate and do not block synthetic runtime.

## 17. Failure and recovery matrix

| # | scenario | detection | startup/readiness effect | provider/core state | corrective action | rollback/recovery | safe evidence | forbidden response | future proof owner |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | expected Git base changed | fresh-main check | stop before work | unchanged | stop; ChatGPT rereads current GitHub main and reissues the task on the verified base | no repository mutation | SHA only | continue on stale base | RF-04 gate |
| 2 | unknown `MAYAK_` key | explicit key check | fail startup | core blocked | remove or accept via future contract | restore accepted key set | key name/class | ignore unknown key | RF-06 |
| 3 | invalid runtime profile | enum validation | fail startup | core blocked | use accepted profile | return to prior accepted profile | profile class | infer profile | RF-06 |
| 4 | malformed source SHA/build identity | typed identity check | not-ready | core blocked | correct accepted build metadata | restore accepted identity | identity class | serve with mismatch | RF-06/RF-07 |
| 5 | process kind mismatch | process validation | fail startup | core blocked | correct command/settings | restart correct process | process class | run wrong command | RF-06/RF-08 |
| 6 | public API bind | bind policy | fail startup | core blocked | use `127.0.0.1` | restore local-only bind | bind class | expose public ingress | RF-05/RF-08 |
| 7 | API host port outside `18080–18099` | range validation | fail startup/deployment | core blocked | select accepted future mapping | remove mapping | range class | claim a current port | RF-05/RF-08 |
| 8 | foreign/external database host configuration | host policy | not-ready | core blocked | use project-owned internal target | restore internal candidate | host class | connect foreign DB | RF-05/RF-09 |
| 9 | application and migration usernames equal | cross-field validation | fail startup | core blocked | assign distinct roles | restore accepted role mapping | role classes | grant DDL to app | RF-09 |
| 10 | invalid timeout/batch/lease bound | bounded validation | fail startup | core blocked | correct bounded values | restore accepted values | error class | coerce silently | RF-06/RF-23 |
| 11 | secrets directory missing | path check | not-ready | core blocked | provision exact future path | remove reference | path class | use `.env` fallback | RF-05/RF-08 |
| 12 | secret file is symlink/non-regular | file-type check | not-ready | affected process blocked | replace with regular file | disable affected scope | type class | follow link | RF-06/RF-08 |
| 13 | secret file permissions too broad | mode check | not-ready | affected process blocked | fix least-privilege mode | disable affected scope | mode class | read anyway | RF-05/RF-08 |
| 14 | secret file empty or oversized | bounded file check | not-ready | affected process blocked | replace operator value | keep process/provider disabled | size class | truncate or print | RF-06/RF-25 |
| 15 | mandatory core secret missing | presence check | fail/not-ready | core blocked | operator provision through future task | remain not-ready | secret name/class | generate during this task | RF-05/RF-09 |
| 16 | optional provider secret missing while provider disabled | enable/secret cross-check | core may be ready | `PROVIDER_DISABLED_CONTINUE` | leave provider disabled | no recovery needed | disabled class | block unrelated core | owning provider RF |
| 17 | provider enabled but credential missing | provider validation | provider blocked | `BLOCKED_CREDENTIAL`; core may continue | disable or operator-provide | keep disabled | provider/class | make live call | owning provider RF |
| 18 | secret present but provider disabled | explicit enable flag | no effect | provider disabled | leave disabled until operator gate | revoke external reference | enabled class | auto-enable | owning provider RF |
| 19 | synthetic identity enabled in production | profile invariant | fail startup | core blocked | disable synthetic identity | return to non-production profile | profile/flag class | serve synthetic account | RF-06/RF-11 |
| 20 | secret supplied through command line/environment in deployed acceptance | process/config audit | fail/not-ready | affected process blocked | remove value and use file mount | disable process | channel class | log/process inspection value | RF-06/RF-25 |
| 21 | redaction failure or secret-bearing validation error | redaction test | fail gate/not-ready | core blocked until fixed | sanitize implementation and evidence | disable diagnostics | error class only | expose value for debugging | RF-25 |
| 22 | source/image/lock identity mismatch | identity comparison | not-ready | core blocked | deploy matching accepted identity | restore accepted release reference | identity classes | run mismatch | RF-07/RF-27 |
| 23 | DB/schema mismatch | migration/readiness check | not-ready | core blocked | run explicit accepted migration | restore compatible schema | revision classes | auto-migrate | RF-09 |
| 24 | credential rotation/revocation during ambiguous external effect | provider outcome/reconciliation | provider disabled or not-ready | unknown effect; no blind retry | reconcile first, revoke and gate | restore accepted reference only | outcome class | blind replay | RF-25/owning RF |

## 18. Roadmap ownership, acceptance checklist and final state

RF-05 verifies actual host paths, modes, service identity, selected port and creates permitted project-owned config/secret boundaries. RF-06 implements Pydantic Settings/toolchain/dependencies and the safe schema. RF-07 verifies CI configuration checks without secrets. RF-08 implements Compose secret mounts and process distribution. RF-09 implements DB roles/credentials/migration readiness. RF-10–RF-22 implement owning runtime/provider configuration. RF-23 wires API/worker/scheduler settings and diagnostics. RF-24 proves synthetic behavior. RF-25 proves secret scan/redaction/least privilege/supply chain. RF-26 implements operability and retention. RF-27 deploys exact accepted config/secret references. RF-28 performs final drills. RF-29 documents operator credential placement/live tests. RF-30 records final evidence without values.

Acceptance checklist: 18 top-level numbered sections; 4 runtime profile rows; 42 canonical non-secret keys; 10 canonical secret rows; 7 secret-allowlist process rows; 5 provider rows; 7 startup/readiness rows; 7 process-distribution rows; 24 failure/recovery rows; one repository-content acceptance marker; one final marker.

RF-04-01 accepted through `2edfbb96c7438dae6bb6f3890cfe007d4467b6ca`.
RF-04-02 accepted through `710f965a66488f99b4c3cc9cf9f44bef54c7434a`.
RF-04-03 accepted at `37785e2cde19b80ba69edd23d07d6b38949dc0cb`.
RF-04-04 accepted at `39f65b3f2de9668be188aec6f16b777d04f23135`.
RF-04-05 accepted through `9062d613d64ded16c9758ea33ae7cfe04c267990`.

This is RF-04 sixth artifact. RF-04 remains active and not closed. RF-05 remains not started. There is no runtime implementation or mutation, no secret created/read/exposed, no provider call and no `PRODUCTION_READY` claim. Final target is `READY_FOR_OPERATOR_ACCEPTANCE`.

RF04_CONFIGURATION_AND_SECRETS_BOUNDARY_REPOSITORY_CONTENT_COMPLETE — PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE

RF04_CONFIGURATION_AND_SECRETS_BOUNDARY_PUBLISHED
