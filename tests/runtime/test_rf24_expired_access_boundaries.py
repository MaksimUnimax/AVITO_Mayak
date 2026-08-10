from __future__ import annotations

from pathlib import Path

import pytest

from scripts.runtime.check_rf24_expired_access_artifact_safety import scan
from scripts.runtime.check_rf24_expired_access_ownership import violations
from scripts.runtime.check_rf24_expired_access_static_delta import delta
from scripts.runtime.check_rf24_expired_access_workflow import validate


def test_scanner_negative_cases_execute_one_to_one(tmp_path: Path) -> None:
    for case_id, payload in (
        ("authorization", "Authorization: Bearer secret"),
        ("password", "password=secret"),
        ("private-key", "-----BEGIN OPENSSH PRIVATE KEY-----"),
        ("provider-body", "raw_provider_payload"),
    ):
        path = tmp_path / case_id
        path.write_text(payload, encoding="utf-8")
        assert scan([path]) > 0, case_id


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        ("from mayak.modules.beacon_management import runtime", "foreign import"),
        (
            "session.execute(text('UPDATE mayak.beacon_beacons SET state=\\'FROZEN\\''))",
            "foreign DML",
        ),
    ],
)
def test_ownership_negative_cases_execute_one_to_one(
    tmp_path: Path, source: str, reason: str
) -> None:
    path = tmp_path / "src/mayak/modules/scan_orchestration/bad.py"
    path.parent.mkdir(parents=True)
    path.write_text(source, encoding="utf-8")
    assert violations(tmp_path), reason


def test_workflow_valid_fixture_and_independent_mutations() -> None:
    workflow = Path(".github/workflows/ci-rf24-expired-access.yml").read_text(encoding="utf-8")
    assert validate(workflow) == []
    for needle in (
        "ref: ${{ github.sha }}",
        "alembic upgrade head",
        "verify_rf24_expired_access.py",
        "upload-artifact",
    ):
        assert validate(workflow.replace(needle, "")), needle


@pytest.mark.parametrize(
    ("base", "candidate", "changed", "accepted"),
    [
        (
            [{"path": "a.py", "code": "E1", "line": "1", "message": "old"}],
            [{"path": "a.py", "code": "E1", "line": "1", "message": "old"}],
            set(),
            True,
        ),
        ([{"path": "a.py", "code": "E1", "line": "1", "message": "old"}], [], set(), True),
        ([], [{"path": "a.py", "code": "E1", "line": "1", "message": "new"}], set(), False),
        ([], [{"path": "a.py", "code": "E1", "line": "1", "message": "new"}], {"a.py"}, False),
    ],
)
def test_static_delta_cases_execute(base, candidate, changed, accepted) -> None:
    assert delta(base, candidate, changed)["accepted"] is accepted
