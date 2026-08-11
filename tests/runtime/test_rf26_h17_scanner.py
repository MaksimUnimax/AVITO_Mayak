from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.runtime.check_rf24_backup_restore_artifact_safety import scan_tree

MODULE = "scripts.runtime.check_rf24_backup_restore_artifact_safety"


def _run(root: Path, result: Path, path_env: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PATH=path_env)
    return subprocess.run(
        [sys.executable, "-m", MODULE, "--root", str(root), "--result", str(result)],
        capture_output=True,
        text=True,
        env=env,
    )


def test_safe_tree_passes_without_rg(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "safe.json").write_text('{"status":"PASS"}\n')
    result = tmp_path / "scan.json"
    completed = _run(root, result, str(tmp_path))
    assert completed.returncode == 0
    assert result.exists()


def test_secret_like_fixture_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "bad.json").write_text("postgresql://user:password@db/app\n")
    completed = _run(root, tmp_path / "scan.json", os.environ["PATH"])
    assert completed.returncode != 0


def test_missing_tree_is_not_clean(tmp_path: Path) -> None:
    completed = _run(tmp_path / "missing", tmp_path / "scan.json", os.environ["PATH"])
    assert completed.returncode != 0


def test_h17_inventory_closes_and_order_is_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "b.json").write_text("{}\n")
    (root / "a.json").write_text("{}\n")
    first = scan_tree(root)
    second = scan_tree(root)
    assert first == second
    assert first["enumerated_entry_count"] == first["classified_entry_count"] == 2
    assert [item["path"] for item in first["inventory"]] == ["a.json", "b.json"]


@pytest.mark.parametrize(
    ("name", "writer", "classification"),
    [
        ("credential.json", lambda p: p.write_text("password=synthetic-secret\n"), "SECRET"),
        ("private.pem", lambda p: p.write_text("-----BEGIN PRIVATE KEY-----\n"), "SECRET"),
        (
            "credential-url.txt",
            lambda p: p.write_text("postgresql://user:synthetic@db/app\n"),
            "SECRET",
        ),
        ("oversized.txt", lambda p: p.write_bytes(b"x" * (1_048_576 + 1)), "OVERSIZED"),
        ("undecodable.txt", lambda p: p.write_bytes(b"\xff\xfe"), "UNDECODABLE"),
        ("binary.bin", lambda p: p.write_bytes(b"\x00synthetic"), "BINARY"),
    ],
)
def test_h17_adversarial_entries_are_explicitly_classified(
    tmp_path: Path, name, writer, classification
) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    path = root / name
    writer(path)
    report = scan_tree(root)
    assert any(item["classification"] == classification for item in report["findings"])
    assert report["enumerated_entry_count"] == report["classified_entry_count"] == 1
    assert "synthetic-secret" not in str(report)


def test_h17_symlink_is_visible_and_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("safe\n")
    (root / "escape").symlink_to(outside)
    report = scan_tree(root)
    assert report["inventory"] == [{"path": "escape", "classification": "SYMLINK"}]
    assert report["findings"][0]["classification"] == "SYMLINK"


def test_h17_empty_root_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="empty"):
        scan_tree(tmp_path / "empty")
