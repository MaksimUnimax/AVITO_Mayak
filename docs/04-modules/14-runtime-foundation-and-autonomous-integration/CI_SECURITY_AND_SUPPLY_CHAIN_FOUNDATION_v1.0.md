# CI Security and Supply Chain Foundation

Version: 1.0
Status: `IMPLEMENTATION_CHAIN_INDEPENDENTLY_ACCEPTED`
Date: 2026-07-26
Technical ID: `RF-07-02-CI-SECURITY-AND-SUPPLY-CHAIN-FOUNDATION-20260726`
Base: `7c594e49db75cce8a6f411fa0c8ceea59d8b0518`
RF-06: `INDEPENDENTLY_ACCEPTED`
RF-07-01: `INDEPENDENTLY_ACCEPTED`
RF-07-02-C01: `INDEPENDENTLY_ACCEPTED`
RF-07-02-C02: `CORRECTIVE_REQUIRED_HISTORICAL`
RF-07-02-C03: `INDEPENDENTLY_ACCEPTED` at `1e911fc4680296a2a81c634e56cd57ed6b333fd5`
RF-07: `ACTIVE`
RF-07-02: `IMPLEMENTATION_CHAIN_INDEPENDENTLY_ACCEPTED`
RF-07-02 closure: `PUBLISHED_PENDING_ACCEPTANCE`
RF-08: `NOT_STARTED`
Runtime: `STOPPED`
Environment: `RUNTIME_ELIGIBLE`
Production: `NOT_PRODUCTION_READY`

## Scope

This foundation provides one immutable-pinned, least-privilege workflow and a standard-library-only deterministic verifier for tracked secret scanning, frozen-lock vulnerability auditing, dependency/artifact inventory, installed-distribution reconciliation and license metadata inventory. It does not alter dependencies, source, tests or runtime.

## Independent review and corrective authority

Independent review: `INDEPENDENTLY_ACCEPTED` for C03 and the implementation chain. Artifact content was independently downloaded and verified by ChatGPT through an authenticated GitHub connector. C02 remains corrective-required historical evidence; its first bad object and primary cause are preserved in [CI_SECURITY_SUPPLY_CHAIN_VERIFIER_SELF_TEST_CORRECTION_v1.0.md](CI_SECURITY_SUPPLY_CHAIN_VERIFIER_SELF_TEST_CORRECTION_v1.0.md). C03 is independently accepted at `1e911fc4680296a2a81c634e56cd57ed6b333fd5` in [CI_SECURITY_WORKFLOW_REJECTION_MATRIX_CORRECTION_v1.0.md](CI_SECURITY_WORKFLOW_REJECTION_MATRIX_CORRECTION_v1.0.md). Closure: [CI_SECURITY_AND_SUPPLY_CHAIN_CLOSURE_v1.0.md](CI_SECURITY_AND_SUPPLY_CHAIN_CLOSURE_v1.0.md).

Tracked-file evidence now records the normalized classification stream and `classification_inventory_sha256`; text, binary and safe-symlink counts must sum to the tracked count. The historical published evidence remains preserved: zero secret findings and zero vulnerability findings. RF-07-02 implementation and corrective chain is independently accepted; deferred RF-07 gates remain required and production remains `NOT_PRODUCTION_READY`.

## Accepted correction prerequisite

The pytest correction is independently accepted through `7c594e49db75cce8a6f411fa0c8ceea59d8b0518`, run `30200967700`, with downloaded integrity and quality evidence PASS. The accepted lock contains pytest 9.0.3 and pytest-asyncio 1.4.0; RF-07-02 remains blocked pending C03 acceptance.

## Workflow triggers and permissions

`CI Security and Supply Chain Foundation` runs on pushes to `main`, pull requests and `workflow_dispatch`. It has one `security-supply-chain` job, top-level `contents: read`, ref-scoped concurrency and a 30-minute timeout.

## Immutable action pins

Checkout, setup-uv and upload-artifact are pinned to the required 40-character commit IDs. Credentials are not persisted and artifact retention is 30 days.

## Secret-scan rules

The verifier enumerates only `git ls-files -z`, scans all tracked regular text files, classifies binary files, rejects unsafe symlinks and fails closed on unreadable or oversized text. It detects private-key markers, high-confidence GitHub/AWS/Slack/Telegram formats, URL userinfo passwords, sensitive tracked filenames and populated secret-like assignments while allowing documented placeholders and prose examples.

## Secret evidence redaction

Evidence stores repository-relative path, line, rule, binary classification and a SHA-256 digest of a match. It never stores the matched value, environment dumps or absolute task paths.

## Vulnerability-audit contract

The exact frozen `uv audit --frozen --output-format json --no-progress` command is recorded with normalized advisory data. Any active finding or adverse status fails; no ignore or suppression policy exists.

## Dependency inventory

`tomllib` parses committed `pyproject.toml` and `uv.lock`. The accepted inventory is 50 package records, 49 registry records, one editable root, 48 sdists, 246 wheels, 294 artifacts, all hashed, 294 unique URLs and no duplicate or conflicting URL/hash records.

## Installed-distribution reconciliation

`importlib.metadata` inventories only the supplied task environment. Non-project distributions must match the lock at the same version; platform-excluded lock records are not required to be installed.

## License inventory and explicit absence of legal policy

Each installed distribution receives exactly one metadata classification: SPDX expression, License field, classifier-only, metadata unspecified or project-owned undeclared. This records metadata only; it invents no SPDX mapping, allow/deny rule or legal-compliance conclusion. Status is `INVENTORY_COMPLETE_POLICY_NOT_EVALUATED`.

## Workflow supply-chain checks

The verifier checks exact action sequence and immutable pins, exact top-level `contents: read`, absence of every explicit write permission, secrets context, persisted credentials, `pull_request_target`, forbidden commands, `continue-on-error` and exact single 30-day artifact retention. C03 ST17 proves the 13-subcase rejection matrix.

## Local equivalent evidence

The local gate runs offline and online lock checks, frozen sync, `uv pip check`, verifier self-test, complete security verification and the existing unchanged quality verifier. Accepted local quality remains Ruff 648/648, mypy 249/249/249 with 29 notes, import-linter 3/0, pytest 4511/4511 and 85% coverage.

## Remote CI evidence

The push-triggered workflow must complete successfully with zero secret findings, zero vulnerability findings and PASS evidence. Safe task artifacts are retained for 30 days and are not production evidence.

## Artifact schema and retention

Evidence JSON uses schema version 1, stable sorted keys, UTF-8/LF atomic writes and safe redacted summaries. The artifact is named by published SHA and retained 30 days.

## No dependency/source/test/runtime mutation

`pyproject.toml`, `uv.lock`, source, tests, the existing quality workflow and verifier are unchanged. PostgreSQL, migrations, Docker, Compose, services, providers and deployment are outside this task.

## Rollback

The task-owned backup contains all eight preimages, one absent marker, identity records and an aggregate digest. Before push, restore preimages, remove new files and task residue, then remove the disposable worktree and branch. The source checkout and promoted inputs remain unchanged.

## Deferred RF-07 gates

This task does not yet provide PostgreSQL integration CI, migration from-zero CI, migration current-head CI, Docker build, Compose validation, synthetic E2E or deployment. These remain later exact RF-07 tasks; RF-08 is not started.

## Limitations

Metadata inventory is not a legal policy and zero current findings do not prove production readiness. Runtime remains stopped.

## Verdict

`RF07_CI_SECURITY_AND_SUPPLY_CHAIN_CLOSURE_PUBLISHED_PENDING_ACCEPTANCE`
