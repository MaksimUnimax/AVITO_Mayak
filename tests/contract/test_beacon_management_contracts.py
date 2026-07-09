from __future__ import annotations

import ast
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path

import pytest
from pydantic import ValidationError

from mayak.modules import beacon_management
from mayak.modules.beacon_management import contracts
from mayak.platform import boundaries

_SUBMITTED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc)


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


def test_malformed_and_captcha_parser_outcomes_cannot_be_clean_accepted_snapshots() -> None:
    for status in (
        contracts.BeaconParserOutcomeStatus.MALFORMED,
        contracts.BeaconParserOutcomeStatus.CAPTCHA_AFFECTED,
        contracts.BeaconParserOutcomeStatus.BLOCKED,
        contracts.BeaconParserOutcomeStatus.ROUTE_FAILED,
        contracts.BeaconParserOutcomeStatus.AMBIGUOUS,
    ):
        with pytest.raises(ValidationError):
            contracts.ExtractedSearchConfigurationSnapshot(
                snapshot_id=f"snap-contract-{status.value.lower()}",
                parser_outcome_status=status,
                accepted_as_clean=True,
                normalized_filter_values=(),
                evidence_reference="evidence-contract-unsafe",
            )


def test_permanently_deleted_beacon_cannot_be_restorable() -> None:
    snapshot = contracts.ExtractedSearchConfigurationSnapshot(
        snapshot_id="snap-contract-003",
        parser_outcome_status=contracts.BeaconParserOutcomeStatus.CLEAN,
        accepted_as_clean=True,
        normalized_filter_values=("city=synthetic-city",),
        evidence_reference="evidence-contract-003",
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
