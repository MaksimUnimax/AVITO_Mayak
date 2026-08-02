from pathlib import Path

TABLE_9_BLOCK = (
    "### 9. `entitlement_tariff_definitions`\n"
    "Owner: module 03. Purpose: versioned Free/Basic tariff terms. Mutability: immutable. "
    "PK: id uuid. Required: code varchar(64) NOT NULL, version bigint NOT NULL, "
    "price_minor bigint NOT NULL, currency char(3) NOT NULL, min_interval_seconds bigint NOT NULL, "
    "step_seconds bigint NOT NULL, active_beacon_limit bigint NOT NULL, "
    "active_from timestamptz NOT NULL, active_until timestamptz NULL, "
    "created_at timestamptz NOT NULL. "
    "FKs: none. Unique: (code,version). "
    "Indexes: (code,active_from). Checks: price nonnegative; interval and step positive; "
    "active_beacon_limit > 0; currency length 3; active_until > active_from. "
    "Retention/delete: immutable, retain synthetic max 14 days only where applicable. "
    "Privacy: internal. Forbidden: provider payload. Writer: Entitlement owner only; "
    "current approved Free/Basic active-Beacon limits are tariff authority "
    "and are not supplied by Beacon/UI callers."
)

FOCUSED_PYTEST_PATHS = {
    "tests/runtime/test_rf12_command_matrix.py",
    "tests/runtime/test_rf12_runtime_postgres.py",
    "tests/runtime/test_rf12_persistence_injection.py",
    "tests/runtime/test_rf12_finalizer.py",
    "tests/runtime/test_rf12_verifier_schema.py",
    "tests/runtime/test_rf12_tamper_matrix.py",
    "tests/runtime/test_rf12_phase_ownership.py",
    "tests/runtime/test_rf12_usage_policy_contract.py",
    "tests/runtime/test_rf12_workflow_inventory.py",
    "tests/unit/test_entitlements_and_billing_contracts.py",
    "tests/unit/test_usage_consumption_semantics.py",
    "tests/runtime/test_entitlements_schema.py",
}

RUFF_PATHS = {
    "alembic/env.py",
    "alembic/versions/20260802_RF12_BASIC_BEACON_LIMIT.py",
    "scripts/runtime/run_rf12_postgres_acceptance.py",
    "scripts/runtime/verify_rf12_acceptance.py",
    "scripts/runtime/finalize_rf12_acceptance_evidence.py",
    "scripts/runtime/run_rf12_tamper_matrix.py",
    "src/mayak/modules/entitlements_and_billing/contracts.py",
    "src/mayak/modules/entitlements_and_billing/policies.py",
    "src/mayak/modules/entitlements_and_billing/runtime.py",
    "src/mayak/modules/entitlements_and_billing/usage_consumption.py",
    "src/mayak/persistence/config.py",
    "src/mayak/persistence/schema/entitlements.py",
    "tests/runtime/test_entitlements_schema.py",
    "tests/runtime/test_rf12_command_matrix.py",
    "tests/runtime/test_rf12_runtime_postgres.py",
    "tests/runtime/test_rf12_persistence_injection.py",
    "tests/runtime/test_rf12_finalizer.py",
    "tests/runtime/test_rf12_verifier_schema.py",
    "tests/runtime/test_rf12_tamper_matrix.py",
    "tests/runtime/test_rf12_phase_ownership.py",
    "tests/runtime/test_rf12_usage_policy_contract.py",
    "tests/runtime/test_rf12_workflow_inventory.py",
    "tests/unit/test_entitlements_and_billing_contracts.py",
    "tests/unit/test_usage_consumption_semantics.py",
}

MYPY_PATHS = {
    "src/mayak/modules/entitlements_and_billing/contracts.py",
    "src/mayak/modules/entitlements_and_billing/policies.py",
    "src/mayak/modules/entitlements_and_billing/runtime.py",
    "src/mayak/modules/entitlements_and_billing/usage_consumption.py",
    "src/mayak/persistence/config.py",
    "src/mayak/persistence/schema/entitlements.py",
    "scripts/runtime/run_rf12_postgres_acceptance.py",
    "scripts/runtime/verify_rf12_acceptance.py",
    "scripts/runtime/finalize_rf12_acceptance_evidence.py",
    "scripts/runtime/run_rf12_tamper_matrix.py",
}


def _command_paths(source: str, prefix: str) -> set[str]:
    return set(source.split(prefix, 1)[1].split("\n", 1)[0].split())


def test_hosted_workflow_invokes_every_rf12_harness_test() -> None:
    source = Path(".github/workflows/ci-rf12-acceptance.yml").read_text(encoding="utf-8")
    pytest_command = source.split("uv run pytest -q ", 1)[1].split("\n", 1)[0]
    assert FOCUSED_PYTEST_PATHS <= set(pytest_command.split())
    assert RUFF_PATHS <= _command_paths(source, "uv run ruff check ")
    assert MYPY_PATHS <= _command_paths(source, "uv run mypy ")


def test_workflow_identity_and_verifier_stage_are_fail_closed() -> None:
    source = Path(".github/workflows/ci-rf12-acceptance.yml").read_text(encoding="utf-8")
    technical_id = "RF-12-CORRECTIVE-VERIFIER-FAIL-CLOSED-AND-EVIDENCE-IDENTITY-CLOSURE-20260802-08"
    assert f"RF12_TECHNICAL_ID: {technical_id}" in source
    producer = source.index("run_rf12_postgres_acceptance.py")
    verifier = source.index("verify_rf12_acceptance.py", producer)
    tamper = source.index("run_rf12_tamper_matrix.py", verifier)
    assert source.count("$RF12_TECHNICAL_ID") >= 3
    assert "--technical-id \"$RF12_TECHNICAL_ID\"" in source
    assert '"$RF12_TECHNICAL_ID" 2>&1 | tee' in source
    assert "set -o pipefail" in source
    assert "grep -Fxq 'RF12_ACCEPTANCE_VERIFIED'" in source
    assert "if: success()" in source
    assert producer < verifier < tamper
    assert "continue-on-error" not in source
    assert "|| true" not in source[source.index("Run final independent verifier"):]
    assert "verifier.txt" in source
    assert "tamper-negative.json" in source


def test_shell_contract_cannot_mask_nonzero_verifier_with_tee(tmp_path: Path) -> None:
    import subprocess

    script = "set -o pipefail; sh -c 'echo RF12 verifier failed; exit 7' 2>&1 | tee verifier.txt"
    result = subprocess.run(["bash", "-c", script], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 7


def test_physical_data_model_table_9_is_canonical() -> None:
    document = Path(
        "docs/04-modules/14-runtime-foundation-and-autonomous-integration/PHYSICAL_DATA_MODEL_v1.0.md"
    ).read_text(encoding="utf-8")
    assert document.count("### 9. `entitlement_tariff_definitions`") == 1
    assert document.count(TABLE_9_BLOCK) == 1
    assert "9. entitlement_tariff_definitions" not in document
    table_8 = "### 8. `identity_link_challenges`"
    table_10 = "### 10. `entitlement_access_grants`"
    assert document.index(table_8) < document.index(TABLE_9_BLOCK) < document.index(table_10)
