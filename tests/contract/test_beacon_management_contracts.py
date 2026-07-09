from __future__ import annotations

import ast
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from mayak.modules import beacon_management
from mayak.modules.beacon_management import contracts
from mayak.modules.beacon_management.contracts import (
    Beacon,
    BeaconActionCausation,
    BeaconActorContext,
    BeaconActorKind,
    BeaconAuthorizationDecision,
    BeaconAuthorizationOutcome,
    BeaconCurrentConfiguration,
    BeaconLifecycleState,
    BeaconNameOrigin,
    BeaconNamingMetadata,
    BeaconOwnershipDecision,
    BeaconParserEvidenceReference,
    BeaconParserEvidenceSafetyClass,
    BeaconParserOutcomeStatus,
    BeaconPreparedSourceUrl,
    BeaconProtectedAction,
    BeaconSnapshotAcceptanceDecision,
    BeaconSnapshotAcceptanceOutcome,
    BeaconSnapshotRejectionReason,
    BeaconSourceUrl,
    BeaconSourceUrlFingerprintPolicy,
    BeaconSourceUrlIdempotencyBasis,
    BeaconSourceUrlPreparationDecision,
    BeaconSourceUrlPreparationOutcome,
    BeaconSourceUrlSafetyClassification,
    BeaconSystemActorClass,
    ExtractedSearchConfigurationSnapshot,
)
from mayak.platform import boundaries

_SUBMITTED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc)


def _bm04_source_url(
    submitted_url: str,
    evidence_reference: str,
    *,
    source_channel: str = "user-submitted",
    submitted_at: datetime | None = _SUBMITTED_AT,
    submitted_by_label: str | None = "synthetic-user",
) -> BeaconSourceUrl:
    return BeaconSourceUrl(
        submitted_url=submitted_url,
        evidence_reference=evidence_reference,
        submitted_at=submitted_at,
        source_channel=source_channel,
        submitted_by_label=submitted_by_label,
    )


def _bm04_fingerprint_policy() -> BeaconSourceUrlFingerprintPolicy:
    return BeaconSourceUrlFingerprintPolicy(
        policy_reference="policy-contract-bm04-001",
        comparison_reference="comparison-contract-bm04-001",
        idempotency_reference="idempotency-contract-bm04-001",
        debug_reference="debug-contract-bm04-001",
    )


def _bm04_prepared_source_url(
    source_url: BeaconSourceUrl,
    *,
    classification: BeaconSourceUrlSafetyClassification,
    opaque_fingerprint_reference: str | None = None,
    fingerprint_policy: BeaconSourceUrlFingerprintPolicy | None = None,
    source_url_overwritten_by_snapshot: bool = False,
    source_url_overwritten_by_override: bool = False,
    source_url_rewritten: bool = False,
) -> BeaconPreparedSourceUrl:
    return BeaconPreparedSourceUrl(
        prepared_source_url_reference="prepared-contract-bm04-001",
        submitted_source_url=source_url,
        preserved_submitted_url=source_url.submitted_url,
        safety_classification=classification,
        source_url_overwritten_by_snapshot=source_url_overwritten_by_snapshot,
        source_url_overwritten_by_override=source_url_overwritten_by_override,
        source_url_rewritten=source_url_rewritten,
        opaque_fingerprint_reference=opaque_fingerprint_reference,
        fingerprint_policy=fingerprint_policy,
    )


def _bm04_idempotency_basis(
    source_url: BeaconSourceUrl,
    *,
    command_reference: str,
    account_id: str,
    beacon_id: str | None = None,
    requested_beacon_id: str | None = None,
    source_url_only_basis: bool = False,
) -> BeaconSourceUrlIdempotencyBasis:
    return BeaconSourceUrlIdempotencyBasis(
        source_url_reference=source_url.evidence_reference,
        command_reference=command_reference,
        account_id=account_id,
        beacon_id=beacon_id,
        requested_beacon_id=requested_beacon_id,
        source_url_only_basis=source_url_only_basis,
    )


def _bm04_snapshot(evidence_reference: str) -> ExtractedSearchConfigurationSnapshot:
    return ExtractedSearchConfigurationSnapshot(
        snapshot_id="snapshot-contract-bm04-001",
        parser_outcome_status=BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic",),
        unsupported_parameters=(),
        warning_codes=(),
        evidence_reference=evidence_reference,
        parser_evidence_reference=BeaconParserEvidenceReference(
            evidence_reference="parser-evidence-contract-bm04-001",
        ),
    )


def _bm05_parser_evidence_reference(
    evidence_reference: str,
    *,
    safety_class: BeaconParserEvidenceSafetyClass = BeaconParserEvidenceSafetyClass.OPAQUE,
    raw_provider_payload_authority: bool = False,
) -> BeaconParserEvidenceReference:
    return BeaconParserEvidenceReference(
        evidence_reference=evidence_reference,
        safety_class=safety_class,
        raw_provider_payload_authority=raw_provider_payload_authority,
    )


def _bm05_acceptance_decision(
    *,
    decision_id: str,
    parser_outcome_status: BeaconParserOutcomeStatus,
    parser_evidence_reference: BeaconParserEvidenceReference | None,
    acceptance_outcome: BeaconSnapshotAcceptanceOutcome,
    rejection_reason: BeaconSnapshotRejectionReason | None = None,
    parser_adapter_evidence_gate_reference: str | None = None,
    exact_acceptance_threshold_percent: int | None = None,
    unsupported_parameters: tuple[str, ...] = (),
    claims_full_parser_adapter_implementation_present: bool = False,
) -> BeaconSnapshotAcceptanceDecision:
    return BeaconSnapshotAcceptanceDecision(
        decision_id=decision_id,
        parser_outcome_status=parser_outcome_status,
        parser_evidence_reference=parser_evidence_reference,
        acceptance_outcome=acceptance_outcome,
        rejection_reason=rejection_reason,
        parser_adapter_evidence_gate_reference=parser_adapter_evidence_gate_reference,
        exact_acceptance_threshold_percent=exact_acceptance_threshold_percent,
        unsupported_parameters=unsupported_parameters,
        claims_full_parser_adapter_implementation_present=claims_full_parser_adapter_implementation_present,
    )


def _bm04_current_configuration(
    *,
    beacon_id: str,
    account_id: str,
    source_url: BeaconSourceUrl,
    display_name: str,
    lifecycle_state: BeaconLifecycleState,
    current_revision_id: str,
) -> BeaconCurrentConfiguration:
    return BeaconCurrentConfiguration(
        beacon_id=beacon_id,
        account_id=account_id,
        source_url=source_url,
        accepted_snapshot=_bm04_snapshot(f"{beacon_id}-snapshot-evidence"),
        overrides=(),
        current_revision_id=current_revision_id,
        display_name=display_name,
        lifecycle_state=lifecycle_state,
        retained_evidence_references=(f"{beacon_id}-retained-evidence",),
        previous_user_facing_revision_ids=(),
    )


def _bm04_beacon(
    *,
    beacon_id: str,
    account_id: str,
    source_url: BeaconSourceUrl,
    display_name: str,
    lifecycle_state: BeaconLifecycleState,
    current_revision_id: str,
    source_title: str = "synthetic search source",
    source_context_reference: str = "ctx-contract-bm04-001",
) -> Beacon:
    return Beacon(
        beacon_id=beacon_id,
        account_id=account_id,
        naming=BeaconNamingMetadata(
            display_name=display_name,
            name_origin=BeaconNameOrigin.USER_PROVIDED,
            source_title=source_title,
            source_context_reference=source_context_reference,
            default_name="synthetic-default-name",
        ),
        source_url=source_url,
        current_configuration=_bm04_current_configuration(
            beacon_id=beacon_id,
            account_id=account_id,
            source_url=source_url,
            display_name=display_name,
            lifecycle_state=lifecycle_state,
            current_revision_id=current_revision_id,
        ),
        lifecycle_state=lifecycle_state,
        restorable=True,
        counts_toward_active_limit=True,
        history_entries=(),
    )


def _bm04_beacon_with_current_source_url(
    *,
    beacon_id: str,
    account_id: str,
    source_url: BeaconSourceUrl,
    current_configuration_source_url: BeaconSourceUrl,
    display_name: str,
    lifecycle_state: BeaconLifecycleState,
    current_revision_id: str,
) -> Beacon:
    return Beacon(
        beacon_id=beacon_id,
        account_id=account_id,
        naming=BeaconNamingMetadata(
            display_name=display_name,
            name_origin=BeaconNameOrigin.USER_PROVIDED,
            source_title="synthetic search source",
            source_context_reference="ctx-contract-bm04-001",
            default_name="synthetic-default-name",
        ),
        source_url=source_url,
        current_configuration=_bm04_current_configuration(
            beacon_id=beacon_id,
            account_id=account_id,
            source_url=current_configuration_source_url,
            display_name=display_name,
            lifecycle_state=lifecycle_state,
            current_revision_id=current_revision_id,
        ),
        lifecycle_state=lifecycle_state,
        restorable=True,
        counts_toward_active_limit=True,
        history_entries=(),
    )


def _bm04_preparation_decision(
    source_url: BeaconSourceUrl,
    *,
    prepared_source_url: BeaconPreparedSourceUrl,
    outcome: BeaconSourceUrlPreparationOutcome,
    safe_reason_code: str,
    account_id: str = "acct-contract-bm04-001",
    beacon_id: str | None = None,
    requested_beacon_id: str | None = None,
    duplicate_source_url_blocking_policy: bool = False,
    idempotency_basis: BeaconSourceUrlIdempotencyBasis,
    source_url_is_unique_key: bool = False,
    shell_command_text: str | None = None,
    shell_interpolation_field: str | None = None,
    tracking_params_ignored: bool = False,
    tracking_policy_reference: str | None = None,
    opaque_fingerprint_reference: str | None = None,
) -> BeaconSourceUrlPreparationDecision:
    return BeaconSourceUrlPreparationDecision(
        decision_id="decision-contract-bm04-001",
        account_id=account_id,
        beacon_id=beacon_id,
        requested_beacon_id=requested_beacon_id,
        submitted_source_url=source_url,
        prepared_source_url=prepared_source_url,
        outcome=outcome,
        safe_reason_code=safe_reason_code,
        duplicate_source_url_blocking_policy=duplicate_source_url_blocking_policy,
        idempotency_basis=idempotency_basis,
        source_url_is_unique_key=source_url_is_unique_key,
        shell_command_text=shell_command_text,
        shell_interpolation_field=shell_interpolation_field,
        tracking_params_ignored=tracking_params_ignored,
        tracking_policy_reference=tracking_policy_reference,
        opaque_fingerprint_reference=opaque_fingerprint_reference,
    )


def _assert_no_forbidden_imports(module_path: Path, allowed_roots: set[str]) -> None:
    tree = ast.parse(module_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in allowed_roots, (
                    f"forbidden import root {alias.name!r} in {module_path}"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".", 1)[0]
            assert root in allowed_roots, f"forbidden import root {node.module!r} in {module_path}"


def test_beacon_management_package_import_and_module_id() -> None:
    module = import_module("mayak.modules.beacon_management")

    assert module.MODULE_ID == boundaries.BEACON_MANAGEMENT_MODULE_ID
    assert beacon_management.MODULE_ID == boundaries.BEACON_MANAGEMENT_MODULE_ID


def test_beacon_management_package_exports_contract_primitives() -> None:
    for name in contracts.__all__:
        assert hasattr(beacon_management, name)
        assert getattr(beacon_management, name) is getattr(contracts, name)


def test_beacon_management_package_exports_bm03_authorization_primitives() -> None:
    bm03_names = (
        "BeaconActionCausation",
        "BeaconActorContext",
        "BeaconActorKind",
        "BeaconAuthorizationDecision",
        "BeaconAuthorizationOutcome",
        "BeaconOwnershipDecision",
        "BeaconProtectedAction",
        "BeaconSystemActorClass",
    )

    for name in bm03_names:
        assert hasattr(beacon_management, name)
        assert getattr(beacon_management, name) is getattr(contracts, name)


def test_beacon_management_package_exports_bm04_source_url_primitives() -> None:
    bm04_names = (
        "BeaconPreparedSourceUrl",
        "BeaconSourceUrl",
        "BeaconSourceUrlFingerprintPolicy",
        "BeaconSourceUrlIdempotencyBasis",
        "BeaconSourceUrlPreparationDecision",
        "BeaconSourceUrlPreparationOutcome",
        "BeaconSourceUrlSafetyClassification",
    )

    for name in bm04_names:
        assert hasattr(beacon_management, name)
        assert getattr(beacon_management, name) is getattr(contracts, name)


def test_beacon_management_package_exports_bm05_parser_snapshot_primitives() -> None:
    bm05_names = (
        "BeaconParserEvidenceReference",
        "BeaconParserEvidenceSafetyClass",
        "BeaconSnapshotAcceptanceDecision",
        "BeaconSnapshotAcceptanceOutcome",
        "BeaconSnapshotRejectionReason",
    )

    for name in bm05_names:
        assert hasattr(beacon_management, name)
        assert getattr(beacon_management, name) is getattr(contracts, name)


def test_beacon_management_contract_module_exports_bm04_source_url_primitives() -> None:
    assert BeaconPreparedSourceUrl.__name__ == "BeaconPreparedSourceUrl"
    assert BeaconSourceUrl.__name__ == "BeaconSourceUrl"
    assert BeaconSourceUrlFingerprintPolicy.__name__ == "BeaconSourceUrlFingerprintPolicy"
    assert BeaconSourceUrlIdempotencyBasis.__name__ == "BeaconSourceUrlIdempotencyBasis"
    assert BeaconSourceUrlPreparationDecision.__name__ == "BeaconSourceUrlPreparationDecision"
    assert BeaconSourceUrlPreparationOutcome.__name__ == "BeaconSourceUrlPreparationOutcome"
    assert BeaconSourceUrlSafetyClassification.__name__ == "BeaconSourceUrlSafetyClassification"


def test_beacon_management_contract_module_exports_bm05_parser_snapshot_primitives() -> None:
    assert BeaconParserEvidenceReference.__name__ == "BeaconParserEvidenceReference"
    assert BeaconParserEvidenceSafetyClass.__name__ == "BeaconParserEvidenceSafetyClass"
    assert BeaconSnapshotAcceptanceDecision.__name__ == "BeaconSnapshotAcceptanceDecision"
    assert BeaconSnapshotAcceptanceOutcome.__name__ == "BeaconSnapshotAcceptanceOutcome"
    assert BeaconSnapshotRejectionReason.__name__ == "BeaconSnapshotRejectionReason"


def test_submitted_source_url_is_preserved_and_not_overwritten() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=preserved-source&city=synthetic",
        "evidence-contract-bm04-preserved-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )
    decision = _bm04_preparation_decision(
        source_url,
        prepared_source_url=prepared_source_url,
        outcome=BeaconSourceUrlPreparationOutcome.CREATED,
        safe_reason_code="SOURCE_URL_PRESERVED",
        beacon_id="beacon-contract-bm04-preserved-001",
        idempotency_basis=_bm04_idempotency_basis(
            source_url,
            command_reference="command-contract-bm04-preserved-001",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-preserved-001",
        ),
    )

    assert decision.submitted_source_url.submitted_url == source_url.submitted_url
    assert decision.prepared_source_url.preserved_submitted_url == source_url.submitted_url
    assert decision.prepared_source_url.source_url_overwritten_by_snapshot is False
    assert decision.prepared_source_url.source_url_overwritten_by_override is False


def test_beacon_accepts_matching_source_url_and_current_configuration_source_url() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-source-match&city=synthetic",
        "evidence-contract-bm04-beacon-match-001",
    )
    beacon = _bm04_beacon(
        beacon_id="beacon-contract-bm04-match-001",
        account_id="acct-contract-bm04-001",
        source_url=source_url,
        display_name="Synthetic matching beacon",
        lifecycle_state=BeaconLifecycleState.ACTIVE,
        current_revision_id="rev-contract-bm04-match-001",
    )

    assert beacon.source_url == beacon.current_configuration.source_url
    assert beacon.source_url.submitted_url == beacon.current_configuration.source_url.submitted_url
    assert (
        beacon.source_url.evidence_reference
        == beacon.current_configuration.source_url.evidence_reference
    )


def test_beacon_rejects_mismatched_source_url_submitted_url() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-source-match&city=synthetic",
        "evidence-contract-bm04-beacon-mismatch-url-001",
    )
    current_configuration_source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-current-config-different&city=synthetic",
        "evidence-contract-bm04-beacon-mismatch-url-001",
    )

    with pytest.raises(
        ValidationError,
        match="source URL must match current configuration source URL",
    ):
        _bm04_beacon_with_current_source_url(
            beacon_id="beacon-contract-bm04-mismatch-url-001",
            account_id="acct-contract-bm04-001",
            source_url=source_url,
            current_configuration_source_url=current_configuration_source_url,
            display_name="Synthetic mismatched beacon URL",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-contract-bm04-mismatch-url-001",
        )


def test_beacon_rejects_mismatched_source_url_evidence_reference() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-source-match&city=synthetic",
        "evidence-contract-bm04-beacon-mismatch-evidence-001",
    )
    current_configuration_source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-source-match&city=synthetic",
        "evidence-contract-bm04-beacon-mismatch-evidence-different-001",
    )

    with pytest.raises(
        ValidationError,
        match="evidence reference must match current configuration source URL",
    ):
        _bm04_beacon_with_current_source_url(
            beacon_id="beacon-contract-bm04-mismatch-evidence-001",
            account_id="acct-contract-bm04-001",
            source_url=source_url,
            current_configuration_source_url=current_configuration_source_url,
            display_name="Synthetic mismatched beacon evidence",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-contract-bm04-mismatch-evidence-001",
        )


@pytest.mark.parametrize(
    "source_url_kwargs, expected_message",
    (
        (
            {"source_channel": "parser-adapter"},
            "source channel must not contradict current configuration",
        ),
        (
            {"submitted_at": datetime(2026, 7, 9, 10, 1, tzinfo=timezone.utc)},
            "submitted_at must not contradict current configuration",
        ),
        (
            {"submitted_by_label": "different-label"},
            "submitted_by_label must not contradict current configuration",
        ),
    ),
)
def test_beacon_rejects_contradictory_source_url_metadata(
    source_url_kwargs: dict[str, Any],
    expected_message: str,
) -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-source-match&city=synthetic",
        "evidence-contract-bm04-beacon-metadata-001",
    )
    current_configuration_source_url = _bm04_source_url(
        "https://example.invalid/search?query=beacon-source-match&city=synthetic",
        "evidence-contract-bm04-beacon-metadata-001",
        **source_url_kwargs,
    )

    with pytest.raises(ValidationError, match=expected_message):
        _bm04_beacon_with_current_source_url(
            beacon_id="beacon-contract-bm04-metadata-001",
            account_id="acct-contract-bm04-001",
            source_url=source_url,
            current_configuration_source_url=current_configuration_source_url,
            display_name="Synthetic mismatched beacon metadata",
            lifecycle_state=BeaconLifecycleState.ACTIVE,
            current_revision_id="rev-contract-bm04-metadata-001",
        )


def test_same_account_duplicate_source_url_allowed_when_beacon_ids_differ() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=duplicate-source&city=synthetic",
        "evidence-contract-bm04-duplicate-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )
    first = _bm04_preparation_decision(
        source_url,
        prepared_source_url=prepared_source_url,
        outcome=BeaconSourceUrlPreparationOutcome.CREATED,
        safe_reason_code="DUPLICATE_SOURCE_URL_ALLOWED",
        beacon_id="beacon-contract-bm04-duplicate-a",
        idempotency_basis=_bm04_idempotency_basis(
            source_url,
            command_reference="command-contract-bm04-duplicate-a",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-duplicate-a",
        ),
    )
    second = _bm04_preparation_decision(
        source_url,
        prepared_source_url=prepared_source_url,
        outcome=BeaconSourceUrlPreparationOutcome.CREATED,
        safe_reason_code="DUPLICATE_SOURCE_URL_ALLOWED",
        beacon_id="beacon-contract-bm04-duplicate-b",
        idempotency_basis=_bm04_idempotency_basis(
            source_url,
            command_reference="command-contract-bm04-duplicate-b",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-duplicate-b",
        ),
    )

    assert first.submitted_source_url.submitted_url == second.submitted_source_url.submitted_url
    assert first.beacon_id != second.beacon_id
    assert first.account_id == second.account_id
    assert first.outcome is BeaconSourceUrlPreparationOutcome.CREATED
    assert second.outcome is BeaconSourceUrlPreparationOutcome.CREATED


def test_cross_account_duplicate_source_url_can_be_represented_as_allowed() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=cross-account-duplicate&city=synthetic",
        "evidence-contract-bm04-cross-duplicate-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )
    own = _bm04_preparation_decision(
        source_url,
        prepared_source_url=prepared_source_url,
        outcome=BeaconSourceUrlPreparationOutcome.CREATED,
        safe_reason_code="CROSS_ACCOUNT_DUPLICATE_ALLOWED",
        account_id="acct-contract-bm04-001",
        beacon_id="beacon-contract-bm04-cross-a",
        idempotency_basis=_bm04_idempotency_basis(
            source_url,
            command_reference="command-contract-bm04-cross-a",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-cross-a",
        ),
    )
    foreign = _bm04_preparation_decision(
        source_url,
        prepared_source_url=prepared_source_url,
        outcome=BeaconSourceUrlPreparationOutcome.CREATED,
        safe_reason_code="CROSS_ACCOUNT_DUPLICATE_ALLOWED",
        account_id="acct-contract-bm04-002",
        beacon_id="beacon-contract-bm04-cross-b",
        idempotency_basis=_bm04_idempotency_basis(
            source_url,
            command_reference="command-contract-bm04-cross-b",
            account_id="acct-contract-bm04-002",
            beacon_id="beacon-contract-bm04-cross-b",
        ),
    )

    assert own.submitted_source_url.submitted_url == foreign.submitted_source_url.submitted_url
    assert own.account_id != foreign.account_id


def test_source_url_alone_cannot_be_valid_idempotency_basis() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=idempotency-source-only&city=synthetic",
        "evidence-contract-bm04-idempotency-001",
    )

    with pytest.raises(ValidationError):
        BeaconSourceUrlIdempotencyBasis(
            source_url_reference=source_url.evidence_reference,
            source_url_only_basis=True,
        )


def _assert_blank_preparation_identity_fields_are_rejected(
    field_name: str,
) -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=blank-field&city=synthetic",
        "evidence-contract-bm04-blank-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )
    idempotency_basis = _bm04_idempotency_basis(
        source_url,
        command_reference="command-contract-bm04-blank-001",
        account_id="acct-contract-bm04-001",
        beacon_id="beacon-contract-bm04-blank-001",
    )
    with pytest.raises(ValidationError):
        if field_name == "account_id":
            BeaconSourceUrlPreparationDecision(
                decision_id="decision-contract-bm04-blank-001",
                account_id="",
                beacon_id="beacon-contract-bm04-blank-001",
                submitted_source_url=source_url,
                prepared_source_url=prepared_source_url,
                outcome=BeaconSourceUrlPreparationOutcome.CREATED,
                safe_reason_code="BLANK_FIELD_REJECTED",
                idempotency_basis=idempotency_basis,
            )
        elif field_name == "beacon_id":
            BeaconSourceUrlPreparationDecision(
                decision_id="decision-contract-bm04-blank-001",
                account_id="acct-contract-bm04-001",
                beacon_id="",
                submitted_source_url=source_url,
                prepared_source_url=prepared_source_url,
                outcome=BeaconSourceUrlPreparationOutcome.CREATED,
                safe_reason_code="BLANK_FIELD_REJECTED",
                idempotency_basis=idempotency_basis,
            )
        elif field_name == "requested_beacon_id":
            BeaconSourceUrlPreparationDecision(
                decision_id="decision-contract-bm04-blank-001",
                account_id="acct-contract-bm04-001",
                requested_beacon_id="",
                submitted_source_url=source_url,
                prepared_source_url=prepared_source_url,
                outcome=BeaconSourceUrlPreparationOutcome.CREATED,
                safe_reason_code="BLANK_FIELD_REJECTED",
                idempotency_basis=idempotency_basis,
            )
        else:
            raise AssertionError(f"unsupported field name: {field_name}")


@pytest.mark.parametrize("field_name", ("account_id", "beacon_id", "requested_beacon_id"))
def test_blank_preparation_identity_fields_are_rejected_parametrized(
    field_name: str,
) -> None:
    _assert_blank_preparation_identity_fields_are_rejected(field_name)


def test_blank_idempotency_command_reference_is_rejected() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=blank-command&city=synthetic",
        "evidence-contract-bm04-command-001",
    )

    with pytest.raises(ValidationError):
        BeaconSourceUrlIdempotencyBasis(
            source_url_reference=source_url.evidence_reference,
            command_reference="",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-command-001",
        )


@pytest.mark.parametrize(
    "outcome",
    (
        BeaconSourceUrlPreparationOutcome.CREATED,
        BeaconSourceUrlPreparationOutcome.REPLAYED,
    ),
)
def test_malformed_source_url_cannot_produce_created_or_replayed(
    outcome: BeaconSourceUrlPreparationOutcome,
) -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/%zz-malformed-source-url",
        "evidence-contract-bm04-malformed-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.MALFORMED,
    )

    with pytest.raises(ValidationError):
        BeaconSourceUrlPreparationDecision(
            decision_id=f"decision-contract-bm04-malformed-{outcome.value.lower()}",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-malformed-001",
            submitted_source_url=source_url,
            prepared_source_url=prepared_source_url,
            outcome=outcome,
            safe_reason_code="MALFORMED_URL_CANNOT_BE_CREATED_OR_REPLAYED",
            idempotency_basis=_bm04_idempotency_basis(
                source_url,
                command_reference="command-contract-bm04-malformed-001",
                account_id="acct-contract-bm04-001",
                beacon_id="beacon-contract-bm04-malformed-001",
            ),
        )


def test_duplicate_url_blocking_policy_cannot_be_default_valid_behavior() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=blocking-policy&city=synthetic",
        "evidence-contract-bm04-blocking-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )

    with pytest.raises(ValidationError):
        BeaconSourceUrlPreparationDecision(
            decision_id="decision-contract-bm04-blocking-001",
            account_id="acct-contract-bm04-001",
            requested_beacon_id="requested-beacon-contract-bm04-blocking-001",
            submitted_source_url=source_url,
            prepared_source_url=prepared_source_url,
            outcome=BeaconSourceUrlPreparationOutcome.REJECTED,
            safe_reason_code="DUPLICATE_BLOCKING_POLICY_NOT_ALLOWED",
            duplicate_source_url_blocking_policy=True,
            idempotency_basis=_bm04_idempotency_basis(
                source_url,
                command_reference="command-contract-bm04-blocking-001",
                account_id="acct-contract-bm04-001",
                requested_beacon_id="requested-beacon-contract-bm04-blocking-001",
            ),
        )


def test_external_source_url_cannot_appear_in_shell_command_text() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=shell-boundary&city=synthetic",
        "evidence-contract-bm04-shell-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.BLOCKED,
    )
    with pytest.raises(ValidationError):
        BeaconSourceUrlPreparationDecision(
            decision_id="decision-contract-bm04-shell-001",
            account_id="acct-contract-bm04-001",
            requested_beacon_id="requested-beacon-contract-bm04-shell-001",
            submitted_source_url=source_url,
            prepared_source_url=prepared_source_url,
            outcome=BeaconSourceUrlPreparationOutcome.BLOCKED,
            safe_reason_code="EXTERNAL_URL_MUST_NOT_BE_INTERPOLATED",
            idempotency_basis=_bm04_idempotency_basis(
                source_url,
                command_reference="command-contract-bm04-shell-001",
                account_id="acct-contract-bm04-001",
                requested_beacon_id="requested-beacon-contract-bm04-shell-001",
            ),
            shell_command_text=f"curl --fail {source_url.submitted_url}",
        )


@pytest.mark.parametrize(
    "outcome",
    (
        BeaconSourceUrlPreparationOutcome.CREATED,
        BeaconSourceUrlPreparationOutcome.REPLAYED,
    ),
)
def test_shell_interpolation_field_cannot_represent_external_source_url_interpolation(
    outcome: BeaconSourceUrlPreparationOutcome,
) -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=shell-field&city=synthetic",
        "evidence-contract-bm04-shell-field-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )

    with pytest.raises(ValidationError, match="shell interpolation field"):
        BeaconSourceUrlPreparationDecision(
            decision_id=f"decision-contract-bm04-shell-field-{outcome.value.lower()}",
            account_id="acct-contract-bm04-001",
            requested_beacon_id="requested-beacon-contract-bm04-shell-field-001",
            submitted_source_url=source_url,
            prepared_source_url=prepared_source_url,
            outcome=outcome,
            safe_reason_code="SHELL_INTERPOLATION_FIELD_NOT_ALLOWED",
            idempotency_basis=_bm04_idempotency_basis(
                source_url,
                command_reference="command-contract-bm04-shell-field-001",
                account_id="acct-contract-bm04-001",
                requested_beacon_id="requested-beacon-contract-bm04-shell-field-001",
            ),
            shell_interpolation_field="submitted_source_url",
        )


def test_canonical_fingerprint_cannot_be_marked_as_configuration_authority() -> None:
    with pytest.raises(ValidationError):
        BeaconSourceUrlFingerprintPolicy(
            policy_reference="policy-contract-bm04-authority-001",
            comparison_reference="comparison-contract-bm04-authority-001",
            idempotency_reference="idempotency-contract-bm04-authority-001",
            debug_reference="debug-contract-bm04-authority-001",
            authoritative_configuration_source=True,
        )


def test_tracking_params_cannot_be_ignored_without_captured_policy_reference() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=tracking-policy&city=synthetic&utm_source=test",
        "evidence-contract-bm04-tracking-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )

    with pytest.raises(ValidationError):
        BeaconSourceUrlPreparationDecision(
            decision_id="decision-contract-bm04-tracking-001",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-tracking-001",
            submitted_source_url=source_url,
            prepared_source_url=prepared_source_url,
            outcome=BeaconSourceUrlPreparationOutcome.CREATED,
            safe_reason_code="TRACKING_POLICY_REFERENCE_REQUIRED",
            idempotency_basis=_bm04_idempotency_basis(
                source_url,
                command_reference="command-contract-bm04-tracking-001",
                account_id="acct-contract-bm04-001",
                beacon_id="beacon-contract-bm04-tracking-001",
            ),
            tracking_params_ignored=True,
        )


def test_source_url_unique_key_cannot_be_represented_as_valid_behavior() -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=unique-key&city=synthetic",
        "evidence-contract-bm04-unique-key-001",
    )
    prepared_source_url = _bm04_prepared_source_url(
        source_url,
        classification=BeaconSourceUrlSafetyClassification.PRESERVED,
    )

    with pytest.raises(ValidationError):
        BeaconSourceUrlPreparationDecision(
            decision_id="decision-contract-bm04-unique-key-001",
            account_id="acct-contract-bm04-001",
            beacon_id="beacon-contract-bm04-unique-key-001",
            submitted_source_url=source_url,
            prepared_source_url=prepared_source_url,
            outcome=BeaconSourceUrlPreparationOutcome.CREATED,
            safe_reason_code="SOURCE_URL_UNIQUE_KEY_NOT_ALLOWED",
            idempotency_basis=_bm04_idempotency_basis(
                source_url,
                command_reference="command-contract-bm04-unique-key-001",
                account_id="acct-contract-bm04-001",
                beacon_id="beacon-contract-bm04-unique-key-001",
            ),
            source_url_is_unique_key=True,
        )


@pytest.mark.parametrize(
    "overwritten_field",
    (
        "source_url_overwritten_by_snapshot",
        "source_url_overwritten_by_override",
        "source_url_rewritten",
    ),
)
def test_prepared_source_url_overwrite_flags_are_rejected(overwritten_field: str) -> None:
    source_url = _bm04_source_url(
        "https://example.invalid/search?query=overwrite-boundary&city=synthetic",
        "evidence-contract-bm04-overwrite-001",
    )
    with pytest.raises(ValidationError):
        if overwritten_field == "source_url_overwritten_by_snapshot":
            BeaconPreparedSourceUrl(
                prepared_source_url_reference="prepared-contract-bm04-overwrite-001",
                submitted_source_url=source_url,
                preserved_submitted_url=source_url.submitted_url,
                safety_classification=BeaconSourceUrlSafetyClassification.PRESERVED,
                source_url_overwritten_by_snapshot=True,
            )
        elif overwritten_field == "source_url_overwritten_by_override":
            BeaconPreparedSourceUrl(
                prepared_source_url_reference="prepared-contract-bm04-overwrite-001",
                submitted_source_url=source_url,
                preserved_submitted_url=source_url.submitted_url,
                safety_classification=BeaconSourceUrlSafetyClassification.PRESERVED,
                source_url_overwritten_by_override=True,
            )
        elif overwritten_field == "source_url_rewritten":
            BeaconPreparedSourceUrl(
                prepared_source_url_reference="prepared-contract-bm04-overwrite-001",
                submitted_source_url=source_url,
                preserved_submitted_url=source_url.submitted_url,
                safety_classification=BeaconSourceUrlSafetyClassification.PRESERVED,
                source_url_rewritten=True,
            )
        else:
            raise AssertionError(f"unsupported field name: {overwritten_field}")


def test_verified_owner_update_decision_is_allowed_for_matching_account() -> None:
    decision = BeaconOwnershipDecision(
        decision_id="decision-contract-bm03-001",
        protected_action=BeaconProtectedAction.UPDATE_BEACON,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-001",
            actor_kind=BeaconActorKind.ACCOUNT_OWNER,
            is_verified=True,
            account_id="acct-contract-bm03-001",
            actor_reference_id="actor-ref-contract-bm03-001",
        ),
        beacon_id="beacon-contract-bm03-001",
        beacon_account_id="acct-contract-bm03-001",
        outcome=BeaconAuthorizationOutcome.ALLOWED,
        safe_reason_code="OWNER_UPDATE_ALLOWED",
        reason="verified owner may update own Beacon",
    )

    assert decision.outcome is BeaconAuthorizationOutcome.ALLOWED
    assert decision.actor_context.account_id == decision.beacon_account_id
    assert decision.actor_context.is_verified is True


def test_unverified_actor_cannot_receive_allowed_mutation_decision() -> None:
    with pytest.raises(ValidationError):
        BeaconOwnershipDecision(
            decision_id="decision-contract-bm03-002",
            protected_action=BeaconProtectedAction.UPDATE_BEACON,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-002",
                actor_kind=BeaconActorKind.ACCOUNT_OWNER,
                is_verified=False,
                account_id="acct-contract-bm03-002",
                actor_reference_id="actor-ref-contract-bm03-002",
            ),
            beacon_id="beacon-contract-bm03-002",
            beacon_account_id="acct-contract-bm03-002",
            outcome=BeaconAuthorizationOutcome.ALLOWED,
            safe_reason_code="OWNER_UPDATE_ALLOWED",
            reason="unverified owner must not be allowed to mutate",
        )


def test_actor_account_mismatch_cannot_receive_allowed_owner_mutation_decision() -> None:
    with pytest.raises(ValidationError):
        BeaconOwnershipDecision(
            decision_id="decision-contract-bm03-003",
            protected_action=BeaconProtectedAction.UPDATE_BEACON,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-003",
                actor_kind=BeaconActorKind.ACCOUNT_OWNER,
                is_verified=True,
                account_id="acct-contract-bm03-003-actor",
                actor_reference_id="actor-ref-contract-bm03-003",
            ),
            beacon_id="beacon-contract-bm03-003",
            beacon_account_id="acct-contract-bm03-003-target",
            outcome=BeaconAuthorizationOutcome.ALLOWED,
            safe_reason_code="OWNER_UPDATE_ALLOWED",
            reason="mismatched account must not be allowed",
        )


def test_foreign_account_denial_is_non_existence_sensitive() -> None:
    decision = BeaconOwnershipDecision(
        decision_id="decision-contract-bm03-004",
        protected_action=BeaconProtectedAction.READ_BEACON,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-004",
            actor_kind=BeaconActorKind.ACCOUNT_OWNER,
            is_verified=True,
            account_id="acct-contract-bm03-004-actor",
            actor_reference_id="actor-ref-contract-bm03-004",
        ),
        beacon_id="beacon-contract-bm03-004",
        beacon_account_id="acct-contract-bm03-004-target",
        outcome=BeaconAuthorizationOutcome.BLOCKED,
        safe_reason_code="FOREIGN_READ_BLOCKED",
        reason="foreign account must not receive existence-sensitive detail",
    )

    assert decision.outcome is BeaconAuthorizationOutcome.BLOCKED
    assert decision.existence_sensitive_detail is None
    assert decision.foreign_account_existence_sensitive_detail is False


def test_admin_support_allowed_action_requires_server_side_scope_reference() -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-005",
            protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-005",
                actor_kind=BeaconActorKind.ADMIN_SUPPORT,
                is_verified=True,
                account_id="acct-contract-bm03-support",
                actor_reference_id="actor-ref-contract-bm03-005",
            ),
            beacon_id="beacon-contract-bm03-005",
            beacon_account_id="acct-contract-bm03-005-target",
            outcome=BeaconAuthorizationOutcome.ALLOWED,
            safe_reason_code="ADMIN_SUPPORT_READ_ALLOWED",
            reason="admin/support read must require server-side scope",
            server_audit_reference="audit-contract-bm03-005",
        )


def test_admin_support_allowed_action_requires_audit_reference() -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-006",
            protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-006",
                actor_kind=BeaconActorKind.ADMIN_SUPPORT,
                is_verified=True,
                account_id="acct-contract-bm03-support",
                actor_reference_id="actor-ref-contract-bm03-006",
            ),
            beacon_id="beacon-contract-bm03-006",
            beacon_account_id="acct-contract-bm03-006-target",
            outcome=BeaconAuthorizationOutcome.ALLOWED,
            safe_reason_code="ADMIN_SUPPORT_READ_ALLOWED",
            reason="admin/support read must require audit",
            server_role_scope_reference="support-scope-contract-bm03-006",
        )


@pytest.mark.parametrize(
    "protected_action",
    (
        BeaconProtectedAction.ADMIN_SUPPORT_READ,
        BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
    ),
)
def test_unverified_admin_support_allowed_action_is_rejected(
    protected_action: BeaconProtectedAction,
) -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id=f"decision-contract-bm03-unverified-{protected_action.value.lower()}",
            protected_action=protected_action,
            actor_context=BeaconActorContext(
                actor_context_id=f"actor-contract-bm03-unverified-{protected_action.value.lower()}",
                actor_kind=BeaconActorKind.ADMIN_SUPPORT,
                is_verified=False,
                account_id="acct-contract-bm03-support",
                actor_reference_id="actor-ref-contract-bm03-unverified",
            ),
            beacon_id="beacon-contract-bm03-unverified",
            beacon_account_id="acct-contract-bm03-target",
            outcome=BeaconAuthorizationOutcome.ALLOWED,
            safe_reason_code="ADMIN_SUPPORT_ALLOWED_REQUIRES_VERIFIED_ACTOR",
            reason="unverified admin/support actor must not be allowed",
            server_role_scope_reference="support-scope-contract-bm03-unverified",
            server_audit_reference="audit-contract-bm03-unverified",
        )


def test_verified_admin_support_allowed_action_is_allowed_with_scope_and_audit() -> None:
    decision = BeaconAuthorizationDecision(
        decision_id="decision-contract-bm03-allowed",
        protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-allowed",
            actor_kind=BeaconActorKind.ADMIN_SUPPORT,
            is_verified=True,
            account_id="acct-contract-bm03-support",
            actor_reference_id="actor-ref-contract-bm03-allowed",
        ),
        beacon_id="beacon-contract-bm03-allowed",
        beacon_account_id="acct-contract-bm03-target",
        outcome=BeaconAuthorizationOutcome.ALLOWED,
        safe_reason_code="ADMIN_SUPPORT_READ_ALLOWED",
        reason="verified admin/support actor may be allowed",
        server_role_scope_reference="support-scope-contract-bm03-allowed",
        server_audit_reference="audit-contract-bm03-allowed",
    )

    assert decision.outcome is BeaconAuthorizationOutcome.ALLOWED
    assert decision.actor_context.is_verified is True
    assert decision.server_role_scope_reference == "support-scope-contract-bm03-allowed"
    assert decision.server_audit_reference == "audit-contract-bm03-allowed"


def test_requires_verified_actor_outcome_rejects_verified_actor() -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-requires-verified",
            protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-requires-verified",
                actor_kind=BeaconActorKind.ADMIN_SUPPORT,
                is_verified=True,
                account_id="acct-contract-bm03-support",
                actor_reference_id="actor-ref-contract-bm03-requires-verified",
            ),
            beacon_id="beacon-contract-bm03-requires-verified",
            beacon_account_id="acct-contract-bm03-target",
            outcome=BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR,
            safe_reason_code="ADMIN_SUPPORT_READ_REQUIRES_VERIFIED_ACTOR",
            reason="verified actor cannot be represented as requires verified actor",
        )


def test_requires_verified_actor_outcome_accepts_unverified_actor() -> None:
    decision = BeaconAuthorizationDecision(
        decision_id="decision-contract-bm03-requires-verified-ok",
        protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-requires-verified-ok",
            actor_kind=BeaconActorKind.ADMIN_SUPPORT,
            is_verified=False,
            account_id="acct-contract-bm03-support",
            actor_reference_id="actor-ref-contract-bm03-requires-verified-ok",
        ),
        beacon_id="beacon-contract-bm03-requires-verified-ok",
        beacon_account_id="acct-contract-bm03-target",
        outcome=BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR,
        safe_reason_code="ADMIN_SUPPORT_READ_REQUIRES_VERIFIED_ACTOR",
        reason="unverified actor can be represented as requires verified actor",
    )

    assert decision.outcome is BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR
    assert decision.actor_context.is_verified is False


def test_requires_scope_outcome_rejects_present_scope_reference() -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-requires-scope",
            protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-requires-scope",
                actor_kind=BeaconActorKind.ADMIN_SUPPORT,
                is_verified=True,
                account_id="acct-contract-bm03-support",
                actor_reference_id="actor-ref-contract-bm03-requires-scope",
            ),
            beacon_id="beacon-contract-bm03-requires-scope",
            beacon_account_id="acct-contract-bm03-target",
            outcome=BeaconAuthorizationOutcome.REQUIRES_SCOPE,
            safe_reason_code="ADMIN_SUPPORT_READ_REQUIRES_SCOPE",
            reason="scope reference cannot be present on requires-scope outcome",
            server_role_scope_reference="support-scope-contract-bm03-requires-scope",
            server_audit_reference="audit-contract-bm03-requires-scope",
        )


def test_requires_scope_outcome_accepts_missing_scope_reference() -> None:
    decision = BeaconAuthorizationDecision(
        decision_id="decision-contract-bm03-requires-scope-ok",
        protected_action=BeaconProtectedAction.ADMIN_SUPPORT_READ,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-requires-scope-ok",
            actor_kind=BeaconActorKind.ADMIN_SUPPORT,
            is_verified=True,
            account_id="acct-contract-bm03-support",
            actor_reference_id="actor-ref-contract-bm03-requires-scope-ok",
        ),
        beacon_id="beacon-contract-bm03-requires-scope-ok",
        beacon_account_id="acct-contract-bm03-target",
        outcome=BeaconAuthorizationOutcome.REQUIRES_SCOPE,
        safe_reason_code="ADMIN_SUPPORT_READ_REQUIRES_SCOPE",
        reason="missing scope reference is valid for requires-scope outcome",
        server_audit_reference="audit-contract-bm03-requires-scope-ok",
    )

    assert decision.outcome is BeaconAuthorizationOutcome.REQUIRES_SCOPE
    assert decision.server_role_scope_reference is None
    assert decision.server_audit_reference == "audit-contract-bm03-requires-scope-ok"


def test_requires_audit_outcome_rejects_present_audit_reference() -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-requires-audit",
            protected_action=BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-requires-audit",
                actor_kind=BeaconActorKind.ADMIN_SUPPORT,
                is_verified=True,
                account_id="acct-contract-bm03-support",
                actor_reference_id="actor-ref-contract-bm03-requires-audit",
            ),
            beacon_id="beacon-contract-bm03-requires-audit",
            beacon_account_id="acct-contract-bm03-target",
            outcome=BeaconAuthorizationOutcome.REQUIRES_AUDIT,
            safe_reason_code="ADMIN_SUPPORT_MUTATE_REQUIRES_AUDIT",
            reason="audit reference cannot be present on requires-audit outcome",
            server_role_scope_reference="support-scope-contract-bm03-requires-audit",
            server_audit_reference="audit-contract-bm03-requires-audit",
        )


def test_requires_audit_outcome_accepts_missing_audit_reference() -> None:
    decision = BeaconAuthorizationDecision(
        decision_id="decision-contract-bm03-requires-audit-ok",
        protected_action=BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-requires-audit-ok",
            actor_kind=BeaconActorKind.ADMIN_SUPPORT,
            is_verified=True,
            account_id="acct-contract-bm03-support",
            actor_reference_id="actor-ref-contract-bm03-requires-audit-ok",
        ),
        beacon_id="beacon-contract-bm03-requires-audit-ok",
        beacon_account_id="acct-contract-bm03-target",
        outcome=BeaconAuthorizationOutcome.REQUIRES_AUDIT,
        safe_reason_code="ADMIN_SUPPORT_MUTATE_REQUIRES_AUDIT",
        reason="missing audit reference is valid for requires-audit outcome",
        server_role_scope_reference="support-scope-contract-bm03-requires-audit-ok",
    )

    assert decision.outcome is BeaconAuthorizationOutcome.REQUIRES_AUDIT
    assert decision.server_role_scope_reference == "support-scope-contract-bm03-requires-audit-ok"
    assert decision.server_audit_reference is None


def test_client_channel_flags_are_not_authorization_proof() -> None:
    with pytest.raises(ValidationError):
        BeaconActorContext(
            actor_context_id="actor-contract-bm03-007",
            actor_kind=BeaconActorKind.ANONYMOUS,
            is_verified=False,
            client_channel_flag="TELEGRAM",
            client_channel_flag_is_authorization_proof=True,
        )


def test_system_lifecycle_action_requires_service_actor_class_causation_and_policy_source() -> None:
    causation = BeaconActionCausation(
        service_actor_class=BeaconSystemActorClass.MAINTENANCE_SERVICE,
        causation_reference="causation-contract-bm03-001",
        policy_source_reference="policy-source-contract-bm03-001",
    )

    decision = BeaconAuthorizationDecision(
        decision_id="decision-contract-bm03-007",
        protected_action=BeaconProtectedAction.SYSTEM_FREEZE_AFTER_EXPIRY,
        actor_context=BeaconActorContext(
            actor_context_id="actor-contract-bm03-007",
            actor_kind=BeaconActorKind.SYSTEM,
            is_verified=False,
            actor_reference_id="actor-ref-contract-bm03-007",
        ),
        beacon_id="beacon-contract-bm03-007",
        beacon_account_id="acct-contract-bm03-007-target",
        outcome=BeaconAuthorizationOutcome.ALLOWED,
        safe_reason_code="SYSTEM_FREEZE_ALLOWED",
        reason="system freeze requires service actor causation and policy source",
        action_causation=causation,
    )

    assert decision.action_causation == causation
    assert (
        decision.action_causation.service_actor_class is BeaconSystemActorClass.MAINTENANCE_SERVICE
    )


def test_system_lifecycle_allowed_action_requires_causation() -> None:
    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-008",
            protected_action=BeaconProtectedAction.SYSTEM_FREEZE_AFTER_EXPIRY,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-008",
                actor_kind=BeaconActorKind.SYSTEM,
                is_verified=False,
                actor_reference_id="actor-ref-contract-bm03-008",
            ),
            beacon_id="beacon-contract-bm03-008",
            beacon_account_id="acct-contract-bm03-008-target",
            outcome=BeaconAuthorizationOutcome.ALLOWED,
            safe_reason_code="SYSTEM_FREEZE_ALLOWED",
            reason="system freeze without causation must be rejected",
        )


def test_system_lifecycle_blocked_outcome_rejects_action_causation() -> None:
    causation = BeaconActionCausation(
        service_actor_class=BeaconSystemActorClass.MAINTENANCE_SERVICE,
        causation_reference="causation-contract-bm03-003",
        policy_source_reference="policy-source-contract-bm03-003",
    )

    with pytest.raises(ValidationError):
        BeaconAuthorizationDecision(
            decision_id="decision-contract-bm03-009",
            protected_action=BeaconProtectedAction.SYSTEM_FREEZE_AFTER_EXPIRY,
            actor_context=BeaconActorContext(
                actor_context_id="actor-contract-bm03-009",
                actor_kind=BeaconActorKind.SYSTEM,
                is_verified=False,
                actor_reference_id="actor-ref-contract-bm03-009",
            ),
            beacon_id="beacon-contract-bm03-009",
            beacon_account_id="acct-contract-bm03-009-target",
            outcome=BeaconAuthorizationOutcome.BLOCKED,
            safe_reason_code="SYSTEM_FREEZE_BLOCKED",
            reason="system freeze blocked outcome must not carry causation",
            action_causation=causation,
        )


def test_blank_policy_source_is_rejected_for_system_lifecycle_causation() -> None:
    with pytest.raises(ValidationError):
        BeaconActionCausation(
            service_actor_class=BeaconSystemActorClass.MAINTENANCE_SERVICE,
            causation_reference="causation-contract-bm03-002",
            policy_source_reference="",
        )


def test_beacon_management_source_url_duplicates_are_allowed_when_beacon_ids_differ() -> None:
    source_url = contracts.BeaconSourceUrl(
        submitted_url="https://example.invalid/search?query=duplicate-source",
        evidence_reference="evidence-bm-contract-001",
        submitted_at=_SUBMITTED_AT,
        source_channel="user-submitted",
        submitted_by_label="synthetic-user",
    )
    snapshot = contracts.ExtractedSearchConfigurationSnapshot(
        snapshot_id="snap-contract-001",
        parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic-city",),
        evidence_reference="evidence-contract-001",
        parser_evidence_reference=contracts.BeaconParserEvidenceReference(
            evidence_reference="parser-evidence-contract-001"
        ),
    )
    configuration_a = contracts.BeaconCurrentConfiguration(
        beacon_id="beacon-contract-a",
        account_id="acct-contract-001",
        source_url=source_url,
        accepted_snapshot=snapshot,
        overrides=(),
        current_revision_id="rev-contract-a",
        display_name="Synthetic beacon A",
        lifecycle_state=contracts.BeaconLifecycleState.READY,
    )
    configuration_b = configuration_a.model_copy(
        update={
            "beacon_id": "beacon-contract-b",
            "current_revision_id": "rev-contract-b",
            "display_name": "Synthetic beacon B",
        }
    )

    beacon_a = contracts.Beacon(
        beacon_id="beacon-contract-a",
        account_id="acct-contract-001",
        naming=contracts.BeaconNamingMetadata(
            display_name="Synthetic beacon A",
            name_origin=contracts.BeaconNameOrigin.USER_PROVIDED,
            source_title="synthetic source",
            source_context_reference="ctx-contract-001",
        ),
        source_url=source_url,
        current_configuration=configuration_a,
        lifecycle_state=contracts.BeaconLifecycleState.READY,
    )
    beacon_b = contracts.Beacon(
        beacon_id="beacon-contract-b",
        account_id="acct-contract-001",
        naming=contracts.BeaconNamingMetadata(
            display_name="Synthetic beacon B",
            name_origin=contracts.BeaconNameOrigin.USER_PROVIDED,
            source_title="synthetic source",
            source_context_reference="ctx-contract-002",
        ),
        source_url=source_url,
        current_configuration=configuration_b,
        lifecycle_state=contracts.BeaconLifecycleState.READY,
    )

    assert beacon_a.source_url.submitted_url == beacon_b.source_url.submitted_url
    assert beacon_a.beacon_id != beacon_b.beacon_id


def test_beacon_management_source_url_is_preserved_separately_from_snapshot_and_overrides() -> None:
    source_url = contracts.BeaconSourceUrl(
        submitted_url="https://example.invalid/search?query=preserved-source",
        evidence_reference="evidence-bm-contract-002",
        submitted_at=_SUBMITTED_AT,
        source_channel="user-submitted",
        submitted_by_label="synthetic-user",
    )
    snapshot = contracts.ExtractedSearchConfigurationSnapshot(
        snapshot_id="snap-contract-002",
        parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic-city", "category=synthetic-category"),
        evidence_reference="evidence-contract-002",
        parser_evidence_reference=contracts.BeaconParserEvidenceReference(
            evidence_reference="parser-evidence-contract-002"
        ),
    )
    override = contracts.BeaconFilterOverride(
        field_name="amenities",
        field_supported=True,
        status=contracts.BeaconOverrideStatus.APPLIED,
        requested_values=("wifi", "parking"),
        applied_values=("wifi", "parking"),
        override_reference="override-contract-001",
        reason="synthetic supported override",
    )
    current = contracts.BeaconCurrentConfiguration(
        beacon_id="beacon-contract-003",
        account_id="acct-contract-001",
        source_url=source_url,
        accepted_snapshot=snapshot,
        overrides=(override,),
        current_revision_id="rev-contract-003",
        display_name="Synthetic preserved source",
        lifecycle_state=contracts.BeaconLifecycleState.ACTIVE,
    )

    assert (
        current.source_url.submitted_url == "https://example.invalid/search?query=preserved-source"
    )
    assert current.accepted_snapshot.accepted_as_clean is True
    assert current.overrides[0].field_name == "amenities"
    assert "submitted_url" not in type(current.accepted_snapshot).model_fields


def test_free_country_wide_activation_cannot_be_allowed() -> None:
    with pytest.raises(ValidationError):
        contracts.BeaconActivationDecision(
            beacon_id="beacon-contract-free-001",
            account_id="acct-contract-001",
            access_tier=contracts.BeaconAccessTier.FREE,
            status=contracts.BeaconDecisionStatus.ALLOWED,
            requested_interval_minutes=180,
            interval_floor_minutes=180,
            interval_step_minutes=180,
            active_beacon_limit=1,
            requested_country_wide=True,
            country_wide_allowed=False,
            city_required=True,
            requested_city="synthetic-city",
            selected_beacon_id=None,
            expiry_outcomes=(),
            reason_code="FREE_COUNTRY_WIDE_NOT_ALLOWED",
            reason="synthetic free-tier country-wide activation must be blocked",
        )


def test_basic_country_wide_activation_can_be_allowed() -> None:
    decision = contracts.BeaconActivationDecision(
        beacon_id="beacon-contract-basic-001",
        account_id="acct-contract-001",
        access_tier=contracts.BeaconAccessTier.BASIC,
        status=contracts.BeaconDecisionStatus.ALLOWED,
        requested_interval_minutes=5,
        interval_floor_minutes=5,
        interval_step_minutes=5,
        active_beacon_limit=5,
        requested_country_wide=True,
        country_wide_allowed=True,
        city_required=False,
        requested_city=None,
        selected_beacon_id=None,
        expiry_outcomes=(),
        reason_code="BASIC_COUNTRY_WIDE_ALLOWED",
        reason="synthetic basic-tier country-wide activation is allowed",
    )

    assert decision.status is contracts.BeaconDecisionStatus.ALLOWED
    assert decision.country_wide_allowed is True


def test_free_and_basic_interval_floor_and_step_are_exact() -> None:
    free_decision = contracts.BeaconActivationDecision(
        beacon_id="beacon-contract-free-002",
        account_id="acct-contract-001",
        access_tier=contracts.BeaconAccessTier.FREE,
        status=contracts.BeaconDecisionStatus.BLOCKED,
        requested_interval_minutes=180,
        interval_floor_minutes=180,
        interval_step_minutes=180,
        active_beacon_limit=1,
        requested_country_wide=False,
        country_wide_allowed=False,
        city_required=True,
        requested_city=None,
        selected_beacon_id=None,
        expiry_outcomes=(contracts.BeaconExpiryOutcome.USER_CHOICE_REQUIRED,),
        reason_code="FREE_INTERVAL_POLICY",
        reason="synthetic free-tier interval policy",
    )
    basic_decision = contracts.BeaconActivationDecision(
        beacon_id="beacon-contract-basic-002",
        account_id="acct-contract-001",
        access_tier=contracts.BeaconAccessTier.BASIC,
        status=contracts.BeaconDecisionStatus.ALLOWED,
        requested_interval_minutes=5,
        interval_floor_minutes=5,
        interval_step_minutes=5,
        active_beacon_limit=5,
        requested_country_wide=False,
        country_wide_allowed=True,
        city_required=False,
        requested_city=None,
        selected_beacon_id=None,
        expiry_outcomes=(),
        reason_code="BASIC_INTERVAL_POLICY",
        reason="synthetic basic-tier interval policy",
    )

    assert free_decision.interval_floor_minutes == 180
    assert free_decision.interval_step_minutes == 180
    assert basic_decision.interval_floor_minutes == 5
    assert basic_decision.interval_step_minutes == 5


def test_unsupported_filter_override_cannot_be_represented_as_applied() -> None:
    with pytest.raises(ValidationError):
        contracts.BeaconFilterOverride(
            field_name="unsupported_field",
            field_supported=False,
            status=contracts.BeaconOverrideStatus.APPLIED,
            requested_values=("unexpected",),
            applied_values=("unexpected",),
            override_reference="override-contract-002",
            reason="synthetic unsupported override must stay unapplied",
        )


def test_clean_parser_outcome_can_be_accepted_with_opaque_evidence_reference() -> None:
    evidence_reference = _bm05_parser_evidence_reference("parser-evidence-contract-bm05-clean-001")
    snapshot = contracts.ExtractedSearchConfigurationSnapshot(
        snapshot_id="snap-contract-bm05-clean-001",
        parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic-city",),
        evidence_reference="evidence-contract-bm05-clean-001",
        parser_evidence_reference=evidence_reference,
    )
    decision = _bm05_acceptance_decision(
        decision_id="decision-contract-bm05-clean-001",
        parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
        parser_evidence_reference=evidence_reference,
        acceptance_outcome=contracts.BeaconSnapshotAcceptanceOutcome.ACCEPTED,
        parser_adapter_evidence_gate_reference="parser-adapter-evidence-gate-contract-bm05-001",
    )

    assert snapshot.accepted_as_clean is True
    assert snapshot.parser_evidence_reference == evidence_reference
    assert decision.acceptance_outcome is contracts.BeaconSnapshotAcceptanceOutcome.ACCEPTED
    assert decision.parser_evidence_reference == evidence_reference


@pytest.mark.parametrize(
    "status",
    (
        contracts.BeaconParserOutcomeStatus.MALFORMED,
        contracts.BeaconParserOutcomeStatus.INCOMPLETE,
        contracts.BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
        contracts.BeaconParserOutcomeStatus.BLOCKED,
        contracts.BeaconParserOutcomeStatus.ROUTE_FAILED,
        contracts.BeaconParserOutcomeStatus.AMBIGUOUS,
        contracts.BeaconParserOutcomeStatus.UNSUPPORTED,
    ),
)
def test_unsafe_parser_outcomes_cannot_be_clean_accepted_snapshots(
    status: contracts.BeaconParserOutcomeStatus,
) -> None:
    with pytest.raises(ValidationError):
        contracts.ExtractedSearchConfigurationSnapshot(
            snapshot_id=f"snap-contract-{status.value.lower()}",
            parser_outcome_status=status,
            accepted_as_clean=True,
            normalized_filter_values=(),
            evidence_reference="evidence-contract-unsafe",
        )


@pytest.mark.parametrize(
    "raw_reference,safety_class,expected_message",
    (
        (
            "<html><body>raw</body></html>",
            contracts.BeaconParserEvidenceSafetyClass.RAW_HTML,
            "raw HTML payload text",
        ),
        (
            'searchCore={"raw": true}',
            contracts.BeaconParserEvidenceSafetyClass.RAW_SEARCH_CORE,
            "raw searchCore payload text",
        ),
        (
            'context={"raw": true}',
            contracts.BeaconParserEvidenceSafetyClass.RAW_CONTEXT,
            "raw context payload text",
        ),
    ),
)
def test_raw_payload_text_cannot_be_represented_in_public_parser_evidence_reference(
    raw_reference: str,
    safety_class: contracts.BeaconParserEvidenceSafetyClass,
    expected_message: str,
) -> None:
    with pytest.raises(ValidationError, match=expected_message):
        contracts.BeaconParserEvidenceReference(
            evidence_reference=raw_reference,
            safety_class=safety_class,
        )


def test_raw_provider_payload_authority_cannot_be_accepted_as_clean_snapshot_evidence() -> None:
    with pytest.raises(ValidationError, match="non-ambiguous parser evidence"):
        contracts.ExtractedSearchConfigurationSnapshot(
            snapshot_id="snap-contract-bm05-raw-provider-authority-001",
            parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
            accepted_as_clean=True,
            normalized_filter_values=(),
            evidence_reference="evidence-contract-bm05-raw-provider-authority-001",
            parser_evidence_reference=_bm05_parser_evidence_reference(
                "parser-evidence-contract-bm05-raw-provider-authority-001",
                safety_class=contracts.BeaconParserEvidenceSafetyClass.RAW_PROVIDER_PAYLOAD_AUTHORITY,
                raw_provider_payload_authority=True,
            ),
        )


def test_invented_numeric_threshold_without_explicit_parser_adapter_evidence_gate_is_rejected() -> (
    None
):
    with pytest.raises(ValidationError, match="explicit parser adapter evidence gate"):
        _bm05_acceptance_decision(
            decision_id="decision-contract-bm05-threshold-001",
            parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
            parser_evidence_reference=_bm05_parser_evidence_reference(
                "parser-evidence-contract-bm05-threshold-001"
            ),
            acceptance_outcome=contracts.BeaconSnapshotAcceptanceOutcome.ACCEPTED,
            exact_acceptance_threshold_percent=97,
        )


def test_unsupported_parameters_cannot_be_silently_accepted() -> None:
    with pytest.raises(ValidationError, match="unsupported parameters cannot be silently accepted"):
        _bm05_acceptance_decision(
            decision_id="decision-contract-bm05-unsupported-params-001",
            parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
            parser_evidence_reference=_bm05_parser_evidence_reference(
                "parser-evidence-contract-bm05-unsupported-params-001"
            ),
            acceptance_outcome=contracts.BeaconSnapshotAcceptanceOutcome.ACCEPTED,
            unsupported_parameters=("unsupported=synthetic",),
        )


def test_full_parser_adapter_implementation_claim_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must not claim full Parser Adapter implementation"):
        _bm05_acceptance_decision(
            decision_id="decision-contract-bm05-full-parser-adapter-claim-001",
            parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
            parser_evidence_reference=_bm05_parser_evidence_reference(
                "parser-evidence-contract-bm05-full-parser-adapter-claim-001"
            ),
            acceptance_outcome=contracts.BeaconSnapshotAcceptanceOutcome.REJECTED,
            claims_full_parser_adapter_implementation_present=True,
        )


def test_permanently_deleted_beacon_cannot_be_restorable() -> None:
    snapshot = contracts.ExtractedSearchConfigurationSnapshot(
        snapshot_id="snap-contract-003",
        parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic-city",),
        evidence_reference="evidence-contract-003",
        parser_evidence_reference=contracts.BeaconParserEvidenceReference(
            evidence_reference="parser-evidence-contract-003"
        ),
    )
    source_url = contracts.BeaconSourceUrl(
        submitted_url="https://example.invalid/search?query=permanently-deleted",
        evidence_reference="evidence-contract-004",
        submitted_at=_SUBMITTED_AT,
        source_channel="user-submitted",
        submitted_by_label="synthetic-user",
    )
    configuration = contracts.BeaconCurrentConfiguration(
        beacon_id="beacon-contract-004",
        account_id="acct-contract-001",
        source_url=source_url,
        accepted_snapshot=snapshot,
        overrides=(),
        current_revision_id="rev-contract-004",
        display_name="Synthetic deleted beacon",
        lifecycle_state=contracts.BeaconLifecycleState.PERMANENTLY_DELETED,
    )

    with pytest.raises(ValidationError):
        contracts.Beacon(
            beacon_id="beacon-contract-004",
            account_id="acct-contract-001",
            naming=contracts.BeaconNamingMetadata(
                display_name="Synthetic deleted beacon",
                name_origin=contracts.BeaconNameOrigin.USER_PROVIDED,
                source_title="synthetic source",
                source_context_reference="ctx-contract-004",
            ),
            source_url=source_url,
            current_configuration=configuration,
            lifecycle_state=contracts.BeaconLifecycleState.PERMANENTLY_DELETED,
            restorable=True,
            counts_toward_active_limit=False,
        )


def test_beacon_management_contracts_do_not_import_forbidden_modules() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    module_path = repo_root / "src/mayak/modules/beacon_management/contracts.py"
    allowed_roots = {
        "__future__",
        "datetime",
        "enum",
        "typing",
        "pydantic",
    }

    _assert_no_forbidden_imports(module_path, allowed_roots)
