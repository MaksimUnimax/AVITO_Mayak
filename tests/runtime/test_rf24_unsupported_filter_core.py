from __future__ import annotations

from mayak.modules.filter_catalog import (
    BeaconOverrideCandidateState,
    BuilderDraftValidationReason,
    BuilderDraftValidationState,
    FilterCapabilityState,
)


def test_unsupported_semantic_states_are_explicit() -> None:
    assert FilterCapabilityState.UNSUPPORTED.value == "UNSUPPORTED"
    assert BuilderDraftValidationState.UNSUPPORTED.value == "UNSUPPORTED"
    assert BeaconOverrideCandidateState.UNSUPPORTED.value == "UNSUPPORTED"
    assert BuilderDraftValidationReason.FIELD_UNSUPPORTED.value == "FIELD_UNSUPPORTED"


def test_client_advisory_flags_cannot_be_authority() -> None:
    from mayak.modules.filter_catalog.builder_validation import BuilderFieldServerEntry

    assert BuilderFieldServerEntry.model_fields["client_visibility_authority"].default is False
    assert BuilderFieldServerEntry.model_fields["client_enablement_authority"].default is False
