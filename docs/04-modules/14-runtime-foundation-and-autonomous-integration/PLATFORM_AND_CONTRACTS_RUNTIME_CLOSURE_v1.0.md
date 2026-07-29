# Platform & Contracts runtime closure

Technical-ID: `RF-10-PLATFORM-CONTRACTS-RUNTIME-COMPLETION-AND-CLOSURE-20260729-01`

## Status and base

- Expected base: `54300eb672a883cc052c131bf788501ed4b4a918`.
- RF-09 prerequisite: independently accepted through `54300eb672a883cc052c131bf788501ed4b4a918`; the RF-09 closure now records that acceptance.
- RF-10 status: `PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`.
- `CHATGPT_REVIEW_REQUIRED: YES`.
- No RF-11 work was started; no production-ready claim is made.

## Complete RF-10 chain and inventory

The complete existing RF-10 implementation chain preserved by this closure is: `6a3e5f7`, `460d617`, `9da66b7`, `4737ea1`, `537b76c`, `37ed4ed`, `e5d085f`, `4f14b75`, `1c81e53`, followed by RF-09 foundation/corrective commits through the expected base. This task adds the health/version and readiness-composition completion and one direct-child closure commit.

| Requirement family | Existing implementation preserved | Completion proof |
|---|---|---|
| Canonical contract serialization | `src/mayak/contracts/serialization.py` | deterministic sorted JSON, UTF-8 bytes, SHA-256, NaN/unsupported rejection; `test_contract_serialization.py` |
| Contract identity/version registry | `src/mayak/contracts/registry.py`, `metadata.py` | duplicate, unknown name, unsupported version and model mismatch tests |
| Results/errors | `results.py`, `errors.py`, `error_mapping.py` | accepted categories/retry classes and safe unknown-exception normalization tests |
| Idempotency | `src/mayak/persistence/idempotency.py`, platform contracts/schema | first call, terminal replay, mismatch, expiry, corruption and concurrent uniqueness proof |
| Transactions | `src/mayak/persistence/session.py` | caller commit/rollback/no hidden commit/session lifecycle tests |
| Audit | `src/mayak/contracts/audit.py`, `src/mayak/persistence/audit.py` | immutable safe envelope, rollback, retrieval, duplicate and foreign actor proof |
| Correlation | `src/mayak/platform/correlation*.py` | nested, async and thread isolation tests |
| Typed configuration | `src/mayak/runtime/settings.py`, `.env.example` | explicit-key, profile, localhost, roles, bounded HTTP and redaction tests |
| Process/readiness | `platform/process.py`, `platform/readiness.py`, `contracts/readiness.py` | deterministic composer tests; optional disabled dependency remains non-blocking when ready |
| Health/build/version | `src/mayak/contracts/health.py` | immutable identity, liveness separation, source-proven/unproven and safe snapshot tests |

## Public API inventory

Public exports are maintained through `mayak.contracts` and include canonical serialization/digest, `ContractMetadata`, `ContractRegistry`, `CommonOutcome`, `CommonErrorOutcome`, `ExceptionNormalizer`, idempotency decisions/identifiers, audit/configuration/correlation contracts, `ProcessReadinessOutcome`, `compose_process_readiness`, `BuildVersionIdentity`, `BuildVersionInfo`, `HealthSnapshot`, `LivenessOutcome`, `LivenessStatus` and `SourceIdentityStatus`. Existing `mayak.platform` and `mayak.runtime` exports remain compatible. No framework, ORM, provider or transport type is exposed by the common contract surface.

## Changed paths and implementation

New paths: `src/mayak/contracts/health.py`, `tests/unit/test_health_and_readiness_completion.py`, this closure artifact. Changed paths: `src/mayak/contracts/readiness.py`, `src/mayak/contracts/__init__.py`, RF-09 closure artifact, current governance documents and append-only worklog. Existing serialization, registry, result/error, persistence, transaction, audit, correlation and settings implementations were reused without duplicate abstraction families. Readiness now sorts dependency outcomes and applies `BLOCKED > NOT_READY > SOURCE_UNPROVEN > READY`; health identity is transport-neutral and never contains raw environment/configuration.

## Evidence

- Contract serialization/registry/results/errors: focused existing unit tests passed.
- Idempotency: PostgreSQL first call, same-fingerprint terminal replay, mismatch, expiry, corrupt-result fail-closed, rollback and concurrent same/different fingerprint behavior passed.
- Transactions/audit: caller commit and rollback, atomic multi-write rollback, audit persistence/retrieval, duplicate protection, foreign actor rejection and session cleanup passed.
- Correlation: nested restoration, async task isolation, thread isolation and no-context behavior passed.
- Configuration: immutable typed settings, exact 42-key allowlist, unknown/missing/malformed inputs, production/provider restrictions, local bind, distinct DB roles, bounded HTTP and safe errors passed; `.env.example` contains placeholders only.
- Process/readiness: all dependency statuses, deterministic sorting and precedence, immutable composition and optional-provider semantics are covered.
- Health/version: exact safe application/build fields, digest/SHA validation, explicit source-unproven state, liveness independence and no secret-bearing snapshot fields are covered.
- Public/architecture: changed-surface Ruff passed; changed-surface mypy passed with no issues in 25 source files; import-linter passed with `3 kept, 0 broken`; compile/import checks passed. Historical full-tree baseline remains non-clean (`648` Ruff findings and `248` mypy errors in 33 files), all outside this RF-10 change surface.

## PostgreSQL and gates

- PostgreSQL version: `18.4` from the task-owned `postgres:18-bookworm` image; RF-09 accepted image/schema evidence is reused for migration identity.
- Migration head: `RF09_FINALIZE`; no migration or schema file changed.
- Task-owned DB proof: `46 passed` focused persistence tests in a new internal-only PostgreSQL 18 container, with current metadata tables created in an empty disposable database; no host-published port.
- Focused contract tests: `117 passed`.
- Shared/public suite excluding the separately executed DB-backed files: `5588 passed`, `4 warnings`, `0 failed`.
- Initial all-suite attempt without the required task DSN: `5617 passed`, `17 errors` at DB fixture setup; it was not treated as a pass. The DB gate was then rerun in the isolated resource and passed.
- Coverage/quality: repository quality-baseline tests passed in the shared suite; no new coverage threshold or dependency was introduced.
- Security/redaction: focused redaction/configuration/exception/audit/idempotency tests passed; changed-surface scan found no credentials, DSNs, private keys, populated `.env` or raw provider payloads.
- Dependency/lock verdict: `uv.lock` and dependency versions unchanged; no dependency change required.
- Migration change: `NONE`.

## Isolation, rollback and limitations

Task resources: Compose-equivalent project `avito-mayak-acceptance-rf10-platform-20260729-01`, internal network, disposable PostgreSQL volume and one PostgreSQL container. All were cleaned by exact names; post-cleanup container/network/volume inventory was empty. No accepted persistent project data or foreign resource was inspected or mutated. The expected base remains the rollback point; no reset, rebase, merge, cherry-pick, amend, squash or force-push was used. No credentials were exposed.

Limitations are the independent ChatGPT review, later API/worker/scheduler deployment, provider/live-call gates, RF-23–RF-30 runtime/operator gates and production launch gates. RF-09 independent acceptance is recorded; RF-10 is not independently accepted.

Exact status: `PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`

CHATGPT_REVIEW_REQUIRED: YES
