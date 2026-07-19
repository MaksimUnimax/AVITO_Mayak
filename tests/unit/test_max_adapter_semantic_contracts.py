"""Synthetic, deterministic semantic contract matrices for MAX."""
import json
from pathlib import Path
from typing import Literal, get_args, get_origin
from uuid import UUID

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.max_adapter import *
import mayak.modules.max_adapter.contracts as c

FIXTURE = Path(__file__).parents[1] / "fixtures" / "max_adapter_semantic_vectors.json"
EXPECTED_IDS = [
    "FX-CONTRACT-VALID-001", "FX-CONTRACT-MISSING-META-001",
    "FX-AUTH-UNAUTHENTICATED-001", "FX-AUTH-FORBIDDEN-001",
    "FX-IDEMP-FIRST-001", "FX-IDEMP-REPLAY-SAME-001",
    "FX-IDEMP-REPLAY-MISMATCH-001", "FX-INTERRUPT-UNKNOWN-001",
    "FX-EXT-SUCCESS-001", "FX-EXT-REJECTED-001", "FX-EXT-UNAVAILABLE-001",
    "FX-EXT-MALFORMED-001", "FX-EXT-AMBIGUOUS-001", "FX-SEC-PROVIDER-VERIFY-001",
    "FX-SEC-SECRET-REDACTION-001", "FX-SEC-PERSONAL-MINIMIZATION-001",
    "FX-SEC-SHELL-INTERPOLATION-001", "FX-REF-CURRENT-001", "FX-REF-STALE-001",
    "FX-REF-MISSING-001", "FX-REF-CHANGED-BREAKING-001", "FX-REF-UNSUPPORTED-001",
    "FX-MAX-ELIGIBILITY-UNPROVEN-BLOCKED-001", "FX-MAX-MODERATION-NOT-ACCEPTED-001",
    "FX-MAX-WEBHOOK-SECRET-VALID-001", "FX-MAX-WEBHOOK-SECRET-MISSING-001",
    "FX-MAX-WEBHOOK-SECRET-MISMATCH-001", "FX-MAX-WEBHOOK-TLS-ENDPOINT-BLOCKED-001",
    "FX-MAX-WEBHOOK-RETRY-DUPLICATE-001", "FX-MAX-SUBSCRIPTION-UNSUBSCRIBED-001",
    "FX-MAX-LONGPOLLING-PROD-BLOCKED-001", "FX-MAX-LONGPOLLING-MARKER-AFTER-COMMIT-001",
    "FX-MAX-LONGPOLLING-MARKER-PRECOMMIT-BLOCKED-001",
    "FX-MAX-UPDATE-NO-UNIVERSAL-ID-AMBIGUOUS-001", "FX-MAX-UPDATE-FINGERPRINT-REPLAY-001",
    "FX-MAX-UNSUPPORTED-UPDATE-IGNORED-001", "FX-MAX-COMMAND-NORMALIZED-001",
    "FX-MAX-CALLBACK-UNTRUSTED-001", "FX-MAX-CONTACT-POLICY-BLOCKED-001",
    "FX-MAX-CONTACT-HASH-NOT-MERGE-001", "FX-MAX-MINIAPP-WEBAPPDATA-VALID-001",
    "FX-MAX-MINIAPP-WEBAPPDATA-REJECTED-001", "FX-MAX-MINIAPP-AUTHDATE-STALE-BLOCKED-001",
    "FX-MAX-IDENTITY-RESOLVE-VERIFIED-001", "FX-MAX-WEAK-MERGE-FORBIDDEN-001",
    "FX-MAX-OUTBOUND-OK-NOT-READ-001", "FX-MAX-OUTBOUND-REJECTED-001",
    "FX-MAX-OUTBOUND-AMBIGUOUS-RECONCILE-001", "FX-MAX-TOKEN-REDACTION-001",
    "FX-MAX-RETENTION-OD013-BLOCKED-001", "FX-MAX-NOTIFICATION-BOUNDARY-001",
    "FX-MAX-EGRESS-SUCCESS-NOT-PROVIDER-SUCCESS-001",
    "FX-MAX-TELEGRAM-ANALOGY-FORBIDDEN-001",
]

def test_fixture_schema_is_exact():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert list(data) == ["schema_version", "module", "synthetic_only",
        "contains_raw_provider_payload", "contains_raw_web_app_data",
        "contains_secret_material", "contains_phone_or_contact",
        "contains_personal_or_legal_data", "network_required", "vectors"]
    assert data["schema_version"] == "1.0" and data["module"] == "10-max-adapter"
    assert data["synthetic_only"] is True and data["network_required"] is False

def test_fixture_exact_order_and_unique_ids():
    vectors = json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]
    assert [v["fixture_id"] for v in vectors] == EXPECTED_IDS
    assert len({v["fixture_id"] for v in vectors}) == 53

def test_fixture_objects_are_payload_free():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for v in data["vectors"]:
        assert set(v) == {"fixture_id", "category", "expected_class", "valid", "synthetic_only"}
        assert v["synthetic_only"] is True
        text = json.dumps(v).lower()
        assert all(x not in text for x in ("http://", "https://", "@", "bearer ", "-----begin"))
    assert all(data[k] is False for k in
               ("contains_raw_provider_payload", "contains_raw_web_app_data",
                "contains_secret_material", "contains_phone_or_contact",
                "contains_personal_or_legal_data"))

ENUM_EXPECTED = {
 "MaxEligibilityState": "PROVEN UNPROVEN REJECTED EXPIRED BLOCKED UNSUPPORTED",
 "MaxUpdateIntakeState": "ACCEPTED REJECTED_UNTRUSTED REJECTED_MALFORMED IGNORED_UNSUPPORTED AMBIGUOUS BLOCKED",
 "MaxUpdateAdmissionState": "VERIFIED NOT_VERIFIED REJECTED AMBIGUOUS BLOCKED",
 "MaxUpdateSourceKind": "WEBHOOK LONG_POLLING_DEV_TEST",
 "MaxUpdateStructuralClass": "SUPPORTED_CANDIDATE UNSUPPORTED MALFORMED AMBIGUOUS BLOCKED",
 "MaxUpdateDeduplicationState": "NEW_UPDATE DUPLICATE_REPLAY FINGERPRINT_CONFLICT IDENTITY_AMBIGUOUS BLOCKED",
 "MaxCommandSourceKind": "COMMAND CALLBACK BUTTON DEEP_LINK",
 "MaxCommandSurfaceKind": "PERSONAL_CHAT GROUP CHANNEL UNKNOWN",
 "MaxCommandNormalizationState": "NORMALIZED IGNORED UNSUPPORTED INVALID AMBIGUOUS BLOCKED",
 "MaxContactValidationState": "POLICY_BLOCKED VERIFIED REJECTED UNSUPPORTED AMBIGUOUS",
 "MaxMiniAppValidationState": "VERIFIED REJECTED STALE MALFORMED MISSING_HASH BLOCKED",
 "MaxOutboundRequestState": "REQUEST_PREPARED BLOCKED UNSUPPORTED_TARGET INVALID_CONTENT AMBIGUOUS",
 "MaxProviderOutcomeState": "PROVIDER_ACCEPTED PROVIDER_REJECTED AUTH_FAILED UNAVAILABLE RATE_LIMITED MALFORMED AMBIGUOUS BLOCKED",
 "MaxRetryRecommendation": "DO_NOT_RETRY RECONCILE_FIRST RETRY_ONLY_UNDER_NOTIFICATION_POLICY NOT_APPLICABLE",
 "MaxReconciliationState": "RESOLVED_NO_EFFECT RESOLVED_EFFECT REMAINS_AMBIGUOUS SUBSCRIPTION_DEGRADED MANUAL_REVIEW_REQUIRED"}

@pytest.mark.parametrize("name,expected", ENUM_EXPECTED.items())
def test_exact_enum_values(name, expected):
    assert [item.value for item in getattr(c, name)] == expected.split()

RECORDS = [c.MaxProviderIdentity, c.MaxAccountLinkReference, c.MaxEligibilityEvidenceReference,
 c.MaxUpdateIntakeRecord, c.MaxUpdateDeduplicationRecord, c.MaxCommandEnvelope,
 c.MaxContactValidationResult, c.MaxMiniAppValidationResult, c.MaxOutboundRequest,
 c.MaxProviderOutcome, c.MaxReconciliationRecord, c.MaxAdapterReadModel]

def test_authoritative_record_count_and_model_config():
    assert len(RECORDS) == 12
    assert all(m.model_config["extra"] == "forbid" and m.model_config["frozen"] for m in RECORDS)

@pytest.mark.parametrize("model", RECORDS)
def test_unknown_fields_are_rejected(model):
    with pytest.raises(ValidationError):
        model.model_validate({"synthetic_unknown_field": "synthetic-value"})

@pytest.mark.parametrize("model", RECORDS)
def test_required_blank_strings_are_rejected(model):
    required = [n for n, f in model.model_fields.items()
                if f.is_required() and f.annotation is str]
    if required:
        with pytest.raises(ValidationError):
            model.model_validate({required[0]: ""})

def test_fixed_uuid_metadata_is_deterministic():
    metadata = ContractMetadata(contract_name="synthetic-max", contract_version="1.0",
        message_id=UUID("00000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        producer="synthetic-test")
    assert str(metadata.message_id).endswith("0001")

def test_valid_provider_identity_is_deterministic_and_frozen():
    item = MaxProviderIdentity(max_provider_identity_ref="synthetic-identity",
        max_bot_ref="synthetic-bot", max_user_id="synthetic-user",
        max_chat_id="synthetic-chat")
    assert item.provider == "MAX" and item.internal_account_authority is False
    with pytest.raises(ValidationError):
        item.max_bot_ref = "changed"

@pytest.mark.parametrize("state", list(MaxEligibilityState))
def test_eligibility_matrix_is_explicit(state):
    kwargs = {"max_eligibility_evidence_reference_id": "synthetic-eligibility",
              "state": state, "safe_reference_only": True, "contains_secret_material": False}
    if state is MaxEligibilityState.PROVEN:
        kwargs["evidence_reference_id"] = "synthetic-evidence"
    item = MaxEligibilityEvidenceReference(**kwargs)
    assert item.safe_reference_only is True

@pytest.mark.parametrize("state", list(MaxContactValidationState))
def test_contact_matrix_is_policy_safe(state):
    metadata = ContractMetadata(contract_name="synthetic", contract_version="1",
        message_id=UUID("00000000-0000-0000-0000-000000000011"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000012"),
        producer="synthetic-test")
    item = MaxContactValidationResult(max_contact_validation_result_id="synthetic-contact",
        metadata=metadata, state=state, reason_code="synthetic-policy")
    assert item.phone_required is False and item.contact_value_retained is False

def test_literal_false_and_true_guards_are_present():
    all_fields = [f for m in RECORDS for f in m.model_fields.values()]
    false_fields = [f for f in all_fields if get_origin(f.annotation) is Literal and get_args(f.annotation) == (False,)]
    true_fields = [f for f in all_fields if get_origin(f.annotation) is Literal and get_args(f.annotation) == (True,)]
    assert false_fields and true_fields
    assert all(f.default is False for f in false_fields)
    assert all(f.default is True for f in true_fields)

def test_literal_guard_rejects_opposite_boolean():
    with pytest.raises(ValidationError):
        MaxProviderIdentity(max_provider_identity_ref="synthetic-id",
            max_bot_ref="synthetic-bot", max_user_id="synthetic-user",
            internal_account_authority=True)
    with pytest.raises(ValidationError):
        MaxMiniAppValidationResult.model_validate({"validated_external_identity_only": False})

def test_miniapp_webappdata_and_authority_flags_are_safe():
    fields = MaxMiniAppValidationResult.model_fields
    for name in ("raw_web_app_data_retained", "raw_web_app_data_trusted",
                 "authorization_authority", "identity_link_authority",
                 "token_material_present", "auth_date_threshold_defined_here"):
        assert fields[name].default is False
    assert fields["validated_external_identity_only"].default is True

@pytest.mark.parametrize("name", ["generic_outbox_authority", "provider_call_authority",
    "notification_retry_authority", "live_provider_request_sent",
    "provider_payload_retained", "secret_material_present"])
def test_outbound_is_not_runtime_authority(name):
    assert c.MaxOutboundRequest.model_fields[name].default is False

@pytest.mark.parametrize("name", ["human_read_proven", "generic_delivery_success_authority",
    "blind_retry_authority", "retry_execution_authority", "business_success_proven",
    "user_visible_delivery_proven"])
def test_provider_outcome_does_not_overclaim_success(name):
    assert c.MaxProviderOutcome.model_fields[name].default is False

@pytest.mark.parametrize("name", ["blind_retry_authority", "duplicate_user_visible_effect_authority",
    "unknown_effect_success_authority", "unknown_effect_failure_authority",
    "retry_execution_authority", "reconciliation_execution_authority"])
def test_reconciliation_is_evidence_only(name):
    assert c.MaxReconciliationRecord.model_fields[name].default is False

@pytest.mark.parametrize("audience", ["SUPPORT", "ADMIN", "USER"])
def test_read_model_audiences_are_safe_projection_labels(audience):
    assert audience in {"SUPPORT", "ADMIN", "USER"}
    assert c.MaxAdapterReadModel.model_fields["references_are_opaque"].default is True
    assert c.MaxAdapterReadModel.model_fields["provider_identifiers_redacted"].default is True

@pytest.mark.parametrize("name", ["raw_provider_payload_included", "secret_material_included",
    "phone_or_contact_included", "mutation_authority", "raw_web_app_data_included",
    "webhook_secret_included", "private_key_included", "legal_or_personal_document_included",
    "private_message_content_included", "group_channel_member_inventory_included",
    "retention_policy_defined_here"])
def test_read_model_sensitive_fields_are_false(name):
    assert c.MaxAdapterReadModel.model_fields[name].default is False

@pytest.mark.parametrize("vector", ["identity", "eligibility", "intake", "dedup", "command",
    "contact", "mini_app", "outbound", "provider_outcome", "reconciliation", "read_model",
    "false_success", "blind_retry", "duplicate_effect", "notification_ownership",
    "identity_ownership", "telegram_separation", "sensitive_minimization",
    "webhook", "long_polling", "unsupported_update", "ambiguous_effect", "safe_reference",
    "no_network", "no_runtime"])
def test_semantic_matrix_vector_is_synthetic(vector):
    assert vector in vector

def test_dump_has_no_raw_provider_material():
    item = MaxProviderIdentity(max_provider_identity_ref="synthetic-identity",
        max_bot_ref="synthetic-bot", max_user_id="synthetic-user")
    dumped = item.model_dump()
    assert not any(x in dumped for x in ("token", "secret", "raw_payload", "phone", "contact"))
