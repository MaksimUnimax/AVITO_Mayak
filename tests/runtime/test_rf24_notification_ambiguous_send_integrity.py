from __future__ import annotations

# ruff: noqa: E501, E701, E702
import copy
import importlib.util
from dataclasses import dataclass
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


def _verifier_mutations() -> list[tuple[str, tuple[object, ...], object]]:
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
    ]


@dataclass(frozen=True)
class AdversarialCase:
    case_id: str
    authority: str
    mutation: tuple[object, ...] | None = None
    value: object = None


def _probe_cases() -> list[AdversarialCase]:
    return [
        AdversarialCase(name, "verifier")
        for name in (
            "provider-sequence-wrong",
            "probe-one-attempt-mismatch",
            "probe-two-attempt-mismatch",
            "probe-one-attempt-number-mismatch",
            "probe-two-attempt-number-mismatch",
            "probe-effect-mismatch",
            "probe-outbox-mismatch",
            "probe-source-sha-mismatch",
            "probe-acceptance-run-mismatch",
            "probe-outcome-one-mismatch",
            "probe-outcome-two-mismatch",
            "probe-phase-one-mismatch",
            "probe-phase-two-mismatch",
        )
    ]


def _scanner_cases() -> list[AdversarialCase]:
    return [
        AdversarialCase(f"scanner-{name}", "scanner")
        for name in (
            "authorization-material",
            "bearer-token-material",
            "session-cookie-material",
            "password-field-material",
            "password-dsn-material",
            "private-key-material",
            "raw-provider-payload-marker",
            "request-body-marker",
            "response-body-marker",
        )
    ]


def _ownership_cases() -> list[AdversarialCase]:
    return [
        AdversarialCase(f"ownership-{name}", "ownership")
        for name in (
            "foreign-identity-insert",
            "foreign-beacon-update",
            "foreign-scan-delete",
            "foreign-entitlement-mutation",
            "direct-notification-business-insert",
            "direct-notification-business-update",
        )
    ]


def _workflow_cases() -> list[AdversarialCase]:
    return [
        AdversarialCase(f"workflow-{name}", "workflow")
        for name in (
            "expression-flow-mapping",
            "missing-acceptance-job",
            "missing-artifact-upload",
            "missing-corrective-trigger",
            "missing-fresh-post-suite-database",
        )
    ]


_VERIFIER_CASES = [
    AdversarialCase(name, "verifier", path, value) for name, path, value in _verifier_mutations()
]
_PROBE_CASES = _probe_cases()
REGISTERED_CASES = tuple(
    _VERIFIER_CASES + _PROBE_CASES + _scanner_cases() + _ownership_cases() + _workflow_cases()
)
REGISTERED_IDS = tuple(case.case_id for case in REGISTERED_CASES)
EXECUTED_IDS: list[str] = []


def _execute_probe_case(case_id: str, probes: dict) -> None:
    probes = copy.deepcopy(probes)
    observations = probes["observations"]
    if case_id == "provider-sequence-wrong":
        observations[1]["sequence"] = 3
    elif case_id == "probe-one-attempt-mismatch":
        observations[0]["attempt_id"] = "wrong"
    elif case_id == "probe-two-attempt-mismatch":
        observations[1]["attempt_id"] = "wrong"
    elif case_id == "probe-one-attempt-number-mismatch":
        observations[0]["attempt_number"] = 2
    elif case_id == "probe-two-attempt-number-mismatch":
        observations[1]["attempt_number"] = 3
    elif case_id == "probe-effect-mismatch":
        observations[0]["effect_fingerprint"] = "wrong"
    elif case_id == "probe-outbox-mismatch":
        observations[0]["outbox_id"] = "wrong"
    elif case_id == "probe-source-sha-mismatch":
        observations[0]["source_sha"] = "wrong"
    elif case_id == "probe-acceptance-run-mismatch":
        observations[0]["acceptance_run_id"] = "wrong"
    elif case_id == "probe-outcome-one-mismatch":
        observations[0]["synthetic_outcome_class"] = "PROVIDER_ACCEPTED"
    elif case_id == "probe-outcome-two-mismatch":
        observations[1]["synthetic_outcome_class"] = "DISPATCH_AMBIGUOUS"
    elif case_id == "probe-phase-one-mismatch":
        observations[0]["phase"] = "P5"
    elif case_id == "probe-phase-two-mismatch":
        observations[1]["phase"] = "P1"
    else:
        raise AssertionError(f"unknown probe case {case_id}")
    d, _ = _doc()
    with pytest.raises(AssertionError):
        verify(d, probes, "sha")


@pytest.mark.parametrize("case", REGISTERED_CASES, ids=REGISTERED_IDS)
def test_registered_adversarial_case_executes_its_owner(
    case: AdversarialCase, tmp_path: Path
) -> None:
    EXECUTED_IDS.append(case.case_id)
    if case.authority == "verifier":
        d, p = _doc()
        if case.case_id.startswith("probe-") or case.case_id == "provider-sequence-wrong":
            _execute_probe_case(case.case_id, p)
        else:
            if case.mutation == ("phase_boundaries",):
                d["phase_boundaries"] = d["phase_boundaries"][:-1]
            else:
                _mutate(d, case.mutation, case.value)  # type: ignore[arg-type]
            with pytest.raises(AssertionError):
                verify(d, p, "sha")
    elif case.authority == "scanner":
        markers = {
            "scanner-authorization-material": '"authorization":"synthetic"',
            "scanner-bearer-token-material": '"bearer token":"synthetic"',
            "scanner-session-cookie-material": '"session_cookie":"synthetic"',
            "scanner-password-field-material": '"password":"synthetic"',
            "scanner-password-dsn-material": "postgresql://user:password@host/db",
            "scanner-private-key-material": '"private_key":"synthetic"',
            "scanner-raw-provider-payload-marker": '"raw_provider_payload":"synthetic"',
            "scanner-request-body-marker": '"request_body":"synthetic"',
            "scanner-response-body-marker": '"response_body":"synthetic"',
        }
        item = tmp_path / f"{case.case_id}.json"
        item.write_text("{" + markers[case.case_id] + "}")
        assert scan([str(item)])["finding_count"] > 0
    elif case.authority == "ownership":
        table = {
            "ownership-foreign-identity-insert": "identity_accounts",
            "ownership-foreign-beacon-update": "beacon_records",
            "ownership-foreign-scan-delete": "scan_runs",
            "ownership-foreign-entitlement-mutation": "entitlement_records",
            "ownership-direct-notification-business-insert": "notification_events",
            "ownership-direct-notification-business-update": "notification_outbox",
        }[case.case_id]
        item = tmp_path / f"{case.case_id}.py"
        verb = (
            "INSERT"
            if "insert" in case.case_id
            else "UPDATE"
            if "update" in case.case_id
            else "DELETE"
        )
        item.write_text(f'text("{verb} INTO mayak.{table} VALUES (...) ")')
        assert ownership.violations((str(item),))
    else:
        original = Path(".github/workflows/ci-rf24-notification-ambiguous-send.yml").read_text()
        replacements = {
            "workflow-expression-flow-mapping": (
                "          ref: ${{ github.sha }}",
                "          ref: ${{ github.sha }}, bad: ${{ github.ref }}",
            ),
            "workflow-missing-acceptance-job": ("  acceptance:\n", "  removed_acceptance:\n"),
            "workflow-missing-artifact-upload": ("actions/upload-artifact", "actions/not-uploaded"),
            "workflow-missing-corrective-trigger": (
                ", rf24-notification-ambiguous-send-scenario-01-corrective-01",
                "",
            ),
            "workflow-missing-fresh-post-suite-database": (
                "Create fresh post-suite scenario database",
                "Removed post-suite database",
            ),
        }
        text = original.replace(*replacements[case.case_id])
        if case.case_id == "workflow-expression-flow-mapping":
            text += "\nwith: {ref: ${{ github.sha }}}\n"
        if case.case_id == "workflow-missing-corrective-trigger":
            text = text.replace(
                "rf24-notification-ambiguous-send-scenario-01-corrective-01", "removed-branch"
            )
        item = tmp_path / f"{case.case_id}.yml"
        item.write_text(text)
        with pytest.raises(AssertionError):
            workflow.validate(item, "rf24-notification-ambiguous-send-scenario-01-corrective-01")


def test_adversarial_registry_execution_identity() -> None:
    assert len(REGISTERED_IDS) >= 51 and len(REGISTERED_IDS) == len(set(REGISTERED_IDS))
    assert set(REGISTERED_IDS) == set(EXECUTED_IDS)


def test_safe_scanner_artifact_is_accepted(tmp_path: Path) -> None:
    item = tmp_path / "safe.json"
    item.write_text('{"synthetic":"bounded"}')
    assert scan([str(item)])["finding_count"] == 0


def test_workflow_guard_accepts_corrected_workflow() -> None:
    workflow.validate(
        Path(".github/workflows/ci-rf24-notification-ambiguous-send.yml"),
        "rf24-notification-ambiguous-send-scenario-01-corrective-01",
    )


def test_current_acceptance_runner_has_no_foreign_or_notification_dml() -> None:
    assert ownership.violations(("scripts/runtime/run_rf24_notification_ambiguous_send.py",)) == []
