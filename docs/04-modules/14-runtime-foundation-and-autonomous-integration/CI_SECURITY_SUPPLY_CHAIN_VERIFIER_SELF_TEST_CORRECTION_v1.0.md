# CI Security Supply-Chain Verifier Self-Test Correction

Version: 1.0
Status: `PUBLISHED_PENDING_ACCEPTANCE`
Date: 2026-07-26
Technical ID: `RF-07-02-CORRECTIVE-02-SECURITY-VERIFIER-SELF-TEST-AND-CLASSIFICATION-DETERMINISM-20260726`
Base: `7814cf7fa8553f75fdbe53c51fd03428e87f4738`
RF-07: `ACTIVE`
RF-07-02-C02: `PUBLISHED_PENDING_ACCEPTANCE`
RF-07-02: `BLOCKED_PENDING_CORRECTION_ACCEPTANCE`
RF-08: `NOT_STARTED`
Runtime: `STOPPED`
Environment: `RUNTIME_ELIGIBLE`
Production: `NOT_PRODUCTION_READY`

## Scope

This atomic correction changes only verifier self-test authority, deterministic tracked-file classification evidence, the existing security workflow gate and the necessary governance/index records. Dependencies, source, tests, runtime and the quality workflow are unchanged.

## Independent rejection trigger

The published RF-07-02 self-test emitted a single success marker while proving only smoke assertions. Independent source inspection found missing required behavior classes, and local and remote classification counts differed.

## First bad object

`scripts/ci/verify_security_supply_chain.py::self_test`

## Primary proven cause

`SELF_TEST_IMPLEMENTED_AS_SMOKE_ASSERTIONS_WITHOUT_EXPLICIT_CASE_COVERAGE_AUTHORITY`

## Five-transition trace

1. `TRANSITION_01_TASK_CONTRACT`: RF-07-02 required 17 explicit self-test behavior classes.
2. `TRANSITION_02_PUBLISHED_IMPLEMENTATION`: published `self_test()` contained only narrow smoke assertions.
3. `TRANSITION_03_LOCAL_REPORTED_PASS`: CLI reported `Security-Verifier-Self-Test: PASS` without case inventory or count proof.
4. `TRANSITION_04_REMOTE_JOB_PASS`: Actions accepted the single `SELF_TEST_PASS` marker.
5. `TRANSITION_05_INDEPENDENT_DIVERGENCE`: source inspection proved missing classes and classification counts differed.

## Missing published self-test coverage

The missing contracts were PEM keys, populated assignments, finding schema, binary classification, unsafe symlink rejection, ordering, duplicate elimination, zero/non-zero audit parsing, license classification, lock parsing, installed reconciliation and workflow rejection cases.

## Exact 17 corrected test cases

`ST01_PEM_PRIVATE_KEY_DETECTION`, `ST02_KNOWN_TOKEN_FORMAT_DETECTION`, `ST03_POPULATED_SECRET_ASSIGNMENT_DETECTION`, `ST04_PLACEHOLDER_ASSIGNMENT_NOT_FLAGGED`, `ST05_URL_USERINFO_REDACTION`, `ST06_RAW_SECRET_VALUE_NOT_STORED`, `ST07_FINDING_SCHEMA_MINIMAL_FIELDS`, `ST08_BINARY_FILE_CLASSIFICATION`, `ST09_UNSAFE_SYMLINK_REJECTION`, `ST10_DETERMINISTIC_FINDING_SORT`, `ST11_DUPLICATE_FINDING_ELIMINATION`, `ST12_ZERO_VULNERABILITY_AUDIT_PARSE`, `ST13_NONZERO_VULNERABILITY_AUDIT_PARSE`, `ST14_LICENSE_METADATA_CLASSIFICATION`, `ST15_LOCK_INVENTORY_PARSE`, `ST16_INSTALLED_DISTRIBUTION_RECONCILIATION`, `ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS`.

## Machine-readable self-test evidence

`--self-test --evidence-dir PATH` executes production helpers against synthetic temporary data, fails closed on the first failed case, and writes `self-test-evidence.json` with schema version 1, source SHA, exact case IDs, executed/passed/failed counts and safe detail codes. Success requires 17/17 and stdout exactly ends with `SELF_TEST_PASS cases=17/17`. Full mode validates the same evidence before writing final evidence.

## Local-versus-remote classification discrepancy

The original local report was `453/452/1/0`; the downloaded remote artifact was `453/453/0/0`. The corrected classifier enumerates only `git ls-files -z`, never follows symlinks, rejects invalid UTF-8 and oversized files, and emits a bytewise UTF-8/LF normalized path/classification stream.

## Discrepancy cause result

`CLASSIFICATION_DISCREPANCY_CAUSE_NOT_PROVEN`: the original CLI report cannot be reproduced as a distinct file-level result from the published source without its original execution trace. No file was excluded or reclassified by machine-specific path. Corrected local and remote evidence must be equal before acceptance.

## Deterministic classification identity

Every tracked path has exactly one of `TEXT`, `BINARY`, or `SAFE_SYMLINK`. Evidence includes the equation, counts, binary/symlink relative-path lists and `classification_inventory_sha256`; no absolute paths, timestamps, locale or task environment paths participate.

## Local corrected evidence

Required local evidence is self-test 17/17, repeated byte-deterministic self-test JSON, repeated stable classification inventory, zero secret findings, zero vulnerabilities, PASS dependency and installed reconciliation, complete license inventory with policy not evaluated, PASS workflow security and final PASS.

## Remote corrected evidence

The existing security workflow requires the self-test evidence file and all prior evidence files, uploads them under the immutable published-SHA artifact name, and independently verifies the same counts, lists, digest and final status.

## Existing quality regression evidence

The unchanged quality workflow/verifier remains authoritative: Ruff 648/648, mypy 249/249/249 with 29 notes, import-linter 3 kept/0 broken, pytest 4511/4511 and 85% coverage.

## No dependency/source/test/runtime mutation

`pyproject.toml`, `uv.lock`, `src/**`, `tests/**`, the quality workflow and quality verifier are unchanged. No runtime, Docker, database, listener, service or foreign resource was started or mutated.

## Rollback

The task backup retains seven preimages, the absent new-file marker, identity metadata, rollback instructions and a deterministic aggregate digest. Restore those preimages, remove the correction file and task residue, then remove the disposable worktree and task branch before push if rollback is required.

## Limitations

This is verifier and evidence correction only. It does not establish production readiness, legal license policy, runtime deployment or acceptance of deferred RF-07 gates.

## Verdict

`RF07_SECURITY_VERIFIER_SELF_TEST_AND_CLASSIFICATION_CORRECTION_PUBLISHED_PENDING_ACCEPTANCE`
