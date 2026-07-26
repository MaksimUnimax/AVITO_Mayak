# CI Security Supply-Chain Verifier Self-Test Correction

Version: 1.0
Status: `CORRECTIVE_REQUIRED`
Date: 2026-07-26
Technical ID: `RF-07-02-CORRECTIVE-02-SECURITY-VERIFIER-SELF-TEST-AND-CLASSIFICATION-DETERMINISM-20260726`
Base: `7814cf7fa8553f75fdbe53c51fd03428e87f4738`
RF-07: `ACTIVE`
RF-07-02-C02: `CORRECTIVE_REQUIRED`
RF-07-02: `BLOCKED_PENDING_CORRECTION_ACCEPTANCE`
RF-08: `NOT_STARTED`
Runtime: `STOPPED`
Environment: `RUNTIME_ELIGIBLE`
Production: `NOT_PRODUCTION_READY`

## Scope

This atomic correction changes only verifier self-test authority, deterministic tracked-file classification evidence, the existing security workflow gate and the necessary governance/index records. Dependencies, source, tests, runtime and the quality workflow are unchanged.

## Independent rejection trigger

The published RF-07-02 artifact was independently downloaded and verified: run `30203557863`, job `89797607207`, artifact `8632382718`, digest `sha256:d708d25fea7a493848cf7c49b0be7aa2fad39d537ee4358e8fc6d2bf56817e71`, source `1ca9b56860d72e13bb21cd437684f95f1a39aa90`, 17/17, classification `454/454/0/0`, zero secret and vulnerability findings, final `PASS`. Artifact unavailability is not a current blocker.

Independent source inspection found the next first proven blocking defect: published ST17 proves only one positive workflow assertion and zero rejection cases.

## First bad object

`scripts/ci/verify_security_supply_chain.py::self_test::ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS`

## Primary proven cause

`WORKFLOW_SECURITY_SELF_TEST_POSITIVE_ONLY_AND_HELPER_FAILS_OPEN_ON_MISSING_ACTIONS_OR_ADDITIONAL_WRITE_PERMISSIONS`

## Five-transition trace

1. `TRANSITION_01_C02_CONTRACT`: C02 required ST17 to prove action-pin and permission rejection cases.
2. `TRANSITION_02_PUBLISHED_ST17`: published ST17 contained one positive PASS assertion and zero negative assertions.
3. `TRANSITION_03_FAIL_OPEN_HELPER`: published `workflow_check()` accepted an empty action list and did not reject all explicit write-permission forms.
4. `TRANSITION_04_REMOTE_SELF_TEST_PASS`: remote CI emitted 17/17 PASS because positive-only ST17 did not exercise rejection behavior.
5. `TRANSITION_05_INDEPENDENT_SOURCE_REVIEW`: source inspection proved the missing negative matrix and fail-open helper conditions despite successful artifact evidence.

## Missing published self-test coverage

The missing contracts were PEM keys, populated assignments, finding schema, binary classification, unsafe symlink rejection, ordering, duplicate elimination, zero/non-zero audit parsing, license classification, lock parsing, installed reconciliation and workflow rejection cases.

## Exact 17 corrected test cases

`ST01_PEM_PRIVATE_KEY_DETECTION`, `ST02_KNOWN_TOKEN_FORMAT_DETECTION`, `ST03_POPULATED_SECRET_ASSIGNMENT_DETECTION`, `ST04_PLACEHOLDER_ASSIGNMENT_NOT_FLAGGED`, `ST05_URL_USERINFO_REDACTION`, `ST06_RAW_SECRET_VALUE_NOT_STORED`, `ST07_FINDING_SCHEMA_MINIMAL_FIELDS`, `ST08_BINARY_FILE_CLASSIFICATION`, `ST09_UNSAFE_SYMLINK_REJECTION`, `ST10_DETERMINISTIC_FINDING_SORT`, `ST11_DUPLICATE_FINDING_ELIMINATION`, `ST12_ZERO_VULNERABILITY_AUDIT_PARSE`, `ST13_NONZERO_VULNERABILITY_AUDIT_PARSE`, `ST14_LICENSE_METADATA_CLASSIFICATION`, `ST15_LOCK_INVENTORY_PARSE`, `ST16_INSTALLED_DISTRIBUTION_RECONCILIATION`, `ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS`.

## Machine-readable self-test evidence

`--self-test --evidence-dir PATH` executes production helpers against synthetic temporary data, fails closed on the first failed case, and writes exact 17-case evidence. ST17 now executes exactly 13 subcases (`WF00`–`WF12`), records their IDs and expected failed named checks, and requires safe detail code `WORKFLOW_REJECTION_MATRIX_PASS_13_OF_13`. The 16 other top-level cases and their order remain preserved. Success requires 17/17 and stdout exactly ends with `SELF_TEST_PASS cases=17/17`; full mode rejects any other ST17 detail code.

## C03 corrective artifact

The corrective implementation and evidence authority are published in [CI_SECURITY_WORKFLOW_REJECTION_MATRIX_CORRECTION_v1.0.md](CI_SECURITY_WORKFLOW_REJECTION_MATRIX_CORRECTION_v1.0.md). It retains the exact accepted current workflow, rejects missing, mutable, duplicate, unexpected and incorrectly pinned actions, and rejects every explicit write permission. RF-07-02 remains blocked pending C03 acceptance.

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

`RF07_SECURITY_VERIFIER_SELF_TEST_AND_CLASSIFICATION_CORRECTION_CORRECTIVE_REQUIRED`
