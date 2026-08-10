"""Independent, fail-closed verifier for RF24 ambiguous notification evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _fail(message: str) -> None:
    raise AssertionError(message)


def _phase(doc: dict, name: str) -> dict:
    value = doc.get("phases", {}).get(name)
    if not isinstance(value, dict):
        _fail(f"missing phase {name}")
    return value


def _snapshot(phase: dict, name: str = "") -> dict:
    value = phase.get("snapshot", phase)
    if not isinstance(value, dict):
        _fail(f"invalid snapshot {name}")
    return value


def _identity(snapshot: dict) -> tuple[str, str, str]:
    events = snapshot.get("events", [])
    outbox = snapshot.get("outbox", [])
    if len(events) != 1 or len(outbox) != 1:
        _fail("snapshot cardinality")
    return (
        str(events[0]["id"]),
        str(outbox[0]["id"]),
        str(events[0].get("source_effect_fingerprint", "")),
    )


def verify(doc: dict, probes: dict, source_sha: str) -> dict[str, object]:
    if doc.get("source_sha") != source_sha or probes.get("source_sha") != source_sha:
        _fail("source SHA mismatch")
    if doc.get("technical_id") != "RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01":
        _fail("technical identity mismatch")
    required = (
        "account_id",
        "beacon_id",
        "event_id",
        "outbox_id",
        "effect_fingerprint",
        "acceptance_run_id",
    )
    if any(not doc.get(k) for k in required):
        _fail("missing binding identity")
    p0, p1, p2, p3, p4, p5 = (_phase(doc, n) for n in ("P0", "P1", "P2", "P3", "P4", "P5"))
    if not (
        len(p0["events"]) == len(p0["outbox"]) == 1
        and not p0["attempts"]
        and not p0["reconciliations"]
    ):
        _fail("P0 cardinality")
    identities = [
        _identity(_snapshot(phase, name))
        for name, phase in (("P0", p0), ("P1", p1), ("P2", p2), ("P3", p3), ("P4", p4), ("P5", p5))
    ]
    if any(identity != identities[0] for identity in identities[1:]):
        _fail("source or outbox identity changed across phases")
    if identities[0][0] != str(doc["event_id"]) or identities[0][1] != str(doc["outbox_id"]):
        _fail("document identity does not bind durable rows")
    if len(p1["attempts"]) != 1 or len(p1["reconciliations"]) != 1:
        _fail("P1 cardinality")
    a1, r1, o1 = p1["attempts"][0], p1["reconciliations"][0], p1["outbox"][0]
    if (
        a1["state"] != "RECONCILIATION_REQUIRED"
        or o1["state"] != "RECONCILIATION_REQUIRED"
        or r1["state"] != "UNRESOLVED"
    ):
        _fail("P1 state")
    if (
        str(r1["attempt_id"]) != str(a1["id"])
        or r1["safe_metadata"]["effect_fingerprint"] != a1["effect_fingerprint"]
    ):
        _fail("P1 effect binding")
    if str(a1["outbox_id"]) != str(doc["outbox_id"]):
        _fail("attempt outbox binding")
    if (
        len(p2["attempts"]) != 1
        or len(p2["reconciliations"]) != 1
        or p2["outbox"][0]["state"] != "RECONCILIATION_REQUIRED"
        or p2["attempts"][0]["state"] != "RECONCILIATION_REQUIRED"
    ):
        _fail("P2 changed or blind retry")
    if len(probes.get("observations", [])) != 2:
        _fail("provider probe count")
    observations = probes["observations"]
    if [item.get("sequence") for item in observations] != [1, 2]:
        _fail("provider sequence numbers")
    if observations[0].get("phase") != "P1" or observations[1].get("phase") != "P5":
        _fail("provider phase boundary")
    if (
        observations[0]["synthetic_outcome_class"] != "DISPATCH_AMBIGUOUS"
        or observations[1]["synthetic_outcome_class"] != "PROVIDER_ACCEPTED"
    ):
        _fail("provider sequence")
    if observations[0]["attempt_id"] != str(a1["id"]):
        _fail("probe attempt binding")
    if (
        observations[0].get("attempt_number") != 1
        or observations[0].get("effect_fingerprint") != a1["effect_fingerprint"]
    ):
        _fail("probe one durable binding")
    rejections = p3.get("rejections", [])
    if len(rejections) < 4 or any(item.get("class") in {"none", None} for item in rejections):
        _fail("untrusted reconciliation not rejected")
    if (
        p3["snapshot"]["outbox"][0]["state"] != "RECONCILIATION_REQUIRED"
        or p3["snapshot"]["reconciliations"][0]["state"] != "UNRESOLVED"
    ):
        _fail("rejected reconciliation changed state")
    for rejected in p3.get("rejected_cases", []):
        rejected_snapshot = rejected.get("snapshot", {})
        if (
            _identity(rejected_snapshot) != identities[0]
            or len(rejected_snapshot.get("attempts", [])) != 1
            or len(rejected_snapshot.get("reconciliations", [])) != 1
        ):
            _fail("rejected reconciliation changed cardinality")
        if (
            rejected_snapshot["outbox"][0]["state"] != "RECONCILIATION_REQUIRED"
            or rejected_snapshot["attempts"][0]["state"] != "RECONCILIATION_REQUIRED"
            or rejected_snapshot["reconciliations"][0]["state"] != "UNRESOLVED"
        ):
            _fail("rejected reconciliation changed durable state")
    evidence = doc.get("reconciliation_evidence", {})
    if (
        not evidence.get("committed")
        or not evidence.get("evidence_reference_ids")
        or evidence.get("attempt_id") != str(a1["id"])
        or evidence.get("effect_fingerprint") != a1["effect_fingerprint"]
    ):
        _fail("trusted evidence binding")
    stored = p4["reconciliations"][0].get("safe_metadata", {})
    for key in ("resolution_id", "effect_fingerprint", "evidence_reference_ids", "conclusion"):
        if key not in stored:
            _fail(f"P4 metadata missing {key}")
    if (
        stored["resolution_id"] != evidence.get("resolution_id")
        or stored["effect_fingerprint"] != evidence.get("effect_fingerprint")
        or tuple(stored["evidence_reference_ids"])
        != tuple(evidence.get("evidence_reference_ids", ()))
    ):
        _fail("P4 persisted evidence mismatch")
    if p4["reconciliations"][0].get("resolved_at") is None:
        _fail("P4 missing resolved_at")
    if (
        p4["reconciliations"][0]["state"] != "RESOLVED_NO_EFFECT_RETRY"
        or p4["attempts"][0]["state"] != "FAILED_RETRYABLE_AFTER_POLICY"
        or p4["outbox"][0]["state"] != "RETRY"
    ):
        _fail("P4 transition")
    if (
        len(p5["events"]) != 1
        or len(p5["outbox"]) != 1
        or len(p5["attempts"]) != 2
        or len(p5["reconciliations"]) != 1
    ):
        _fail("P5 cardinality")
    attempts5 = sorted(p5["attempts"], key=lambda item: item["attempt_number"])
    if (
        attempts5[1]["attempt_number"] != 2
        or attempts5[1]["state"] != "DELIVERED_ACCEPTED"
        or p5["outbox"][0]["state"] != "DELIVERED"
    ):
        _fail("P5 final state")
    if observations[1]["attempt_id"] != str(attempts5[1]["id"]):
        _fail("probe two attempt binding")
    if (
        observations[1].get("attempt_number") != 2
        or observations[1].get("effect_fingerprint") != attempts5[1]["effect_fingerprint"]
    ):
        _fail("probe two durable binding")
    if str(attempts5[1]["outbox_id"]) != str(doc["outbox_id"]):
        _fail("retry outbox binding")
    if any(
        item["acceptance_run_id"] != doc["acceptance_run_id"]
        or item["source_sha"] != source_sha
        or item["outbox_id"] != str(doc["outbox_id"])
        for item in observations
    ):
        _fail("probe provenance")
    return {
        "verdict": "PASS",
        "technical_id": doc["technical_id"],
        "acceptance_run_id": doc["acceptance_run_id"],
        "source_sha": source_sha,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--evidence", required=True)
    p.add_argument("--probes", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--result", required=True)
    a = p.parse_args()
    result = verify(
        json.loads(Path(a.evidence).read_text()),
        json.loads(Path(a.probes).read_text()),
        a.source_sha,
    )
    Path(a.result).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("RF24_AMBIGUOUS_VERIFIER=PASS")


if __name__ == "__main__":
    main()
