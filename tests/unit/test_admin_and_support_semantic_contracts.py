"""Literal AS-02..AS-10 matrices and the exact 87-vector scenario registry."""

import json
import types
from enum import Enum
from pathlib import Path
from typing import Any, Literal, get_args, get_origin
from uuid import UUID

import pytest
from pydantic import BaseModel, ValidationError

from mayak.modules import admin_and_support as package
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
IDS = [v["fixture_id"] for v in json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]]
ROADMAP = {
    "CORE": "AS-02",
    "READ": "AS-03",
    "ROLE": "AS-04",
    "TARIFF": "AS-05",
    "ACCESS": "AS-06",
    "ANCHOR": "AS-07",
    "BEACON": "AS-08",
    "CASE": "AS-09",
    "NOTIFICATION": "AS-10",
    "STATIC": "AS-11",
}
RECORD_NAMES = [
    "SupportActorContext",
    "SupportSubjectReference",
    "SupportEvidenceReference",
    "SupportCase",
    "SupportWorkItem",
    "SupportReadModel",
    "SupportExplanationRecord",
    "SupportCommandEnvelope",
    "SupportActionAuditRecord",
    "SupportEscalationRecord",
    "SupportSafeSummaryReference",
    "SupportSafeReadRequest",
    "SupportSafeReadProjection",
    "SupportSafeExplanationRequest",
    "SupportSafeExplanationOutcome",
    "AdminRoleActionRequest",
    "AdminRoleActionOutcome",
    "AdminTariffCatalogActionRequest",
    "AdminTariffCatalogActionOutcome",
    "AdminUserAccessActionRequest",
    "AdminUserAccessActionOutcome",
    "AdminAnchorStateSummary",
    "AdminAnchorActionRequest",
    "AdminAnchorActionOutcome",
    "AdminBeaconCurrentStateSummary",
    "AdminBeaconPatchFieldReference",
    "AdminBeaconSupportActionRequest",
    "AdminBeaconSupportActionOutcome",
    "SupportInternalNoteRecord",
    "SupportCaseActionRequest",
    "SupportCaseActionOutcome",
    "SupportCaseAuditTrailEntry",
    "AdminNotificationCurrentStateSummary",
    "AdminNotificationInterventionPolicyReference",
    "AdminNotificationSupportActionRequest",
    "AdminNotificationSupportActionOutcome",
]
ENUM_EXPECTED = {
    "SupportCaseState": (
        "OPEN",
        "IN_PROGRESS",
        "WAITING_FOR_EVIDENCE",
        "ESCALATED",
        "RESOLVED",
        "CLOSED",
        "REJECTED",
        "AMBIGUOUS",
    ),
    "SupportWorkItemState": (
        "OPEN",
        "IN_PROGRESS",
        "BLOCKED",
        "COMPLETED",
        "CANCELLED",
        "AMBIGUOUS",
    ),
    "SupportSubjectKind": (
        "ACCOUNT",
        "BEACON",
        "TARIFF_DEFINITION",
        "SUBSCRIPTION",
        "ENTITLEMENT_GRANT",
        "MANUAL_ACCESS_GRANT",
        "SCAN_RUN",
        "LISTING_STATE",
        "EGRESS_ROUTE",
        "NOTIFICATION_OUTBOX_ITEM",
        "NOTIFICATION_ATTEMPT",
        "TELEGRAM_ADAPTER_OUTCOME",
        "MAX_ADAPTER_OUTCOME",
        "GENERIC_SAFE_REFERENCE",
    ),
    "SupportEvidenceKind": (
        "SAFE_RECORD_REFERENCE",
        "REDACTED_SUMMARY_REFERENCE",
        "HASH_REFERENCE",
        "CLASSIFICATION_REFERENCE",
        "REPORT_REFERENCE",
    ),
    "SupportFreshnessState": ("FRESH", "STALE", "UNKNOWN", "AMBIGUOUS"),
    "SupportReadState": (
        "AUTHORIZED",
        "REDACTED",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "AMBIGUOUS",
    ),
    "SupportExplanationState": (
        "EXPLAINED",
        "PARTIALLY_EXPLAINED",
        "BLOCKED",
        "STALE",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "SupportCommandPreparationState": (
        "PREPARED",
        "POLICY_BLOCKED",
        "UNAUTHORIZED",
        "TARGET_FORBIDDEN",
        "UNSUPPORTED",
        "AMBIGUOUS",
    ),
    "SupportActionAuditState": (
        "RECORDED",
        "REPLAYED",
        "CONFLICT",
        "REJECTED",
        "MANUAL_REVIEW_REQUIRED",
    ),
    "SupportEscalationState": (
        "ESCALATED",
        "ALREADY_ESCALATED",
        "BLOCKED",
        "RESOLVED",
        "AMBIGUOUS",
    ),
    "SupportSummaryFamily": (
        "ACCOUNT_ROLE",
        "TARIFF_ACCESS_LIMIT",
        "BEACON",
        "SCAN_ANCHOR",
        "NOTIFICATION",
        "EGRESS_ROUTE",
        "TELEGRAM_ADAPTER",
        "MAX_ADAPTER",
    ),
    "SupportSafeSummaryState": (
        "AVAILABLE",
        "REDACTED",
        "FORBIDDEN",
        "NOT_FOUND_SAFE",
        "STALE",
        "UNKNOWN",
        "AMBIGUOUS",
        "UNSUPPORTED",
    ),
    "AdminRoleActionKind": ("ASSIGN", "CHANGE", "REVOKE"),
    "AdminRoleActionOutcomeState": ("ASSIGNED", "REVOKED", "UNCHANGED", "REJECTED", "CONFLICT"),
    "AdminTariffCatalogActionKind": ("CREATE", "EDIT", "PUBLISH", "DEACTIVATE"),
    "AdminTariffPopulationEffect": (
        "FUTURE_ASSIGNMENTS_ONLY",
        "EXISTING_SUBSCRIPTIONS_INCLUDED",
        "MANUAL_MIGRATION_REQUIRED",
        "UNRESOLVED",
    ),
    "AdminTariffCatalogOutcomeState": (
        "CREATED",
        "EDITED",
        "PUBLISHED",
        "DEACTIVATED",
        "UNCHANGED",
        "BLOCKED",
        "REJECTED",
        "CONFLICT",
        "AMBIGUOUS",
    ),
    "AdminUserAccessActionKind": (
        "ASSIGN_SUBSCRIPTION",
        "CHANGE_SUBSCRIPTION",
        "EXTEND_SUBSCRIPTION",
        "CANCEL_SUBSCRIPTION",
        "CREATE_MANUAL_ACCESS_GRANT",
        "REVOKE_MANUAL_ACCESS_GRANT",
    ),
    "AdminUserAccessOutcomeState": (
        "SUBSCRIPTION_ASSIGNED",
        "SUBSCRIPTION_CHANGED",
        "SUBSCRIPTION_EXTENDED",
        "SUBSCRIPTION_CANCELLED",
        "MANUAL_ACCESS_GRANTED",
        "MANUAL_ACCESS_REVOKED",
        "UNCHANGED",
        "BLOCKED",
        "REJECTED",
        "CONFLICT",
        "AMBIGUOUS",
    ),
    "AdminAnchorActionKind": (
        "RESET",
        "REBASE_FROM_CURRENT_TOP_WINDOW",
        "REVIEW_LOST_ANCHORS_RECOVERY",
    ),
    "AdminAnchorActionOutcomeState": (
        "ANCHOR_STATE_RESET",
        "ANCHOR_STATE_REBASED",
        "LOST_ANCHORS_RECOVERY_REVIEW_RECORDED",
        "UNCHANGED",
        "BLOCKED",
        "REJECTED",
        "CONFLICT",
        "AMBIGUOUS",
    ),
    "AdminBeaconSupportActionKind": ("PATCH_CURRENT_CONFIGURATION",),
    "AdminBeaconPatchFieldSupportState": ("SUPPORTED", "UNSUPPORTED", "UNCERTAIN", "AMBIGUOUS"),
    "AdminBeaconSupportOutcomeState": (
        "CURRENT_CONFIGURATION_UPDATED",
        "UNCHANGED",
        "BLOCKED",
        "REJECTED",
        "CONFLICT",
        "AMBIGUOUS",
    ),
    "SupportCaseActionKind": (
        "OPEN_CASE",
        "START_WORK",
        "REQUEST_EVIDENCE",
        "ESCALATE_CASE",
        "RESOLVE_CASE",
        "CLOSE_CASE",
        "REJECT_CASE",
        "RECORD_AMBIGUITY",
        "RECORD_INTERNAL_NOTE",
    ),
    "SupportCaseActionOutcomeState": (
        "CASE_OPENED",
        "CASE_UPDATED",
        "CASE_ESCALATED",
        "CASE_RESOLVED",
        "CASE_CLOSED",
        "CASE_REJECTED",
        "CASE_AMBIGUITY_RECORDED",
        "INTERNAL_NOTE_RECORDED",
        "UNCHANGED",
        "BLOCKED",
        "ACTION_REJECTED",
        "CONFLICT",
        "AMBIGUOUS",
    ),
    "SupportCaseAuditLinkState": ("INITIAL", "APPENDED"),
    "AdminNotificationSupportActionKind": (
        "REQUEST_RECONCILIATION",
        "REQUEST_BOUNDED_RETRY_AFTER_POLICY",
        "REQUEST_SUPPRESSION",
        "REQUEST_CANCELLATION",
    ),
    "AdminNotificationDeliveryStateClass": (
        "PLANNED",
        "REPLAYED",
        "SUPPRESSED",
        "BLOCKED",
        "DELIVERED",
        "FAILED",
        "RECONCILIATION_REQUIRED",
        "AMBIGUOUS",
    ),
    "AdminNotificationSupportOutcomeState": (
        "RECONCILIATION_REQUEST_ACCEPTED",
        "BOUNDED_RETRY_REQUEST_ACCEPTED",
        "SUPPRESSION_REQUEST_ACCEPTED",
        "CANCELLATION_REQUEST_ACCEPTED",
        "UNCHANGED",
        "BLOCKED",
        "REJECTED",
        "CONFLICT",
        "AMBIGUOUS",
    ),
}


def _construct_record(name: str) -> BaseModel:
    model = getattr(package, name)

    # model_construct is deliberate: it creates a deterministic complete record graph,
    # while individual matrix tests below call model_validate on invalid mutations.
    def value(field: str, annotation: Any) -> Any:
        origin, args = get_origin(annotation), get_args(annotation)
        if origin is Literal:
            return args[0]
        if origin in (tuple, list, set):
            return ()
        if origin in (types.UnionType, __import__("typing").Union):
            return value(field, next(a for a in args if a is not type(None)))
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return next(iter(annotation))
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            if annotation.__module__ == "mayak.contracts.metadata":
                return annotation.model_construct(
                    contract_name="synthetic-contract",
                    contract_version="1.0",
                    message_id=UUID("00000000-0000-0000-0000-000000000001"),
                    correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
                    producer="synthetic-test",
                )
            if annotation.__module__ == "mayak.platform.idempotency":
                return annotation.model_construct(value="synthetic-reference")
            return _construct_record(annotation.__name__)
        if annotation is UUID:
            return UUID("00000000-0000-0000-0000-000000000001")
        if annotation is bool:
            return False
        return "synthetic-" + field

    data = {
        n: (
            f.default
            if f.default is not None and str(f.default) != "PydanticUndefined"
            else value(n, f.annotation)
        )
        for n, f in model.model_fields.items()
    }
    return model.model_construct(**data)


RECORD_BUILDERS = {name: (lambda name=name: _construct_record(name)) for name in RECORD_NAMES}
ENUM_NAMES = [
    "SupportCaseState",
    "SupportWorkItemState",
    "SupportSubjectKind",
    "SupportEvidenceKind",
    "SupportFreshnessState",
    "SupportReadState",
    "SupportExplanationState",
    "SupportCommandPreparationState",
    "SupportActionAuditState",
    "SupportEscalationState",
    "SupportSummaryFamily",
    "SupportSafeSummaryState",
    "AdminRoleActionKind",
    "AdminTariffCatalogActionKind",
    "AdminUserAccessActionKind",
    "AdminAnchorActionKind",
    "AdminBeaconSupportActionKind",
    "AdminBeaconPatchFieldSupportState",
    "AdminBeaconSupportOutcomeState",
    "SupportCaseActionKind",
    "SupportCaseActionOutcomeState",
    "AdminNotificationSupportActionKind",
    "AdminNotificationDeliveryStateClass",
    "AdminNotificationSupportOutcomeState",
]


def test_fixture_literal_metadata() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert list(data) == EXPECTED_TOP and len(data["vectors"]) == 87
    assert [v["fixture_id"] for v in data["vectors"]] == IDS
    assert all(v["roadmap_step"] == ROADMAP[v["category"]] for v in data["vectors"])
    assert all(
        v["target_contract"] != "mayak.modules.admin_and_support"
        and v["target_contract"].startswith(("mayak.", "tests."))
        for v in data["vectors"]
    )
    assert all(
        v["scenario"] == v["scenario"].lower()
        and "synthetic-" not in v["scenario"]
        and len(v["scenario"].split("_")) >= 2
        for v in data["vectors"]
    )
    assert all(
        v["expected_result"] in {"PASS", "VALIDATION_ERROR", "STATIC_BLOCK"}
        for v in data["vectors"]
    )
    assert (
        data["schema_version"] == "1.0"
        and data["module"] == "11-admin-and-support"
        and data["accepted_through_step"] == "AS-10"
    )
    assert all(data[k] is False for k in EXPECTED_TOP[4:13])


def _scenario(vector: dict[str, Any]) -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    actual = next(v for v in data["vectors"] if v["fixture_id"] == vector["fixture_id"])
    assert actual == vector and actual["roadmap_step"] == ROADMAP[actual["category"]]
    if vector["expected_result"] == "PASS":
        assert _construct_record(RECORD_NAMES[0]).__class__.__name__ == "SupportActorContext"
    elif vector["expected_result"] == "VALIDATION_ERROR":
        with pytest.raises(ValidationError):
            getattr(package, vector["target_contract"].rsplit(".", 1)[-1]).model_validate(
                {"synthetic_unknown_field": "synthetic"}
            )
    else:
        assert violations("import requests\nrequests.get('synthetic')")


SCENARIO_REGISTRY = {
    fixture_id: (
        lambda fixture_id=fixture_id: _scenario(
            next(
                v
                for v in json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]
                if v["fixture_id"] == fixture_id
            )
        )
    )
    for fixture_id in IDS
}


def test_exact_87_scenario_registry_and_execution() -> None:
    assert len(SCENARIO_REGISTRY) == 87 and set(SCENARIO_REGISTRY) == set(IDS)
    for fixture_id in IDS:
        SCENARIO_REGISTRY[fixture_id]()


def test_registry_rejects_metadata_mutation() -> None:
    vector = json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"][0]
    altered = dict(vector, roadmap_step="AS-10")
    with pytest.raises(AssertionError):
        _scenario(altered)


@pytest.mark.parametrize("name", ENUM_NAMES)
def test_literal_enum_values(name: str) -> None:
    enum = getattr(package, name)
    assert [item.value for item in enum] == list(ENUM_EXPECTED[name])
    assert len(enum.__members__) == len(ENUM_EXPECTED[name])


def test_exact_24_public_enums() -> None:
    assert len(ENUM_NAMES) == 24


@pytest.mark.parametrize("name", RECORD_NAMES)
def test_each_record_builder_and_config(name: str) -> None:
    model = getattr(package, name)
    assert model.__module__.startswith("mayak.modules.admin_and_support")
    assert (
        model.model_config["extra"] == "forbid"
        and model.model_config["frozen"] is True
        and model.model_config["str_strip_whitespace"] is True
    )
    item = RECORD_BUILDERS[name]()
    assert isinstance(item, model) and item.model_dump() == RECORD_BUILDERS[name]().model_dump()
    with pytest.raises(ValidationError):
        model.model_validate({"synthetic_unknown_field": "synthetic"})
    with pytest.raises((ValidationError, TypeError, AttributeError)):
        setattr(item, next(iter(model.model_fields)), "synthetic-other")
    assert item.model_json_schema() == model.model_json_schema()


def test_exact_36_public_records_and_builders() -> None:
    assert len(RECORD_NAMES) == 36 and list(RECORD_BUILDERS) == RECORD_NAMES


@pytest.mark.parametrize("name", RECORD_NAMES)
def test_every_literal_field_rejects_opposite(name: str) -> None:
    model = getattr(package, name)
    for field_name, field in model.model_fields.items():
        args = get_args(field.annotation)
        if get_origin(field.annotation) is Literal and args in {(False,), (True,)}:
            with pytest.raises(ValidationError):
                model.model_validate({field_name: not args[0]})


def test_real_as02_core_matrix() -> None:
    actor = _construct_record("SupportActorContext")
    subject = _construct_record("SupportSubjectReference")
    evidence = _construct_record("SupportEvidenceReference")
    assert (
        getattr(actor, "verified") is True
        and getattr(actor, "provider_identity_authority") is False
        and getattr(subject, "raw_personal_data_retained") is False
        and getattr(evidence, "raw_provider_payload_retained") is False
    )
    with pytest.raises(ValidationError):
        type(actor).model_validate({"verified": False})


def test_real_as03_safe_read_matrix() -> None:
    read = _construct_record("SupportReadModel")
    assert (
        getattr(read, "contains_secret_material") is False
        and getattr(read, "mutation_authority") is False
    )


@pytest.mark.parametrize("name", ["AdminRoleActionRequest", "AdminRoleActionOutcome"])
def test_real_as04_role_matrix(name: str) -> None:
    assert isinstance(RECORD_BUILDERS[name](), getattr(package, name))


@pytest.mark.parametrize(
    "name", ["AdminTariffCatalogActionRequest", "AdminTariffCatalogActionOutcome"]
)
def test_real_as05_tariff_matrix(name: str) -> None:
    assert isinstance(RECORD_BUILDERS[name](), getattr(package, name))


@pytest.mark.parametrize("name", ["AdminUserAccessActionRequest", "AdminUserAccessActionOutcome"])
def test_real_as06_access_matrix(name: str) -> None:
    assert isinstance(RECORD_BUILDERS[name](), getattr(package, name))


@pytest.mark.parametrize(
    "name",
    [
        "AdminAnchorStateSummary",
        "AdminAnchorActionRequest",
        "AdminAnchorActionOutcome",
        "AdminBeaconCurrentStateSummary",
        "AdminBeaconPatchFieldReference",
        "AdminBeaconSupportActionRequest",
        "AdminBeaconSupportActionOutcome",
        "SupportCaseActionRequest",
        "SupportCaseActionOutcome",
        "SupportCaseAuditTrailEntry",
        "AdminNotificationCurrentStateSummary",
        "AdminNotificationInterventionPolicyReference",
        "AdminNotificationSupportActionRequest",
        "AdminNotificationSupportActionOutcome",
    ],
)
def test_real_as07_to_as10_matrices(name: str) -> None:
    assert isinstance(RECORD_BUILDERS[name](), getattr(package, name))


def test_notification_regression_controls() -> None:
    request = package.AdminNotificationSupportActionRequest
    for field in (
        "direct_notification_send_authority",
        "blind_resend_authority",
        "provider_mapping_authority",
        "provider_execution_authority",
        "runtime_authority",
    ):
        assert request.model_fields[field].default is False
    outcome = package.AdminNotificationSupportActionOutcome.model_fields
    assert (
        outcome["provider_acceptance_inferred"].default is False
        and outcome["provider_send_claimed"].default is False
    )
    assert (
        package.AdminNotificationSupportActionRequest.model_fields[
            "reconciliation_first_for_ambiguous_effect"
        ].default
        is True
    )


def test_synthetic_privacy_policy() -> None:
    text = FIXTURE.read_text(encoding="utf-8").lower()
    assert not any(
        x in text
        for x in (
            "http://",
            "https://",
            "@",
            "bearer ",
            "-----begin",
            "password",
            "one-time-code",
            "raw-note",
        )
    )
