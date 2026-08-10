from __future__ import annotations
# ruff: noqa: E501, E701, E702, E401, I001
import importlib.util
from pathlib import Path
import pytest
def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, Path("scripts/runtime") / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

scan = _load("check_rf24_notification_ambiguous_send_artifact_safety").scan
verify = _load("verify_rf24_notification_ambiguous_send").verify

def _doc() -> tuple[dict, dict]:
    a1={"id":"a1","state":"RECONCILIATION_REQUIRED","attempt_number":1,"effect_fingerprint":"f"*64}
    a2={"id":"a2","state":"DELIVERED_ACCEPTED","attempt_number":2,"effect_fingerprint":"f"*64}
    event={"id":"event"}; out={"id":"out","state":"RECONCILIATION_REQUIRED"}; rec={"id":"rec","attempt_id":"a1","state":"UNRESOLVED","safe_metadata":{"effect_fingerprint":"f"*64}}
    def p(attempts,recs,state=out["state"]): return {"events":[event],"outbox":[{"id":"out","state":state}],"attempts":attempts,"reconciliations":recs}
    d={"technical_id":"RF24-NOTIFICATION-AMBIGUOUS-SEND-SCENARIO-01","source_sha":"sha","acceptance_run_id":"run","account_id":"account","beacon_id":"beacon","event_id":"event","outbox_id":"out","effect_fingerprint":"f"*64,"P0":None}
    d["phases"]={"P0":{"events":[event],"outbox":[{"id":"out","state":"PENDING"}],"attempts":[],"reconciliations":[]},"P1":p([a1],[rec]),"P2":p([a1],[rec]),"P3":{"snapshot":p([a1],[rec]),"rejections":[{"class":"ReconciliationConflict"}]*4},"P4":p([{**a1,"state":"FAILED_RETRYABLE_AFTER_POLICY"}],[{**rec,"state":"RESOLVED_NO_EFFECT_RETRY","resolved_at":"now"}],"RETRY"),"P5":p([a1,a2],[{**rec,"state":"RESOLVED_NO_EFFECT_RETRY","resolved_at":"now"}],"DELIVERED")}
    d["reconciliation_evidence"]={"attempt_id":"a1","effect_fingerprint":"f"*64,"committed":True,"evidence_reference_ids":["evidence"],"resolution_id":"resolution"}
    probes={"source_sha":"sha","observations":[{"acceptance_run_id":"run","source_sha":"sha","attempt_id":"a1","outbox_id":"out","synthetic_outcome_class":"DISPATCH_AMBIGUOUS"},{"acceptance_run_id":"run","source_sha":"sha","attempt_id":"a2","outbox_id":"out","synthetic_outcome_class":"PROVIDER_ACCEPTED"}]}
    return d,probes

def test_verifier_rejects_missing_reconciliation_and_bad_p2() -> None:
    d,p=_doc(); d["phases"]["P1"]["reconciliations"]=[]
    with pytest.raises(AssertionError): verify(d,p,"sha")
    d,p=_doc(); d["phases"]["P2"]["outbox"][0]["state"]="RETRY"
    with pytest.raises(AssertionError): verify(d,p,"sha")

def test_verifier_rejects_wrong_probe_identity() -> None:
    d,p=_doc(); p["observations"][0]["attempt_id"]="wrong"
    with pytest.raises(AssertionError): verify(d,p,"sha")

def test_scanner_rejects_credential_and_raw_provider_material(tmp_path: Path) -> None:
    item=tmp_path/"unsafe.json"; item.write_text('{"password":"x", "raw_provider_payload":"x"}')
    result=scan([str(item)])
    assert result["finding_count"] == 2
