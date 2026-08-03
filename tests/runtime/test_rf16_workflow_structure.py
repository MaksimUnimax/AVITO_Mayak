from pathlib import Path

WORKFLOW = (Path(__file__).parents[2] / ".github/workflows/ci-rf16-acceptance.yml").read_text()


def test_rf16_workflow_uses_block_checkout_and_required_order() -> None:
    assert "with: {ref: ${{ github.sha }}}" not in WORKFLOW
    assert 'ref: "${{ github.sha }}"' in WORKFLOW
    ordered = [
        "image: postgres:18",
        "uses: actions/checkout@v4",
        "python-version: '3.14.6'",
        "version: '0.11.31'",
        "uv sync --frozen",
        "bootstrap_database",
        "alembic upgrade head",
        "run_rf16_postgres_acceptance.py",
        "verify_rf16_acceptance.py",
        "Independent immutable RF16 meta-gate",
        "if: always()",
    ]
    positions = [WORKFLOW.index(item) for item in ordered]
    assert positions == sorted(positions)


def test_rf16_workflow_separates_verifier_surfaces_and_binds_sha() -> None:
    for required in (
        '--expected-sha "$GITHUB_SHA"',
        "rf16-verifier-diagnostics.json",
        "rf16-verifier.stdout",
        "rf16-verifier.stderr",
        "RF16_ACCEPTANCE_VERIFIED",
        "requirement_count",
        "tamper_rejected_count",
    ):
        assert required in WORKFLOW
