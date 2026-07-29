# PostgreSQL and Alembic Foundation Closure v1.0

Status: `PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
CHATGPT_REVIEW_REQUIRED: `YES`

## Identity and recovery

- Technical ID: `RF-09-CLOSURE-POSTGRESQL-ALEMBIC-PROOF-AND-GOVERNANCE-RECONCILIATION-20260729-01`
- Execution mode: `RECOVER_AND_COMPLETE_EXISTING_ITERATION`
- Expected base: `1c81e534611330a9e066afa25af06f72d9407300`
- RF-08 prerequisite: independently accepted through `104e9777f298c47428fa8bdb07af109c234c4630`.
- Recovery note: the first delivery was incomplete and had no terminal report. Existing M06 line wrapping, Compose quoting correction and boundary-test correction were preserved. No replacement worktree, Technical ID, closure file or worklog entry was created.

The complete RF-09 implementation/corrective chain is the existing ancestor chain from `086a55dae112f4be3241f61c7dd8abd352f72d65` through base `1c81e534611330a9e066afa25af06f72d9407300`, including: `ae37389`, `b622bea`, `9611ec4`, `4fe36ab`, `4b365f0`, `c0a1f07`, `f69fd6b`, `c69fbb3`, `b004b6c`, `e6f6134`, `ee77625`, `dfb955f`, `88e7532`, `762453e`, `1959d8f`, `5e1572d`, `1077c88`, `ffa86d2`, `9719610`, `2630c40`, `ade73da`, `fd33611`, `823712f`, `6ec141f`, `ea5efc7`, `c6350d1`, `358c390`, `ce66c08`, `92d4bd4`, `1d8906e`, `8008753`, `fb04189`, `f7abcc0`, `9d9111c`, `7228753`, `d945609`, `c2d54a5`, `663892f`, plus the preserved local RF-09 corrective changes.

## Source, migrations and model

PostgreSQL image: `postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296`.
Alembic revisions in order:

`RF09_BOOTSTRAP` → `RF09_M01` → `RF09_M02` → `RF09_M03` → `RF09_M13` → `RF09_M04` → `RF09_M05` → `RF09_M06` → `RF09_M07` → `RF09_M08` → `RF09_M09` → `RF09_M10` → `RF09_M11` → `RF09_FINALIZE`.

Head count: `1`. Current head: `RF09_FINALIZE`. The chain is contiguous and has no branch head. Physical model ownership remains in the Module 14 persistence schema modules; no domain state is written outside the migration/schema boundary.

Runtime inventory from the clean rebuild: 52 tables, 170 indexes, 698 constraints, 72 foreign keys. Three deferred-origin foreign keys were finalized and validated (`convalidated=t`, `condeferrable=f`): beacon current-revision, scan parser-outcome, and egress work-item references. Unvalidated constraint count: `0`.

## PostgreSQL proof

Project: `avito-mayak-acceptance-rf09-closure-20260729-01`. The network and volume were project-scoped and labeled project-owned. PostgreSQL exposed `5432/tcp` internally with no published host port (`PublishedPort=0`, `Ports={"5432/tcp":null}`). API, worker and scheduler were not started; live providers were disabled and never called.

- Synthetic generated credentials were stored outside Git under the task-owned runtime root, with no values in logs or this artifact; all four files were `0600` and owned by the task service UID for non-root secret consumption.
- Application role `mayak_application` and migration role `mayak_migration` are distinct, login-capable, non-superuser, non-createdb, non-createrole, no-inherit, no-replication, no-bypassrls roles. Application has schema usage without create; migration owns/creates the `mayak` schema.
- Effective migration search path is public-only; current role/session proof returned `"$user", public` for the bootstrap inspection and the Alembic migration URL is configured with `search_path=public`. Domain objects are explicitly schema-qualified in the migration model.
- Empty database bootstrap passed; bootstrap replay passed; zero-to-head upgrade passed; second upgrade-to-head no-op passed; current revision was exactly `RF09_FINALIZE`.
- Alembic `check` returned `No new upgrade operations detected.` with exit `0`.
- A second clean project volume was created after scoped removal of the first project volume/network; bootstrap and zero-to-head passed again.

## Migration lock proof

The source-derived bootstrap key is `7342190309`; the source-derived migration serialization key is `7342190310`. Checkpoint A held the migration key in controlled PostgreSQL backend PID `352`. Checkpoint B ran migration separately and received deterministic `MigrationSerializationError: migration serialization unavailable`, exit `1`; schema remained at the current head. Checkpoint C terminated only that recorded controlled backend, observed advisory-lock count `0`, and reran migration successfully with exit `0`. Checkpoint D used safe invalid Alembic target `RF09_NONEXISTENT`; it performed no DDL, returned exit `255`, left revision `RF09_FINALIZE` and advisory-lock count `0`, and a subsequent normal migration returned exit `0`.

## Tests and static gates

Focused command used 22 separate pytest argv paths (the requested RF-09 persistence, Alembic, Compose-boundary, schema, finalize and quality-baseline paths) through `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/bin/python`. Result: collected `958`, passed `958`, failed `0`, skipped `0`, duration `21.62s`, exit `0`. The initial system-Python invocation was not accepted as evidence because it stopped at collection with missing dependencies; it was replaced by the compatible project environment.

Affected Ruff evidence from the incomplete delivery was retained: M06 migration and Compose-boundary test reported `All checks passed!`; M06 changes are line wrapping only and preserve SQL semantics. `git diff --check` passed. Compose config validation passed. No broad repository suite was repeated because the affected/public RF-09 gates and the acceptance-required focused suite passed, while RF-10 semantics were untouched.

## Orchestration diagnostics

The first incorrect object was the malformed focused pytest invocation: a quoted path list with extra quoting/backslash. The five evidenced transitions were: (1) Input — malformed focused pytest command; (2) Output — no reliable terminal pytest result/exit status; (3) Function-Script-File — prior Bridge execution wrapper/command assembly, not repository source; (4) Value-Source — list paths were assembled as one quoted shell argument and cleanup used rejected `rm -f`; (5) Proof — recovery inventory showed no repository/runtime material damage, and a corrected argv-array run produced the terminal compatible-environment result above. The rejected cleanup was orchestration-only: the environment rejected `rm -f`; no deletion occurred. Failed `apply_patch` attempts were orchestration-only path/context mismatches; Compose was inspected and the preserved correction was already present. The invalid lock identity, wrong lock key and bare `check` override were also invocation defects, each corrected without source changes.

## Governance, scope and security

RF-00–RF-06 remain accepted; RF-07 remains open only for genuinely deferred runtime-dependent gates; RF-08 remains independently accepted; RF-09 is no longer `not started` and is published for independent acceptance; RF-10 is partially published and active/not accepted. Complete runtime/deployment is not reached. Environment is `RUNTIME_ELIGIBLE`; production is `NOT_PRODUCTION_READY`; `READY_FOR_OPERATOR_ACCEPTANCE` remains gated by RF-30. RF-10 contract serialization, registry, exception normalization, idempotency/audit semantics, correlation context and typed settings were preserved; no RF-11 or module 02–13 domain semantics were changed.

Task-owned resources found at recovery: none. Created: one isolated PostgreSQL 18 container, one internal network, one volume, ephemeral bootstrap/migration containers and synthetic secret files. Cleaned: all task-owned Compose containers, network and volume with exact project-scoped Compose cleanup; no global prune. The final runtime root contains only task-owned secret files for the report window and no secret values are included here. Foreign containers/networks/volumes were not inspected beyond names/labels needed to avoid mutation and were not changed.

Rollback state: no repository rollback was performed; the local worktree changes remain the intended RF-09 closure/corrective scope. No foreign-resource impact. Credentials-exposure verdict: none; no secret values, DSN, passwords, tokens, private keys, provider credentials or production data were printed, staged or committed.

Limitations: independent ChatGPT review, GitHub publication verification, operator acceptance, production deployment, live-provider tests, RF-24 synthetic E2E, RF-25 extended runtime security, RF-26 recovery, RF-27 deployment, RF-28 drills, RF-29 operator pack and RF-30 final handoff remain future gates. This closure does not claim `INDEPENDENTLY_ACCEPTED` or `PRODUCTION_READY`.

Exact status: `PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
CHATGPT_REVIEW_REQUIRED: `YES`

## Independent review corrective — cleanup and governance consistency

- Corrective Technical ID: `RF-09-CORRECTIVE-CLOSURE-CLEANUP-AND-GOVERNANCE-CONSISTENCY-20260729-02`.
- Expected base: `74653a6187a34eaec522db7f5fac098e080a9aed` (`chore(rf09): publish PostgreSQL foundation closure`).
- Defect found by independent ChatGPT review: the published closure described the task-owned Compose resources as cleaned while also stating that task-owned secret files remained in the runtime root; `CURRENT_STATE.md` also retained the stale migration-from-zero/current-head remaining-gap bullet despite preserving the published proof.
- Pre-cleanup classification: `ALREADY_CLEAN`.
- Safe metadata-only residual inventory: `/opt/avito-mayak-runtime/acceptance-rf09-closure-20260729-01` existed as an empty directory (`uid=0`, `gid=0`, mode `0700`); it had no direct or nested entries. Exact project-scoped inspection found no matching container, network or volume. No process FD, mount reference or container mount reference used the exact runtime root.
- Cleanup required: `NO`. No residual task-owned file or Compose resource required removal.
- Cleanup method: no deletion or Docker cleanup was performed because the exact pre-cleanup inventory was already clean. No global prune, broad-prefix resource operation or foreign-resource operation was used.
- Post-cleanup proof: the exact runtime root remains present and empty; residual entry count is `0`; no matching Compose container, network or volume exists; no active process, FD or mount reference exists.
- Docker/Compose resource result: no exact-project resources remained before or after inspection; no resource lacking exact project ownership evidence was changed.
- Process/mount result: no process, container mount or open-file reference to the exact runtime root was found before or after inspection.
- No secret contents were read; no secret values, hashes derived from secret contents, DSNs or credentials were output.
- No foreign resource was changed.
- Reused RF-09 evidence identity: RF-09 source, migrations, `compose.yaml`, boundary test, `pyproject.toml`, `uv.lock`, `Dockerfile`, PostgreSQL image identity and closure source identity remain unchanged from the expected base; the corrective commit is documentation-only.
- Exact changed-path identity: `docs/00-governance/CURRENT_STATE.md`, `docs/00-governance/WORKLOG_APPEND_ONLY.md`, `docs/04-modules/14-runtime-foundation-and-autonomous-integration/POSTGRESQL_AND_ALEMBIC_FOUNDATION_CLOSURE_v1.0.md` only.
- Remaining limitations: independent ChatGPT acceptance, operator acceptance, deployment, live-provider proof and later RF-24–RF-30 gates remain open. This corrective does not claim `INDEPENDENTLY_ACCEPTED` or `PRODUCTION_READY`.

Status: `CORRECTIVE_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`
CHATGPT_REVIEW_REQUIRED: `YES`
