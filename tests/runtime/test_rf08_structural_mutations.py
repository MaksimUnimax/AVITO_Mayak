from __future__ import annotations

from pathlib import Path

from scripts.runtime.rf08_verify_structural_gateway import verify_source

ROOT = Path(__file__).resolve().parents[2]


def test_exact_production_identity_passes() -> None:
    result = verify_source(ROOT)
    assert result["finding_count"] == 0
    assert result["task_verifier_executable_content"] == "PASS"


def test_host_path_authority_is_rejected(tmp_path: Path) -> None:
    authority = (ROOT / "scripts/runtime/rf08_docker_authority.py").read_text(encoding="utf-8")
    registry = ROOT / "src/mayak/runtime/task_acceptance/__init__.py"
    (tmp_path / "scripts/runtime").mkdir(parents=True)
    (tmp_path / "src/mayak/runtime/task_acceptance").mkdir(parents=True)
    (tmp_path / "scripts/runtime/rf08_docker_authority.py").write_text(
        authority + "\nverifier_path = '/tmp/attacker.py'\n", encoding="utf-8"
    )
    (tmp_path / "src/mayak/runtime/task_acceptance/__init__.py").write_text(
        registry.read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert verify_source(tmp_path)["finding_count"] > 0


def test_safe_local_renaming_does_not_change_verdict(tmp_path: Path) -> None:
    authority = (
        (ROOT / "scripts/runtime/rf08_docker_authority.py")
        .read_text(encoding="utf-8")
        .replace("semantic", "action_value")
    )
    registry = ROOT / "src/mayak/runtime/task_acceptance/__init__.py"
    (tmp_path / "scripts/runtime").mkdir(parents=True)
    (tmp_path / "src/mayak/runtime/task_acceptance").mkdir(parents=True)
    (tmp_path / "scripts/runtime/rf08_docker_authority.py").write_text(authority, encoding="utf-8")
    (tmp_path / "src/mayak/runtime/task_acceptance/__init__.py").write_text(
        registry.read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert verify_source(tmp_path)["finding_count"] == 0
