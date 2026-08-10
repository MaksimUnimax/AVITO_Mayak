from pathlib import Path

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/ci-rf24-backup-restore.yml"


def test_workflow_is_exact_candidate_and_pg18_safe() -> None:
    text = WORKFLOW.read_text()
    for marker in (
        "postgres:18-bookworm",
        "github.sha",
        "uv sync --frozen",
        "pg_dump",
        "pg_restore",
        "pytest -q",
        "upload-artifact",
        "RF25",
    ):
        assert marker in text
    assert "*.dump" not in text
    assert "postgresql" not in text.split("upload-artifact", 1)[-1]


def test_acceptance_scripts_have_no_business_table_dml() -> None:
    for path in (ROOT / "scripts/runtime").glob("*rf24_backup_restore*.py"):
        if path.name == "check_rf24_backup_restore_ownership.py":
            continue
        text = path.read_text()
        assert "INSERT INTO mayak." not in text
        assert "UPDATE mayak." not in text
        assert "DELETE FROM mayak." not in text
