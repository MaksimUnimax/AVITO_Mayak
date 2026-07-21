"""Semantic Web Cabinet boundary for safe cross-interface channel linking."""

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
from mayak.modules.web_cabinet.read_models import WebReadFreshness, WebViewAudience
from mayak.platform.boundaries import (
    MAX_ADAPTER_MODULE_ID,
    NOTIFICATION_DELIVERY_MODULE_ID,
    TELEGRAM_ADAPTER_MODULE_ID,
    WEB_CABINET_MODULE_ID,
)


class _WebChannelLinkingContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


def _validate_references(values: tuple[str, ...], label: str, *, non_empty: bool = False) -> None:
    if non_empty and not values:
        raise ValueError(f"{label} must be non-empty")
    if any(not value.strip() for value in values):
        raise ValueError(f"{label} references must be non-blank")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} references are not allowed")


class WebChannelKind(str, Enum):
    TELEGRAM = "TELEGRAM"
    MAX = "MAX"


class WebChannelNotificationPreferenceState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED_BY_USER = "DISABLED_BY_USER"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebChannelSurfaceState(str, Enum):
    NOT_CONNECTED = "NOT_CONNECTED"
    LINK_CHALLENGE_REQUIRED = "LINK_CHALLENGE_REQUIRED"
    LINKED_ENABLED = "LINKED_ENABLED"
    LINKED_DISABLED_BY_USER = "LINKED_DISABLED_BY_USER"
    LINKED_TARGET_UNVERIFIED = "LINKED_TARGET_UNVERIFIED"
    LINKED_TARGET_UNAVAILABLE = "LINKED_TARGET_UNAVAILABLE"
    FUTURE_GATED = "FUTURE_GATED"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebChannelSurfaceResultState(str, Enum):
    AVAILABLE = "AVAILABLE"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebChannelCommandKind(str, Enum):
    START_CONNECTION = "START_CONNECTION"
    ENABLE_NOTIFICATIONS = "ENABLE_NOTIFICATIONS"
    DISABLE_NOTIFICATIONS = "DISABLE_NOTIFICATIONS"


class WebChannelCommandSubmitState(str, Enum):
    SUBMITTED = "SUBMITTED"
    REPLAYED = "REPLAYED"
    REJECTED = "REJECTED"
    FORBIDDEN = "FORBIDDEN"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


_ADAPTER_BY_CHANNEL = {
    WebChannelKind.TELEGRAM: TELEGRAM_ADAPTER_MODULE_ID,
    WebChannelKind.MAX: MAX_ADAPTER_MODULE_ID,
}


class RequestWebChannelSurfaceQuery(_WebChannelLinkingContract):
    web_channel_surface_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    requested_audience: WebViewAudience
    requested_channels: tuple[WebChannelKind, ...]
    channel_read_policy_reference_id: _NonEmptyReferenceId
    identity_link_policy_reference_id: _NonEmptyReferenceId
    notification_preference_policy_reference_id: _NonEmptyReferenceId
    freshness_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_actor_required: Literal[True] = True
    account_scope_required: Literal[True] = True
    read_only: Literal[True] = True
    identity_authority_required: Literal[True] = True
    adapter_authority_required: Literal[True] = True
    notification_authority_required: Literal[True] = True
    client_identity_authority: Literal[False] = False
    client_link_authority: Literal[False] = False
    client_preference_authority: Literal[False] = False
    browser_state_authority: Literal[False] = False
    provider_identifier_requested: Literal[False] = False
    raw_link_requested: Literal[False] = False
    raw_mini_app_data_requested: Literal[False] = False
    telegram_runtime_capability_requested: Literal[False] = False
    runtime_execution_requested: Literal[False] = False
    direct_foreign_state_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    retention_policy_defined: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebChannelSurfaceQuery":
        if not self.requested_channels or len(set(self.requested_channels)) != len(
            self.requested_channels
        ):
            raise ValueError("requested channels must be non-empty and unique")
        return self


class WebChannelSurfaceProjection(_WebChannelLinkingContract):
    web_channel_surface_projection_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    channel: WebChannelKind
    state: WebChannelSurfaceState
    preference_state: WebChannelNotificationPreferenceState
    freshness: WebReadFreshness
    owning_adapter_module_id: _NonEmptyReferenceId
    adapter_projection_reference_id: _NonEmptyReferenceId
    adapter_eligibility_reference_id: _NonEmptyReferenceId | None = None
    adapter_runtime_gate_safe_reference_id: _NonEmptyReferenceId | None = None
    provider_identity_safe_reference_id: _NonEmptyReferenceId | None = None
    adapter_account_link_reference_id: _NonEmptyReferenceId | None = None
    identity_decision_reference_id: _NonEmptyReferenceId | None = None
    identity_account_reference_id: _NonEmptyReferenceId | None = None
    identity_link_challenge_reference_id: _NonEmptyReferenceId | None = None
    notification_channel_gate_decision_reference_id: _NonEmptyReferenceId | None = None
    notification_target_safe_reference_id: _NonEmptyReferenceId | None = None
    notification_push_eligible: bool
    safe_start_connection_action_reference_id: _NonEmptyReferenceId | None = None
    safe_enable_notifications_action_reference_id: _NonEmptyReferenceId | None = None
    safe_disable_notifications_action_reference_id: _NonEmptyReferenceId | None = None
    safe_cross_interface_return_reference_id: _NonEmptyReferenceId | None = None
    safe_mini_app_surface_reference_id: _NonEmptyReferenceId | None = None
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    safe_projection_only: Literal[True] = True
    same_internal_account_required: Literal[True] = True
    identity_authoritative: Literal[True] = True
    adapter_provider_mapping_authoritative: Literal[True] = True
    notification_preference_authoritative: Literal[True] = True
    telegram_runtime_gate_reference_only: Literal[True] = True
    web_identity_authority: Literal[False] = False
    web_link_authority: Literal[False] = False
    web_preference_authority: Literal[False] = False
    web_target_authority: Literal[False] = False
    web_runtime_authority: Literal[False] = False
    provider_identifier_present: Literal[False] = False
    raw_link_present: Literal[False] = False
    raw_mini_app_data_present: Literal[False] = False
    runtime_capability_present: Literal[False] = False
    runtime_execution_authority: Literal[False] = False
    weak_correlation_link_allowed: Literal[False] = False
    automatic_account_merge_allowed: Literal[False] = False
    phone_requirement_defined: Literal[False] = False
    provider_call_authority: Literal[False] = False
    direct_mutation_authority: Literal[False] = False
    business_success_authority: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True

    @model_validator(mode="after")
    def _validate_projection(self) -> "WebChannelSurfaceProjection":
        if self.owning_adapter_module_id != _ADAPTER_BY_CHANNEL[self.channel]:
            raise ValueError("adapter owner does not match channel")
        _validate_references(self.source_reference_ids, "source", non_empty=True)
        _validate_references(self.evidence_reference_ids, "evidence", non_empty=True)
        refs = (
            self.safe_start_connection_action_reference_id,
            self.safe_enable_notifications_action_reference_id,
            self.safe_disable_notifications_action_reference_id,
        )
        present = tuple(ref for ref in refs if ref is not None)
        if len(present) > 1:
            raise ValueError("at most one channel action is allowed")
        linked = {
            WebChannelSurfaceState.LINKED_ENABLED,
            WebChannelSurfaceState.LINKED_DISABLED_BY_USER,
            WebChannelSurfaceState.LINKED_TARGET_UNVERIFIED,
            WebChannelSurfaceState.LINKED_TARGET_UNAVAILABLE,
        }
        if (
            self.state not in {WebChannelSurfaceState.STALE, WebChannelSurfaceState.AMBIGUOUS}
            and self.freshness is not WebReadFreshness.FRESH
        ):
            raise ValueError("only stale or ambiguous states may use non-fresh freshness")
        if self.state is WebChannelSurfaceState.STALE and (
            self.freshness is not WebReadFreshness.STALE
            or self.preference_state is not WebChannelNotificationPreferenceState.STALE
            or present
        ):
            raise ValueError("stale state matrix mismatch")
        if self.state is WebChannelSurfaceState.AMBIGUOUS and (
            self.freshness is not WebReadFreshness.AMBIGUOUS
            or self.preference_state is not WebChannelNotificationPreferenceState.AMBIGUOUS
            or self.ambiguity_reference_id is None
            or present
        ):
            raise ValueError("ambiguous state matrix mismatch")
        if (
            self.state is not WebChannelSurfaceState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("only ambiguous state may carry ambiguity reference")
        if (
            self.state is WebChannelSurfaceState.UNSUPPORTED
            and self.preference_state is not WebChannelNotificationPreferenceState.UNSUPPORTED
        ):
            raise ValueError("unsupported state requires unsupported preference")
        if self.state is WebChannelSurfaceState.UNSUPPORTED and (
            present or self.notification_push_eligible
        ):
            raise ValueError("unsupported state cannot carry actions or push eligibility")
        if self.state is WebChannelSurfaceState.NOT_CONNECTED:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.NOT_APPLICABLE,
                not any(
                    (
                        self.provider_identity_safe_reference_id,
                        self.adapter_account_link_reference_id,
                        self.identity_decision_reference_id,
                        self.identity_account_reference_id,
                        self.identity_link_challenge_reference_id,
                        self.notification_channel_gate_decision_reference_id,
                        self.notification_target_safe_reference_id,
                    )
                ),
                self.notification_push_eligible is False,
                self.safe_start_connection_action_reference_id is not None
                and not any(
                    (
                        self.safe_enable_notifications_action_reference_id,
                        self.safe_disable_notifications_action_reference_id,
                    )
                ),
            )
        elif self.state is WebChannelSurfaceState.LINK_CHALLENGE_REQUIRED:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.NOT_APPLICABLE,
                self.provider_identity_safe_reference_id is not None
                and self.identity_decision_reference_id is not None
                and self.identity_link_challenge_reference_id is not None,
                self.adapter_account_link_reference_id is None
                and self.identity_account_reference_id is None,
                self.notification_channel_gate_decision_reference_id is None
                and self.notification_target_safe_reference_id is None,
                self.notification_push_eligible is False,
                self.safe_start_connection_action_reference_id is not None,
            )
        elif self.state is WebChannelSurfaceState.FUTURE_GATED:
            self._require_exact(
                self.channel is WebChannelKind.MAX,
                self.adapter_eligibility_reference_id is not None,
                self.preference_state is WebChannelNotificationPreferenceState.NOT_APPLICABLE,
                not any(
                    (
                        self.identity_decision_reference_id,
                        self.identity_account_reference_id,
                        self.identity_link_challenge_reference_id,
                        self.notification_channel_gate_decision_reference_id,
                        self.notification_target_safe_reference_id,
                        *refs,
                    )
                ),
                self.notification_push_eligible is False,
            )
        elif self.state is WebChannelSurfaceState.BLOCKED:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.NOT_APPLICABLE,
                not present,
                self.notification_push_eligible is False,
            )
        elif self.state not in {
            WebChannelSurfaceState.STALE,
            WebChannelSurfaceState.AMBIGUOUS,
            WebChannelSurfaceState.UNSUPPORTED,
        }:
            self._validate_linked(linked)
        if (self.adapter_account_link_reference_id is None) != (
            self.identity_account_reference_id is None
        ):
            raise ValueError(
                "adapter account-link and Identity account references must appear together"
            )
        if self.state in linked and self.identity_link_challenge_reference_id is not None:
            raise ValueError("linked states cannot carry a challenge")
        if self.notification_push_eligible is not (
            self.state is WebChannelSurfaceState.LINKED_ENABLED
        ):
            raise ValueError("only linked enabled may be push eligible")
        return self

    def _require_exact(self, *conditions: bool) -> None:
        if not all(conditions):
            raise ValueError("channel surface state matrix mismatch")

    def _validate_linked(self, linked: set[WebChannelSurfaceState]) -> None:
        if self.state not in linked:
            return
        required = (
            self.provider_identity_safe_reference_id,
            self.adapter_account_link_reference_id,
            self.identity_decision_reference_id,
            self.identity_account_reference_id,
            self.notification_channel_gate_decision_reference_id,
        )
        if any(ref is None for ref in required):
            raise ValueError("linked states require Identity, adapter and Notification references")
        if self.state is WebChannelSurfaceState.LINKED_ENABLED:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.ENABLED,
                self.notification_target_safe_reference_id is not None,
                self.safe_disable_notifications_action_reference_id is not None,
                self.notification_push_eligible is True,
                not any(
                    (
                        self.safe_start_connection_action_reference_id,
                        self.safe_enable_notifications_action_reference_id,
                    )
                ),
            )
        elif self.state is WebChannelSurfaceState.LINKED_DISABLED_BY_USER:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.DISABLED_BY_USER,
                self.notification_push_eligible is False,
                self.safe_enable_notifications_action_reference_id is not None,
                not any(
                    (
                        self.safe_start_connection_action_reference_id,
                        self.safe_disable_notifications_action_reference_id,
                    )
                ),
            )
        elif self.state is WebChannelSurfaceState.LINKED_TARGET_UNVERIFIED:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.ENABLED,
                self.notification_target_safe_reference_id is None,
                self.notification_push_eligible is False,
                self.safe_start_connection_action_reference_id is not None,
                not any(
                    (
                        self.safe_enable_notifications_action_reference_id,
                        self.safe_disable_notifications_action_reference_id,
                    )
                ),
            )
        elif self.state is WebChannelSurfaceState.LINKED_TARGET_UNAVAILABLE:
            self._require_exact(
                self.preference_state is WebChannelNotificationPreferenceState.ENABLED,
                self.notification_target_safe_reference_id is not None,
                self.notification_push_eligible is False,
                not present_actions(self),
            )


def present_actions(projection: WebChannelSurfaceProjection) -> bool:
    return any(
        (
            projection.safe_start_connection_action_reference_id,
            projection.safe_enable_notifications_action_reference_id,
            projection.safe_disable_notifications_action_reference_id,
        )
    )


class WebChannelSurfaceResult(_WebChannelLinkingContract):
    web_channel_surface_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebChannelSurfaceQuery
    state: WebChannelSurfaceResultState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    channel_read_policy_reference_id: _NonEmptyReferenceId
    channel_projections: tuple[WebChannelSurfaceProjection, ...]
    linked_channel_count: int = Field(ge=0)
    push_eligible_channel_count: int = Field(ge=0)
    disabled_channel_count: int = Field(ge=0)
    future_gated_channel_count: int = Field(ge=0)
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    safe_presentation_boundary: Literal[True] = True
    single_account_boundary: Literal[True] = True
    identity_authoritative: Literal[True] = True
    adapters_authoritative: Literal[True] = True
    notification_authoritative: Literal[True] = True
    eligible_channel_set_from_notification: Literal[True] = True
    telegram_runtime_gate_reference_only: Literal[True] = True
    web_foreign_authority: Literal[False] = False
    runtime_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    direct_write_authority: Literal[False] = False
    business_success_authority: Literal[False] = False
    raw_provider_data_present: Literal[False] = False
    raw_link_data_present: Literal[False] = False
    raw_mini_app_data_present: Literal[False] = False
    automatic_account_merge_allowed: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True

    @model_validator(mode="after")
    def _validate_result(self) -> "WebChannelSurfaceResult":
        if (
            self.owning_module_id != WEB_CABINET_MODULE_ID
            or self.channel_read_policy_reference_id != self.query.channel_read_policy_reference_id
        ):
            raise ValueError("result owner or policy mismatch")
        _validate_references(self.source_reference_ids, "source", non_empty=True)
        _validate_references(self.evidence_reference_ids, "evidence", non_empty=True)
        if len({p.web_channel_surface_projection_id for p in self.channel_projections}) != len(
            self.channel_projections
        ) or len({p.channel for p in self.channel_projections}) != len(self.channel_projections):
            raise ValueError("projection IDs and channels must be unique")
        if self.state not in {
            WebChannelSurfaceResultState.FORBIDDEN,
            WebChannelSurfaceResultState.NOT_FOUND_SAFE,
        } and (
            {p.channel for p in self.channel_projections}
            != set(self.query.requested_channels)
            or any(p.account_id != self.query.account_id for p in self.channel_projections)
        ):
            raise ValueError("projections must exactly cover the requested single account")
        if any(
            p.owning_adapter_module_id != _ADAPTER_BY_CHANNEL[p.channel]
            for p in self.channel_projections
        ):
            raise ValueError("projection adapter owner mismatch")
        linked = {
            WebChannelSurfaceState.LINKED_ENABLED,
            WebChannelSurfaceState.LINKED_DISABLED_BY_USER,
            WebChannelSurfaceState.LINKED_TARGET_UNVERIFIED,
            WebChannelSurfaceState.LINKED_TARGET_UNAVAILABLE,
        }
        if (
            self.linked_channel_count != sum(p.state in linked for p in self.channel_projections)
            or self.push_eligible_channel_count
            != sum(p.notification_push_eligible for p in self.channel_projections)
            or self.disabled_channel_count
            != sum(
                p.state is WebChannelSurfaceState.LINKED_DISABLED_BY_USER
                for p in self.channel_projections
            )
            or self.future_gated_channel_count
            != sum(p.state is WebChannelSurfaceState.FUTURE_GATED for p in self.channel_projections)
        ):
            raise ValueError("result counts do not match projections")
        states = {p.state for p in self.channel_projections}
        if (
            self.state is WebChannelSurfaceResultState.NOT_FOUND_SAFE
            and self.freshness is not WebReadFreshness.FRESH
        ):
            raise ValueError("not-found-safe result requires fresh freshness")
        if (
            self.state is not WebChannelSurfaceResultState.STALE
            and self.freshness is WebReadFreshness.STALE
        ):
            raise ValueError("only stale result may use stale freshness")
        if (
            self.state is not WebChannelSurfaceResultState.AMBIGUOUS
            and self.freshness is WebReadFreshness.AMBIGUOUS
        ):
            raise ValueError("only ambiguous result may use ambiguous freshness")
        if (
            self.state is not WebChannelSurfaceResultState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("only ambiguous result may carry ambiguity reference")
        if self.state is WebChannelSurfaceResultState.AVAILABLE and (
            not self.channel_projections
            or self.freshness is not WebReadFreshness.FRESH
            or states
            & {
                WebChannelSurfaceState.STALE,
                WebChannelSurfaceState.AMBIGUOUS,
                WebChannelSurfaceState.UNSUPPORTED,
            }
        ):
            raise ValueError("available result matrix mismatch")
        if self.state in {
            WebChannelSurfaceResultState.FORBIDDEN,
            WebChannelSurfaceResultState.NOT_FOUND_SAFE,
        } and (
            self.channel_projections
            or any(
                (
                    self.linked_channel_count,
                    self.push_eligible_channel_count,
                    self.disabled_channel_count,
                    self.future_gated_channel_count,
                )
            )
            or self.ambiguity_reference_id is not None
        ):
            raise ValueError("empty result matrix mismatch")
        if self.state is WebChannelSurfaceResultState.STALE and (
            self.freshness is not WebReadFreshness.STALE
            or WebChannelSurfaceState.STALE not in states
        ):
            raise ValueError("stale result matrix mismatch")
        if self.state is WebChannelSurfaceResultState.AMBIGUOUS and (
            self.freshness is not WebReadFreshness.AMBIGUOUS
            or WebChannelSurfaceState.AMBIGUOUS not in states
            or self.ambiguity_reference_id is None
        ):
            raise ValueError("ambiguous result matrix mismatch")
        if (
            self.state is WebChannelSurfaceResultState.UNSUPPORTED
            and WebChannelSurfaceState.UNSUPPORTED not in states
        ):
            raise ValueError("unsupported result requires unsupported projection")
        return self


class SubmitWebChannelCommandCommand(_WebChannelLinkingContract):
    web_channel_command_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    idempotency_key: IdempotencyKey
    idempotency_scope: IdempotencyScope
    fingerprint: IdempotencyFingerprint
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    channel: WebChannelKind
    command_kind: WebChannelCommandKind
    requested_owning_module_id: _NonEmptyReferenceId
    current_channel_projection_reference_id: _NonEmptyReferenceId
    expected_source_version_reference_id: _NonEmptyReferenceId
    adapter_action_reference_id: _NonEmptyReferenceId | None = None
    adapter_runtime_gate_safe_reference_id: _NonEmptyReferenceId | None = None
    identity_link_contract_reference_id: _NonEmptyReferenceId | None = None
    identity_decision_reference_id: _NonEmptyReferenceId | None = None
    notification_preference_contract_reference_id: _NonEmptyReferenceId | None = None
    notification_channel_gate_decision_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    verified_actor_account_server_validation: Literal[True] = True
    web_draft_client_identity_authority: Literal[False] = False
    web_draft_client_link_authority: Literal[False] = False
    web_draft_client_preference_authority: Literal[False] = False
    direct_identity_adapter_notification_write_authority: Literal[False] = False
    runtime_gate_reference_only: Literal[True] = True
    runtime_capability_requested: Literal[False] = False
    runtime_execution_requested: Literal[False] = False
    provider_authority: Literal[False] = False
    raw_provider_data_present: Literal[False] = False
    raw_link_data_present: Literal[False] = False
    raw_mini_app_data_present: Literal[False] = False
    account_merge_authority: Literal[False] = False
    phone_requirement_defined: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_command(self) -> "SubmitWebChannelCommandCommand":
        if self.command_kind is WebChannelCommandKind.START_CONNECTION:
            if (
                self.requested_owning_module_id != _ADAPTER_BY_CHANNEL[self.channel]
                or self.adapter_action_reference_id is None
                or self.identity_link_contract_reference_id is None
                or self.notification_preference_contract_reference_id is not None
                or self.notification_channel_gate_decision_reference_id is not None
            ):
                raise ValueError("start connection routing matrix mismatch")
            if self.channel is WebChannelKind.MAX and self.adapter_action_reference_id is None:
                raise ValueError("MAX requires adapter-approved opaque action")
        else:
            if (
                self.requested_owning_module_id != NOTIFICATION_DELIVERY_MODULE_ID
                or self.identity_decision_reference_id is None
                or self.notification_preference_contract_reference_id is None
                or self.notification_channel_gate_decision_reference_id is None
                or any(
                    (
                        self.adapter_action_reference_id,
                        self.adapter_runtime_gate_safe_reference_id,
                        self.identity_link_contract_reference_id,
                    )
                )
            ):
                raise ValueError("preference command routing matrix mismatch")
        return self


class WebChannelCommandSubmitOutcome(_WebChannelLinkingContract):
    web_channel_command_submit_outcome_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    command: SubmitWebChannelCommandCommand
    state: WebChannelCommandSubmitState
    owning_module_id: _NonEmptyReferenceId
    owning_command_reference_id: _NonEmptyReferenceId | None = None
    replayed_outcome_reference_id: _NonEmptyReferenceId | None = None
    safe_owning_outcome_reference_id: _NonEmptyReferenceId | None = None
    reconciliation_reference_id: _NonEmptyReferenceId | None = None
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    safe_status_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    safe_outcome: Literal[True] = True
    owning_module_authority: Literal[True] = True
    web_submission_only_authority: Literal[True] = True
    runtime_gate_reference_only: Literal[True] = True
    runtime_gate_satisfied: Literal[False] = False
    runtime_execution_completed: Literal[False] = False
    link_established: Literal[False] = False
    preference_applied: Literal[False] = False
    target_verified: Literal[False] = False
    provider_operation_completed: Literal[False] = False
    user_receipt_confirmed: Literal[False] = False
    business_success_authority: Literal[False] = False
    direct_write_authority: Literal[False] = False
    provider_authority: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    secret_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome(self) -> "WebChannelCommandSubmitOutcome":
        if self.owning_module_id != self.command.requested_owning_module_id:
            raise ValueError("outcome owner must match command owner")
        if (
            self.state is not WebChannelCommandSubmitState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("only ambiguous outcome may carry ambiguity reference")
        if (
            self.state is not WebChannelCommandSubmitState.RECONCILIATION_REQUIRED
            and self.reconciliation_reference_id is not None
        ):
            raise ValueError(
                "only reconciliation-required outcome may carry reconciliation reference"
            )
        if self.state is WebChannelCommandSubmitState.SUBMITTED and (
            self.owning_command_reference_id is None
            or self.safe_owning_outcome_reference_id is None
            or any(
                (
                    self.replayed_outcome_reference_id,
                    self.reconciliation_reference_id,
                    self.ambiguity_reference_id,
                )
            )
        ):
            raise ValueError("submitted outcome matrix mismatch")
        if self.state is WebChannelCommandSubmitState.REPLAYED and (
            self.replayed_outcome_reference_id is None
            or self.safe_owning_outcome_reference_id is None
            or any(
                (
                    self.owning_command_reference_id,
                    self.reconciliation_reference_id,
                    self.ambiguity_reference_id,
                )
            )
        ):
            raise ValueError("replayed outcome matrix mismatch")
        if self.state is WebChannelCommandSubmitState.RECONCILIATION_REQUIRED and (
            self.reconciliation_reference_id is None
            or any((self.replayed_outcome_reference_id, self.ambiguity_reference_id))
        ):
            raise ValueError("reconciliation outcome matrix mismatch")
        if self.state is WebChannelCommandSubmitState.AMBIGUOUS and (
            self.ambiguity_reference_id is None
            or any((self.replayed_outcome_reference_id, self.reconciliation_reference_id))
        ):
            raise ValueError("ambiguous outcome matrix mismatch")
        if (
            self.state
            not in {WebChannelCommandSubmitState.SUBMITTED, WebChannelCommandSubmitState.REPLAYED}
            and self.owning_command_reference_id is not None
        ):
            raise ValueError("non-accepting outcome cannot claim owning acceptance")
        if self.state not in {
            WebChannelCommandSubmitState.SUBMITTED,
            WebChannelCommandSubmitState.REPLAYED,
        } and (
            self.replayed_outcome_reference_id is not None
            or self.safe_owning_outcome_reference_id is not None
        ):
            raise ValueError("non-corresponding outcome cannot carry owning outcome references")
        if (
            self.state is not WebChannelCommandSubmitState.REPLAYED
            and self.replayed_outcome_reference_id is not None
        ):
            raise ValueError("only replayed outcome may carry replay reference")
        return self


__all__ = [
    "RequestWebChannelSurfaceQuery",
    "SubmitWebChannelCommandCommand",
    "WebChannelCommandKind",
    "WebChannelCommandSubmitOutcome",
    "WebChannelCommandSubmitState",
    "WebChannelKind",
    "WebChannelNotificationPreferenceState",
    "WebChannelSurfaceProjection",
    "WebChannelSurfaceResult",
    "WebChannelSurfaceResultState",
    "WebChannelSurfaceState",
]
