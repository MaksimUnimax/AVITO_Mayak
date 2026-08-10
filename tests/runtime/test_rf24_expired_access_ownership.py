from pathlib import Path

from scripts.runtime.check_rf24_expired_access_ownership import violations

ROOT = Path(__file__).parents[2]


def test_owner_guard_is_clean():
    assert violations(ROOT) == []


def test_owner_guard_rejects_scan_owner_import(tmp_path):
    (tmp_path / "src/mayak/modules/scan_orchestration").mkdir(parents=True)
    (tmp_path / "src/mayak/modules/scan_orchestration/bad.py").write_text(
        "from mayak.modules.beacon_management import runtime\n", encoding="utf-8"
    )
    assert violations(tmp_path)
