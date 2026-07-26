# CI Security Workflow Rejection Matrix Correction

Version: 1.0
Status: `INDEPENDENTLY_ACCEPTED`
Date: 2026-07-26
Technical ID: `RF-07-02-CORRECTIVE-03-WORKFLOW-SECURITY-REJECTION-MATRIX-20260726`
Base: `1ca9b56860d72e13bb21cd437684f95f1a39aa90`
RF-07: `ACTIVE`
RF-07-02-C02: `CORRECTIVE_REQUIRED_HISTORICAL`
RF-07-02-C03: `INDEPENDENTLY_ACCEPTED`
RF-07-02: `IMPLEMENTATION_CHAIN_INDEPENDENTLY_ACCEPTED`
RF-08: `NOT_STARTED`
Runtime: `STOPPED`
Environment: `RUNTIME_ELIGIBLE`
Production: `NOT_PRODUCTION_READY`

## Scope

This atomic correction changes only the RF-07-02 workflow-security helper, ST17 rejection-matrix authority and the necessary governance/index records. The workflow YAML, dependencies, source, tests, runtime and quality baseline are unchanged.

## Independent artifact verification clearing the C02 download blocker

The accepted artifact is ID `8632808900`, digest `sha256:41e602b2a67aac18c444a9fb8f1084de10bf8bfa77287ba7ec15e22fc0cb03d2`, source SHA `1e911fc4680296a2a81c634e56cd57ed6b333fd5`, and independent artifact-content verification is `PASS`. Artifact content was independently downloaded and verified by ChatGPT through an authenticated GitHub connector before this closure task; the CLI did not download it.

## Independent rejection trigger

Independent source review proved that published ST17 executed one positive PASS assertion and no rejection case. The evidence therefore did not prove the required workflow-security rejection matrix.

## First bad object

`scripts/ci/verify_security_supply_chain.py::self_test::ST17_WORKFLOW_PIN_PERMISSION_AND_FORBIDDEN_CHECKS`

## Primary proven cause

`WORKFLOW_SECURITY_SELF_TEST_POSITIVE_ONLY_AND_HELPER_FAILS_OPEN_ON_MISSING_ACTIONS_OR_ADDITIONAL_WRITE_PERMISSIONS`

## Five-transition trace

1. `TRANSITION_01_C02_CONTRACT`: C02 required ST17 action-pin and permission rejection cases.
2. `TRANSITION_02_PUBLISHED_ST17`: published ST17 contained one positive PASS assertion and zero negative assertions.
3. `TRANSITION_03_FAIL_OPEN_HELPER`: empty action lists and additional write permissions were not rejected by the published helper.
4. `TRANSITION_04_REMOTE_SELF_TEST_PASS`: remote CI emitted 17/17 PASS because rejection behavior was not exercised.
5. `TRANSITION_05_INDEPENDENT_SOURCE_REVIEW`: source inspection proved the missing matrix and fail-open conditions despite successful artifact evidence.

## Published positive-only ST17 behavior

The rejected C02 ST17 constructed one nominal synthetic workflow and asserted only `status == PASS`. It did not execute any rejection case.

## Published helper fail-open behavior

The rejected C02 helper treated `all(...)` over an empty action list as true and searched only for one `contents: read` fragment plus absence of literal `write-all`; it did not enforce the exact action sequence or reject additional write permissions.

## Exact accepted action sequence

The only accepted sequence, exactly once and in order, is:

1. `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
2. `astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b`
3. `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

## Named workflow-security checks

`exact_action_sequence`, `nonempty_action_sequence`, `immutable_action_pins`, `top_level_permissions_exact`, `no_write_permissions`, `no_secrets_context`, `persist_credentials_false_exactly_once`, `no_pull_request_target`, `no_continue_on_error`, `no_forbidden_commands`, `retention_30_exactly_once`.

## Exact 13-subcase rejection matrix

`WF00_CURRENT_WORKFLOW_PASS`, `WF01_EMPTY_ACTION_LIST_REJECTED`, `WF02_MISSING_EXPECTED_ACTION_REJECTED`, `WF03_DUPLICATE_ACTION_REJECTED`, `WF04_MUTABLE_OR_WRONG_PIN_REJECTED`, `WF05_UNEXPECTED_ACTION_REJECTED`, `WF06_CONTENTS_WRITE_REJECTED`, `WF07_ADDITIONAL_WRITE_PERMISSION_REJECTED`, `WF08_SECRETS_CONTEXT_REJECTED`, `WF09_PERSISTED_CREDENTIALS_REJECTED`, `WF10_PULL_REQUEST_TARGET_REJECTED`, `WF11_FORBIDDEN_OR_CONTINUE_COMMAND_REJECTED`, `WF12_INVALID_RETENTION_REJECTED`.

Each negative case mutates only an in-memory workflow string, requires overall `FAIL` and verifies the exact named check becomes false. The matrix includes an incorrect 40-character SHA, an empty action list and `actions: write` while `contents: read` remains present. No workflow content is executed and no repository file is mutated.

## Machine-readable ST17 authority

ST17 executes the production `workflow_check()` helper. Its evidence contains the exact 13 IDs, expected failed-check identities, 13/13 counts and safe detail code `WORKFLOW_REJECTION_MATRIX_PASS_13_OF_13`. Full verification rejects any other ST17 detail code. Top-level self-test authority remains exactly 17 IDs, 17 executed, 17 passed and zero failed, with stdout `SELF_TEST_PASS cases=17/17`.

## Local evidence

Local repeated self-test, direct helper matrix and full security runs pass deterministically. Required results are 13/13 matrix, 17/17 self-test, tracked files 455, zero secret findings, zero vulnerabilities, dependency inventory PASS, installed-vs-lock PASS, license inventory `INVENTORY_COMPLETE_POLICY_NOT_EVALUATED`, workflow security PASS and final PASS.

## Remote evidence

The push-triggered security and quality workflows are required to complete successfully. Security must report 17/17, ST17 detail `WORKFLOW_REJECTION_MATRIX_PASS_13_OF_13`, workflow security PASS, zero secret/vulnerability findings, dependency and installed-vs-lock PASS, license policy not evaluated and final PASS. Quality remains Ruff 648/648, mypy 249/249/249 with 29 notes, import-linter 3/0, pytest 4511/4511 and 85% coverage.

## Unchanged workflow YAML

`.github/workflows/ci-security-supply-chain.yml` remains byte-identical at blob `026b6d2746bec8c9ec5e333d387fccc58c96ce88`.

## Existing quality regression evidence

The existing quality workflow and verifier remain unchanged and authoritative: Ruff 648/648, mypy 249/249/249 with 29 notes, import-linter 3/0, pytest 4511/4511 and 85% coverage.

## No dependency/source/test/runtime mutation

`pyproject.toml`, `uv.lock`, `src/**`, `tests/**`, quality files and runtime inputs are unchanged. No Docker, database, migration, listener, service, provider or foreign-resource operation occurred.

## Rollback

The task backup retains eight preimages, an absent marker for this file, identity records, safe evidence summaries and a deterministic aggregate digest. Before push, restoring preimages, removing this file and task residue, and deleting the disposable worktree and branch is feasible without touching the source checkout or promoted environments.

## Limitations

This correction proves workflow-verifier behavior and evidence authority only. License policy is not evaluated, deferred RF-07 gates remain, runtime is stopped and production readiness is not established.

## Verdict

`RF07_WORKFLOW_SECURITY_REJECTION_MATRIX_CORRECTION_INDEPENDENTLY_ACCEPTED`
