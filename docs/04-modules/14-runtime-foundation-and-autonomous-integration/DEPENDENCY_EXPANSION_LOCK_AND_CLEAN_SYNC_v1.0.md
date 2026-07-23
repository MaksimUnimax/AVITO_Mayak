# RF-06-03 Dependency Expansion, Lock and Clean Sync

**version:** 1.0
**status:** `PUBLISHED_PENDING_ACCEPTANCE`
**date:** 2026-07-23
**Technical ID:** `RF-06-03-CORRECTIVE-05-MARKDOWN-HYGIENE-PREFLIGHT-AND-DEPENDENCY-PUBLICATION-20260723`
**scope:** RF-06-03
**exact source SHA:** `4c28354bceaf8325084d8ffd99a31e662c518a71`

## Acceptance context

RF-06-02 is independently accepted at the exact expected base. This RF-06-03 corrective chain repeats the prior safe candidate assembly from that base. The previous iteration stopped before publication because a new Markdown artifact contained trailing whitespace detected after commit creation. The actual root cause was `CONTENT_HYGIENE_GATE_EXECUTED_TOO_LATE`; the applicable marker is `STOP_CONTENT_HYGIENE_FAILED`. Commit `03e07fde1ee0c48c940b2e2bb578472f2b064aa7` was not used as a base, resurrected, cherry-picked, amended or pushed.

The accepted toolchain is CPython 3.14.6 standard-GIL and uv 0.11.31 with manifest SHA-256 `a5c2fa436d3721f1fbb0a05c9c335486455e5292835b5ac87dc6720cfb0091a2`. Runtime, Docker, database and listeners remained stopped.

## FC-08 historical boundary correction

The exact test method now reads the immutable committed range only:

```python
committed_paths = sorted(result.stdout.strip().split("\n")) if result.stdout.strip() else []
assert committed_paths == EXPECTED_FC08_PATHS, (
    f"FC-08 path set mismatch: expected {EXPECTED_FC08_PATHS}, got {committed_paths}"
)
```

The test has a short comment stating that it checks the immutable historical FC-08 commit range and that the current-task changed-path allowlist is a separate task gate. The staged/unstaged diff reads, `working_paths`, `all_paths` and current-worktree mixing were removed. The four historical paths, ancestry checks, source/docs prohibitions, SHA constants, production blob constants, forbidden imports, fixtures and other assertions are unchanged. `EXPECTED_FC08_PATHS` contains no dependency or documentation path.

## Dependency declarations and deterministic lock

Runtime declarations are alphabetically ordered: alembic, fastapi, httpx, jinja2, opentelemetry-api, opentelemetry-sdk, pydantic, pydantic-settings, psycopg[binary], sqlalchemy and uvicorn. Existing pydantic declarations remain unchanged. Dev declarations preserve the existing tools and add `respx>=0.22,<1`. No scripts, entry points, source overrides, unrelated libraries or direct semantic-conventions/exporter/instrumentation dependencies were added.

The exact command was:

```
uv lock --python /opt/avito-mayak-runtime/toolchain/bin/python --default-index https://pypi.org/simple
```

Both `uv lock --check` and offline `uv lock --check --offline` succeeded. Lock revision is 3 and requires Python is `==3.14.*`. The lock has 50 package records: 49 public PyPI registry records and one editable project root. The lock contains 48 sdist entries and 246 wheel entries, for 294 total artifact entries; all 294 entries contain SHA-256 hashes. The selected sync is wheel-only and did not build from the 48 recorded source distributions. Direct prereleases: 0. The only prerelease is the accepted coupled transitive `opentelemetry-semantic-conventions==0.65b0`; no Git, URL, path or custom-index dependency and no selected yanked release was found.

Direct locked versions are alembic 1.18.5, fastapi 0.139.2, httpx 0.28.1, jinja2 3.1.6, opentelemetry-api 1.44.0, opentelemetry-sdk 1.44.0, psycopg 3.3.4, pydantic 2.13.4, pydantic-settings 2.14.2, sqlalchemy 2.0.51, uvicorn 0.51.0 and respx 0.23.1. OpenTelemetry distribution metadata proves API/SDK 1.44.0, semantic conventions 0.65b0 and the exact official Requires-Dist coupling. Public imports and compatible hashed wheels were verified. `importlib.util.find_spec("opentelemetry.api") is None` is classified `EXPECTED_ABSENT_NONPUBLIC_MODULE`.

## Environments and functional verification

Baseline staging used the original lock and installed 25 packages. Candidate staging used the new lock and installed 47 packages. Both used frozen all-groups sync with no project installation, no build and managed-Python downloads disabled. `uv pip check` succeeded for both; installed-vs-lock was exact; colorama and tzdata are marker-excluded examples. The accepted interpreter path, base prefix and Python version were verified. No foreign site-packages were present; the two standard venv/coverage .pth markers are task-environment internals, not external package roots.

Candidate runtime imports and versions were verified for alembic, fastapi, httpx, jinja2, OpenTelemetry, psycopg, pydantic, pydantic-settings, sqlalchemy and uvicorn. Dev imports were verified for coverage, grimp, mypy, pytest, pytest-asyncio, respx, Ruff and import-linter. Psycopg reported PQ 18.0. Pydantic validation/settings, SQLAlchemy metadata/expression, and no-exporter/no-network OpenTelemetry tracer/meter/resource smokes succeeded. Runtime was never started.

## Differential quality and tests

Ruff ran twice in each environment: 648 diagnostics in baseline and 648 in candidate, deterministic, with no candidate-only diagnostic and no regression outside the exact FC-08 edit. Verdict: `RUFF_PREEXISTING_DEBT_NO_REGRESSION`. Mypy ran twice in each environment: 249 errors in baseline and 249 in candidate, deterministic, with no candidate-only error after mapping line shifts from the exact FC-08 edit. Verdict: `MYPY_PREEXISTING_DEBT_NO_REGRESSION`. The pre-existing diagnostics were not repaired.

Import-linter reported 3 contracts kept and 0 broken. Baseline and candidate full pytest each collected 4511 and passed 4511 with zero failures/errors. The exact FC-08 test passed pre-commit. Branch coverage was 85% for both runs.

## Governance, hygiene and rollback

Governance transitions are RF-06-02 accepted; RF-06-03 corrective publication pending independent acceptance; RF-06-04 blocked; RF-07 blocked; runtime stopped; differential static no regression; full pytest pass; `RUNTIME_ELIGIBLE`; `NOT_PRODUCTION_READY`. `PRODUCTION_READY` is not claimed.

The first pre-normalization scan found 6 trailing-whitespace lines in this new Markdown artifact only. Only those trailing spaces were removed; no semantic Markdown reformat was performed. Post-normalization trailing whitespace, CR residue and missing-final-newline counts are zero. Pre-stage and staged custom scans, `git diff --check` and `git diff --cached --check` are required zero-result gates. Markdown links, documentation consistency and secret scans are required before commit and after publication.

The promoted environment manifest is `/opt/avito-mayak-runtime/venvs/rf06-dependencies-v1/environment-manifest.json`; its SHA remains unchanged because its `registry_policy.artifacts: 246` and `registry_policy.hashed_artifacts: 246/246` fields are explicit wheel-only registry-policy counts, not generic total-artifact claims. Ownership is root:avito-mayak, mode 0640 for the manifest, service-readable and service-non-writable; `current` is a relative link to `rf06-dependencies-v1`. Baseline staging and cache are disposable; candidate cache is retained only as evidence.

## Artifact-count correction notice

The original phrase “246 artifacts, all 246 hash-complete” conflated the wheel count with the total artifact count. The authoritative current breakdown is 48 sdist entries, 246 wheel entries, 294 total artifact entries, and 294/294 SHA-256 coverage. The dependency graph, lock bytes, selected wheels, installed environment and wheel-only sync verdict are unchanged. The correction artifact `DEPENDENCY_ARTIFACT_COUNT_SEMANTICS_CORRECTION_v1.0.md` is the authoritative source for artifact-count semantics.

Rollback before push is limited to deleting task-owned environments, link and caches, restoring the nine allowlisted paths, and removing disposable worktrees/branches. The accepted toolchain, source checkout, prerequisites, configuration and foreign resources are not changed. No credentials or secrets were accessed or exposed.

Limitations: pre-existing Ruff/mypy debt remains; no CI, deployment, runtime, database integration or provider integration was performed. RF-06-04 and RF-07 remain blocked. Final verdict is `NOT_PRODUCTION_READY`.
