from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path("scripts/runtime") / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scan = _load("check_rf24_notification_ambiguous_send_artifact_safety").scan
verify = _load("verify_rf24_notification_ambiguous_send").verify
ownership = _load("check_rf24_notification_ambiguous_send_ownership")
workflow = _load("check_rf24_notification_ambiguous_send_workflow")


def _doc() -> tuple[dict, dict]:
    a1 = {
        "id": "a1",
        "outbox_id": "out",
        "state": "RECONCILIATION_REQUIRED",
        "attempt_number": 1,
        "effect_fingerprint": "f" * 64,
    }
    a2 = {
        "id": "a2",
        "outbox_id": "out",
        "state": "DELIVERED_ACCEPTED",
        "attempt_number": 2,
        "effect_fingerprint": "f" * 64,
    }
    event = {"id": "event"}
    out = {"id": "out", "state": "RECONCILIATION_REQUIRED"}
    rec = {
        "id": "rec",
        "attempt_id": "a1",
        "state": "UNRESOLVED",
        "safe_metadata": {"effect_fingerprint": "f" * 64},
    }

    def p(attempts, recs, state=out["state"]):
        return {
            "events": [event],
            "outbox": [{"id": "out", "state": state}],
            "attempts": attempts,
            "reconciliations": recs,
        }

    d = {
        "technical_id": "RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01",
        "source_sha": "sha",
        "acceptance_run_id": "run",
        "account_id": "account",
        "beacon_id": "beacon",
        "event_id": "event",
        "outbox_id": "out",
        "effect_fingerprint": "f" * 64,
        "P0": None,
    }
    d["phases"] = {
        "P0": {
            "events": [event],
            "outbox": [{"id": "out", "state": "PENDING"}],
            "attempts": [],
            "reconciliations": [],
        },
        "P1": p([a1], [rec]),
        "P2": p([a1], [rec]),
        "P3": {"snapshot": p([a1], [rec]), "rejections": [{"class": "ReconciliationConflict"}] * 4},
        "P4": p(
            [{**a1, "state": "FAILED_RETRYABLE_AFTER_POLICY"}],
            [
                {
                    **rec,
                    "state": "RESOLVED_NO_EFFECT_RETRY",
                    "resolved_at": "now",
                    "safe_metadata": {
                        "resolution_id": "resolution",
                        "effect_fingerprint": "f" * 64,
                        "evidence_reference_ids": ["evidence"],
                        "conclusion": "RESOLVED_NO_EFFECT_RETRY",
                    },
                }
            ],
            "RETRY",
        ),
        "P5": p(
            [a1, a2],
            [
                {
                    **rec,
                    "state": "RESOLVED_NO_EFFECT_RETRY",
                    "resolved_at": "now",
                    "safe_metadata": {
                        "resolution_id": "resolution",
                        "effect_fingerprint": "f" * 64,
                        "evidence_reference_ids": ["evidence"],
                        "conclusion": "RESOLVED_NO_EFFECT_RETRY",
                    },
                }
            ],
            "DELIVERED",
        ),
    }
    d["reconciliation_evidence"] = {
        "attempt_id": "a1",
        "effect_fingerprint": "f" * 64,
        "committed": True,
        "evidence_reference_ids": ["evidence"],
        "resolution_id": "resolution",
    }
    d["phases"]["P3"]["rejected_cases"] = []
    probes = {
        "source_sha": "sha",
        "observations": [
            {
                "sequence": 1,
                "phase": "P1",
                "acceptance_run_id": "run",
                "source_sha": "sha",
                "attempt_id": "a1",
                "outbox_id": "out",
                "attempt_number": 1,
                "effect_fingerprint": "f" * 64,
                "synthetic_outcome_class": "DISPATCH_AMBIGUOUS",
            },
            {
                "sequence": 2,
                "phase": "P5",
                "acceptance_run_id": "run",
                "source_sha": "sha",
                "attempt_id": "a2",
                "outbox_id": "out",
                "attempt_number": 2,
                "effect_fingerprint": "f" * 64,
                "synthetic_outcome_class": "PROVIDER_ACCEPTED",
            },
        ],
    }
    return d, probes


def test_verifier_rejects_missing_reconciliation_and_bad_p2() -> None:
    d, p = _doc()
    d["phases"]["P1"]["reconciliations"] = []
    with pytest.raises(AssertionError):
        verify(d, p, "sha")
    d, p = _doc()
    d["phases"]["P2"]["outbox"][0]["state"] = "RETRY"
    with pytest.raises(AssertionError):
        verify(d, p, "sha")


def test_verifier_rejects_wrong_probe_identity() -> None:
    d, p = _doc()
    p["observations"][0]["attempt_id"] = "wrong"
    with pytest.raises(AssertionError):
        verify(d, p, "sha")


def test_scanner_rejects_credential_and_raw_provider_material(tmp_path: Path) -> None:
    item = tmp_path / "unsafe.json"
    item.write_text('{"password":"x", "raw_provider_payload":"x"}')
    result = scan([str(item)])
    assert result["finding_count"] == 2


def test_ownership_guard_rejects_foreign_business_dml(tmp_path: Path) -> None:
    source = tmp_path / "fixture.py"
    source.write_text('text("INSERT INTO mayak.identity_accounts ...")')
    assert ownership.violations((str(source),))


def test_ownership_guard_accepts_select_observations(tmp_path: Path) -> None:
    source = tmp_path / "observation.py"
    source.write_text('text("SELECT id FROM mayak.scan_runs WHERE beacon_id=:beacon")')
    assert ownership.violations((str(source),)) == []


def test_workflow_guard_rejects_broken_expression_flow_mapping(tmp_path: Path) -> None:
    workflow_file = tmp_path / "broken.yml"
    workflow_file.write_text(
        "on:\n jobs:\n  acceptance:\n    steps:\n      - uses: actions/checkout@v4\n"
        "\n        with: {ref: ${{ github.sha }}}\n"
        "      - uses: actions/upload-artifact@v4\n"
    )
    with pytest.raises(AssertionError, match="flow mapping"):
        workflow.validate(
            workflow_file, "rf24-notification-ambiguous-send-scenario-01-corrective-01"
        )


def test_workflow_guard_accepts_corrected_workflow() -> None:
    workflow.validate(
        Path(".github/workflows/ci-rf24-notification-ambiguous-send.yml"),
        "rf24-notification-ambiguous-send-scenario-01-corrective-01",
    )


def test_current_acceptance_runner_has_no_foreign_or_notification_dml() -> None:
    assert ownership.violations(("scripts/runtime/run_rf24_notification_ambiguous_send.py",)) == []
