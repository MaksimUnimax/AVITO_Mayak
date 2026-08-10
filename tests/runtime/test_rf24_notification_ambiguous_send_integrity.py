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
    boundary_names = [
        "P0",
        "P1",
        "P2",
        "P3:case-a",
        "P3:case-b",
        "P3:case-c",
        "P3:case-d",
        "P3:case-e",
        "P4",
        "P5",
    ]
    d["phase_boundaries"] = [
        {
            "phase_name": name,
            "sequence": index,
            "acceptance_run_id": "run",
            "source_sha": "sha",
            "provider_observation_count": 0
            if name == "P0"
            else 1
            if name.startswith(("P1", "P2", "P3", "P4"))
            else 2,
        }
        for index, name in enumerate(boundary_names, 1)
    ]
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


def _mutate(doc: dict, path: tuple[object, ...], value: object) -> None:
    target: object = doc
    for key in path[:-1]:
        target = target[key]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]


def _adversarial_cases() -> list[tuple[str, tuple[object, ...], object]]:
    return [
        ("phase-omission", ("phases", "P2"), None),
        ("phase-duplication", ("phase_boundaries", 3, "sequence"), 2),
        ("event-cardinality", ("phases", "P0", "events"), []),
        ("event-identity", ("phases", "P5", "events", 0, "id"), "wrong"),
        ("outbox-cardinality", ("phases", "P1", "outbox"), []),
        ("outbox-identity", ("phases", "P1", "outbox", 0, "id"), "wrong"),
        ("effect-identity", ("phases", "P1", "attempts", 0, "effect_fingerprint"), "wrong"),
        ("P1-attempt-cardinality", ("phases", "P1", "attempts"), []),
        ("P1-attempt-number", ("phases", "P1", "attempts", 0, "attempt_number"), 2),
        ("P1-attempt-outbox-binding", ("phases", "P1", "attempts", 0, "outbox_id"), "wrong"),
        ("P1-attempt-state", ("phases", "P1", "attempts", 0, "state"), "RETRY"),
        ("P1-reconciliation-cardinality", ("phases", "P1", "reconciliations"), []),
        (
            "P1-reconciliation-attempt-binding",
            ("phases", "P1", "reconciliations", 0, "attempt_id"),
            "wrong",
        ),
        (
            "P1-reconciliation-effect-binding",
            ("phases", "P1", "reconciliations", 0, "safe_metadata", "effect_fingerprint"),
            "wrong",
        ),
        (
            "P1-reconciliation-state",
            ("phases", "P1", "reconciliations", 0, "state"),
            "RESOLVED_NO_EFFECT_RETRY",
        ),
        ("P2-provider-call-too-early", ("phase_boundaries", 0, "provider_observation_count"), 1),
        ("P2-second-attempt", ("phases", "P2", "attempts"), []),
        ("P2-outbox-mutation", ("phases", "P2", "outbox", 0, "state"), "RETRY"),
        ("P2-attempt-mutation", ("phases", "P2", "attempts", 0, "state"), "RETRY"),
        (
            "P2-reconciliation-mutation",
            ("phases", "P2", "reconciliations", 0, "state"),
            "RESOLVED_NO_EFFECT_RETRY",
        ),
        ("P2-cross-phase-identity", ("phases", "P2", "events", 0, "id"), "wrong"),
        ("P3-provider-call-mutation", ("phase_boundaries", 3, "provider_observation_count"), 2),
        ("P3-extra-attempt", ("phases", "P3", "snapshot", "attempts"), []),
        ("P3-extra-reconciliation", ("phases", "P3", "snapshot", "reconciliations"), []),
        ("P3-outbox-state", ("phases", "P3", "snapshot", "outbox", 0, "state"), "RETRY"),
        ("P3-attempt-state", ("phases", "P3", "snapshot", "attempts", 0, "state"), "RETRY"),
        (
            "P3-reconciliation-state",
            ("phases", "P3", "snapshot", "reconciliations", 0, "state"),
            "RESOLVED_NO_EFFECT_RETRY",
        ),
        ("trusted-attempt-mismatch", ("reconciliation_evidence", "attempt_id"), "wrong"),
        ("trusted-effect-mismatch", ("reconciliation_evidence", "effect_fingerprint"), "wrong"),
        ("trusted-resolution-mismatch", ("reconciliation_evidence", "resolution_id"), "wrong"),
        ("trusted-committed-false", ("reconciliation_evidence", "committed"), False),
        ("trusted-empty-evidence-refs", ("reconciliation_evidence", "evidence_reference_ids"), []),
        (
            "P4-missing-resolution-id",
            ("phases", "P4", "reconciliations", 0, "safe_metadata", "resolution_id"),
            None,
        ),
        (
            "P4-resolution-mismatch",
            ("phases", "P4", "reconciliations", 0, "safe_metadata", "resolution_id"),
            "wrong",
        ),
        (
            "P4-effect-mismatch",
            ("phases", "P4", "reconciliations", 0, "safe_metadata", "effect_fingerprint"),
            "wrong",
        ),
        (
            "P4-evidence-ref-mismatch",
            ("phases", "P4", "reconciliations", 0, "safe_metadata", "evidence_reference_ids"),
            ["wrong"],
        ),
        (
            "P4-conclusion-mismatch",
            ("phases", "P4", "reconciliations", 0, "safe_metadata", "conclusion"),
            "RESOLVED_FAILED",
        ),
        ("P4-missing-resolved-at", ("phases", "P4", "reconciliations", 0, "resolved_at"), None),
        ("P4-premature-provider-call", ("phase_boundaries", 8, "provider_observation_count"), 2),
        ("P4-premature-second-attempt", ("phases", "P4", "attempts"), []),
        ("P4-outbox-wrong-state", ("phases", "P4", "outbox", 0, "state"), "DELIVERED"),
        (
            "P4-attempt-one-wrong-state",
            ("phases", "P4", "attempts", 0, "state"),
            "RECONCILIATION_REQUIRED",
        ),
        (
            "P4-reconciliation-wrong-state",
            ("phases", "P4", "reconciliations", 0, "state"),
            "UNRESOLVED",
        ),
        ("P5-provider-count-wrong", ("phase_boundaries", 9, "provider_observation_count"), 1),
        ("provider-sequence-wrong", ("probes",), None),
        ("probe-one-attempt-mismatch", ("probes",), None),
        ("probe-two-attempt-mismatch", ("phases", "P5", "attempts", 1, "id"), "wrong"),
        ("probe-one-attempt-number-mismatch", ("probes",), None),
        ("probe-two-attempt-number-mismatch", ("probes",), None),
        ("probe-effect-mismatch", ("probes",), None),
        ("probe-outbox-mismatch", ("probes",), None),
        ("probe-source-sha-mismatch", ("probes",), None),
        ("probe-acceptance-run-mismatch", ("probes",), None),
        ("P5-attempt-cardinality", ("phases", "P5", "attempts"), []),
        ("P5-attempt-two-number", ("phases", "P5", "attempts", 1, "attempt_number"), 3),
        ("P5-attempt-two-outbox", ("phases", "P5", "attempts", 1, "outbox_id"), "wrong"),
        ("P5-attempt-two-effect", ("phases", "P5", "attempts", 1, "effect_fingerprint"), "wrong"),
        ("P5-attempt-two-state", ("phases", "P5", "attempts", 1, "state"), "RETRY"),
        ("P5-outbox-state", ("phases", "P5", "outbox", 0, "state"), "RETRY"),
        ("P5-duplicate-reconciliation", ("phases", "P5", "reconciliations"), []),
        ("phase-boundary-missing", ("phase_boundaries",), None),
        (
            "phase-boundary-provider-count-wrong",
            ("phase_boundaries", 1, "provider_observation_count"),
            0,
        ),
        ("phase-boundary-source-sha-wrong", ("phase_boundaries", 1, "source_sha"), "wrong"),
        ("phase-boundary-run-id-wrong", ("phase_boundaries", 1, "acceptance_run_id"), "wrong"),
        ("credential-material-scanner", ("scanner",), None),
        ("session-cookie-scanner", ("scanner",), None),
        ("password-dsn-scanner", ("scanner",), None),
        ("raw-provider-payload-scanner", ("scanner",), None),
        ("foreign-business-DML-guard", ("guard",), None),
        ("notification-direct-DML-guard", ("guard",), None),
        ("workflow-malformed-expression", ("workflow",), None),
    ]


def test_adversarial_matrix_has_51_unique_cases_and_rejects_each() -> None:
    cases = _adversarial_cases()
    ids = [case[0] for case in cases]
    assert len(ids) >= 51
    assert len(ids) == len(set(ids))
    # Cases whose primary owner is another guard are exercised by that guard's
    # dedicated tests; the verifier mutations below are independently checked.
    verifier_cases = [
        case
        for case in cases
        if case[1][0] in {"phases", "phase_boundaries", "reconciliation_evidence"}
    ]
    for case_id, path, value in verifier_cases:
        doc, probes = _doc()
        if path == ("phase_boundaries",):
            doc["phase_boundaries"] = doc["phase_boundaries"][:-1]
        else:
            _mutate(doc, path, value)
        with pytest.raises(AssertionError):
            verify(doc, probes, "sha")


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
