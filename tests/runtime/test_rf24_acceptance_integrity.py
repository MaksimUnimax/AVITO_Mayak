# ruff: noqa: E501
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]


def _module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_scanner = _module("rf24_scanner", "scripts/runtime/check_rf24_spine_artifact_safety.py")
_producer = _module("rf24_producer", "scripts/runtime/run_rf24_vertical_spine.py")
_verifier = _module("rf24_verifier", "scripts/runtime/verify_rf24_vertical_spine.py")
scan = _scanner.scan
SafeResponse = _producer.SafeResponse
verify = _verifier.verify


def test_safe_response_never_projects_transport_cookie() -> None:
    response = SafeResponse(200, {"account_id": "synthetic-account", "set_cookie": "fake"}, "fake-cookie")
    evidence = response.evidence()
    assert "set_cookie" not in json.dumps(evidence)
    assert "fake-cookie" not in repr(evidence)
    assert "fake-cookie" not in repr(response)


@pytest.mark.parametrize(
    "value",
    [
        {"Mayak session cookie": "mayak_session=fake-session"},
        {"set_cookie": "mayak_session=fake-session"},
        {"Cookie": "mayak_session=fake-session"},
        {"Set-Cookie": "mayak_session=fake-session"},
        {"Authorization": "Bearer fake-bearer"},
        {"dsn": "postgresql://user:fake-password@db:5432/mayak"},
        {"key": "-----BEGIN PRIVATE KEY-----"},
    ],
)
def test_safety_scanner_rejects_realistic_credential_shapes(tmp_path: Path, value: dict[str, str]) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert scan([path]) > 0


@pytest.mark.parametrize(
    "value",
    [
        {"session_cookie_issued": True},
        {"safe": None, "empty": "", "redacted": "<redacted>"},
        {"token": "synthetic-id", "password": "schema-field"},
        {"Authorization": None, "Cookie": "<redacted>"},
    ],
)
def test_safety_scanner_allows_safe_schema_and_redaction(tmp_path: Path, value: dict[str, object]) -> None:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    assert scan([path]) == 0


def _known_good() -> dict[str, object]:
    return {
        "source_sha": "a" * 40, "run_id": "rf24-test", "api_bind": "127.0.0.1",
        "postgres_host_published": False, "provider_live_calls": 0,
        "foreign_resource_impact": 0, "production_personal_data": 0, "credentials_exposure": False,
        "security": {"credentials_exposure": False, "serialized_cookie_value_present": False, "authorization_material_present": False},
        "processes": [{"kind": k, "pid": i} for i, k in enumerate(("api", "worker", "scheduler"), 1)],
        "scheduler_cycles": [
            {"cycle": 1, "schedule_id": "s", "work_item_id": "w1", "work_state": "DUE", "run_id": "r1"},
            {"cycle": 2, "schedule_id": "s", "work_item_id": "w2", "work_state": "DUE", "run_id": "r2"},
        ],
        "worker_cycles": [{"claimed_work_item_id": "w1", "run_id": "r1"}, {"claimed_work_item_id": "w2", "run_id": "r2"}],
        "scan_cycles": [{"state": "SUCCEEDED_BASELINE", "notification_delta": 0}, {"state": "SUCCEEDED_DIFFERENCE", "new_listing_count": 1, "scan_new_listing_event_count": 1}],
        "notification": {"event_id": "e", "effect_count": 1, "telegram_attempt_count": 1},
        "telegram": {"fake_delivery_committed": True, "live_provider_calls": 0},
        "web_status_read_model": {"web_delivery_mode": "WEB_STATUS_READ_MODEL", "web_event_id": "e", "web_account_id": "a", "web_beacon_id": "b", "web_visible": True},
        "web_cabinet": {"status": 200, "target_state_visible": True, "notification_event_id": "e", "account_id": "a", "beacon_id": "b"},
        "admin_diagnostics": {"authenticated": True, "authorized": True, "target_diagnostics_visible": True, "operator_account_id": "operator", "target_account_id": "a", "beacon_id": "b", "notification_event_id": "e"},
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["security"].update(serialized_cookie_value_present=True),
        lambda d: d["scheduler_cycles"].__getitem__(1).update(work_item_id="w1"),
        lambda d: d["scan_cycles"].__getitem__(0).update(notification_delta=1),
        lambda d: d["web_status_read_model"].update(web_delivery_mode="FAKE_PROVIDER"),
        lambda d: d["admin_diagnostics"].update(authenticated=False),
    ],
)
def test_verifier_rejects_previously_accepted_false_positive_shapes(tmp_path: Path, mutation: object) -> None:
    evidence = _known_good()
    mutation(evidence)  # type: ignore[operator]
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError):
        verify(path, "a" * 40)


def test_verifier_rejects_generic_unauthenticated_admin_page(tmp_path: Path) -> None:
    evidence = _known_good()
    evidence["admin_diagnostics"] = {"status": 200, "title": "Admin", "authenticated": False, "authorized": False}
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError):
        verify(path, "a" * 40)


def test_verifier_rejects_db_reconstructed_process_provenance(tmp_path: Path) -> None:
    """Regression: DB rows plus expected constants do not prove process origin."""
    evidence = _known_good()
    evidence["durable_provenance"] = [
        {"schedule_id": "s", "work_item_id": "w1", "run_id": "r1"},
        {"schedule_id": "s", "work_item_id": "w2", "run_id": "r2"},
    ]
    evidence.pop("scheduler_observations", None)
    evidence.pop("worker_observations", None)
    path = tmp_path / "db-reconstructed.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ValueError, match="scheduler observations"):
        verify(path, "a" * 40)
