"""Independent, fail-closed verifier for RF24 ambiguous notification evidence."""
# ruff: noqa: E501, E701, E702, E401, I001
from __future__ import annotations
import argparse, json
from pathlib import Path

def _fail(message: str) -> None: raise AssertionError(message)
def _phase(doc: dict, name: str) -> dict:
    value = doc.get("phases", {}).get(name)
    if not isinstance(value, dict): _fail(f"missing phase {name}")
    return value
def verify(doc: dict, probes: dict, source_sha: str) -> dict[str, object]:
    if doc.get("source_sha") != source_sha or probes.get("source_sha") != source_sha: _fail("source SHA mismatch")
    if doc.get("technical_id") != "RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01": _fail("technical identity mismatch")
    required = ("account_id", "beacon_id", "event_id", "outbox_id", "effect_fingerprint", "acceptance_run_id")
    if any(not doc.get(k) for k in required): _fail("missing binding identity")
    p0, p1, p2, p3, p4, p5 = (_phase(doc, n) for n in ("P0", "P1", "P2", "P3", "P4", "P5"))
    if not (len(p0["events"]) == len(p0["outbox"]) == 1 and not p0["attempts"] and not p0["reconciliations"]): _fail("P0 cardinality")
    if len(p1["attempts"]) != 1 or len(p1["reconciliations"]) != 1: _fail("P1 cardinality")
    a1, r1, o1 = p1["attempts"][0], p1["reconciliations"][0], p1["outbox"][0]
    if a1["state"] != "RECONCILIATION_REQUIRED" or o1["state"] != "RECONCILIATION_REQUIRED" or r1["state"] != "UNRESOLVED": _fail("P1 state")
    if str(r1["attempt_id"]) != str(a1["id"]) or r1["safe_metadata"]["effect_fingerprint"] != a1["effect_fingerprint"]: _fail("P1 effect binding")
    if len(p2["attempts"]) != 1 or len(p2["reconciliations"]) != 1 or p2["outbox"][0]["state"] != "RECONCILIATION_REQUIRED" or p2["attempts"][0]["state"] != "RECONCILIATION_REQUIRED": _fail("P2 changed or blind retry")
    if len(probes.get("observations", [])) != 2: _fail("provider probe count")
    observations = probes["observations"]
    if observations[0]["synthetic_outcome_class"] != "DISPATCH_AMBIGUOUS" or observations[1]["synthetic_outcome_class"] != "PROVIDER_ACCEPTED": _fail("provider sequence")
    if observations[0]["attempt_id"] != str(a1["id"]): _fail("probe attempt binding")
    rejections = p3.get("rejections", [])
    if len(rejections) < 4 or any(item.get("class") in {"none", None} for item in rejections): _fail("untrusted reconciliation not rejected")
    if p3["snapshot"]["outbox"][0]["state"] != "RECONCILIATION_REQUIRED" or p3["snapshot"]["reconciliations"][0]["state"] != "UNRESOLVED": _fail("rejected reconciliation changed state")
    evidence = doc.get("reconciliation_evidence", {})
    if not evidence.get("committed") or not evidence.get("evidence_reference_ids") or evidence.get("attempt_id") != str(a1["id"]) or evidence.get("effect_fingerprint") != a1["effect_fingerprint"]: _fail("trusted evidence binding")
    if p4["reconciliations"][0]["state"] != "RESOLVED_NO_EFFECT_RETRY" or p4["attempts"][0]["state"] != "FAILED_RETRYABLE_AFTER_POLICY" or p4["outbox"][0]["state"] != "RETRY": _fail("P4 transition")
    if len(p5["events"]) != 1 or len(p5["outbox"]) != 1 or len(p5["attempts"]) != 2 or len(p5["reconciliations"]) != 1: _fail("P5 cardinality")
    attempts5 = sorted(p5["attempts"], key=lambda item: item["attempt_number"])
    if attempts5[1]["attempt_number"] != 2 or attempts5[1]["state"] != "DELIVERED_ACCEPTED" or p5["outbox"][0]["state"] != "DELIVERED": _fail("P5 final state")
    if any(item["acceptance_run_id"] != doc["acceptance_run_id"] or item["source_sha"] != source_sha or item["outbox_id"] != str(doc["outbox_id"]) for item in observations): _fail("probe provenance")
    return {"verdict": "PASS", "technical_id": doc["technical_id"], "acceptance_run_id": doc["acceptance_run_id"], "source_sha": source_sha}
def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--evidence", required=True); p.add_argument("--probes", required=True); p.add_argument("--source-sha", required=True); p.add_argument("--result", required=True); a=p.parse_args()
    result=verify(json.loads(Path(a.evidence).read_text()), json.loads(Path(a.probes).read_text()), a.source_sha); Path(a.result).write_text(json.dumps(result, sort_keys=True, indent=2)+"\n"); print("RF24_AMBIGUOUS_VERIFIER=PASS")
if __name__ == "__main__": main()
