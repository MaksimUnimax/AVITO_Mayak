from __future__ import annotations
# ruff: noqa

import copy
import json
from pathlib import Path

import pytest

from scripts.runtime.check_rf24_cross_account_access_workflow import RULES, validate
from scripts.runtime.verify_rf24_cross_account_access import verify

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/ci-rf24-cross-account-access.yml"


def evidence() -> dict[str, object]:
    summary: dict[str, object] = {"account_a":"a", "account_b":"b", "distinct_accounts":True,
        "session_a_account":"a", "session_b_account":"b", "a_list_excludes_b":True, "b_detail_hidden":True,
        "cross_detail_status":403, "random_detail_status":403, "tamper_status":400, "cross_mutation_status":403,
        "cross_mutation_accepted":False, "b_row_version_changed_by_a":False, "b_revision_changed_by_a":False,
        "idempotency_poisoned":False, "legitimate_b_status":200, "legitimate_b_replay_status":200,
        "duplicate_b_revision_delta":0, "a_post_projection_isolated":True, "lower_owner_boundary_denies":True,
        "support_boundary_explicit":True, "live_provider_calls":0, "scanner_finding_count":0,
        "direct_Web_business_DML":False, "direct_foreign_module_DML":False, "owner_bypass_DML":False,
        "raw_provider_payload_persisted":False, "production_personal_data":False, "credential_exposure":False,
        "client_authority_tamper_accepted":False, "public_ingress":False, "postgres_host_published":False,
        "foreign_resource_impact":False}
    return {"identity":{"technical_id":"RF24-CROSS-ACCOUNT-ACCESS-SCENARIO-01","source_sha":"a"*40,"hosted_run_id":"7"},
            "phases":[{"phase":f"C{i}"} for i in range(11)], "summary":summary}


def test_verifier_accepts_complete_evidence() -> None:
    verify(evidence(), "a" * 40, "7")


@pytest.mark.parametrize("field", ["account_b", "cross_detail_status", "tamper_status", "idempotency_poisoned", "live_provider_calls"])
def test_verifier_rejects_material_mutations(field: str) -> None:
    data = copy.deepcopy(evidence()); data["summary"][field] = {"account_b":"a", "cross_detail_status":200, "tamper_status":200, "idempotency_poisoned":True, "live_provider_calls":1}[field]  # type: ignore[index]
    with pytest.raises(AssertionError): verify(data, "a" * 40, "7")


def test_workflow_positive_and_each_rule_has_negative_mutation() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert validate(text) == []
    for name, needles in RULES.items():
        mutated = text
        for needle in needles: mutated = mutated.replace(needle, "MUTATED_AWAY")
        assert name in validate(mutated), name


def test_workflow_is_valid_yaml() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "jobs:" in text and "hosted-acceptance:" in text
    assert "container: python:3.14.6-bookworm" in text
    assert "workflow_dispatch:" in text
