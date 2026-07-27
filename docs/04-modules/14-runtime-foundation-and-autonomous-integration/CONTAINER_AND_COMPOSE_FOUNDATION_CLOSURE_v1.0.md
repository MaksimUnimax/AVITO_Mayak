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
- Status: `PUBLISHED_PENDING_ACCEPTANCE`
- Production: `NOT_PRODUCTION_READY`

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

`RF08_REPOSITORY_AND_BOOTSTRAP_EVIDENCE_COMPLETE_CLOSURE_PUBLISHED_PENDING_ACCEPTANCE`

## Next gate

Independent ChatGPT verification is required. RF-09 is next but not started and remains blocked until independent acceptance of this RF-08 closure commit. The CLI does not choose or start RF-09.
