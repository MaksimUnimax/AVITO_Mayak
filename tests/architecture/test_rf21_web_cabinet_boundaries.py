from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]
WEB = ROOT / "src/mayak/modules/web_cabinet"


def test_web_package_has_no_sql_or_foreign_owner_imports() -> None:
    source = "\n".join(path.read_text() for path in WEB.glob("*.py"))
    assert "sqlalchemy" not in source
    assert "mayak.persistence" not in source
    assert "httpx" not in source


def test_templates_and_static_are_local_and_untracked() -> None:
    source = "\n".join(path.read_text() for path in (WEB / "templates").glob("*"))
    source += "\n" + "\n".join(path.read_text() for path in (WEB / "static").glob("*"))
    for marker in (
        "cdn.", "unpkg.com", "fonts.googleapis", "analytics", "tracking", "<script src=",
    ):
        assert marker not in source.lower()
    assert not list(ROOT.glob("package.json"))
    assert not list(ROOT.glob("**/package-lock.json"))
