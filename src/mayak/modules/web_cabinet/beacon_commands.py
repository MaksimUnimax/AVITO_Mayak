"""Transport-neutral Web Cabinet command envelopes for Beacon Management."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import (
    ContractMetadata,
    IdempotencyFingerprint,
    IdempotencyKey,
    IdempotencyScope,
)
from mayak.platform.boundaries import BEACON_MANAGEMENT_MODULE_ID


class _WebBeaconCommandContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyString = Annotated[str, Field(min_length=1)]


class WebBeaconCommandKind(str, Enum):
    PATCH_CURRENT_CONFIGURATION = "PATCH_CURRENT_CONFIGURATION"
    ARCHIVE_TO_HISTORY = "ARCHIVE_TO_HISTORY"
    DELETE_TO_HISTORY = "DELETE_TO_HISTORY"
    RESTORE_FROM_HISTORY = "RESTORE_FROM_HISTORY"
    PERMANENT_DELETE = "PERMANENT_DELETE"


class WebBeaconCommandSubmitState(str, Enum):
    SUBMITTED = "SUBMITTED"
    REPLAYED = "REPLAYED"
    REJECTED = "REJECTED"
    FORBIDDEN = "FORBIDDEN"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class WebBeaconPatchField(_WebBeaconCommandContract):
    web_patch_field_id: _NonEmptyString
    field_name: _NonEmptyString
    requested_value_reference_id: _NonEmptyString
    owning_module_validation_family_reference_id: _NonEmptyString
    client_validation_reference_id: _NonEmptyString | None = None
    explicitly_supplied: Literal[True] = True
    server_validation_required: Literal[True] = True
    client_validation_authority: Literal[False] = False
    field_support_authority: Literal[False] = False
    raw_value_retained: Literal[False] = False
    provider_payload_retained: Literal[False] = False


class SubmitBeaconWebCommandCommand(_WebBeaconCommandContract):
    web_beacon_command_id: _NonEmptyString
    metadata: ContractMetadata
    account_id: _NonEmptyString
    actor_context_reference_id: _NonEmptyString
    authorization_decision_reference_id: _NonEmptyString
    tenant_scope_reference_id: _NonEmptyString
    beacon_id: _NonEmptyString
    command_kind: WebBeaconCommandKind
    owning_module_id: _NonEmptyString
    owning_module_command_family_reference_id: _NonEmptyString
    web_observed_state_reference_id: _NonEmptyString
    patch_fields: tuple[WebBeaconPatchField, ...]
    history_entry_reference_id: _NonEmptyString | None = None
    confirmation_reference_id: _NonEmptyString | None = None
    entitlement_recheck_reference_id: _NonEmptyString | None = None
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    idempotency_fingerprint: IdempotencyFingerprint
    correlation_id: _NonEmptyString
    causation_id: _NonEmptyString
    reason_code: _NonEmptyString
    verified_actor_required: Literal[True] = True
    ownership_scope_validation_required: Literal[True] = True
    server_side_validation_required: Literal[True] = True
    owning_module_current_state_reload_required: Literal[True] = True
    client_validation_authority: Literal[False] = False
    web_observed_state_authority: Literal[False] = False
    direct_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    entitlement_mutation_authority: Literal[False] = False
    scan_mutation_authority: Literal[False] = False
    notification_mutation_authority: Literal[False] = False
    stale_full_form_overwrite: Literal[False] = False
    source_url_only_idempotency: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_command(self) -> "SubmitBeaconWebCommandCommand":
        if self.owning_module_id != BEACON_MANAGEMENT_MODULE_ID:
            raise ValueError("command owner must be Beacon Management")
        patch_ids = tuple(field.web_patch_field_id for field in self.patch_fields)
        field_names = tuple(field.field_name for field in self.patch_fields)
        if len(patch_ids) != len(set(patch_ids)):
            raise ValueError("duplicate web patch field identifiers are not allowed")
        if len(field_names) != len(set(field_names)):
            raise ValueError("duplicate patch field names are not allowed")
        if self.command_kind is WebBeaconCommandKind.PATCH_CURRENT_CONFIGURATION:
            if not self.patch_fields:
                raise ValueError("patch command requires patch fields")
        elif self.patch_fields:
            raise ValueError("lifecycle command cannot carry patch fields")
        if (
            self.command_kind is WebBeaconCommandKind.DELETE_TO_HISTORY
            and self.confirmation_reference_id is None
        ):
            raise ValueError("ordinary delete requires confirmation")
        if self.command_kind is WebBeaconCommandKind.PERMANENT_DELETE and (
            self.history_entry_reference_id is None or self.confirmation_reference_id is None
        ):
            raise ValueError("permanent delete requires history entry and confirmation")
        if self.command_kind is WebBeaconCommandKind.RESTORE_FROM_HISTORY and (
            self.history_entry_reference_id is None or self.entitlement_recheck_reference_id is None
        ):
            raise ValueError("restore requires history entry and entitlement recheck")
        if self.command_kind not in {
            WebBeaconCommandKind.RESTORE_FROM_HISTORY,
            WebBeaconCommandKind.PERMANENT_DELETE,
        } and self.history_entry_reference_id is not None:
            raise ValueError("only restore and permanent delete may carry history entry")
        if (
            self.command_kind is not WebBeaconCommandKind.RESTORE_FROM_HISTORY
            and self.entitlement_recheck_reference_id is not None
        ):
            raise ValueError("only restore may carry entitlement recheck")
        return self


class WebBeaconCommandSubmitOutcome(_WebBeaconCommandContract):
    web_beacon_command_submit_outcome_id: _NonEmptyString
    metadata: ContractMetadata
    command: SubmitBeaconWebCommandCommand
    state: WebBeaconCommandSubmitState
    owning_module_id: _NonEmptyString
    owning_module_outcome_reference_id: _NonEmptyString | None = None
    authoritative_state_reference_id: _NonEmptyString | None = None
    replay_of_outcome_reference_id: _NonEmptyString | None = None
    rejection_reason_code: _NonEmptyString | None = None
    ambiguity_reference_id: _NonEmptyString | None = None
    applied_field_names: tuple[_NonEmptyString, ...] = ()
    owning_module_accepted: bool
    authoritative_state_reloaded: bool
    safe_display_outcome: Literal[True] = True
    explicit_owning_module_outcome_required: Literal[True] = True
    web_business_success_authority: Literal[False] = False
    direct_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    full_form_state_retained: Literal[False] = False
    committed_scan_audit_facts_rewritten: Literal[False] = False
    physical_delete_implementation_claimed: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome(self) -> "WebBeaconCommandSubmitOutcome":
        if (
            self.owning_module_id != BEACON_MANAGEMENT_MODULE_ID
            or self.command.owning_module_id != self.owning_module_id
        ):
            raise ValueError("outcome owner must match Beacon Management command owner")
        accepted_state = self.state in {
            WebBeaconCommandSubmitState.SUBMITTED,
            WebBeaconCommandSubmitState.REPLAYED,
        }
        if self.state is WebBeaconCommandSubmitState.SUBMITTED:
            if not self.owning_module_accepted or self.owning_module_outcome_reference_id is None:
                raise ValueError("submitted outcome requires owning-module acceptance and outcome")
            if (
                self.authoritative_state_reference_id is None
                or not self.authoritative_state_reloaded
            ):
                raise ValueError("submitted outcome requires reloaded authoritative state")
        if self.state is WebBeaconCommandSubmitState.REPLAYED:
            if (
                self.replay_of_outcome_reference_id is None
                or self.owning_module_outcome_reference_id is None
            ):
                raise ValueError("replayed outcome requires replay and owning-module references")
            if self.owning_module_accepted and (
                self.authoritative_state_reference_id is None
                or not self.authoritative_state_reloaded
            ):
                raise ValueError("accepted replay requires reloaded authoritative state")
        if not accepted_state and self.owning_module_accepted:
            raise ValueError("non-submitted outcome cannot be accepted")
        if self.state in {
            WebBeaconCommandSubmitState.REJECTED,
            WebBeaconCommandSubmitState.FORBIDDEN,
            WebBeaconCommandSubmitState.BLOCKED,
            WebBeaconCommandSubmitState.STALE,
            WebBeaconCommandSubmitState.UNSUPPORTED,
        } and self.rejection_reason_code is None:
            raise ValueError("rejected outcome requires rejection reason")
        if self.state in {
            WebBeaconCommandSubmitState.AMBIGUOUS,
            WebBeaconCommandSubmitState.RECONCILIATION_REQUIRED,
        } and self.ambiguity_reference_id is None:
            raise ValueError("ambiguous outcome requires ambiguity reference")
        if self.state not in {
            WebBeaconCommandSubmitState.AMBIGUOUS,
            WebBeaconCommandSubmitState.RECONCILIATION_REQUIRED,
        } and self.ambiguity_reference_id is not None:
            raise ValueError("only ambiguous outcomes may carry ambiguity reference")
        if (
            self.state is not WebBeaconCommandSubmitState.REPLAYED
            and self.replay_of_outcome_reference_id is not None
        ):
            raise ValueError("only replayed outcomes may carry replay reference")
        if self.authoritative_state_reference_id is None and self.authoritative_state_reloaded:
            raise ValueError("reloaded state requires authoritative reference")
        if (
            self.authoritative_state_reference_id is not None
            and not self.authoritative_state_reloaded
        ):
            raise ValueError("authoritative state reference requires reload")
        if not self.owning_module_accepted and self.applied_field_names:
            raise ValueError("non-accepted outcome cannot carry applied fields")
        if self.command.command_kind is WebBeaconCommandKind.PATCH_CURRENT_CONFIGURATION:
            if self.owning_module_accepted and not self.applied_field_names:
                raise ValueError("accepted patch outcome requires applied fields")
            command_names = {field.field_name for field in self.command.patch_fields}
            if not set(self.applied_field_names).issubset(command_names):
                raise ValueError("applied fields must be a subset of patch fields")
        elif self.applied_field_names:
            raise ValueError("non-patch outcome cannot carry applied fields")
        if len(self.applied_field_names) != len(set(self.applied_field_names)):
            raise ValueError("duplicate applied field names are not allowed")
        return self


__all__ = [
    "SubmitBeaconWebCommandCommand",
    "WebBeaconCommandKind",
    "WebBeaconCommandSubmitOutcome",
    "WebBeaconCommandSubmitState",
    "WebBeaconPatchField",
]
