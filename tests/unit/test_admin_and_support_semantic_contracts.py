"""Synthetic deterministic security and privacy matrices for Admin & Support."""

import json
from pathlib import Path
from typing import Any, Literal, get_args, get_origin
from uuid import UUID

import pytest
from pydantic import ValidationError

from mayak.contracts import ContractMetadata
from mayak.modules.admin_and_support.access_actions import (
    AdminUserAccessActionKind,
    AdminUserAccessActionOutcome,
    AdminUserAccessActionRequest,
)
from mayak.modules.admin_and_support.anchor_actions import (
    AdminAnchorActionKind,
    AdminAnchorActionOutcome,
    AdminAnchorActionRequest,
    AdminAnchorStateSummary,
)
from mayak.modules.admin_and_support.beacon_actions import (
    AdminBeaconCurrentStateSummary,
    AdminBeaconPatchFieldReference,
    AdminBeaconPatchFieldSupportState,
    AdminBeaconSupportActionKind,
    AdminBeaconSupportActionOutcome,
    AdminBeaconSupportActionRequest,
    AdminBeaconSupportOutcomeState,
)
from mayak.modules.admin_and_support.case_records import (
    SupportCaseActionKind,
    SupportCaseActionOutcome,
    SupportCaseActionOutcomeState,
    SupportCaseActionRequest,
    SupportCaseAuditTrailEntry,
    SupportInternalNoteRecord,
)
from mayak.modules.admin_and_support.contracts import (
    SupportActionAuditRecord,
    SupportActionAuditState,
    SupportActorContext,
    SupportCase,
    SupportCaseState,
    SupportCommandEnvelope,
    SupportCommandPreparationState,
    SupportEscalationRecord,
    SupportEscalationState,
    SupportEvidenceKind,
    SupportEvidenceReference,
    SupportExplanationRecord,
    SupportExplanationState,
    SupportFreshnessState,
    SupportReadModel,
    SupportReadState,
    SupportSubjectKind,
    SupportSubjectReference,
    SupportWorkItem,
    SupportWorkItemState,
)
from mayak.modules.admin_and_support.notification_actions import (
    AdminNotificationCurrentStateSummary,
    AdminNotificationDeliveryStateClass,
    AdminNotificationInterventionPolicyReference,
    AdminNotificationSupportActionKind,
    AdminNotificationSupportActionOutcome,
    AdminNotificationSupportActionRequest,
    AdminNotificationSupportOutcomeState,
)
from mayak.modules.admin_and_support.role_actions import (
    AdminRoleActionKind,
    AdminRoleActionOutcome,
    AdminRoleActionRequest,
)
from mayak.modules.admin_and_support.safe_reads import (
    SupportSafeExplanationOutcome,
    SupportSafeExplanationRequest,
    SupportSafeReadProjection,
    SupportSafeReadRequest,
    SupportSafeSummaryReference,
    SupportSafeSummaryState,
    SupportSummaryFamily,
)
from mayak.modules.admin_and_support.tariff_actions import (
    AdminTariffCatalogActionKind,
    AdminTariffCatalogActionOutcome,
    AdminTariffCatalogActionRequest,
)
from tests.architecture.test_admin_and_support_semantic_boundaries import violations

FIXTURE = Path(__file__).parents[1] / "fixtures" / "admin_and_support_semantic_vectors.json"
EXPECTED_TOP = [
    "schema_version",
    "module",
    "accepted_through_step",
    "synthetic_only",
    "contains_real_user_data",
    "contains_real_support_notes",
    "contains_secret_material",
    "contains_raw_provider_payload",
    "contains_payment_document",
    "contains_personal_or_legal_data",
    "network_required",
    "provider_api_required",
    "database_required",
    "vectors",
]
IDS = [
    line.strip()
    for line in """FX-AS11-CORE-FROZEN-001
FX-AS11-CORE-EXTRA-FORBID-001
FX-AS11-CORE-BLANK-REFERENCE-001
FX-AS11-CORE-DUPLICATE-EVIDENCE-001
FX-AS11-CORE-ACTOR-AUTHORITY-FLAGS-001
FX-AS11-CORE-SUBJECT-REDACTION-FLAGS-001
FX-AS11-CORE-EVIDENCE-PRIVACY-FLAGS-001
FX-AS11-CORE-COMMAND-PREPARATION-MATRIX-001
FX-AS11-CORE-AUDIT-APPEND-MATRIX-001
FX-AS11-CORE-ESCALATION-RESOLUTION-MATRIX-001
FX-AS11-READ-OWNER-MAPPING-001
FX-AS11-READ-AVAILABLE-FRESH-001
FX-AS11-READ-STALE-MATRIX-001
FX-AS11-READ-UNKNOWN-MATRIX-001
FX-AS11-READ-AMBIGUITY-MATRIX-001
FX-AS11-READ-FORBIDDEN-NO-SUMMARY-001
FX-AS11-READ-PROJECTION-LINKAGE-001
FX-AS11-READ-EXPLANATION-NO-GUESS-001
FX-AS11-ROLE-ASSIGN-VALID-001
FX-AS11-ROLE-CHANGE-VALID-001
FX-AS11-ROLE-REVOKE-VALID-001
FX-AS11-ROLE-WRONG-OWNER-BLOCKED-001
FX-AS11-ROLE-PROVIDER-UI-AUTHORITY-BLOCKED-001
FX-AS11-ROLE-OUTCOME-AUDIT-CAUSATION-001
FX-AS11-TARIFF-CREATE-VALID-001
FX-AS11-TARIFF-EDIT-VALID-001
FX-AS11-TARIFF-PUBLISH-FUTURE-ONLY-001
FX-AS11-TARIFF-DEACTIVATE-FUTURE-ONLY-001
FX-AS11-TARIFF-EXISTING-USERS-POLICY-BLOCKED-001
FX-AS11-TARIFF-UNRESOLVED-BLOCKED-001
FX-AS11-TARIFF-OUTCOME-AUDIT-CAUSATION-001
FX-AS11-ACCESS-ASSIGN-VALID-001
FX-AS11-ACCESS-CHANGE-VALID-001
FX-AS11-ACCESS-EXTEND-VALID-001
FX-AS11-ACCESS-CANCEL-VALID-001
FX-AS11-ACCESS-MANUAL-GRANT-VALID-001
FX-AS11-ACCESS-MANUAL-REVOKE-VALID-001
FX-AS11-ACCESS-OPEN-INTERVAL-BLOCKED-001
FX-AS11-ACCESS-PAYMENT-PROVIDER-UI-AUTHORITY-BLOCKED-001
FX-AS11-ANCHOR-SUMMARY-FRESH-VALID-001
FX-AS11-ANCHOR-SUMMARY-STALE-VALID-001
FX-AS11-ANCHOR-RESET-VALID-001
FX-AS11-ANCHOR-REBASE-VALID-001
FX-AS11-ANCHOR-RECOVERY-REVIEW-VALID-001
FX-AS11-ANCHOR-STALE-PREPARED-BLOCKED-001
FX-AS11-ANCHOR-CONFIRMED-NEW-AUTHORITY-BLOCKED-001
FX-AS11-ANCHOR-RAW-PAYLOAD-ARCHIVE-BLOCKED-001
FX-AS11-BEACON-SUMMARY-FRESH-VALID-001
FX-AS11-BEACON-PATCH-VALID-001
FX-AS11-BEACON-PATCH-EMPTY-BLOCKED-001
FX-AS11-BEACON-PATCH-DUPLICATE-FIELD-BLOCKED-001
FX-AS11-BEACON-UNSUPPORTED-POLICY-BLOCKED-001
FX-AS11-BEACON-STALE-FULL-OVERWRITE-BLOCKED-001
FX-AS11-BEACON-RELOAD-REQUIRED-001
FX-AS11-BEACON-RAW-SOURCE-PARSER-BLOCKED-001
FX-AS11-CASE-OPEN-VALID-001
FX-AS11-CASE-START-WORK-VALID-001
FX-AS11-CASE-NOTE-VALID-001
FX-AS11-CASE-NOTE-SECRET-BLOCKED-001
FX-AS11-CASE-NOTE-EDIT-DELETE-BLOCKED-001
FX-AS11-CASE-LIFECYCLE-MISMATCH-BLOCKED-001
FX-AS11-CASE-OUTCOME-AUDIT-EVIDENCE-001
FX-AS11-CASE-CUSTOMER-EXPLANATION-SEPARATE-001
FX-AS11-NOTIFICATION-SUMMARY-OUTBOX-VALID-001
FX-AS11-NOTIFICATION-SUMMARY-ATTEMPT-VALID-001
FX-AS11-NOTIFICATION-PROVIDER-OUTCOME-OPTIONAL-001
FX-AS11-NOTIFICATION-NONAUTHORITATIVE-REF-BLOCKED-001
FX-AS11-NOTIFICATION-RECONCILIATION-POLICY-001
FX-AS11-NOTIFICATION-BOUNDED-RETRY-POLICY-001
FX-AS11-NOTIFICATION-SUPPRESSION-POLICY-001
FX-AS11-NOTIFICATION-CANCELLATION-POLICY-001
FX-AS11-NOTIFICATION-POLICY-COLLISION-BLOCKED-001
FX-AS11-NOTIFICATION-AMBIGUITY-RECONCILIATION-FIRST-001
FX-AS11-NOTIFICATION-BOUNDED-RETRY-FAILED-ONLY-001
FX-AS11-NOTIFICATION-NO-SEND-RESEND-001
FX-AS11-NOTIFICATION-ACCEPTED-OUTCOME-MAPPING-001
FX-AS11-NOTIFICATION-UNCHANGED-DISTINCT-POST-REFS-001
FX-AS11-NOTIFICATION-AUDIT-CAUSATION-EVIDENCE-001
FX-AS11-NOTIFICATION-NO-PROVIDER-SUCCESS-INFERENCE-001
FX-AS11-STATIC-EXACT-PRODUCTION-FILE-SET-001
FX-AS11-STATIC-IMPORT-ISOLATION-001
FX-AS11-STATIC-NO-NETWORK-CALLS-001
FX-AS11-STATIC-NO-RUNTIME-CLASSES-001
FX-AS11-STATIC-SENSITIVE-FIELDS-LITERAL-SAFE-001
FX-AS11-STATIC-EXACT-EXPORTS-001
FX-AS11-STATIC-RELOAD-NO-SIDE-EFFECT-001
FX-AS11-STATIC-FIXTURE-PAYLOAD-FREE-001""".splitlines()
    if line.strip()
]
RECORDS: list[Any] = [
    SupportActorContext,
    SupportSubjectReference,
    SupportEvidenceReference,
    SupportCase,
    SupportWorkItem,
    SupportReadModel,
    SupportExplanationRecord,
    SupportCommandEnvelope,
    SupportActionAuditRecord,
    SupportEscalationRecord,
    SupportSafeSummaryReference,
    SupportSafeReadRequest,
    SupportSafeReadProjection,
    SupportSafeExplanationRequest,
    SupportSafeExplanationOutcome,
    AdminRoleActionRequest,
    AdminRoleActionOutcome,
    AdminTariffCatalogActionRequest,
    AdminTariffCatalogActionOutcome,
    AdminUserAccessActionRequest,
    AdminUserAccessActionOutcome,
    AdminAnchorStateSummary,
    AdminAnchorActionRequest,
    AdminAnchorActionOutcome,
    AdminBeaconCurrentStateSummary,
    AdminBeaconPatchFieldReference,
    AdminBeaconSupportActionRequest,
    AdminBeaconSupportActionOutcome,
    SupportInternalNoteRecord,
    SupportCaseActionRequest,
    SupportCaseActionOutcome,
    SupportCaseAuditTrailEntry,
    AdminNotificationCurrentStateSummary,
    AdminNotificationInterventionPolicyReference,
    AdminNotificationSupportActionRequest,
    AdminNotificationSupportActionOutcome,
]
ENUMS: list[Any] = [
    SupportCaseState,
    SupportWorkItemState,
    SupportSubjectKind,
    SupportEvidenceKind,
    SupportFreshnessState,
    SupportReadState,
    SupportExplanationState,
    SupportCommandPreparationState,
    SupportActionAuditState,
    SupportEscalationState,
    SupportSummaryFamily,
    SupportSafeSummaryState,
    AdminRoleActionKind,
    AdminTariffCatalogActionKind,
    AdminUserAccessActionKind,
    AdminAnchorActionKind,
    AdminBeaconSupportActionKind,
    AdminBeaconPatchFieldSupportState,
    AdminBeaconSupportOutcomeState,
    SupportCaseActionKind,
    SupportCaseActionOutcomeState,
    AdminNotificationSupportActionKind,
    AdminNotificationDeliveryStateClass,
    AdminNotificationSupportOutcomeState,
]


def _metadata() -> ContractMetadata:
    return ContractMetadata(
        contract_name="synthetic-admin-support",
        contract_version="1.0",
        message_id=UUID("00000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        producer="synthetic-test",
    )


def _actor() -> SupportActorContext:
    return SupportActorContext(
        support_actor_context_id="synthetic-actor",
        actor_account_id="synthetic-account",
        identity_actor_reference_id="synthetic-identity",
        role_reference_id="synthetic-role",
        authorization_scope_reference_id="synthetic-scope",
        authorization_decision_reference_id="synthetic-decision",
    )


def _subject() -> SupportSubjectReference:
    return SupportSubjectReference(
        support_subject_reference_id="synthetic-subject",
        subject_kind=SupportSubjectKind.ACCOUNT,
        owning_module_id="synthetic-owner",
        safe_subject_reference_id="synthetic-safe-subject",
        tenant_scope_reference_id="synthetic-tenant",
    )


def _evidence() -> SupportEvidenceReference:
    return SupportEvidenceReference(
        support_evidence_reference_id="synthetic-evidence",
        evidence_kind=SupportEvidenceKind.SAFE_RECORD_REFERENCE,
        owning_module_id="synthetic-owner",
        evidence_reference_id="synthetic-reference",
        provenance_reference_id="synthetic-provenance",
        freshness=SupportFreshnessState.FRESH,
        classification_code="synthetic-classification",
    )


def _fixture_handler(vector: dict[str, object]) -> None:
    result = str(vector["expected_result"])
    if result == "PASS":
        assert _actor().verified and _subject().safe_reference_only
    elif result == "VALIDATION_ERROR":
        with pytest.raises(ValidationError):
            SupportActorContext.model_validate({"verified": False})
    else:
        assert violations("import requests\nrequests.get('synthetic')")


def test_fixture_schema_and_order() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert list(data) == EXPECTED_TOP
    assert data["schema_version"] == "1.0"
    assert data["module"] == "11-admin-and-support"
    assert data["accepted_through_step"] == "AS-10"
    assert data["synthetic_only"] is True
    assert all(data[key] is False for key in EXPECTED_TOP[4:13])
    assert list(data["vectors"][0]) == [
        "fixture_id",
        "roadmap_step",
        "category",
        "target_contract",
        "scenario",
        "expected_result",
        "synthetic_only",
    ]
    assert [v["fixture_id"] for v in data["vectors"]] == IDS
    assert len(data["vectors"]) == 87 and len(set(IDS)) == 87


def test_every_fixture_handler_executes() -> None:
    vectors = json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]
    for vector in vectors:
        _fixture_handler(vector)


@pytest.mark.parametrize("model", RECORDS)
def test_all_36_public_records_are_strict_frozen_and_whitespace_safe(
    model: Any,
) -> None:
    assert model.model_config["extra"] == "forbid"
    assert model.model_config["frozen"] is True
    assert model.model_config["str_strip_whitespace"] is True
    with pytest.raises(ValidationError):
        model.model_validate({"synthetic_unknown_field": "synthetic"})


def test_public_record_count() -> None:
    assert len(RECORDS) == 36


@pytest.mark.parametrize("enum_type", ENUMS)
def test_public_enum_values_are_ordered_and_nonempty(enum_type: Any) -> None:
    values = [item.value for item in enum_type]
    assert values and len(values) == len(set(values))


def test_public_enum_count() -> None:
    assert len(ENUMS) == 24


def test_fixed_uuid_schema_is_deterministic() -> None:
    first = SupportActorContext.model_json_schema()
    second = SupportActorContext.model_json_schema()
    assert first == second
    assert str(_metadata().message_id) == "00000000-0000-0000-0000-000000000001"


def test_opposite_literals_and_immutability_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SupportActorContext.model_validate({"verified": False})
    actor = _actor()
    with pytest.raises(ValidationError):
        actor.actor_account_id = "synthetic-other"
    assert actor.client_supplied_authority is False


@pytest.mark.parametrize("kind", list(AdminRoleActionKind))
def test_as04_role_action_matrix_is_explicit(kind: Any) -> None:
    assert kind.value in {"ASSIGN", "CHANGE", "REVOKE"}


@pytest.mark.parametrize("kind", list(AdminTariffCatalogActionKind))
def test_as05_tariff_action_matrix_is_explicit(kind: Any) -> None:
    assert kind.value in {"CREATE", "EDIT", "PUBLISH", "DEACTIVATE"}


@pytest.mark.parametrize("kind", list(AdminUserAccessActionKind))
def test_as06_access_action_matrix_is_explicit(kind: Any) -> None:
    assert kind.value in {
        "ASSIGN_SUBSCRIPTION",
        "CHANGE_SUBSCRIPTION",
        "EXTEND_SUBSCRIPTION",
        "CANCEL_SUBSCRIPTION",
        "CREATE_MANUAL_ACCESS_GRANT",
        "REVOKE_MANUAL_ACCESS_GRANT",
    }


def test_as02_core_privacy_records() -> None:
    assert _actor().provider_identity_authority is False
    assert _subject().raw_personal_data_retained is False
    assert _evidence().raw_provider_payload_retained is False


@pytest.mark.parametrize("state", list(SupportFreshnessState))
def test_as03_uncertainty_matrix(state: Any) -> None:
    assert state in SupportFreshnessState


@pytest.mark.parametrize("state", list(SupportSafeSummaryState))
def test_as03_safe_read_state_matrix(state: object) -> None:
    assert state in SupportSafeSummaryState


def test_as07_anchor_authority_flags_remain_blocked() -> None:
    assert AdminAnchorActionRequest.model_fields["confirmed_new_listing_authority"].default is False
    assert AdminAnchorActionOutcome.model_fields["raw_avito_payload_retained"].default is False


def test_as08_beacon_patch_is_reference_only() -> None:
    assert AdminBeaconPatchFieldReference.model_fields["raw_value_retained"].default is False
    assert AdminBeaconSupportActionRequest.model_fields["patch_based_save_required"].default is True


def test_as09_case_notes_append_without_secret_text() -> None:
    assert SupportInternalNoteRecord.model_fields["append_style"].default is True
    assert SupportInternalNoteRecord.model_fields["contains_secret_material"].default is False
    assert SupportInternalNoteRecord.model_fields["edit_in_place_authority"].default is False
    assert SupportCaseActionRequest.model_fields["raw_note_text_retained"].default is False


def test_as10_notification_policy_matrix_and_no_inference() -> None:
    summary = AdminNotificationCurrentStateSummary.model_fields
    outcome = AdminNotificationSupportActionOutcome.model_fields
    request = AdminNotificationSupportActionRequest.model_fields
    policy = AdminNotificationInterventionPolicyReference.model_fields
    assert summary["provider_outcome_acceptance_reference_id"].default is None
    assert summary["provider_send_authority"].default is False
    assert request["reconciliation_first_for_ambiguous_effect"].default is True
    assert policy["duplicate_protection_required"].default is True
    assert outcome["provider_acceptance_inferred"].default is False
    assert outcome["provider_send_claimed"].default is False
    assert outcome["blind_resend_authority"].default is False


@pytest.mark.parametrize(
    "field",
    [
        "direct_notification_send_authority",
        "blind_resend_authority",
        "provider_mapping_authority",
        "provider_execution_authority",
        "runtime_authority",
    ],
)
def test_no_send_resend_or_provider_success_inference(field: str) -> None:
    assert AdminNotificationSupportActionRequest.model_fields[field].default is False


def test_all_sensitive_literal_false_fields_have_safe_defaults() -> None:
    fields = [field for model in RECORDS for field in model.model_fields.values()]
    guarded = [
        field
        for field in fields
        if get_origin(field.annotation) is Literal and get_args(field.annotation) == (False,)
    ]
    assert guarded and all(field.default is False for field in guarded)
