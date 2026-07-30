# Container and Compose Foundation Closure

## Metadata

- Version: `1.0`
- Date: `2026-07-27`
- Technical ID: `RF-08-04-CONTAINER-AND-COMPOSE-FOUNDATION-CLOSURE-20260727`
- Base SHA: `243849bbf724b7bd301b685573f9664290783605`
- Expected publication subject: `docs(rf08): close container compose foundation`
- Module 14 phase: `AUTONOMOUS_RUNTIME_COMPLETION`
- Module 14 target: `SYNTHETIC_AND_OPERATOR_ACCEPTANCE_RUNTIME`
- Boundary: `READY_FOR_OPERATOR_ACCEPTANCE`
- Status: `PUBLISHED_FOR_CHATGPT_REVIEW`
- Production: `NOT_PRODUCTION_READY`

Closure publication: `b1db2e7eafa0f625bd45e44436a208857ff7d48a`
Closure publication subject: `docs(rf08): close container compose foundation`
Index correction: `104e9777f298c47428fa8bdb07af109c234c4630`
Index correction subject: `docs(rf08): index closure evidence`
Accepted corrective-chain head: `104e9777f298c47428fa8bdb07af109c234c4630`

## Authority and scope

GitHub `main` is the sole source of truth. ChatGPT independently accepted the prerequisite RF-08 implementation and RF-08-03 bootstrap evidence before issuing this closure task. The CLI publishes closure evidence but does not self-accept it. This task is documentation and governance closure only; no implementation or runtime mutation belongs to it.

## Accepted prerequisite chain

- `RF-08-01-CONTAINER-COMPOSE-FOUNDATION-READ-ONLY-PREFLIGHT-20260726` — accepted read-only preflight.
- `RF-08-02-APPLICATION-IMAGE-AND-COMPOSE-CONFIGURATION-SKELETON-20260727` — original implementation task.
- `RF-08-02-CORRECTIVE-01-RESUME-VALIDATION-AND-PUBLICATION-20260727` — blocked historical attempt caused by stale shared validation-environment selection; it is not rewritten as accepted.
- `RF-08-02-CORRECTIVE-02-ISOLATED-LOCKED-VALIDATION-AND-PUBLICATION-20260727` — isolated locked validation and publication accepted at `af90b77575b3c0a1d9dda4f8cbd3f7ad5e6a73f6`.
- `RF-08-02-CORRECTIVE-03-COMPOSE-PROJECT-SCOPED-RESOURCE-NAMES-20260727` — project-scoped resource-name correction accepted at `243849bbf724b7bd301b685573f9664290783605`.
- `RF-08-03-EPHEMERAL-COMPOSE-BOOTSTRAP-RUNTIME-PROOF-20260727` — independently accepted ephemeral Compose bootstrap runtime proof.

## Repository implementation evidence

Implementation commits:

- `af90b77575b3c0a1d9dda4f8cbd3f7ad5e6a73f6` — `feat(rf08): add image and compose skeleton`.
- `243849bbf724b7bd301b685573f9664290783605` — `fix(rf08): preserve compose project scoping`.

The exact implementation files are `Dockerfile`, `.dockerignore` and `compose.yaml`.

| File | Blob | SHA-256 |
|---|---|---|
| `Dockerfile` | `39c790669467103f48f840c359b8d4079ead710d` | `cc3d68fd2e414c7a7be0a0f435a9d004f7f0adb878c212f9564a6c7afdbaeea7` |
| `.dockerignore` | `2924528d7f903ce1afb755b66f681b5f6715a2cc` | `8d07e42634f69aa7f6e343421088b59eaa0090b9d06ed65e8bd2fa12e783947d` |
| `compose.yaml` | `18203afacc2d15e1603de8b76ec82616902dfb85` | `7b8aae5c5ff56f27f38079ef858ffdd80c13af3ffb24591b4079455d0f48cc3c` |
| `uv.lock` | — | `e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6` |

The application base is `python:3.14.6-slim-bookworm@sha256:86f975aca15cf04a40b399eebede9aea7c82eae084d1f1a0a6ef6bcaae871a30`; uv is `0.11.31`; `uv.lock` is frozen. The application identity is `10001:10001`, with one application image and three future process commands. Profile behavior is fail-closed and non-default.

## Compose isolation and security evidence

The accepted project is `avito-mayak-acceptance` with exactly `mayak-api`, `mayak-worker`, `mayak-scheduler` and `mayak-postgres`, all under the explicit `runtime-foundation` profile; the default profile enables zero services. Its network is internal and project-scoped, and its volume is project-scoped. There is no `container_name`, external network or external volume. The API mapping is localhost-only; PostgreSQL has no host port. Application roots are read-only, all capabilities are dropped, `no-new-privileges` is set, tmpfs is secured, and secrets use process-specific allowlists. All provider flags are false; there is no broker and no public ingress.

The PostgreSQL image is `postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296`.

## Ephemeral bootstrap proof

The independently accepted RF-08-03 proof used application image tag `avito-mayak:243849bbf724b7bd301b685573f9664290783605` with image ID `sha256:955cffbf2be0c46a4cc96b274aa2f4b2f78a85e259bff84d058adb2aff07d73e`, platform `linux/amd64`, and PostgreSQL 18.4. It ran exactly four containers, all healthy for at least 30 continuous seconds, with zero restarts. Application containers were non-root with effective identity `10001:10001`; the accepted import proof passed. The project network was internal, volume ownership was accepted, API publication was `127.0.0.1:18085 -> 8000/tcp`, and PostgreSQL had no host port. Teardown removed all task containers, network and volume, released port 18085, removed temporary synthetic secrets, override, validation root and worktree, and left the repository unchanged. Foreign-resource impact and credential exposure were absent. SQL, migrations, Alembic and provider/business actions were not executed.

## Current server state after proof

This task's read-only recheck reconfirmed no containers for Compose project `avito-mayak-acceptance`, no project network `avito-mayak-acceptance_mayak-internal`, no project volume `avito-mayak-acceptance_postgres-data`, and port `18085` free. Runtime is stopped. The cached application image may remain; a cached image is not deployment evidence.

## Independent acceptance and closure chain

ChatGPT independently verified exact GitHub `main`, the parent chain, changed paths, closure content, implementation identities, accepted server/bootstrap evidence, no foreign-resource impact and no secret exposure. The verified chain is `243849bbf724b7bd301b685573f9664290783605` → `b1db2e7eafa0f625bd45e44436a208857ff7d48a` → `104e9777f298c47428fa8bdb07af109c234c4630`.

## Tests and validation

Inherited accepted evidence is distinct from this task's checks:

- RF-08-02 locked environment: 4511 collected, 4511 passed.
- Ruff accepted baseline: 648 diagnostics, no regression.
- mypy accepted baseline: 249 errors, no regression.
- import-linter: 3 kept, 0 broken.
- Repository integrity and lock verification: PASS.
- Docker build and network-disabled import proof: PASS.
- Compose static/rendered validation: PASS.
- RF-08-03 lifecycle proof: PASS.

This closure task is documentation-only and does not rerun the complete suite.

## Security and secret handling

No real secret entered Git. No secret values, hashes or fragments are in evidence. Temporary synthetic secret files were outside Git and removed. Project deploy-key contents were never read. No `.env` runtime authority, raw provider payload or production personal data was used.

## Foreign-resource non-impact

No foreign container, network, volume, database or listener changed. No global prune and no Nginx, firewall, DNS or certificate change occurred. Only task-owned ephemeral resources were created and removed during RF-08-03.

## Explicit non-claims and deferred ownership

This closure does not claim API HTTP readiness, durable worker readiness, scheduler business readiness, an application DB role, a migration DB role, SQLAlchemy/Psycopg lifecycle, Alembic, migration from zero, current-head proof, a physical application schema, DB-backed domain runtime, deployment, provider live testing or production readiness. RF-09 owns PostgreSQL roles, SQLAlchemy/Psycopg lifecycle, Alembic, migrations, schema-from-zero and current-head proof. Later owning steps cover DB-backed module runtime, wiring, synthetic E2E, security/privacy, observability/recovery, deployment, drills, operator acceptance and final handoff.

## Remaining RF-07 gates

RF-07 remains active only for runtime-dependent gates. PostgreSQL integration and migration gates depend on RF-09; synthetic E2E depends on RF-24. This does not reopen accepted RF-07 foundation work.

## Changed-path inventory

Exactly these six paths are authorized:

1. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/CONTAINER_AND_COMPOSE_FOUNDATION_CLOSURE_v1.0.md`
2. `docs/00-governance/CURRENT_STATE.md`
3. `docs/00-governance/ROADMAP.md`
4. `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`
5. `docs/MANIFEST.md`
6. `docs/04-modules/README.md`

## Rollback

Before publication, rollback is deleting the new closure file, restoring the five byte-exact preimages, removing task caches and proving a clean worktree at the expected base. After publication, correction requires a separately authorized forward commit. Git history is not rewritten.

## Closure verdict

`RF08_CONTAINER_COMPOSE_FOUNDATION_INDEPENDENTLY_ACCEPTED_THROUGH_104E9777`

## RF-08 corrective: non-root file-backed secret delivery

- Technical-ID: `RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01`.
- Execution mode: `REPAIR_SHARED_COMPOSE_SECRET_OWNERSHIP_AND_PROVE_NONROOT_BOOTSTRAP`.
- The previous single-source bootstrap assumption failed because PostgreSQL uses the pinned-image process identity `999:999`, while the Mayak bootstrap, migration and application consumers use `10001:10001`. A single `0400` host file cannot serve both owners.
- The corrective model uses separate physical files for the same logical PostgreSQL bootstrap credential: `mayak_postgres_bootstrap_password_postgres` for `999:999` and `mayak_postgres_bootstrap_password_runtime` for `10001:10001`. Application, migration and session files are runtime-owned `10001:10001` files. Secret files are `0400`; the secret root is `0700`; the production documentation boundary remains `/etc/avito-mayak/secrets/` and no production credential placement was performed.
- Preparation utility: `scripts/runtime/prepare_file_secrets.py`. It generates the logical bootstrap copies in one staged operation, writes with CSPRNG material, validates ownership/mode, rejects symlinks and unsafe roots, preserves unrelated files, supports explicit rotation, and exports no values, digests or traceback.
- Compose uses distinct file-backed sources with stable in-container targets. Runtime consumers remain `10001:10001`, PostgreSQL remains the pinned PostgreSQL 18 image, the network remains internal, and PostgreSQL remains unpublished to the host.
- Safe protocol helper: `scripts/runtime/safe_compose_bootstrap.py`; its allowlisted stages and classifications emit schema-limited JSON only. Runtime proof used task root `/opt/avito-mayak-runtime/rf08-secret-delivery/RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01/secrets`, exact Compose project `avito-mayak-rf08-secret-delivery`, and synthetic credentials only.
- Runtime evidence: Compose config passed; PostgreSQL image process identity `999:999` read only its target; intended runtime consumers read their targets as `10001:10001`; cross-consumer denial passed; PostgreSQL became healthy; bootstrap passed; migration current head was `RF09_FINALIZE`; authenticated application connection passed; restart bootstrap/migration remained idempotent; task-only rotation recreated the task volume, replaced the complete physical set, and passed bootstrap, migration and application connection again.
- Cleanup is required after review and covers only the exact task project resources and acceptance secret root. RF-11 remains blocked pending restoration onto corrected main; RF-12 and RF-11 files are outside this change.
- Status: `PUBLISHED_FOR_CHATGPT_REVIEW`. This corrective evidence is not an acceptance, operator-acceptance or production-readiness claim.

## RF-08 crash-safe generation corrective — 2026-07-29

- Technical-ID: `RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01`.
- The earlier corrective represented by `f0423111ddd0ce74892f85b36e35828f9825905d` is rejected for flat-file, non-crash-consistent activation: lazy snapshots, destructive rollback, lost ownership, no on-disk manifest validation and no bootstrap-copy comparison.
- The current implementation uses immutable complete generations under `sets/<generation-id>/`, a managed relative `active` pointer, safe on-disk manifest validation, constant-time bootstrap-copy comparison, temporary-sibling plus `os.replace` activation, fsync, recovery, retired-generation cleanup and acceptance-only failpoints. No active-generation file is replaced in place.
- The orchestrator owns stage transitions and quarantines child output in private mode-0600 files; it emits one allowlisted JSON record and cannot report caller-asserted success.
- The application image is resolved before any Compose service creation. Exact base inputs were unchanged; the expected image was explicitly built/reused only after source, revision, lock identity, platform, non-root user, safe environment and dependency-import provenance checks. Subsequent service creation uses supported `--no-build` semantics; Compose 2.30.0 one-shot `run` has no such option and is permitted only after the image gate.
- The authoritative A/B/C/D protocol passed with parsed migration head `RF09_FINALIZE`, real candidate-B authentication failure, rollback and from-zero C proof, abrupt child exit `70`, recovery, zero task resources and unchanged foreign snapshots. No raw build output or observable secret was exported.
- Focused evidence for the rejected publication is historical only. The current corrective must derive these fields from executed commands and validated local state; it does not inherit the earlier hardcoded evidence.
- Limitation: the expected-base application image lacks `mayak.runtime.api`, `mayak.runtime.worker` and `mayak.runtime.scheduler`. Those entrypoints are an RF-23 boundary and were not added here; no future process readiness or full runtime deployment is required or claimed. No independent acceptance, operator acceptance or production-readiness claim is made.
- Status: `PUBLISHED_FOR_CHATGPT_REVIEW`; RF-11 and RF-12 remain unchanged.

## RF-08 corrective publication — deterministic stale-resource preflight

- Technical-ID: `RF-08-CORRECTIVE-NONROOT-FILE-SECRET-DELIVERY-20260729-01`.
- The authoritative transcript contains exactly 57 unique ordered stages. Every stage requires an executed typed operation, semantic oracle and safe evidence; only `ProtocolTranscript.execute` appends entries.
- Before generation A, `TASK_RESOURCE_PREFLIGHT` verifies complete project-owned labels for exact task PostgreSQL resources, removes only exact stale task resources, and classifies an unlabeled or foreign collision as `STOP_FOREIGN_RESOURCE`.
- Exact CPython `3.14.6`, uv `0.11.31` and frozen dev sync were used. The complete A/restart-A/B/rollback-A/from-zero-C/D/recovery/cleanup/foreign protocol reran successfully after the corrective source change.
- Evidence: `docs/07-quality/evidence/RF08_AUTHORITATIVE_SECRET_LIFECYCLE_PROOF_v1.json`; verdict `PUBLISHED_FOR_CHATGPT_REVIEW`. RF-11 remains preserved; RF-12 and RF-23 remain unstarted; no independent acceptance, operator readiness or `PRODUCTION_READY` claim is made.

## RF-08 public-bootstrap invariant diagnosis — 2026-07-30

- Stage 55 now uses the accepted `mayak.persistence.bootstrap.bootstrap_database()` public API through `scripts/runtime/rf09_public_bootstrap_adapter.py`; RF-09 CLI class-only output is not diagnostic authority.
- The adapter uses an exact redacted invariant allowlist, a fail-closed static operation observer and one bounded JSON object while preserving RF-09 source and migration semantics.
- Proven RF-08 causes were task-owned adapter bind readability for UID `10001:10001`, stage-specific post-recovery parsing and JSON-safe cleanup evidence. The complete 57-stage execution passed stages 55–57 and foreign equality.
- Evidence was independently verified at `docs/07-quality/evidence/RF08_AUTHORITATIVE_SECRET_LIFECYCLE_PROOF_v1.json`. Status: `PUBLISHED_FOR_CHATGPT_REVIEW`; no independent acceptance or production-readiness claim is made.

## Historical next gate

RF-09 was the historical next gate at the time of the prior closure. This corrective does not start RF-11, RF-12 or RF-23 and does not alter their implementation boundaries.

## RF-08 typed foreign-equality corrective — 2026-07-30

- Preserved Docker-native exact-base BuildKit COPY evidence produced 167 effective files with no generated Python artifacts.
- Raw stage-57 `docker ps` hashing was replaced by independently recomputed typed `ForeignResourceSnapshotV2` records, exact ownership classes, structural/runtime delta classification and task-scoped mutation audit evidence.
- The isolated gate, complete ordered 57-stage protocol and independent stage-55/56/57 verifier passed; task resources and private artifacts were zero after cleanup, and `apm-postgres` was observed and untouched.
- Status: `PUBLISHED_FOR_CHATGPT_REVIEW`; this is not independent acceptance, operator readiness or production readiness.

## RF-08 observed cleanup and foreign recomputation corrective — 2026-07-30

- The e547 candidate remained published but independently unaccepted; the first continuation attempt was not published because its validation toolchain and Docker identity source were incomplete.
- Exact CPython 3.14.6, uv 0.11.31 and frozen development dependencies were validated. Optional Docker `.ID` is not used. Local Unix endpoint identity is derived from socket metadata, SO_PEERCRED/process observations, host boot identity and safe Docker server-version metadata; only hashes and safe version fields are persisted.
- Stage-56 cleanup and stage-57 foreign equality fields are derived from immutable typed observations and mutation records. Producer and independent collectors recompute canonical safe records and the verifier independently reconstructs the verdict. The exact 57-stage protocol and committed evidence verifier passed; summary and safe-record tamper controls rejected.
- Docker-native image-input identity remains unchanged. RF-11 remains preserved and unaccepted; RF-12 and RF-23 remain unstarted. Status is `PUBLISHED_FOR_CHATGPT_REVIEW`; this does not claim independent acceptance, operator readiness or production readiness.
