# RF-11 Identity & Access runtime closure

- Technical ID: `RF-11-IDENTITY-AND-ACCESS-RUNTIME-COMPLETION-AND-CLOSURE-20260729-01`
- Expected base: `74997f4da04fd9ae9e225ea39b22c20acd45353e` (`fix(rf10): validate against current locked environment`).
- RF-10 prerequisite: independently accepted through the expected base; no GitHub CI-success claim.
- Date: `2026-07-29`.

## Requirement-gap matrix

| Area | Base gap | RF-11 result |
|---|---|---|
| Module 02 contracts/fixtures | semantic frozen contracts and safe synthetic IDs only | preserved and extended additively |
| Persistence | no runtime repositories/services | five existing tables mapped; caller-owned SQLAlchemy session |
| Platform | accepted idempotency/audit primitives | reused, no duplicate primitive |
| Runtime | no account/session/provider execution | account resolution, sessions, actor/roles, links, synthetic gate |
| Transport/deployment | absent | intentionally absent; no provider SDK/HTTP/FastAPI/ingress |

## Implementation inventory

Preserved contracts and fixture IDs: all existing exports from `contracts.py`, `__init__.py`, and `SYNTHETIC_FIXTURE_IDS` remain available. Added public families are `VerifiedProviderIdentity`, provider resolution request/outcome, safe session metadata/validation, actor validation request/outcome, link challenge request/outcome, role mutation, authorization decision, and synthetic login request/outcome. `SecretSessionToken` and `IssuedSession` are internal issuance values with redacted repr/string; public contracts contain no ORM, session, transport, SDK, raw payload, credential, token or challenge material.

Changed-path inventory: `src/mayak/modules/identity_and_access/contracts.py`; `runtime.py`; package exports; `src/mayak/runtime/settings.py`; `.env.example`; this closure; RF-10 closure append; governance surfaces and one worklog entry.

Exact tables: `mayak.identity_accounts`, `mayak.identity_provider_links`, `mayak.identity_role_assignments`, `mayak.identity_sessions`, `mayak.identity_link_challenges`. The accepted `RF09_M02` schema is exact at current head and is reused without a migration; historical migrations are untouched. Current migration head remains `RF09_FINALIZE`.

Account authority is UUID `account_id`; verified Telegram and provider-neutral MAX assertions normalize/fingerprint bounded opaque subjects, reject unverified input before mutation, resolve existing unique links, otherwise create exactly one account/link atomically, and never use phone, email, username, display name, avatar or weak correlation. Provider subject never becomes account ID; no merge and no provider call exist.

Synthetic login requires profile `synthetic_acceptance` plus explicit enablement, is disabled by default and never grants elevated roles. Sessions use UTC, cryptographic standard-library randomness, max 86,400 seconds, and SHA-256 hash-only persistence. Active/expired/revoked/unknown validation and idempotent revocation are explicit. Raw session/challenge values are absent from contracts, rows, audit, fixtures, logs, closure and report.

Active verified session is the actor context. Self access is allowed; cross-account, provider-only, client-role and stale-session authority is denied before mutation. Only active server-assigned ADMIN can assign/revoke SUPPORT or ADMIN; role mutations are audited. Link challenges are one-time, hash-only, positive TTL capped at 900 seconds, verified-provider-only, foreign-account rejecting and no-merge. Recovery is verified relink or authenticated ADMIN action with explicit actor, target, reason, verified assertion, idempotency and audit; it may attach an identity or revoke compromised sessions only.

Platform terminal idempotency is used on the same caller transaction for account resolution and applicable mutations; same key/fingerprint replays, mismatch fails closed, and rollback removes domain/audit/idempotency effects. PostgreSQL uniqueness and savepoint reconciliation bound concurrent first resolution; challenge consumption is compare-and-consume. No hidden commit.

## Evidence and governance

Previously passing evidence was reused after recording source identity: aggregate `src/`+`tests/` Python hash `7317efce7942bf210bc341743c94b35e02583c0589af790f1e67cbb54b6998c1`, runtime `runtime.py` hash `94d316b682a4bc607687f5c2bcb88672f35cedb6a130146fd77316644ad9039b`, contracts hash `6423aea33fc6f88c851f7bf516163dd76d3e2c2e7ebcf82c8676d7c6c8727818`, settings hash `e4161c428076af1aef57be3c0f8e61b529305676867b9d85b96688fa589bb07c`, focused test hash `386c6405c6a32873ff23d77a552856c8a7e250f07d044a17222cd3d3218dbe2b`, and lock hash `e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6`. Exact reused commands were the recorded focused `pytest` identity/settings/schema command, broad `pytest` unit/contract/architecture command, changed-surface Ruff, affected mypy and import-linter commands; exact prior results remain `63 passed`, `4658 passed`, Ruff pass, mypy pass, and `3 kept, 0 broken`. Final impact-required focused rerun passed `69` tests with the same lock environment (CPython `3.14.6`).

PostgreSQL command: `docker compose -p avito-mayak-acceptance-rf11-identity-20260729-01 --profile runtime-foundation up -d mayak-postgres mayak-db-bootstrap mayak-migrate`, followed by two internal-network application test-container harness invocations and one rollback recheck. Image was `postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296`; network inspection proved `internal=true`, the database container exposed `5432/tcp` with no host binding, and the task volume/network/container IDs were recorded and then removed. Migration head was `RF09_FINALIZE`. Schema inspection found all five Identity tables, 37 expected columns, UUID primary keys, accepted nullability/types, RESTRICT account FKs, accepted unique constraints/indexes/checks including hash-only SHA-256 checks and 24-hour session TTL. Migration-Decision: `NONE`; no historical or additive migration was needed.

The PostgreSQL harness command completed `26 passed` assertions: verified Telegram resolution, replay, fingerprint conflict, unverified no-state, one account/link, provider-subject separation, 8-worker first-resolution concurrency, session active/expired/revoked behavior, 24-hour bound, synthetic acceptance-only login, cross-account denial, ADMIN-only role mutation, unauthorized zero effect, audit, duplicate active-role prevention, hash-only challenge, consumed/foreign challenge rejection, 6-worker challenge completion at-most-once, rollback of identity/audit/idempotency effects, and absence of password/merge/credential tables. No source corrections were required after DB execution. No host PostgreSQL port, provider network call, raw token/challenge/provider payload, password, phone requirement or merge state was used or persisted.

No passwords, password hashes, phone requirement, account merge, raw provider payload/token, provider credential, real personal data, private-key content or foreign mutation. No RF-12 work. Task-owned PostgreSQL container/network/volume and four synthetic 0600 secret files were cleaned with exact Compose project teardown; post-cleanup exact-label inventory is empty. Runtime/deployment remains incomplete; environment remains `RUNTIME_ELIGIBLE`; RF-30 remains the only route to `READY_FOR_OPERATOR_ACCEPTANCE`.

Production verdict: `NOT_PRODUCTION_READY`.

Status: `PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`.

`CHATGPT_REVIEW_REQUIRED: YES`.

## Security containment and completion run — 2026-07-29

- Technical ID: `RF-11-CORRECTIVE-TRUSTED-AUTHORITY-AND-DURABLE-POSTGRES-TESTS-20260729-02`.
- Confirmed exposure: a failed PostgreSQL acceptance setup path could retain/render a credential-bearing DSN through the raw DSN fixture value and SQLAlchemy setup traceback. No credential value is reproduced here; any Bridge/executor transcript retention is external and cannot be deleted by this worktree.
- Containment: exact task resources were absent at preflight; replacement bootstrap, migration, application and signing credentials were generated with a CSPRNG, kept in exact runtime files mode `0600`, rotated from the failed run, and never printed or committed. Exact Compose teardown removed the task container, internal network and volume.
- Root-cause fix: the PostgreSQL test harness now reads the credential from a protected file or in-process environment and constructs a SQLAlchemy `URL`; diagnostics use masked-password rendering. Internal raw-secret and configuration wrappers have redacted `repr`/`str`.
- Regression proof: redaction tests assert absence from URL rendering, `repr`, `str` and setup diagnostics while retaining safe database identity; no test assertion prints the synthetic credential. Final PostgreSQL package: `10 passed` on a fresh isolated Postgres 18 database.
- RF-11 completion: trusted authenticated `(account_id, session_id)` authority, one transaction-scoped advisory-lock gate, normalized secret-free fingerprints, link terminal idempotency, savepoint reconciliation and fixed-key bootstrap serialization are preserved/completed. Migration-Decision: `NONE`; Migration-Head: `RF09_FINALIZE`.
- Publication SHA: the single direct-child publication SHA is recorded in the terminal report for this closure; no amend or follow-up cleanup commit is permitted.
- Status: `CORRECTIVE_PUBLISHED_FOR_CHATGPT_REVIEW`; `CHATGPT_REVIEW_REQUIRED: YES`; `NOT_PRODUCTION_READY`.

## Corrective recovery — trusted authority and durable PostgreSQL gates

- Technical ID: `RF-11-CORRECTIVE-TRUSTED-AUTHORITY-AND-DURABLE-POSTGRES-TESTS-20260729-02`.
- Expected base and preflight origin: `52d323b6a9ae21224c00c252449a2aea5a997767`; detached candidate HEAD matched.
- Root cause: `UNTRUSTED_CALLER_DATA_CAN_ENTER_TRUSTED_IDENTITY_AND_AUTHORIZATION_PATHS`.
- Public correction: provider input is explicitly untrusted `ProviderIdentityClaim`, restricted to Telegram/MAX; no caller verification boolean, arbitrary provider, generic synthetic provider, internal verified assertion or provider payload is public.
- Verifier: internal `ProviderIdentityVerifier` port and deterministic `FakeProviderIdentityVerifier`; outcomes are `VERIFIED`, `REJECTED` or `AMBIGUOUS`, and verifier-backed resolution rejects generic synthetic claims.
- Secret boundary: `_RawSecret` and `_IssuedSession` remain internal, redacted; public contracts/exports and persisted rows contain no raw session/challenge secret, password, ORM, session or SDK type. Session persistence is SHA-256 hash-only.
- Authority: actor UUID is derived from the active persisted session; caller-supplied actor/account UUID spoofing is rejected. Synthetic login is acceptance-only and idempotent.
- Mutation idempotency matrix: provider resolution; synthetic login; self and Admin target-session revocation; role assignment/revocation; acceptance Admin bootstrap; link challenge start/completion; Admin recovery. Each has normalized non-secret fingerprint, replay, same-key/different-fingerprint conflict, caller-owned transaction, persisted audit where applicable, and rollback proof.
- Roles/bootstrap: active persisted Admin authority is required; bootstrap is acceptance-only, advisory-lock serialized and at most one initial Admin. Role mutation is authorized, audited and replay-safe.
- Link/recovery: authenticated challenge start is replay/mismatch safe; completion is verifier-backed, row-locked and atomic. Provider mismatch, expired/consumed challenge, same-account replay, foreign-account rejection and six-worker completion were exercised. Admin recovery is authorized, verified, idempotent and can revoke target sessions.
- Committed PostgreSQL path: `tests/runtime/test_identity_runtime_postgres.py`; exact task Compose project `avito-mayak-acceptance-rf11-corrective-20260729-02`; ephemeral CPython `3.14.6` test container supplied `MAYAK_RF11_POSTGRES_DSN` only in-process over the internal network. Final focused result: `31 passed`.
- Actual validation: focused Identity unit/contract plus PostgreSQL suite `31 passed`; complete `tests/unit tests/contract tests/architecture` `4658 passed`; Ruff pass; mypy affected source/tests pass; import-linter `3 kept, 0 broken`; `git diff --check` pass.
- Migration/schema: `Migration-Decision: NONE`; `Migration-Head: RF09_FINALIZE`; PostgreSQL inspection proved all five Identity tables, UUID/account authority, unique provider links, hash-only constraints, restricted FKs and TTL checks; historical migrations unchanged.
- Toolchain/lock: CPython `3.14.6`, uv `0.11.31`, current `pyproject.toml`; `uv.lock` SHA-256 `e1faff1ce0f4d5dfd35480ab59d5d599fddf05c38fcd16a26c52098511476ab6`; no dependency change.
- Security/redaction: PostgreSQL 18 pinned image `postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296`; internal network, no host DB port, synthetic secret files mode `0600`, no values printed or committed, no private-key inspection, provider I/O, personal data or foreign-resource impact.
- Resources: exact task containers/network/volume were created/recovered only for this run, then torn down with exact Compose `--volumes --remove-orphans`; exact secrets were unlinked with `Path.unlink`; exact runtime directory was removed with `Path.rmdir`; remaining task containers/networks/volumes and secret files: zero.
- Governance/limitations: RF-11 corrective published for ChatGPT review; RF-11 not accepted yet; RF-12 not started; environment `RUNTIME_ELIGIBLE`; runtime/deployment incomplete; `NOT_PRODUCTION_READY`; no API, deployment, provider transport or production claim.
- Status: `CORRECTIVE_PUBLISHED_FOR_CHATGPT_REVIEW`.
- `CHATGPT_REVIEW_REQUIRED: YES`.
