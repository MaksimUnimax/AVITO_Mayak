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

## Independent review corrective — public health invariants and governance consistency

- Corrective Technical ID: `RF-10-CORRECTIVE-HEALTH-INVARIANTS-AND-GOVERNANCE-CONSISTENCY-20260729-02`.
- Expected base: `f7441ce7cf002e63062a544f711ee31fc7426032` (`feat(rf10): complete Platform Contracts runtime`).
- Independent-review verdict: `CORRECTIVE_REQUIRED`.
- Invalid public states discovered: `PROVEN` identity without the complete proof triplet; `UNPROVEN` identity with any proof value; partial proof sets; unsafe diagnostic identifiers; and `UNPROVEN` identity combined with overall `READY` health.
- Root cause: factory-only testing without model-boundary invariants allowed contradictory direct Pydantic construction.
- Implementation correction: model-level source-proof and health/readiness validators were added; diagnostic identifiers now use the local canonical runtime identifier boundary `^[a-z0-9][a-z0-9_.-]{0,127}$`; existing factories, immutability, aliases, SHA/digest checks and readiness composer semantics were preserved.
- Compatibility verdict: `BuildVersionIdentity` and `BuildVersionInfo` remain public and compatible; no transport, framework, ORM, provider or persistence type was added.
- Focused test commands and counts: `pytest tests/unit/test_health_and_readiness_completion.py -q` — `36 passed`; `pytest tests/unit/test_health_and_readiness_completion.py tests/unit/test_contract_serialization.py tests/architecture -q` — `265 passed`.
- Shared/public suite result: `pytest tests/unit tests/contract tests/architecture -q --ignore=tests/unit/test_runtime_settings.py` — `4616 passed`, `3 failed` only because `pytest-asyncio` is unavailable for three pre-existing async correlation tests; the non-async public/shared tests passed. The complete default collection is additionally blocked by unavailable `pydantic-settings` in `test_runtime_settings.py`; DB-backed RF-10 persistence evidence remains reused, not rerun.
- Ruff/mypy/import-linter/architecture evidence: Ruff changed paths passed; mypy passed with no issues on `src/mayak/contracts/health.py`, `src/mayak/contracts/readiness.py` and the focused test; import-linter passed (`3 kept, 0 broken`); architecture tests are included in the `265 passed` focused applicable result.
- PostgreSQL evidence reused: accepted 46-test RF-10 PostgreSQL persistence proof remains valid because persistence source, migrations/schema, dependencies and lockfile are unchanged; this corrective changes health/readiness contracts only.
- Dependency/lock/migration identity: dependency versions and `uv.lock` unchanged; migration head remains `RF09_FINALIZE`; migration change `NONE`.
- Governance contradictions corrected: README current module state now records RF-04/RF-05 acceptance, RF-06 acceptance, RF-07 deferred gates, RF-08/RF-09 independent acceptance, RF-10 corrective review, RF-11 not started, incomplete runtime/deployment and `NOT_PRODUCTION_READY`; `CURRENT_STATE.md` removes stale RF-09 review gap and partial RF-10 wording, creates the RF-10 current-gate subsection and starts remaining gaps with RF-10 review/corrective acceptance; directly affected manifest, roadmap, module index and playbook statements were reconciled without rewriting historical evidence.
- Changed-path inventory: `src/mayak/contracts/health.py`; `tests/unit/test_health_and_readiness_completion.py`; `README.md`; `docs/MANIFEST.md`; `docs/00-governance/CURRENT_STATE.md`; `docs/00-governance/ROADMAP.md`; `docs/00-governance/WORKLOG_APPEND_ONLY.md`; `docs/04-modules/README.md`; `docs/04-modules/14-runtime-foundation-and-autonomous-integration/MODULE_PLAYBOOK.md`; this closure artifact.
- Security/redaction result: no credentials, DSN, token, private key, populated environment mapping, provider payload or production data added; validation diagnostics use field/reason concepts and do not intentionally echo invalid identifiers.
- Foreign-resource impact: none; no server runtime, database, container, provider or persistent project data was mutated.
- Limitations: independent ChatGPT acceptance remains required; runtime/deployment, provider/live-call, RF-11–RF-30 and production gates remain outside this corrective.
- Status: `CORRECTIVE_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`.
- `CHATGPT_REVIEW_REQUIRED: YES`.

## Corrective recovery — accepted toolchain, copy safety and complete gates

- Technical ID: `RF-10-CORRECTIVE-ACCEPTANCE-GATE-COMPLETION-20260729-03`.
- Expected base: `c6401f02443d6db958719694039fdbb1c249e286` (`fix(rf10): enforce health identity invariants`); preserved RF-10 parents are `f7441ce7cf002e63062a544f711ee31fc7426032` and `c6401f02443d6db958719694039fdbb1c249e286`.
- Prior incomplete result: `4616 passed`, `3 failed`; runtime-settings collection was blocked by missing `pydantic-settings`, and three async correlation tests were blocked by missing `pytest-asyncio`.
- Root cause: acceptance was attempted through an incomplete environment despite both packages being declared and locked project dependencies; the public Pydantic `model_copy(update=...)` path also bypassed cross-field validation.
- Accepted toolchain: `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/bin/python`, CPython `3.14.6` standard GIL, and `/opt/avito-mayak-runtime/toolchain/bin/uv`, uv `0.11.31`; both are project-owned. Lock identity: `sha256:9c9a87fb0c455d36162c3dbcfbdddc8c3f7d3e528157fb0f228678695263c020`.
- Dependency environment identity: reused project-owned `rf06-dependencies-v1`; `pytest 8.4.2`, `pytest-asyncio 0.26.0`, `pydantic 2.13.4`, `pydantic-settings 2.14.2` and all current runtime/static dependencies imported; `uv pip check` passed.
- Collection: `python -m pytest --collect-only -q` — `5669 tests collected`, exit `0`, zero collection errors, including runtime-settings and async tests.
- Focused copy/update proof: before correction, identity and snapshot `model_copy(update=...)` bypassed validation; after correction, `BuildVersionIdentity` and `HealthSnapshot` revalidate merged content, reject invalid proof changes and nested identity replacement, preserve valid liveness/deep updates and exact model types. Focused gate: `114 passed`; runtime-settings: `32 passed`; async correlation: `18 passed`.
- Source correction: added validated `model_copy` overrides to `src/mayak/contracts/health.py` and regression coverage in `tests/unit/test_health_and_readiness_completion.py`.
- Trusted-bypass inventory: repository `model_construct` uses remain in unrelated fixtures/tests; no health, build, readiness or runtime contract construction uses `model_construct`, and it is classified as an unsafe trusted-data escape hatch outside untrusted/public input handling.
- Complete shared/public result: `pytest tests/unit tests/contract tests/architecture -q` — `4653 passed`, `28 warnings`, `0 failed`; async tests executed, runtime-settings tests executed, public exports and architecture tests included.
- DB-backed files excluded and evidence reused: `tests/runtime/test_persistence_session.py`, `tests/runtime/test_persistence_transaction.py`, `tests/runtime/test_platform_audit_repository.py`, `tests/runtime/test_platform_idempotency_repository_postgres.py`; these are the exact PostgreSQL-dependent paths from the accepted RF-10 46-test evidence identity `RF-10-PLATFORM-CONTRACTS-RUNTIME-COMPLETION-AND-CLOSURE-20260729-01` at `f7441ce7cf002e63062a544f711ee31fc7426032`. Persistence, migrations, dependencies and lock are unchanged.
- Static gates: compile/import passed; Ruff changed paths passed; affected-surface mypy passed with no errors; import-linter passed (`3 kept, 0 broken`); architecture tests passed; `git diff --check` passed.
- Governance structural corrections: README current contour consolidated; `CURRENT_STATE.md` now has scoped RF-08/RF-09/RF-10 current gates with RF-09 accepted and RF-10 pending; stale partial/next/review claims and the RF-10–RF-22 current contradiction were removed; roadmap, manifest and module index state were reconciled.
- Changed paths: `src/mayak/contracts/health.py`; `tests/unit/test_health_and_readiness_completion.py`; `README.md`; `docs/MANIFEST.md`; `docs/00-governance/CURRENT_STATE.md`; `docs/00-governance/ROADMAP.md`; `docs/00-governance/WORKLOG_APPEND_ONLY.md`; `docs/04-modules/README.md`; this closure artifact.
- Dependency/migration verdict: no `pyproject.toml`, dependency, `uv.lock`, schema or migration change; migration head remains `RF09_FINALIZE`.
- Security verdict: no secrets, DSNs, tokens, private keys, populated environment values, provider payloads or production data added; invalid opaque values are not echoed by validation errors.
- Foreign-resource impact: none; no database, container, provider, server runtime or foreign resource was mutated.
- Limitations: independent ChatGPT review, RF-11–RF-30 runtime/operator gates and production launch remain outside this corrective; RF-10 is not independently accepted.
- Status: `CORRECTIVE_PUBLISHED_FOR_INDEPENDENT_ACCEPTANCE`.
- `CHATGPT_REVIEW_REQUIRED: YES`.
