from __future__ import annotations

import pytest
from pydantic import ValidationError

from mayak.modules.beacon_management import (
    FIXTURE_IDS,
    SYNTHETIC_FIXTURE_BY_ID,
    SYNTHETIC_FIXTURE_CASES,
)
from mayak.modules.beacon_management.contracts import (
    BeaconAuthorizationOutcome,
    BeaconConfigurationEvidenceRetentionDecision,
    BeaconConfigurationRetentionBoundary,
    BeaconConfigurationStoragePolicyOutcome,
    BeaconConfigurationStoragePolicyRejectionReason,
    BeaconCurrentConfigurationAuthorityStatus,
    BeaconCurrentConfigurationDecision,
    BeaconDecisionStatus,
    BeaconEffectiveConfigurationDecision,
    BeaconEffectiveConfigurationRejectionReason,
    BeaconEntitlementEvidenceFreshnessStatus,
    BeaconLifecycleEntitlementDecision,
    BeaconLifecycleEntitlementOutcome,
    BeaconLifecycleEntitlementRejectionReason,
    BeaconOverrideApplicationOutcome,
    BeaconOverrideFieldSupportStatus,
    BeaconOverridePatchOperation,
    BeaconOverrideRejectionReason,
    BeaconParserEvidenceSafetyClass,
    BeaconParserOutcomeStatus,
    BeaconPatchSaveRejectionReason,
    BeaconProtectedAction,
    BeaconSnapshotAcceptanceOutcome,
    BeaconSourceUrlPreparationOutcome,
    BeaconSourceUrlSafetyClassification,
    BeaconSystemActorClass,
)

EXPECTED_PRE_BM06_FIXTURE_IDS = (
    "FX-BM-ACTIVE-OWN-001",
    "FX-BM-FOREIGN-DENIED-001",
    "FX-BM-DUPLICATE-SAME-ACCOUNT-001",
    "FX-BM-DUPLICATE-CROSS-ACCOUNT-001",
    "FX-BM-FREE-COUNTRY-WIDE-BLOCKED-001",
    "FX-BM-BASIC-COUNTRY-WIDE-ALLOWED-001",
    "FX-BM-FREE-INTERVAL-180-ACCEPTED-001",
    "FX-BM-BASIC-INTERVAL-5-ACCEPTED-001",
    "FX-BM-UNSUPPORTED-OVERRIDE-001",
    "FX-BM-MULTIVALUE-OVERRIDE-001",
    "FX-BM-PARSER-UNSAFE-001",
    "FX-BM-PARSER-CAPTCHA-001",
    "FX-BM-PARSER-BM05-CLEAN-OPAQUE-ACCEPTED-001",
    "FX-BM-PARSER-BM05-MALFORMED-REJECTED-001",
    "FX-BM-PARSER-BM05-INCOMPLETE-REJECTED-001",
    "FX-BM-PARSER-BM05-CAPTCHA-REJECTED-001",
    "FX-BM-PARSER-BM05-BLOCKED-REJECTED-001",
    "FX-BM-PARSER-BM05-ROUTE-FAILED-REJECTED-001",
    "FX-BM-PARSER-BM05-AMBIGUOUS-REJECTED-001",
    "FX-BM-PARSER-BM05-UNSUPPORTED-REJECTED-001",
    "FX-BM-PARSER-BM05-RAW-PROVIDER-AUTHORITY-REJECTED-001",
    "FX-BM-PARSER-BM05-RAW-HTML-REJECTED-001",
    "FX-BM-PARSER-BM05-RAW-SEARCHCORE-REJECTED-001",
    "FX-BM-PARSER-BM05-RAW-CONTEXT-REJECTED-001",
    "FX-BM-PARSER-BM05-THRESHOLD-DEFERRED-001",
    "FX-BM-PARSER-BM05-UNSUPPORTED-PARAMETERS-REJECTED-001",
    "FX-BM-ARCHIVED-EXCLUDED-001",
    "FX-BM-PERMANENTLY-DELETED-001",
    "FX-BM-PATCH-SAVE-001",
    "FX-BM-LAST-WRITE-WINS-001",
    "FX-BM-SOURCE-URL-PREP-CREATED-001",
    "FX-BM-SOURCE-URL-PREP-REPLAYED-001",
    "FX-BM-SOURCE-URL-PREP-DUPLICATE-SAME-ACCOUNT-001",
    "FX-BM-SOURCE-URL-PREP-DUPLICATE-CROSS-ACCOUNT-001",
    "FX-BM-SOURCE-URL-PREP-MALFORMED-REJECTED-001",
    "FX-BM-SOURCE-URL-PREP-SOURCE-ONLY-IDEMPOTENCY-REJECTED-001",
    "FX-BM-SOURCE-URL-PREP-DUPLICATE-BLOCKING-POLICY-REJECTED-001",
    "FX-BM-SOURCE-URL-PREP-SNAPSHOT-OVERRIDE-PRESERVED-001",
    "FX-BM-SOURCE-URL-PREP-FINGERPRINT-OPAQUE-001",
    "FX-BM-SOURCE-URL-PREP-TRACKING-POLICY-001",
    "FX-BM-SOURCE-URL-PREP-SHELL-BLOCKED-001",
    "FX-BM-AUTHZ-OWNER-UPDATE-VERIFIED-001",
    "FX-BM-AUTHZ-OWNER-UPDATE-UNVERIFIED-001",
    "FX-BM-AUTHZ-FOREIGN-READ-BLOCKED-001",
    "FX-BM-AUTHZ-FOREIGN-MUTATE-BLOCKED-001",
    "FX-BM-AUTHZ-ADMIN-SUPPORT-READ-ALLOWED-001",
    "FX-BM-AUTHZ-ADMIN-SUPPORT-READ-REQUIRES-VERIFIED-001",
    "FX-BM-AUTHZ-ADMIN-SUPPORT-READ-REQUIRES-SCOPE-001",
    "FX-BM-AUTHZ-ADMIN-SUPPORT-MUTATE-REQUIRES-AUDIT-001",
    "FX-BM-AUTHZ-CLIENT-FLAG-TELEGRAM-DENIED-001",
    "FX-BM-AUTHZ-CLIENT-FLAG-WEB-DENIED-001",
    "FX-BM-AUTHZ-CLIENT-FLAG-ADMIN-DENIED-001",
    "FX-BM-AUTHZ-SYSTEM-FREEZE-ALLOWED-001",
    "FX-BM-AUTHZ-SYSTEM-FREEZE-BLOCKED-001",
)

EXPECTED_BM06_FIXTURE_IDS = (
    "FX-BM06-OVERRIDE-SUPPORTED-APPLIED-001",
    "FX-BM06-OVERRIDE-UNSUPPORTED-BLOCKED-001",
    "FX-BM06-OVERRIDE-UNCERTAIN-BLOCKED-001",
    "FX-BM06-OVERRIDE-AMBIGUOUS-BLOCKED-001",
    "FX-BM06-OVERRIDE-SOURCE-URL-REJECTED-001",
    "FX-BM06-OVERRIDE-MULTIVALUE-PRESERVED-001",
    "FX-BM06-OVERRIDE-MULTIVALUE-COLLAPSE-REJECTED-001",
    "FX-BM06-OVERRIDE-SINGLE-VALUE-MISMATCH-REJECTED-001",
    "FX-BM06-EFFECTIVE-CONFIG-ACCEPTED-001",
    "FX-BM06-EFFECTIVE-CONFIG-SINGLE-VALUE-MISMATCH-REJECTED-001",
    "FX-BM06-EFFECTIVE-CONFIG-NON-ACCEPTED-REJECTED-001",
    "FX-BM06-PATCH-MERGE-NONOVERLAP-001",
    "FX-BM06-PATCH-LAST-WRITE-WINS-001",
    "FX-BM06-PATCH-STALE-FULL-FORM-REJECTED-001",
)

EXPECTED_BM07_FIXTURE_IDS = (
    "FX-BM07-CURRENT-CONFIG-ACCEPTED-001",
    "FX-BM07-MULTIPLE-CURRENT-CONFIGS-REJECTED-001",
    "FX-BM07-CURRENT-CONFIG-REPLACED-001",
    "FX-BM07-COMMITTED-SCAN-EVIDENCE-RETAINED-001",
    "FX-BM07-NO-REINTERPRETATION-BLOCKED-001",
    "FX-BM07-UNBOUNDED-REVISION-CLOUTTER-REJECTED-001",
    "FX-BM07-PHYSICAL-COMPACTION-DELETE-REJECTED-001",
    "FX-BM07-RUNTIME-PERSISTENCE-CLAIM-REJECTED-001",
    "FX-BM07-SCANRUN-HISTORY-CLAIM-REJECTED-001",
    "FX-BM07-MINIMAL-COMMITTED-EVIDENCE-NOT-EDITABLE-001",
)

EXPECTED_BM08_FIXTURE_IDS = (
    "FX-BM08-BASIC-ALLOWED-001",
    "FX-BM08-BASIC-LIMIT-BLOCKED-001",
    "FX-BM08-BASIC-INTERVAL-BELOW-FLOOR-BLOCKED-001",
    "FX-BM08-BASIC-INTERVAL-STEP-BLOCKED-001",
    "FX-BM08-FREE-ALLOWED-001",
    "FX-BM08-FREE-COUNTRY-WIDE-BLOCKED-001",
    "FX-BM08-FREE-INTERVAL-BELOW-FLOOR-BLOCKED-001",
    "FX-BM08-FREE-INTERVAL-STEP-BLOCKED-001",
    "FX-BM08-FREE-ACTIVE-LIMIT-BLOCKED-001",
    "FX-BM08-DELETED-HISTORY-ARCHIVED-EXCLUDED-001",
    "FX-BM08-AMBIGUOUS-ENTITLEMENT-BLOCKED-001",
    "FX-BM08-DENIED-ENTITLEMENT-BLOCKED-001",
    "FX-BM08-RESUME-RECHECK-REQUIRED-001",
    "FX-BM08-EXPIRED-PAID-FROZEN-001",
    "FX-BM08-EXPIRED-PAID-USER-CHOICE-REQUIRED-001",
    "FX-BM08-EXPIRED-PAID-NO-AUTO-CHOICE-REJECTED-001",
    "FX-BM08-SELECTED-FREE-COMPLIANCE-REQUIRED-001",
    "FX-BM08-NOTIFICATION-FUTURE-REFERENCE-ONLY-001",
    "FX-BM08-NOTIFICATION-SENDING-CLAIM-REJECTED-001",
    "FX-BM08-BILLING-PAYMENT-TARIFF-MUTATION-CLAIM-REJECTED-001",
    "FX-BM08-SCHEDULER-RUNTIME-CLAIM-REJECTED-001",
    "FX-BM08-DB-REPOSITORY-RUNTIME-CLAIM-REJECTED-001",
    "FX-BM08-SCANRUN-HISTORY-CLAIM-REJECTED-001",
    "FX-BM08-PARSER-FILTER-CATALOG-CLAIM-REJECTED-001",
    "FX-BM08-CLIENT-FLAG-NOT-AUTHORIZATION-REJECTED-001",
    "FX-BM08-ACTIVATE-MISSING-EVIDENCE-REJECTED-001",
    "FX-BM08-RESUME-STALE-EVIDENCE-REJECTED-001",
    "FX-BM08-PROVENANCE-BOUNDARIES-DISTINCT-001",
)


def test_fixture_ids_are_unique_and_stable() -> None:
    assert FIXTURE_IDS == tuple(fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_CASES)
    assert len(FIXTURE_IDS) == len(set(FIXTURE_IDS))
    assert SYNTHETIC_FIXTURE_BY_ID[FIXTURE_IDS[0]].fixture_id == FIXTURE_IDS[0]


def test_all_fixtures_are_synthetic_and_have_no_real_avito_url() -> None:
    forbidden_fragments = (
        "avito.ru",
        "www.avito.ru",
        "m.avito.ru",
        "avito.com",
    )

    for fixture in SYNTHETIC_FIXTURE_CASES:
        payload_text = fixture.model_dump_json().lower()
        assert all(fragment not in payload_text for fragment in forbidden_fragments)
        if fixture.source_url is not None:
            assert fixture.source_url.submitted_url.startswith("https://example.invalid/")
        if fixture.beacon is not None:
            assert fixture.beacon.source_url.submitted_url.startswith("https://example.invalid/")
        if fixture.peer_beacon is not None:
            assert fixture.peer_beacon.source_url.submitted_url.startswith(
                "https://example.invalid/"
            )
        if fixture.current_configuration is not None:
            assert fixture.current_configuration.source_url.submitted_url.startswith(
                "https://example.invalid/"
            )
        if fixture.beacon is not None and fixture.current_configuration is not None:
            assert fixture.beacon.source_url == fixture.current_configuration.source_url
        if fixture.peer_beacon is not None:
            assert (
                fixture.peer_beacon.source_url
                == fixture.peer_beacon.current_configuration.source_url
            )


def test_bm04_source_url_fixture_ids_are_present() -> None:
    expected_ids = (
        "FX-BM-SOURCE-URL-PREP-CREATED-001",
        "FX-BM-SOURCE-URL-PREP-REPLAYED-001",
        "FX-BM-SOURCE-URL-PREP-DUPLICATE-SAME-ACCOUNT-001",
        "FX-BM-SOURCE-URL-PREP-DUPLICATE-CROSS-ACCOUNT-001",
        "FX-BM-SOURCE-URL-PREP-MALFORMED-REJECTED-001",
        "FX-BM-SOURCE-URL-PREP-SOURCE-ONLY-IDEMPOTENCY-REJECTED-001",
        "FX-BM-SOURCE-URL-PREP-DUPLICATE-BLOCKING-POLICY-REJECTED-001",
        "FX-BM-SOURCE-URL-PREP-SNAPSHOT-OVERRIDE-PRESERVED-001",
        "FX-BM-SOURCE-URL-PREP-FINGERPRINT-OPAQUE-001",
        "FX-BM-SOURCE-URL-PREP-TRACKING-POLICY-001",
        "FX-BM-SOURCE-URL-PREP-SHELL-BLOCKED-001",
    )

    for fixture_id in expected_ids:
        assert fixture_id in SYNTHETIC_FIXTURE_BY_ID
        assert SYNTHETIC_FIXTURE_BY_ID[fixture_id].fixture_id == fixture_id


def test_bm05_parser_snapshot_fixture_ids_are_present() -> None:
    expected_ids = (
        "FX-BM-PARSER-BM05-CLEAN-OPAQUE-ACCEPTED-001",
        "FX-BM-PARSER-BM05-MALFORMED-REJECTED-001",
        "FX-BM-PARSER-BM05-INCOMPLETE-REJECTED-001",
        "FX-BM-PARSER-BM05-CAPTCHA-REJECTED-001",
        "FX-BM-PARSER-BM05-BLOCKED-REJECTED-001",
        "FX-BM-PARSER-BM05-ROUTE-FAILED-REJECTED-001",
        "FX-BM-PARSER-BM05-AMBIGUOUS-REJECTED-001",
        "FX-BM-PARSER-BM05-UNSUPPORTED-REJECTED-001",
        "FX-BM-PARSER-BM05-RAW-PROVIDER-AUTHORITY-REJECTED-001",
        "FX-BM-PARSER-BM05-RAW-HTML-REJECTED-001",
        "FX-BM-PARSER-BM05-RAW-SEARCHCORE-REJECTED-001",
        "FX-BM-PARSER-BM05-RAW-CONTEXT-REJECTED-001",
        "FX-BM-PARSER-BM05-THRESHOLD-DEFERRED-001",
        "FX-BM-PARSER-BM05-UNSUPPORTED-PARAMETERS-REJECTED-001",
    )

    for fixture_id in expected_ids:
        assert fixture_id in SYNTHETIC_FIXTURE_BY_ID
        assert SYNTHETIC_FIXTURE_BY_ID[fixture_id].fixture_id == fixture_id


def test_created_source_url_fixture_preserves_submitted_url() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-CREATED-001"]

    assert fixture.beacon is not None
    assert fixture.source_url_preparation_decision is not None
    assert fixture.source_url is not None
    assert fixture.current_configuration is not None
    assert fixture.beacon.source_url == fixture.current_configuration.source_url
    assert (
        fixture.current_configuration.source_url.submitted_url == fixture.source_url.submitted_url
    )
    assert (
        fixture.source_url_preparation_decision.prepared_source_url.preserved_submitted_url
        == fixture.source_url.submitted_url
    )
    assert (
        fixture.source_url_preparation_decision.prepared_source_url.source_url_overwritten_by_snapshot
        is False
    )
    assert (
        fixture.source_url_preparation_decision.prepared_source_url.source_url_overwritten_by_override
        is False
    )
    assert (
        fixture.source_url_preparation_decision.outcome is BeaconSourceUrlPreparationOutcome.CREATED
    )


def test_replayed_source_url_fixture_does_not_use_source_url_alone_as_idempotency_basis() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-REPLAYED-001"]

    assert fixture.source_url_preparation_decision is not None
    basis = fixture.source_url_preparation_decision.idempotency_basis
    assert basis.source_url_only_basis is False
    assert basis.command_reference is not None
    assert basis.account_id is not None
    assert basis.beacon_id is not None
    assert (
        fixture.source_url_preparation_decision.outcome
        is BeaconSourceUrlPreparationOutcome.REPLAYED
    )


def test_bm04_duplicate_same_account_source_url_fixture_has_same_url_and_different_beacon_ids() -> (
    None
):
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-DUPLICATE-SAME-ACCOUNT-001"]

    assert fixture.beacon is not None
    assert fixture.peer_beacon is not None
    assert fixture.beacon.source_url == fixture.beacon.current_configuration.source_url
    assert fixture.peer_beacon.source_url == fixture.peer_beacon.current_configuration.source_url
    assert fixture.beacon.source_url.submitted_url == fixture.peer_beacon.source_url.submitted_url
    assert fixture.beacon.beacon_id != fixture.peer_beacon.beacon_id
    assert fixture.beacon.account_id == fixture.peer_beacon.account_id


def test_bm04_duplicate_cross_account_source_url_allowed() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-DUPLICATE-CROSS-ACCOUNT-001"]

    assert fixture.beacon is not None
    assert fixture.peer_beacon is not None
    assert fixture.beacon.source_url == fixture.beacon.current_configuration.source_url
    assert fixture.peer_beacon.source_url == fixture.peer_beacon.current_configuration.source_url
    assert fixture.beacon.source_url.submitted_url == fixture.peer_beacon.source_url.submitted_url
    assert fixture.beacon.account_id != fixture.peer_beacon.account_id


def test_malformed_source_url_fixture_is_rejected_before_effect() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-MALFORMED-REJECTED-001"]

    assert fixture.source_url_preparation_decision is not None
    assert (
        fixture.source_url_preparation_decision.outcome
        is BeaconSourceUrlPreparationOutcome.REJECTED
    )
    assert (
        fixture.source_url_preparation_decision.prepared_source_url.safety_classification
        is BeaconSourceUrlSafetyClassification.MALFORMED
    )


def test_source_url_alone_idempotency_basis_fixture_is_rejected_or_blocked() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-SOURCE-ONLY-IDEMPOTENCY-REJECTED-001"]

    assert fixture.source_url_preparation_decision is not None
    assert (
        fixture.source_url_preparation_decision.outcome
        is BeaconSourceUrlPreparationOutcome.REJECTED
    )
    assert fixture.source_url_preparation_decision.idempotency_basis.source_url_only_basis is False
    assert fixture.source_url_preparation_decision.idempotency_basis.command_reference is not None


def test_duplicate_url_blocking_policy_fixture_is_rejected_by_default() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[
        "FX-BM-SOURCE-URL-PREP-DUPLICATE-BLOCKING-POLICY-REJECTED-001"
    ]

    assert fixture.source_url_preparation_decision is not None
    assert (
        fixture.source_url_preparation_decision.outcome
        is BeaconSourceUrlPreparationOutcome.REJECTED
    )
    assert fixture.source_url_preparation_decision.duplicate_source_url_blocking_policy is False


def test_original_source_url_is_not_overwritten_by_snapshot_or_override_fixture() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-SNAPSHOT-OVERRIDE-PRESERVED-001"]

    assert fixture.beacon is not None
    assert fixture.current_configuration is not None
    assert fixture.source_url_preparation_decision is not None
    assert fixture.source_url is not None
    assert fixture.beacon.source_url == fixture.current_configuration.source_url
    assert (
        fixture.current_configuration.source_url.submitted_url == fixture.source_url.submitted_url
    )
    assert (
        fixture.source_url_preparation_decision.prepared_source_url.source_url_overwritten_by_snapshot
        is False
    )
    assert (
        fixture.source_url_preparation_decision.prepared_source_url.source_url_overwritten_by_override
        is False
    )


def test_canonical_fingerprint_fixture_is_opaque_and_not_configuration_authority() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-FINGERPRINT-OPAQUE-001"]

    assert fixture.source_url_preparation_decision is not None
    prepared = fixture.source_url_preparation_decision.prepared_source_url
    assert prepared.opaque_fingerprint_reference is not None
    assert prepared.fingerprint_policy is not None
    assert prepared.fingerprint_policy.authoritative_configuration_source is False


def test_tracking_params_fixture_requires_explicit_captured_policy_reference() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-TRACKING-POLICY-001"]

    assert fixture.source_url_preparation_decision is not None
    assert fixture.source_url_preparation_decision.tracking_params_ignored is True
    assert fixture.source_url_preparation_decision.tracking_policy_reference is not None


def test_no_valid_fixture_contains_unsafe_shell_interpolation_channel() -> None:
    for fixture in SYNTHETIC_FIXTURE_CASES:
        if fixture.source_url_preparation_decision is None:
            continue
        assert fixture.source_url_preparation_decision.shell_interpolation_field is None


def test_shell_blocked_fixture_remains_blocked_without_interpolation_channel() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-SOURCE-URL-PREP-SHELL-BLOCKED-001"]

    assert fixture.source_url_preparation_decision is not None
    assert fixture.source_url is not None
    shell_command_text = fixture.source_url_preparation_decision.shell_command_text
    assert shell_command_text is not None
    assert fixture.source_url.submitted_url not in shell_command_text
    assert fixture.source_url_preparation_decision.shell_interpolation_field is None
    assert (
        fixture.source_url_preparation_decision.outcome is BeaconSourceUrlPreparationOutcome.BLOCKED
    )


def test_duplicate_same_account_source_url_fixture_has_same_url_and_different_beacon_ids() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-DUPLICATE-SAME-ACCOUNT-001"]

    assert fixture.beacon is not None
    assert fixture.peer_beacon is not None
    assert fixture.beacon.source_url.submitted_url == fixture.peer_beacon.source_url.submitted_url
    assert fixture.beacon.beacon_id != fixture.peer_beacon.beacon_id
    assert fixture.beacon.account_id == fixture.peer_beacon.account_id


def test_duplicate_cross_account_source_url_fixture_has_same_url_and_different_account_ids() -> (
    None
):
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-DUPLICATE-CROSS-ACCOUNT-001"]

    assert fixture.beacon is not None
    assert fixture.peer_beacon is not None
    assert fixture.beacon.source_url.submitted_url == fixture.peer_beacon.source_url.submitted_url
    assert fixture.beacon.account_id != fixture.peer_beacon.account_id


def test_free_country_wide_fixture_is_blocked_and_city_required() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-FREE-COUNTRY-WIDE-BLOCKED-001"]

    assert fixture.activation_decision is not None
    assert fixture.activation_decision.status is BeaconDecisionStatus.BLOCKED
    assert fixture.activation_decision.country_wide_allowed is False
    assert fixture.activation_decision.city_required is True
    assert fixture.activation_decision.requested_city is None


def test_basic_country_wide_fixture_is_allowed() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-BASIC-COUNTRY-WIDE-ALLOWED-001"]

    assert fixture.activation_decision is not None
    assert fixture.activation_decision.status is BeaconDecisionStatus.ALLOWED
    assert fixture.activation_decision.country_wide_allowed is True
    assert fixture.activation_decision.requested_country_wide is True


def test_archived_history_deleted_fixture_does_not_count_toward_active_limit() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-ARCHIVED-EXCLUDED-001"]

    assert fixture.beacon is not None
    assert fixture.history_entry is not None
    assert fixture.beacon.counts_toward_active_limit is False
    assert fixture.history_entry.counts_toward_active_limit is False
    assert fixture.history_entry.outcome.name == "ARCHIVED"


def test_permanently_deleted_fixture_is_not_restorable() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PERMANENTLY-DELETED-001"]

    assert fixture.beacon is not None
    assert fixture.history_entry is not None
    assert fixture.beacon.restorable is False
    assert fixture.history_entry.restorable is False
    assert fixture.beacon.lifecycle_state.name == "PERMANENTLY_DELETED"


def test_patch_based_save_fixture_changes_only_supplied_fields() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PATCH-SAVE-001"]

    assert fixture.mutation_decision is not None
    applied_fields = fixture.mutation_decision.applied_fields
    assert fixture.mutation_decision.patch_fields == ("display_name", "interval_minutes")
    assert applied_fields == ("display_name",)
    assert set(applied_fields).issubset(fixture.mutation_decision.patch_fields)
    assert fixture.mutation_decision.current_configuration_replaced is True


def test_last_write_wins_fixture_represents_later_successful_save_as_authoritative() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-LAST-WRITE-WINS-001"]

    assert fixture.mutation_decision is not None
    assert fixture.mutation_decision.same_field_concurrent_change is True
    assert fixture.mutation_decision.last_write_wins is True
    assert fixture.mutation_decision.status is BeaconDecisionStatus.ALLOWED
    assert fixture.mutation_decision.conflict_fields == ("interval_minutes",)


def test_parser_unsafe_fixtures_remain_not_clean() -> None:
    malformed = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-UNSAFE-001"]
    captcha = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-CAPTCHA-001"]

    assert malformed.snapshot is not None
    assert captcha.snapshot is not None
    assert malformed.snapshot.parser_outcome_status is BeaconParserOutcomeStatus.MALFORMED
    assert captcha.snapshot.parser_outcome_status is BeaconParserOutcomeStatus.CAPTCHA_AFFECTED
    assert malformed.snapshot.accepted_as_clean is False
    assert captcha.snapshot.accepted_as_clean is False


def test_bm05_clean_accepted_fixture_uses_opaque_parser_evidence_reference() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-BM05-CLEAN-OPAQUE-ACCEPTED-001"]

    assert fixture.snapshot is not None
    assert fixture.snapshot_acceptance_decision is not None
    assert fixture.snapshot.accepted_as_clean is True
    assert fixture.snapshot.parser_evidence_reference is not None
    assert fixture.snapshot.parser_evidence_reference.safety_class is (
        BeaconParserEvidenceSafetyClass.OPAQUE
    )
    assert (
        fixture.snapshot_acceptance_decision.acceptance_outcome
        is BeaconSnapshotAcceptanceOutcome.ACCEPTED
    )
    assert fixture.snapshot_acceptance_decision.parser_adapter_evidence_gate_reference is not None


@pytest.mark.parametrize(
    "fixture_id,expected_outcome",
    (
        (
            "FX-BM-PARSER-BM05-MALFORMED-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.REJECTED,
        ),
        (
            "FX-BM-PARSER-BM05-INCOMPLETE-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.REJECTED,
        ),
        (
            "FX-BM-PARSER-BM05-CAPTCHA-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.BLOCKED,
        ),
        (
            "FX-BM-PARSER-BM05-BLOCKED-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.BLOCKED,
        ),
        (
            "FX-BM-PARSER-BM05-ROUTE-FAILED-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.BLOCKED,
        ),
        (
            "FX-BM-PARSER-BM05-AMBIGUOUS-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.REJECTED,
        ),
        (
            "FX-BM-PARSER-BM05-UNSUPPORTED-REJECTED-001",
            BeaconSnapshotAcceptanceOutcome.UNSUPPORTED,
        ),
    ),
)
def test_bm05_negative_parser_fixtures_are_not_accepted(
    fixture_id: str,
    expected_outcome: BeaconSnapshotAcceptanceOutcome,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]

    assert fixture.snapshot is not None
    assert fixture.snapshot_acceptance_decision is not None
    assert fixture.snapshot.accepted_as_clean is False
    assert fixture.snapshot_acceptance_decision.acceptance_outcome is expected_outcome
    assert fixture.snapshot_acceptance_decision.acceptance_outcome is not (
        BeaconSnapshotAcceptanceOutcome.ACCEPTED
    )


def test_bm05_raw_provider_payload_authority_fixture_is_rejected() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-BM05-RAW-PROVIDER-AUTHORITY-REJECTED-001"]

    assert fixture.snapshot is not None
    assert fixture.snapshot_acceptance_decision is not None
    assert fixture.snapshot.parser_evidence_reference is not None
    assert (
        fixture.snapshot.parser_evidence_reference.safety_class
        is BeaconParserEvidenceSafetyClass.RAW_PROVIDER_PAYLOAD_AUTHORITY
    )
    assert fixture.snapshot.parser_evidence_reference.raw_provider_payload_authority is True
    assert (
        fixture.snapshot_acceptance_decision.acceptance_outcome
        is BeaconSnapshotAcceptanceOutcome.REJECTED
    )


@pytest.mark.parametrize(
    "fixture_id,expected_safety_class",
    (
        (
            "FX-BM-PARSER-BM05-RAW-HTML-REJECTED-001",
            BeaconParserEvidenceSafetyClass.RAW_HTML,
        ),
        (
            "FX-BM-PARSER-BM05-RAW-SEARCHCORE-REJECTED-001",
            BeaconParserEvidenceSafetyClass.RAW_SEARCH_CORE,
        ),
        (
            "FX-BM-PARSER-BM05-RAW-CONTEXT-REJECTED-001",
            BeaconParserEvidenceSafetyClass.RAW_CONTEXT,
        ),
    ),
)
def test_bm05_raw_payload_reference_fixtures_are_rejected(
    fixture_id: str,
    expected_safety_class: BeaconParserEvidenceSafetyClass,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]

    assert fixture.snapshot is not None
    assert fixture.snapshot_acceptance_decision is not None
    assert fixture.snapshot.parser_evidence_reference is not None
    assert fixture.snapshot.parser_evidence_reference.safety_class is expected_safety_class
    assert (
        fixture.snapshot_acceptance_decision.acceptance_outcome
        is BeaconSnapshotAcceptanceOutcome.REJECTED
    )


def test_bm05_threshold_deferred_fixture_does_not_invent_numeric_threshold() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-BM05-THRESHOLD-DEFERRED-001"]

    assert fixture.snapshot is not None
    assert fixture.snapshot_acceptance_decision is not None
    assert fixture.snapshot_acceptance_decision.acceptance_outcome is (
        BeaconSnapshotAcceptanceOutcome.DEFERRED
    )
    assert fixture.snapshot_acceptance_decision.exact_acceptance_threshold_percent is None
    assert fixture.snapshot_acceptance_decision.parser_adapter_evidence_gate_reference is None


def test_bm05_unsupported_parameters_fixture_does_not_silently_accept_unsupported_parameters() -> (
    None
):
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-BM05-UNSUPPORTED-PARAMETERS-REJECTED-001"]

    assert fixture.snapshot is not None
    assert fixture.snapshot_acceptance_decision is not None
    assert fixture.snapshot.unsupported_parameters == ("unsupported=synthetic",)
    assert fixture.snapshot_acceptance_decision.unsupported_parameters == ("unsupported=synthetic",)
    assert (
        fixture.snapshot_acceptance_decision.acceptance_outcome
        is BeaconSnapshotAcceptanceOutcome.REJECTED
    )


def test_bm06_fixture_ids_are_present() -> None:
    expected_ids = (
        "FX-BM06-OVERRIDE-SUPPORTED-APPLIED-001",
        "FX-BM06-OVERRIDE-UNSUPPORTED-BLOCKED-001",
        "FX-BM06-OVERRIDE-UNCERTAIN-BLOCKED-001",
        "FX-BM06-OVERRIDE-AMBIGUOUS-BLOCKED-001",
        "FX-BM06-OVERRIDE-SOURCE-URL-REJECTED-001",
        "FX-BM06-OVERRIDE-MULTIVALUE-PRESERVED-001",
        "FX-BM06-OVERRIDE-MULTIVALUE-COLLAPSE-REJECTED-001",
        "FX-BM06-OVERRIDE-SINGLE-VALUE-MISMATCH-REJECTED-001",
        "FX-BM06-EFFECTIVE-CONFIG-ACCEPTED-001",
        "FX-BM06-EFFECTIVE-CONFIG-SINGLE-VALUE-MISMATCH-REJECTED-001",
        "FX-BM06-EFFECTIVE-CONFIG-NON-ACCEPTED-REJECTED-001",
        "FX-BM06-PATCH-MERGE-NONOVERLAP-001",
        "FX-BM06-PATCH-LAST-WRITE-WINS-001",
        "FX-BM06-PATCH-STALE-FULL-FORM-REJECTED-001",
    )

    for fixture_id in expected_ids:
        assert fixture_id in SYNTHETIC_FIXTURE_BY_ID
        assert SYNTHETIC_FIXTURE_BY_ID[fixture_id].fixture_id == fixture_id


def test_bm06_supported_override_fixture_is_applied() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-OVERRIDE-SUPPORTED-APPLIED-001"]

    assert fixture.override_patch_operation is not None
    assert fixture.override_patch_operation.support_status is (
        BeaconOverrideFieldSupportStatus.SUPPORTED
    )
    assert fixture.override_patch_operation.outcome is BeaconOverrideApplicationOutcome.APPLIED
    assert fixture.override_patch_operation.applied_values == ("north",)


@pytest.mark.parametrize(
    "fixture_id,expected_outcome,expected_reason",
    (
        (
            "FX-BM06-OVERRIDE-UNSUPPORTED-BLOCKED-001",
            BeaconOverrideApplicationOutcome.BLOCKED,
            BeaconOverrideRejectionReason.UNSUPPORTED_FIELD,
        ),
        (
            "FX-BM06-OVERRIDE-UNCERTAIN-BLOCKED-001",
            BeaconOverrideApplicationOutcome.REJECTED,
            BeaconOverrideRejectionReason.UNCERTAIN_EVIDENCE,
        ),
        (
            "FX-BM06-OVERRIDE-AMBIGUOUS-BLOCKED-001",
            BeaconOverrideApplicationOutcome.BLOCKED,
            BeaconOverrideRejectionReason.AMBIGUOUS_EVIDENCE,
        ),
        (
            "FX-BM06-OVERRIDE-SOURCE-URL-REJECTED-001",
            BeaconOverrideApplicationOutcome.REJECTED,
            BeaconOverrideRejectionReason.SOURCE_URL_OVERRIDE,
        ),
        (
            "FX-BM06-OVERRIDE-MULTIVALUE-COLLAPSE-REJECTED-001",
            BeaconOverrideApplicationOutcome.BLOCKED,
            BeaconOverrideRejectionReason.MULTIVALUE_COLLAPSE,
        ),
    ),
)
def test_bm06_override_fixtures_are_rejected_or_blocked_and_not_applied(
    fixture_id: str,
    expected_outcome: BeaconOverrideApplicationOutcome,
    expected_reason: BeaconOverrideRejectionReason,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]

    assert fixture.override_patch_operation is not None
    assert fixture.override_patch_operation.outcome is expected_outcome
    assert fixture.override_patch_operation.applied_values is None
    assert fixture.override_patch_operation.rejection_reason is expected_reason


def test_bm06_multivalue_fixture_preserves_approved_values() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-OVERRIDE-MULTIVALUE-PRESERVED-001"]

    assert fixture.override_patch_operation is not None
    assert fixture.override_patch_operation.applied_values == (
        "wifi",
        "parking",
    )
    assert fixture.override_patch_operation.requested_values == (
        "wifi",
        "parking",
    )


def test_bm06_single_value_override_mismatch_fixture_is_rejected() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-OVERRIDE-SINGLE-VALUE-MISMATCH-REJECTED-001"]

    assert fixture.override_patch_operation is not None
    assert fixture.override_patch_operation.requested_values == ("north",)
    assert fixture.override_patch_operation.applied_values == ("south",)
    with pytest.raises(ValidationError, match="applied override must match requested values"):
        BeaconOverridePatchOperation.model_validate(fixture.override_patch_operation.model_dump())


def test_bm06_effective_config_evidence_is_distinct() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-EFFECTIVE-CONFIG-ACCEPTED-001"]

    assert fixture.source_url is not None
    assert fixture.snapshot is not None
    assert fixture.effective_configuration_decision is not None
    decision = fixture.effective_configuration_decision
    assert decision.status is BeaconDecisionStatus.ALLOWED
    assert decision.accepted_snapshot == fixture.snapshot
    assert decision.source_url == fixture.source_url
    first_override = decision.override_operations[0]
    second_override = decision.override_operations[1]
    assert (
        decision.accepted_snapshot.evidence_reference != first_override.override_evidence_reference
    )
    assert (
        decision.accepted_snapshot.evidence_reference != second_override.override_evidence_reference
    )
    expected_effective_configuration_reference = "effective-config-bm06-001"
    expected_authoritative_state_reference = "authoritative-state-bm06-effective-001"
    assert decision.effective_configuration_reference == expected_effective_configuration_reference
    assert decision.authoritative_state_reference == expected_authoritative_state_reference


def test_bm06_effective_config_single_value_mismatch_fixture_is_rejected() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-EFFECTIVE-CONFIG-SINGLE-VALUE-MISMATCH-REJECTED-001"]

    assert fixture.effective_configuration_decision is not None
    invalid_decision = fixture.effective_configuration_decision
    assert invalid_decision.override_operations[0].requested_values == ("north",)
    assert invalid_decision.override_operations[0].applied_values == ("south",)
    with pytest.raises(ValidationError, match="applied override must match requested values"):
        BeaconEffectiveConfigurationDecision(
            decision_id=invalid_decision.decision_id,
            beacon_id=invalid_decision.beacon_id,
            account_id=invalid_decision.account_id,
            source_url=invalid_decision.source_url,
            accepted_snapshot=invalid_decision.accepted_snapshot,
            override_operations=invalid_decision.override_operations,
            status=invalid_decision.status,
            effective_configuration_reference=invalid_decision.effective_configuration_reference,
            authoritative_state_reference=invalid_decision.authoritative_state_reference,
            source_url_overwritten_by_snapshot=invalid_decision.source_url_overwritten_by_snapshot,
            source_url_overwritten_by_override=invalid_decision.source_url_overwritten_by_override,
        )


def test_bm06_non_accepted_snapshot_effective_config_fixture_is_rejected() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-EFFECTIVE-CONFIG-NON-ACCEPTED-REJECTED-001"]

    assert fixture.effective_configuration_decision is not None
    assert fixture.effective_configuration_decision.status is BeaconDecisionStatus.REJECTED
    assert (
        fixture.effective_configuration_decision.rejection_reason
        is BeaconEffectiveConfigurationRejectionReason.NON_ACCEPTED_SNAPSHOT
    )
    assert fixture.effective_configuration_decision.accepted_snapshot.accepted_as_clean is False


def test_bm06_patch_merge_fixture_preserves_non_overlapping_updates() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-PATCH-MERGE-NONOVERLAP-001"]

    assert fixture.patch_save_decision is not None
    assert fixture.patch_save_decision.status is BeaconDecisionStatus.ALLOWED
    assert fixture.patch_save_decision.different_field_updates_merge is True
    assert fixture.patch_save_decision.authoritative_state_reference == (
        "authoritative-state-bm06-patch-merge-001"
    )
    assert (
        fixture.patch_save_decision.claims_db_repository_runtime_persistence_implementation is False
    )


def test_bm06_patch_last_write_wins_fixture_is_semantic_only() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-PATCH-LAST-WRITE-WINS-001"]

    assert fixture.patch_save_decision is not None
    assert fixture.patch_save_decision.same_field_concurrent_change is True
    assert fixture.patch_save_decision.last_write_wins is True
    assert (
        fixture.patch_save_decision.claims_db_repository_runtime_persistence_implementation is False
    )
    assert fixture.patch_save_decision.authoritative_state_reference == (
        "authoritative-state-bm06-patch-lww-001"
    )


def test_bm06_stale_full_form_overwrite_fixture_is_rejected() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM06-PATCH-STALE-FULL-FORM-REJECTED-001"]

    assert fixture.patch_save_decision is not None
    assert fixture.patch_save_decision.status is BeaconDecisionStatus.REJECTED
    assert fixture.patch_save_decision.stale_full_form_overwrite is True
    assert (
        fixture.patch_save_decision.rejection_reason
        is BeaconPatchSaveRejectionReason.STALE_FULL_FORM_OVERWRITE
    )
    assert fixture.patch_save_decision.authoritative_state_reference is None


def test_bm07_current_configuration_fixture_has_one_current_active_configuration() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM07-CURRENT-CONFIG-ACCEPTED-001"]

    assert fixture.current_configuration is not None
    assert fixture.current_configuration_decision is not None
    assert fixture.current_configuration_decision.authority_status is (
        BeaconCurrentConfigurationAuthorityStatus.CURRENT_USER_FACING_ACTIVE
    )
    assert fixture.current_configuration_decision.storage_policy_outcome is (
        BeaconConfigurationStoragePolicyOutcome.ALLOWED
    )
    assert fixture.current_configuration_decision.retention_boundary is (
        BeaconConfigurationRetentionBoundary.CURRENT_USER_FACING_WORKING_CONFIGURATION
    )
    assert (
        len(fixture.current_configuration_decision.current_user_facing_active_configurations) == 1
    )
    assert (
        fixture.current_configuration_decision.current_scan_configuration_reference
        == fixture.current_configuration.current_revision_id
    )
    assert (
        fixture.current_configuration.source_url.evidence_reference
        != fixture.current_configuration.accepted_snapshot.evidence_reference
    )
    assert (
        fixture.current_configuration.accepted_snapshot.evidence_reference
        != fixture.current_configuration.overrides[0].override_reference
    )
    assert (
        fixture.current_configuration.source_url.evidence_reference
        != fixture.current_configuration.overrides[0].override_reference
    )
    assert (
        fixture.current_configuration.current_revision_id
        != fixture.current_configuration.overrides[0].override_reference
    )
    assert (
        fixture.current_configuration.current_revision_id
        != fixture.current_configuration.accepted_snapshot.evidence_reference
    )


def test_bm07_configuration_replacement_fixture_marks_new_configuration_as_current() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM07-CURRENT-CONFIG-REPLACED-001"]

    assert fixture.current_configuration is not None
    assert fixture.current_configuration_decision is not None
    assert (
        fixture.current_configuration_decision.configuration_change_replaces_current_working_configuration
        is True
    )
    assert (
        fixture.current_configuration_decision.replaced_current_user_facing_configuration
        is not None
    )
    assert fixture.current_configuration_decision.current_user_facing_active_configurations[0] == (
        fixture.current_configuration
    )
    assert fixture.current_configuration.previous_user_facing_revision_ids == (
        "current-config-bm07-replaced-old-ref-001",
    )
    assert fixture.current_configuration_decision.current_scan_configuration_reference == (
        fixture.current_configuration.current_revision_id
    )
    assert (
        fixture.current_configuration_decision.replaced_current_user_facing_configuration.current_revision_id
        == "current-config-bm07-replaced-old-ref-001"
    )


def test_bm07_committed_scan_evidence_fixture_retains_original_reference() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM07-COMMITTED-SCAN-EVIDENCE-RETAINED-001"]

    assert fixture.configuration_evidence_retention_decision is not None
    decision = fixture.configuration_evidence_retention_decision
    assert decision.authority_status is (
        BeaconCurrentConfigurationAuthorityStatus.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE
    )
    assert decision.storage_policy_outcome is BeaconConfigurationStoragePolicyOutcome.ALLOWED
    assert decision.retention_boundary is (
        BeaconConfigurationRetentionBoundary.MINIMAL_IMMUTABLE_SCAN_AUDIT_EVIDENCE
    )
    assert (
        decision.current_configuration_reference != decision.committed_scan_audit_evidence_reference
    )
    assert (
        decision.original_current_configuration_reference == "current-config-bm07-original-ref-001"
    )
    assert decision.minimal_immutable_scan_audit_evidence_reference == (
        "retention-boundary-bm07-minimal-001"
    )


@pytest.mark.parametrize(
    "fixture_id,validator,expected_message,expected_reason",
    (
        (
            "FX-BM07-MULTIPLE-CURRENT-CONFIGS-REJECTED-001",
            BeaconCurrentConfigurationDecision,
            "exactly one current user-facing active configuration must be represented",
            BeaconConfigurationStoragePolicyRejectionReason.MORE_THAN_ONE_CURRENT_USER_FACING_ACTIVE_CONFIGURATION,
        ),
        (
            "FX-BM07-UNBOUNDED-REVISION-CLOUTTER-REJECTED-001",
            BeaconCurrentConfigurationDecision,
            "must not become unbounded user-visible clutter",
            BeaconConfigurationStoragePolicyRejectionReason.UNBOUNDED_USER_FACING_REVISION_CLOUTTER,
        ),
        (
            "FX-BM07-NO-REINTERPRETATION-BLOCKED-001",
            BeaconConfigurationEvidenceRetentionDecision,
            "must not be silently reinterpreted",
            BeaconConfigurationStoragePolicyRejectionReason.REINTERPRETING_COMMITTED_SCAN_AUDIT_FACTS,
        ),
        (
            "FX-BM07-PHYSICAL-COMPACTION-DELETE-REJECTED-001",
            BeaconConfigurationEvidenceRetentionDecision,
            "physical delete or compaction in semantic contract is forbidden",
            BeaconConfigurationStoragePolicyRejectionReason.PHYSICAL_DELETE_OR_COMPACTION_CLAIM,
        ),
        (
            "FX-BM07-RUNTIME-PERSISTENCE-CLAIM-REJECTED-001",
            BeaconConfigurationEvidenceRetentionDecision,
            "DB/repository/runtime persistence implementation claim is forbidden",
            BeaconConfigurationStoragePolicyRejectionReason.DB_REPOSITORY_RUNTIME_PERSISTENCE_CLAIM,
        ),
        (
            "FX-BM07-SCANRUN-HISTORY-CLAIM-REJECTED-001",
            BeaconConfigurationEvidenceRetentionDecision,
            "ScanRun/listing history state claim is forbidden",
            BeaconConfigurationStoragePolicyRejectionReason.SCANRUN_LISTING_HISTORY_STATE_CLAIM,
        ),
        (
            "FX-BM07-MINIMAL-COMMITTED-EVIDENCE-NOT-EDITABLE-001",
            BeaconConfigurationEvidenceRetentionDecision,
            "minimal committed evidence cannot be treated as editable current config",
            BeaconConfigurationStoragePolicyRejectionReason.MINIMAL_COMMITTED_EVIDENCE_EDITABLE,
        ),
    ),
)
def test_bm07_blocked_and_rejected_fixtures_are_rejected(
    fixture_id: str,
    validator: type[BeaconCurrentConfigurationDecision]
    | type[BeaconConfigurationEvidenceRetentionDecision],
    expected_message: str,
    expected_reason: BeaconConfigurationStoragePolicyRejectionReason,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
    decision = (
        fixture.current_configuration_decision or fixture.configuration_evidence_retention_decision
    )
    assert decision is not None
    assert decision.rejection_reason is expected_reason

    with pytest.raises(ValidationError, match=expected_message):
        validator.model_validate(decision.model_dump())


def test_pre_bm06_fixture_order_is_preserved_and_bm07_fixtures_are_appended() -> None:
    assert FIXTURE_IDS[: len(EXPECTED_PRE_BM06_FIXTURE_IDS)] == EXPECTED_PRE_BM06_FIXTURE_IDS
    bm06_start = len(EXPECTED_PRE_BM06_FIXTURE_IDS)
    bm06_end = bm06_start + len(EXPECTED_BM06_FIXTURE_IDS)
    assert FIXTURE_IDS[bm06_start:bm06_end] == EXPECTED_BM06_FIXTURE_IDS
    bm07_end = bm06_end + len(EXPECTED_BM07_FIXTURE_IDS)
    assert FIXTURE_IDS[bm06_end:bm07_end] == EXPECTED_BM07_FIXTURE_IDS
    assert FIXTURE_IDS[bm07_end:] == EXPECTED_BM08_FIXTURE_IDS
    for fixture_id in EXPECTED_BM06_FIXTURE_IDS:
        assert fixture_id in SYNTHETIC_FIXTURE_BY_ID
        assert SYNTHETIC_FIXTURE_BY_ID[fixture_id].fixture_id == fixture_id
    for fixture_id in EXPECTED_BM07_FIXTURE_IDS:
        assert fixture_id in SYNTHETIC_FIXTURE_BY_ID
        assert SYNTHETIC_FIXTURE_BY_ID[fixture_id].fixture_id == fixture_id
    for fixture_id in EXPECTED_BM08_FIXTURE_IDS:
        assert fixture_id in SYNTHETIC_FIXTURE_BY_ID
        assert SYNTHETIC_FIXTURE_BY_ID[fixture_id].fixture_id == fixture_id


@pytest.mark.parametrize(
    "fixture_id,expected_outcome,expected_reason",
    (
        (
            "FX-BM08-BASIC-ALLOWED-001",
            BeaconLifecycleEntitlementOutcome.ALLOWED,
            None,
        ),
        (
            "FX-BM08-BASIC-LIMIT-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.ACTIVE_LIMIT_EXCEEDED,
        ),
        (
            "FX-BM08-BASIC-INTERVAL-BELOW-FLOOR-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.BASIC_INTERVAL_BELOW_FLOOR,
        ),
        (
            "FX-BM08-BASIC-INTERVAL-STEP-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.BASIC_INTERVAL_NOT_STEP,
        ),
        (
            "FX-BM08-FREE-ALLOWED-001",
            BeaconLifecycleEntitlementOutcome.ALLOWED,
            None,
        ),
        (
            "FX-BM08-FREE-COUNTRY-WIDE-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.FREE_COUNTRY_WIDE_REQUIRES_CITY,
        ),
        (
            "FX-BM08-FREE-INTERVAL-BELOW-FLOOR-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.FREE_INTERVAL_BELOW_FLOOR,
        ),
        (
            "FX-BM08-FREE-INTERVAL-STEP-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.FREE_INTERVAL_NOT_STEP,
        ),
        (
            "FX-BM08-FREE-ACTIVE-LIMIT-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.BLOCKED,
            BeaconLifecycleEntitlementRejectionReason.ACTIVE_LIMIT_EXCEEDED,
        ),
    ),
)
def test_bm08_basic_and_free_activation_fixtures_cover_allowed_and_blocked_semantics(
    fixture_id: str,
    expected_outcome: BeaconLifecycleEntitlementOutcome,
    expected_reason: BeaconLifecycleEntitlementRejectionReason | None,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
    decision = fixture.lifecycle_entitlement_decision
    snapshot = fixture.effective_entitlement_snapshot

    assert decision is not None
    assert decision.outcome is expected_outcome
    assert decision.rejection_reason is expected_reason
    assert fixture.entitlement_evidence_reference is not None
    assert fixture.tariff_policy_band is not None
    assert snapshot is not None

    if fixture_id == "FX-BM08-BASIC-ALLOWED-001":
        assert decision.active_beacon_count == 4
        assert snapshot.tariff_policy_band.active_beacon_limit == 5
        assert snapshot.requested_interval_minutes == 5
        assert snapshot.requested_country_wide is True
    elif fixture_id == "FX-BM08-FREE-ALLOWED-001":
        assert snapshot.selected_city == "synthetic-city"
        assert snapshot.tariff_policy_band.active_beacon_limit == 1
        assert snapshot.requested_interval_minutes == 180
    elif fixture_id == "FX-BM08-FREE-COUNTRY-WIDE-BLOCKED-001":
        assert decision.requested_country_wide is True
        assert decision.selected_city is None
    elif fixture_id == "FX-BM08-FREE-ACTIVE-LIMIT-BLOCKED-001":
        assert decision.active_beacon_count == 1
        assert snapshot.tariff_policy_band.active_beacon_limit == 1


def test_bm08_deleted_history_archived_excluded_fixture_keeps_non_active_counts_out_of_limit() -> (
    None
):
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM08-DELETED-HISTORY-ARCHIVED-EXCLUDED-001"]

    assert fixture.lifecycle_entitlement_decision is not None
    decision = fixture.lifecycle_entitlement_decision
    snapshot = decision.effective_entitlement_snapshot
    assert decision.outcome is BeaconLifecycleEntitlementOutcome.ALLOWED
    assert decision.active_beacon_count == 0
    assert decision.archived_beacon_count == 1
    assert decision.history_beacon_count == 1
    assert decision.deleted_beacon_count == 1
    assert snapshot is not None
    assert snapshot.active_beacon_count == 0
    assert snapshot.tariff_policy_band.active_beacon_limit == 5


@pytest.mark.parametrize(
    "fixture_id,expected_message",
    (
        (
            "FX-BM08-ACTIVATE-MISSING-EVIDENCE-REJECTED-001",
            "activation/resume requires entitlement evidence reference",
        ),
        (
            "FX-BM08-RESUME-STALE-EVIDENCE-REJECTED-001",
            "activation/resume requires fresh entitlement evidence reference",
        ),
    ),
)
def test_bm08_activation_and_resume_missing_or_stale_evidence_are_rejected(
    fixture_id: str,
    expected_message: str,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
    decision = fixture.lifecycle_entitlement_decision
    assert decision is not None
    if fixture_id == "FX-BM08-RESUME-STALE-EVIDENCE-REJECTED-001":
        assert decision.entitlement_evidence_reference is not None
        assert (
            decision.entitlement_evidence_reference.freshness_status
            is BeaconEntitlementEvidenceFreshnessStatus.STALE
        )

    with pytest.raises(ValidationError, match=expected_message):
        BeaconLifecycleEntitlementDecision.model_validate(decision.model_dump())


@pytest.mark.parametrize(
    "fixture_id,expected_outcome,expected_reason",
    (
        (
            "FX-BM08-AMBIGUOUS-ENTITLEMENT-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.AMBIGUOUS,
            BeaconLifecycleEntitlementRejectionReason.AMBIGUOUS_ENTITLEMENT,
        ),
        (
            "FX-BM08-DENIED-ENTITLEMENT-BLOCKED-001",
            BeaconLifecycleEntitlementOutcome.DENIED,
            BeaconLifecycleEntitlementRejectionReason.DENIED_ENTITLEMENT,
        ),
        (
            "FX-BM08-RESUME-RECHECK-REQUIRED-001",
            BeaconLifecycleEntitlementOutcome.RECHECK_REQUIRED,
            BeaconLifecycleEntitlementRejectionReason.RECHECK_REQUIRED,
        ),
        (
            "FX-BM08-EXPIRED-PAID-FROZEN-001",
            BeaconLifecycleEntitlementOutcome.FROZEN,
            BeaconLifecycleEntitlementRejectionReason.EXPIRED_ENTITLEMENT,
        ),
        (
            "FX-BM08-EXPIRED-PAID-USER-CHOICE-REQUIRED-001",
            BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
            BeaconLifecycleEntitlementRejectionReason.EXPIRED_ENTITLEMENT,
        ),
        (
            "FX-BM08-SELECTED-FREE-COMPLIANCE-REQUIRED-001",
            BeaconLifecycleEntitlementOutcome.FREE_COMPLIANCE_REQUIRED,
            BeaconLifecycleEntitlementRejectionReason.FREE_COMPLIANCE_REQUIRED,
        ),
        (
            "FX-BM08-NOTIFICATION-FUTURE-REFERENCE-ONLY-001",
            BeaconLifecycleEntitlementOutcome.USER_CHOICE_REQUIRED,
            BeaconLifecycleEntitlementRejectionReason.EXPIRED_ENTITLEMENT,
        ),
        (
            "FX-BM08-PROVENANCE-BOUNDARIES-DISTINCT-001",
            BeaconLifecycleEntitlementOutcome.ALLOWED,
            None,
        ),
    ),
)
def test_bm08_expired_paid_flow_and_provenance_semantics_are_explicit(
    fixture_id: str,
    expected_outcome: BeaconLifecycleEntitlementOutcome,
    expected_reason: BeaconLifecycleEntitlementRejectionReason | None,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
    decision = fixture.lifecycle_entitlement_decision
    assert decision is not None
    assert decision.outcome is expected_outcome
    assert decision.rejection_reason is expected_reason
    assert decision.effective_entitlement_snapshot is not None
    assert (
        decision.effective_entitlement_snapshot.beacon_source_reference
        != decision.effective_entitlement_snapshot.entitlement_source_reference
    )
    assert (
        decision.effective_entitlement_snapshot.entitlement_source_reference
        != decision.effective_entitlement_snapshot.provenance_reference
    )
    if fixture_id in {
        "FX-BM08-RESUME-RECHECK-REQUIRED-001",
        "FX-BM08-EXPIRED-PAID-FROZEN-001",
        "FX-BM08-EXPIRED-PAID-USER-CHOICE-REQUIRED-001",
        "FX-BM08-NOTIFICATION-FUTURE-REFERENCE-ONLY-001",
        "FX-BM08-SELECTED-FREE-COMPLIANCE-REQUIRED-001",
    }:
        assert decision.future_notification_reference is not None
    if fixture_id == "FX-BM08-RESUME-RECHECK-REQUIRED-001":
        assert decision.entitlement_recheck_reference is not None
    if fixture_id == "FX-BM08-SELECTED-FREE-COMPLIANCE-REQUIRED-001":
        assert decision.selected_free_beacon_id is not None
        assert decision.selected_free_beacon_user_choice_reference is not None
        assert decision.free_compliance_reference is None


def test_bm08_no_auto_choice_fixture_is_rejected() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM08-EXPIRED-PAID-NO-AUTO-CHOICE-REJECTED-001"]
    decision = fixture.lifecycle_entitlement_decision
    assert decision is not None

    with pytest.raises(
        ValidationError, match="expired paid access must not choose a free Beacon automatically"
    ):
        BeaconLifecycleEntitlementDecision.model_validate(decision.model_dump())


@pytest.mark.parametrize(
    "fixture_id,expected_message",
    (
        (
            "FX-BM08-NOTIFICATION-SENDING-CLAIM-REJECTED-001",
            "notification sending claim is forbidden",
        ),
        (
            "FX-BM08-BILLING-PAYMENT-TARIFF-MUTATION-CLAIM-REJECTED-001",
            "billing/payment/tariff mutation claim is forbidden",
        ),
        (
            "FX-BM08-SCHEDULER-RUNTIME-CLAIM-REJECTED-001",
            "scheduler/runtime claim is forbidden",
        ),
        (
            "FX-BM08-DB-REPOSITORY-RUNTIME-CLAIM-REJECTED-001",
            "DB/repository/runtime persistence implementation claim is forbidden",
        ),
        (
            "FX-BM08-SCANRUN-HISTORY-CLAIM-REJECTED-001",
            "ScanRun/listing history state claim is forbidden",
        ),
        (
            "FX-BM08-PARSER-FILTER-CATALOG-CLAIM-REJECTED-001",
            "Parser/Filter Catalog ownership claim is forbidden",
        ),
        (
            "FX-BM08-CLIENT-FLAG-NOT-AUTHORIZATION-REJECTED-001",
            "client channel flag is not authorization proof",
        ),
    ),
)
def test_bm08_claim_fixtures_are_rejected(
    fixture_id: str,
    expected_message: str,
) -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
    decision = fixture.lifecycle_entitlement_decision
    assert decision is not None

    with pytest.raises(ValidationError, match=expected_message):
        BeaconLifecycleEntitlementDecision.model_validate(decision.model_dump())


def test_bm08_validator_rejects_unsafe_allowed_semantics_for_interval_limit_and_city() -> None:
    blocked_fixtures = (
        "FX-BM08-BASIC-LIMIT-BLOCKED-001",
        "FX-BM08-BASIC-INTERVAL-BELOW-FLOOR-BLOCKED-001",
        "FX-BM08-BASIC-INTERVAL-STEP-BLOCKED-001",
        "FX-BM08-FREE-COUNTRY-WIDE-BLOCKED-001",
        "FX-BM08-FREE-INTERVAL-BELOW-FLOOR-BLOCKED-001",
        "FX-BM08-FREE-INTERVAL-STEP-BLOCKED-001",
        "FX-BM08-FREE-ACTIVE-LIMIT-BLOCKED-001",
    )

    for fixture_id in blocked_fixtures:
        fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
        decision = fixture.lifecycle_entitlement_decision
        assert decision is not None
        unsafe_decision = decision.model_copy(
            update={
                "outcome": BeaconLifecycleEntitlementOutcome.ALLOWED,
                "rejection_reason": None,
                "effective_entitlement_snapshot": (
                    decision.effective_entitlement_snapshot.model_copy(
                        update={"effective_outcome": BeaconLifecycleEntitlementOutcome.ALLOWED}
                    )
                )
                if decision.effective_entitlement_snapshot is not None
                else None,
            }
        )

        expected_message = (
            "active Beacon limit exceeded"
            if fixture_id
            in {
                "FX-BM08-BASIC-LIMIT-BLOCKED-001",
                "FX-BM08-FREE-ACTIVE-LIMIT-BLOCKED-001",
            }
            else "requested interval is below the approved floor"
            if fixture_id
            in {
                "FX-BM08-BASIC-INTERVAL-BELOW-FLOOR-BLOCKED-001",
                "FX-BM08-FREE-INTERVAL-BELOW-FLOOR-BLOCKED-001",
            }
            else "requested interval must follow the approved step"
            if fixture_id
            in {
                "FX-BM08-BASIC-INTERVAL-STEP-BLOCKED-001",
                "FX-BM08-FREE-INTERVAL-STEP-BLOCKED-001",
            }
            else "free country-wide activation requires a city"
        )

        with pytest.raises(ValidationError, match=expected_message):
            BeaconLifecycleEntitlementDecision.model_validate(unsafe_decision.model_dump())


def test_owner_verified_update_fixture_is_allowed() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-OWNER-UPDATE-VERIFIED-001"]

    assert fixture.ownership_decision is not None
    assert fixture.ownership_decision.outcome is BeaconAuthorizationOutcome.ALLOWED
    assert fixture.ownership_decision.protected_action is BeaconProtectedAction.UPDATE_BEACON
    assert fixture.ownership_decision.actor_context.is_verified is True
    assert (
        fixture.ownership_decision.actor_context.account_id
        == fixture.ownership_decision.beacon_account_id
    )


def test_unverified_mutation_fixture_is_blocked_and_requires_verified_actor() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-OWNER-UPDATE-UNVERIFIED-001"]

    assert fixture.ownership_decision is not None
    assert fixture.ownership_decision.outcome is BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR
    assert fixture.ownership_decision.actor_context.is_verified is False


def test_foreign_account_fixtures_deny_without_existence_sensitive_detail() -> None:
    read_fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-FOREIGN-READ-BLOCKED-001"]
    mutate_fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-FOREIGN-MUTATE-BLOCKED-001"]

    for fixture in (read_fixture, mutate_fixture):
        assert fixture.ownership_decision is not None
        assert fixture.ownership_decision.outcome is BeaconAuthorizationOutcome.BLOCKED
        assert fixture.ownership_decision.existence_sensitive_detail is None
        assert fixture.ownership_decision.foreign_account_existence_sensitive_detail is False


def test_admin_support_read_fixture_has_server_side_scope_and_audit_reference() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-ADMIN-SUPPORT-READ-ALLOWED-001"]

    assert fixture.authorization_decision is not None
    assert fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.ALLOWED
    assert (
        fixture.authorization_decision.protected_action is BeaconProtectedAction.ADMIN_SUPPORT_READ
    )
    assert fixture.authorization_decision.actor_context.is_verified is True
    assert fixture.authorization_decision.server_role_scope_reference is not None
    assert fixture.authorization_decision.server_audit_reference is not None


def test_admin_support_requires_verified_fixture_is_unverified() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-ADMIN-SUPPORT-READ-REQUIRES-VERIFIED-001"]

    assert fixture.authorization_decision is not None
    assert (
        fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.REQUIRES_VERIFIED_ACTOR
    )
    assert fixture.authorization_decision.actor_context.is_verified is False
    assert fixture.authorization_decision.server_role_scope_reference is None
    assert fixture.authorization_decision.server_audit_reference is None


def test_admin_support_requires_scope_fixture_has_no_scope_reference() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-ADMIN-SUPPORT-READ-REQUIRES-SCOPE-001"]

    assert fixture.authorization_decision is not None
    assert fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.REQUIRES_SCOPE
    assert fixture.authorization_decision.actor_context.is_verified is True
    assert fixture.authorization_decision.server_role_scope_reference is None
    assert fixture.authorization_decision.server_audit_reference is not None


def test_admin_support_missing_audit_fixture_is_blocked() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-ADMIN-SUPPORT-MUTATE-REQUIRES-AUDIT-001"]

    assert fixture.authorization_decision is not None
    assert fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.REQUIRES_AUDIT
    assert fixture.authorization_decision.server_role_scope_reference is not None
    assert fixture.authorization_decision.server_audit_reference is None


def test_unverified_admin_support_allowed_state_is_not_present_as_a_valid_fixture() -> None:
    for fixture in SYNTHETIC_FIXTURE_CASES:
        if fixture.authorization_decision is None:
            continue
        if fixture.authorization_decision.protected_action not in (
            BeaconProtectedAction.ADMIN_SUPPORT_READ,
            BeaconProtectedAction.ADMIN_SUPPORT_MUTATE,
        ):
            continue
        assert not (
            fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.ALLOWED
            and fixture.authorization_decision.actor_context.is_verified is False
        )


def test_client_flag_only_fixtures_are_denied_not_authorization() -> None:
    for fixture_id in (
        "FX-BM-AUTHZ-CLIENT-FLAG-TELEGRAM-DENIED-001",
        "FX-BM-AUTHZ-CLIENT-FLAG-WEB-DENIED-001",
        "FX-BM-AUTHZ-CLIENT-FLAG-ADMIN-DENIED-001",
    ):
        fixture = SYNTHETIC_FIXTURE_BY_ID[fixture_id]
        assert fixture.ownership_decision is not None
        assert fixture.ownership_decision.outcome is BeaconAuthorizationOutcome.DENIED
        assert fixture.ownership_decision.actor_context.client_channel_flag is not None
        assert (
            fixture.ownership_decision.actor_context.client_channel_flag_is_authorization_proof
            is False
        )


def test_system_freeze_fixture_has_service_actor_class_causation_and_policy_source() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-SYSTEM-FREEZE-ALLOWED-001"]

    assert fixture.authorization_decision is not None
    assert fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.ALLOWED
    assert fixture.authorization_decision.action_causation is not None
    assert (
        fixture.authorization_decision.action_causation.service_actor_class
        is BeaconSystemActorClass.MAINTENANCE_SERVICE
    )
    assert fixture.authorization_decision.action_causation.causation_reference is not None
    assert fixture.authorization_decision.action_causation.policy_source_reference is not None


def test_system_lifecycle_missing_causation_policy_fixture_is_blocked() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-AUTHZ-SYSTEM-FREEZE-BLOCKED-001"]

    assert fixture.authorization_decision is not None
    assert fixture.authorization_decision.outcome is BeaconAuthorizationOutcome.BLOCKED
    assert fixture.authorization_decision.action_causation is None
