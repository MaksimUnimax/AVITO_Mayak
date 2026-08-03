# ruff: noqa: E501, I001
from pathlib import Path


def test_rf17_hosted_migration_uses_consumed_compatibility_alias_and_loopback_gate() -> None:
    workflow = Path(".github/workflows/ci-rf17-acceptance.yml").read_text(encoding="utf-8")
    assert "RF15_MIGRATION_DSN: postgresql+psycopg://mayak_migration" in workflow
    assert "build_migration_url(require_secret=False)" in workflow
    assert "assert url.host == '127.0.0.1'" in workflow
    assert workflow.index("Check migration URL host before Alembic") < workflow.index("uv run alembic upgrade head")
