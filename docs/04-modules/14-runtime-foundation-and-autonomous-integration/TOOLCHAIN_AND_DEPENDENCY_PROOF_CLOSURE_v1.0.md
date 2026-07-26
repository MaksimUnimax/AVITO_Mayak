# Toolchain and Dependency Proof Closure

## Metadata

- Version: 1.0
- Status: `PUBLISHED_PENDING_ACCEPTANCE`
- Date: 2026-07-26
- Technical ID: `RF-06-04-CORRECTIVE-09-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260726`
- RF step: RF-06-04
- Exact source SHA: `f896cbe5efd5690e590913c15e24b988f80dc56a`
- Runtime eligibility: `RUNTIME_ELIGIBLE`
- Production verdict: `NOT_PRODUCTION_READY`

## Accepted chain

- RF-06-01: accepted through `f77a1d85d7c8b8fd1f2e60694729d1b7c3a1598c`.
- RF-06-02: accepted at `4c28354bceaf8325084d8ffd99a31e662c518a71`.
- RF-06-03 implementation: `c0104df4fb356862beffc04abe8b0170498eaf3c`.
- RF-06-03-C06 artifact-count correction: accepted at `372ecc630106e9b813bddf1edd384ce36f48db6d`.
- RF-06-04-C07/C08 mypy authority and SHA transcription corrective chain: accepted through `f896cbe5efd5690e590913c15e24b988f80dc56a`.
- RF-06-04-C07: authoritative current mypy count 249; historical 248 is preserved as unreproducible historical evidence.
- RF-06-04-C08: the correct RF-02 closure SHA is `c92e9299e5c0bd11ea18362673a8ac342b835483`.

## Toolchain identity

- CPython `3.14.6`, standard GIL enabled: `Py_GIL_DISABLED=0` and `sys._is_gil_enabled()=true`.
- uv `0.11.31` at `/opt/avito-mayak-runtime/toolchain/bin/uv`.
- Toolchain manifest SHA-256: `a5c2fa436d3721f1fbb0a05c9c335486455e5292835b5ac87dc6720cfb0091a2`.
- Promoted Python: `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/bin/python`.
- Promoted environment manifest SHA-256: `0be844c148676dbcdc70fb5c16fb0913ab1869f6d30955d38c0301c70ec70fc6`.
- Executables were regular executable files or accepted in-boundary symlinks, non-group/world-writable, and resolved within the accepted toolchain or promoted environment boundaries.
- `uv lock --check --offline` and `uv lock --check` both passed without changing `pyproject.toml` or `uv.lock`.

## Dependency and lock identity

- `pyproject.toml` SHA-256: `c9c905db608ce2ccece5acfcdbff066a241f3c55a03d716d1e08864055b7ffdb`.
- `uv.lock` SHA-256: `9c9a87fb0c455d36162c3dbcfbdddc8c3f7d3e528157fb0f228678695263c020`.
- `uv pip check --python /opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/bin/python`: passed.
- Installed distributions: 47; lock package records: 50; registry records: 49; editable project root records: 1.
- Lock artifact recount: 48 sdists, 246 wheels, 294 total artifacts, 294/294 SHA-256-covered, 294 unique URLs, zero duplicate entries and zero conflicting URL/hash pairs. The 246 value is wheels only, not the total artifact count.
- Direct locked versions include alembic 1.18.5, fastapi 0.139.2, httpx 0.28.1, jinja2 3.1.6, opentelemetry-api/sdk 1.44.0, psycopg 3.3.4, pydantic 2.13.4, pydantic-settings 2.14.2, sqlalchemy 2.0.51, uvicorn 0.51.0 and respx 0.23.1.
- Direct prerelease count: 0. The only accepted transitive prerelease is `opentelemetry-semantic-conventions==0.65b0`, classified `ECOSYSTEM_COUPLED_TRANSITIVE_PRERELEASE`.
- No Git, unbounded URL, local path, custom-index or unexpected editable dependency was found.
- Read-only dependency inventory: `/var/backups/avito-mayak/RF-06-04-CORRECTIVE-09-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260726-20260726T085116Z/inventory/dependency-inventory.json`.
- Read-only license inventory: `/var/backups/avito-mayak/RF-06-04-CORRECTIVE-09-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260726-20260726T085116Z/inventory/license-inventory.json`; unknown legacy license metadata count: 5. This is inventory evidence, not legal approval.

## Mypy authority reconciliation

AUTHORITATIVE_CURRENT_MYPY_COUNT: 249

HISTORICAL_248_CAUSE: NOT_PROVEN

HISTORICAL_248_CLOSURE_EXPECTATION_STATUS: SUPERSEDED

- Mypy version: 1.20.2; command: `mypy --show-error-codes src tests`.
- Canonical runs 1 and 2 used separate fresh caches; no-incremental used a separate task-owned cache path.
- All three runs produced 249 error records, summary count 249, and 29 notes.
- All three normalized error-record identities are `4f6ac7fa39b343f16b207ff5bed187a7447f87515115dee250a25ebf06126e11`, reproduced with the RF-06-04-C02 normalization implementation and identical accepted raw diagnostic stream.
- Parser/summary equality passed and cross-run normalized identity passed.
- Classification: `MYPY_PREEXISTING_DEBT_NO_REGRESSION`. No mypy debt was remediated.

## Static and architecture verification

- Ruff `check --output-format=concise src tests` ran twice independently: 648 diagnostics each, normalized outputs identical, exit status 1 because accepted pre-existing debt remains. Classification: `RUFF_PREEXISTING_DEBT_NO_REGRESSION`.
- Import-linter command `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/bin/lint-imports` passed with 3 contracts kept and 0 broken.
- Runtime and development imports, Psycopg/PQ, Pydantic validation/settings, SQLAlchemy expression construction and OpenTelemetry no-exporter/no-network construction passed. `importlib.util.find_spec("opentelemetry.api")` is `None`, classified `EXPECTED_ABSENT_NONPUBLIC_MODULE`.

## Full semantic suite

- Command: `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/bin/coverage run --branch -m pytest`, followed by `coverage report`.
- Observed current-suite result: 4511 collected, 4511 passed, 0 failed, 0 errors; coverage total 85%; both exits 0.
- Coverage data was task-owned and no tests were changed or skipped to obtain the result.

## Security and isolation

- No secrets, credentials, populated environment files or private key contents were read or exposed.
- No user-site dependency, provider call, network call, database connection, Docker/Compose action, listener mutation, service mutation, runtime start or foreign-resource impact occurred.
- Runtime remained stopped. `RUNTIME_ELIGIBLE` describes environment eligibility only; production verdict remains `NOT_PRODUCTION_READY`.

## Rollback and reproducibility

- Disposable worktree: `/opt/avito-mayak-worktrees/rf06-closure-f896cbe`; exact base: `f896cbe5efd5690e590913c15e24b988f80dc56a`.
- Backup and evidence directory: `/var/backups/avito-mayak/RF-06-04-CORRECTIVE-09-TOOLCHAIN-AND-DEPENDENCY-PROOF-CLOSURE-20260726-20260726T085116Z`.
- Four existing-document preimages, an absent marker for this artifact, file identities, aggregate identity and rollback instructions were retained before mutation.
- Replay is permitted only for this exact Technical ID, exact base, exact parent, exact subject and exact five-path scope.

## Limitations

- Ruff and mypy pre-existing debt remains; no CI exists yet.
- Docker/Compose runtime, PostgreSQL/migrations, deployment and provider live proof were not executed.
- This closure does not claim production readiness: `NOT_PRODUCTION_READY`.

## Verdict

RF06_TOOLCHAIN_AND_DEPENDENCY_PROOF_VERIFIED

RF06_ARTIFACT_COUNT_48_246_294_ACCEPTED

RF06_MYPY_CURRENT_COUNT_249_ACCEPTED

RF06_CURRENT_SEMANTIC_SUITE_PASSED

RF06_CLOSURE_PUBLISHED_PENDING_ACCEPTANCE

RF07_REMAINS_BLOCKED_PENDING_RF06_CLOSURE_ACCEPTANCE

RUNTIME_ELIGIBLE

NOT_PRODUCTION_READY

## Next gate

Only independent ChatGPT acceptance of this exact closure commit may open RF-07. The CLI must not start RF-07.
