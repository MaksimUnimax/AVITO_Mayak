"""Transport-neutral Web Cabinet entitlement and tariff projections."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebReadFreshness
from mayak.platform.boundaries import ENTITLEMENTS_AND_BILLING_MODULE_ID


class _WebEntitlementProjectionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class WebEntitlementAccessState(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebTariffOptionState(str, Enum):
    CURRENT = "CURRENT"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class WebEntitlementProjectionState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"
    USER_CHOICE_REQUIRED = "USER_CHOICE_REQUIRED"
    FREE_COMPLIANCE_REQUIRED = "FREE_COMPLIANCE_REQUIRED"
    CONFLICT = "CONFLICT"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


def _reject_duplicate_references(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} references must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} references are not allowed")


class RequestWebEntitlementProjectionQuery(_WebEntitlementProjectionContract):
    web_entitlement_projection_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    requested_capability_reference_ids: tuple[_NonEmptyReferenceId, ...]
    include_tariff_options: bool
    entitlement_evaluation_policy_reference_id: _NonEmptyReferenceId
    tariff_visibility_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_actor_required: Literal[True] = True
    account_scope_required: Literal[True] = True
    read_only: Literal[True] = True
    entitlements_authority_required: Literal[True] = True
    client_entitlement_authority: Literal[False] = False
    client_tariff_authority: Literal[False] = False
    web_entitlement_evaluator: Literal[False] = False
    direct_entitlement_write_authority: Literal[False] = False
    subscription_mutation_authority: Literal[False] = False
    grant_mutation_authority: Literal[False] = False
    payment_mutation_authority: Literal[False] = False
    usage_counter_mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    payment_response_is_entitlement_authority: Literal[False] = False
    invented_tariff_values_allowed: Literal[False] = False
    raw_payment_payload_present: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebEntitlementProjectionQuery":
        if not self.requested_capability_reference_ids:
            raise ValueError("requested capability references must be non-empty")
        _reject_duplicate_references(self.requested_capability_reference_ids, "capability")
        return self


class WebEntitlementCapabilityProjection(_WebEntitlementProjectionContract):
    web_entitlement_capability_projection_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    capability_reference_id: _NonEmptyReferenceId
    access_state: WebEntitlementAccessState
    effective_entitlement_decision_reference_id: _NonEmptyReferenceId
    safe_limit_display_reference_id: _NonEmptyReferenceId | None = None
    effective_interval_reference_id: _NonEmptyReferenceId | None = None
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    reason_code: _NonEmptyReferenceId
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    derived_from_entitlements: Literal[True] = True
    safe_reference_only: Literal[True] = True
    web_recomputed: Literal[False] = False
    web_limit_authority: Literal[False] = False
    raw_limit_value_retained: Literal[False] = False
    payment_evidence_authority: Literal[False] = False
    raw_payment_payload_retained: Literal[False] = False
    direct_mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_capability(self) -> "WebEntitlementCapabilityProjection":
        _reject_duplicate_references(self.source_reference_ids, "source")
        if self.access_state is WebEntitlementAccessState.ALLOWED and not self.source_reference_ids:
            raise ValueError("allowed capability requires source references")
        if self.safe_limit_display_reference_id is not None and not self.source_reference_ids:
            raise ValueError("limit display reference requires source references")
        if self.effective_interval_reference_id is not None and not self.source_reference_ids:
            raise ValueError("interval reference requires source references")
        if self.access_state is WebEntitlementAccessState.AMBIGUOUS:
            if self.ambiguity_reference_id is None:
                raise ValueError("ambiguous capability requires ambiguity reference")
        elif self.ambiguity_reference_id is not None:
            raise ValueError("non-ambiguous capability cannot carry ambiguity reference")
        return self


class WebTariffOptionProjection(_WebEntitlementProjectionContract):
    web_tariff_option_projection_id: _NonEmptyReferenceId
    owning_module_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    tariff_definition_reference_id: _NonEmptyReferenceId
    semantic_version_reference_id: _NonEmptyReferenceId
    state: WebTariffOptionState
    safe_name_display_reference_id: _NonEmptyReferenceId | None = None
    safe_price_display_reference_id: _NonEmptyReferenceId | None = None
    safe_billing_period_display_reference_id: _NonEmptyReferenceId | None = None
    safe_limit_summary_reference_ids: tuple[_NonEmptyReferenceId, ...]
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    reason_code: _NonEmptyReferenceId
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    approved_definition_reference_required: Literal[True] = True
    safe_display_references_only: Literal[True] = True
    web_tariff_authority: Literal[False] = False
    web_price_authority: Literal[False] = False
    web_limit_authority: Literal[False] = False
    payment_provider_authority: Literal[False] = False
    payment_response_is_entitlement_authority: Literal[False] = False
    raw_payment_payload_retained: Literal[False] = False
    future_tariff_invention_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    direct_mutation_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_option(self) -> "WebTariffOptionProjection":
        if self.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("tariff option must be owned by Entitlements and Billing")
        _reject_duplicate_references(self.source_reference_ids, "source")
        if not self.source_reference_ids:
            raise ValueError("tariff option requires source references")
        _reject_duplicate_references(self.safe_limit_summary_reference_ids, "limit summary")
        if self.state in {
            WebTariffOptionState.CURRENT,
            WebTariffOptionState.AVAILABLE,
            WebTariffOptionState.UNAVAILABLE,
        } and self.safe_name_display_reference_id is None:
            raise ValueError("visible tariff options require a safe name reference")
        if (
            self.safe_price_display_reference_id is not None
            or self.safe_billing_period_display_reference_id is not None
            or self.safe_limit_summary_reference_ids
        ) and not self.source_reference_ids:
            raise ValueError("display references require source references")
        if self.state in {
            WebTariffOptionState.POLICY_BLOCKED,
            WebTariffOptionState.AMBIGUOUS,
            WebTariffOptionState.UNSUPPORTED,
        } and (
            self.safe_price_display_reference_id is not None
            or self.safe_billing_period_display_reference_id is not None
            or self.safe_limit_summary_reference_ids
        ):
            raise ValueError("blocked or unresolved options cannot carry value display references")
        if self.state is WebTariffOptionState.AMBIGUOUS:
            if self.ambiguity_reference_id is None:
                raise ValueError("ambiguous option requires ambiguity reference")
        elif self.ambiguity_reference_id is not None:
            raise ValueError("non-ambiguous option cannot carry ambiguity reference")
        return self


class WebEntitlementProjectionResult(_WebEntitlementProjectionContract):
    web_entitlement_projection_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebEntitlementProjectionQuery
    state: WebEntitlementProjectionState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    effective_entitlement_summary_reference_id: _NonEmptyReferenceId
    current_tariff_definition_reference_id: _NonEmptyReferenceId | None = None
    capabilities: tuple[WebEntitlementCapabilityProjection, ...]
    tariff_options: tuple[WebTariffOptionProjection, ...]
    payment_upgrade_placeholder_reference_id: _NonEmptyReferenceId | None = None
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    safe_projection_only: Literal[True] = True
    entitlements_authoritative: Literal[True] = True
    web_entitlement_authority: Literal[False] = False
    web_tariff_definition_authority: Literal[False] = False
    effective_entitlement_recomputed_by_web: Literal[False] = False
    prices_limits_names_invented: Literal[False] = False
    subscription_mutation_authority: Literal[False] = False
    grant_mutation_authority: Literal[False] = False
    payment_mutation_authority: Literal[False] = False
    usage_counter_mutation_authority: Literal[False] = False
    direct_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    payment_provider_integration_present: Literal[False] = False
    payment_response_is_entitlement_authority: Literal[False] = False
    raw_payment_payload_retained: Literal[False] = False
    card_data_retained: Literal[False] = False
    minimal_personal_data: Literal[True] = True
    redacted: Literal[True] = True
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebEntitlementProjectionResult":
        if self.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("result must be owned by Entitlements and Billing")
        _reject_duplicate_references(self.source_reference_ids, "source")
        if not self.source_reference_ids:
            raise ValueError("result requires source references")
        capability_ids = tuple(
            item.web_entitlement_capability_projection_id for item in self.capabilities
        )
        capability_refs = tuple(item.capability_reference_id for item in self.capabilities)
        if len(capability_ids) != len(set(capability_ids)):
            raise ValueError("duplicate capability projection identifiers are not allowed")
        if len(capability_refs) != len(set(capability_refs)):
            raise ValueError("duplicate capability references are not allowed")
        if set(capability_refs) != set(self.query.requested_capability_reference_ids):
            raise ValueError("capability references must exactly match the query")
        option_ids = tuple(item.web_tariff_option_projection_id for item in self.tariff_options)
        option_refs = tuple(item.tariff_definition_reference_id for item in self.tariff_options)
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("duplicate tariff option identifiers are not allowed")
        if len(option_refs) != len(set(option_refs)):
            raise ValueError("duplicate tariff definition references are not allowed")
        if any(
            item.account_id != self.query.account_id
            for item in self.capabilities + self.tariff_options
        ):
            raise ValueError("projection account must match query account")
        current = tuple(
            item for item in self.tariff_options if item.state is WebTariffOptionState.CURRENT
        )
        if not self.query.include_tariff_options:
            if self.tariff_options or self.payment_upgrade_placeholder_reference_id is not None:
                raise ValueError("tariff options and payment placeholder were not requested")
        else:
            if len(current) > 1:
                raise ValueError("at most one current tariff option is allowed")
            if current and self.current_tariff_definition_reference_id != (
                current[0].tariff_definition_reference_id
            ):
                raise ValueError("current tariff reference must match current option")
            if self.current_tariff_definition_reference_id is not None and (
                len(current) != 1
                or current[0].tariff_definition_reference_id
                != self.current_tariff_definition_reference_id
            ):
                raise ValueError(
                    "current tariff reference requires exactly one matching current option"
                )
        if self.state is WebEntitlementProjectionState.AVAILABLE and (
            self.freshness is not WebReadFreshness.FRESH
            or not self.capabilities
            or any(
                item.access_state is not WebEntitlementAccessState.ALLOWED
                for item in self.capabilities
            )
        ):
            raise ValueError("available result requires fresh all-allowed capabilities")
        required_access = {
            WebEntitlementProjectionState.DENIED: WebEntitlementAccessState.DENIED,
            WebEntitlementProjectionState.BLOCKED: WebEntitlementAccessState.BLOCKED,
            WebEntitlementProjectionState.EXPIRED: WebEntitlementAccessState.EXPIRED,
            WebEntitlementProjectionState.USER_CHOICE_REQUIRED: (
                WebEntitlementAccessState.USER_CHOICE_REQUIRED
            ),
            WebEntitlementProjectionState.FREE_COMPLIANCE_REQUIRED: (
                WebEntitlementAccessState.FREE_COMPLIANCE_REQUIRED
            ),
            WebEntitlementProjectionState.CONFLICT: WebEntitlementAccessState.CONFLICT,
        }
        if self.state in required_access and not any(
            item.access_state is required_access[self.state] for item in self.capabilities
        ):
            raise ValueError("result state requires a matching capability state")
        if self.state is WebEntitlementProjectionState.UNSUPPORTED and not (
            any(
                item.access_state is WebEntitlementAccessState.UNSUPPORTED
                for item in self.capabilities
            )
            or any(item.state is WebTariffOptionState.UNSUPPORTED for item in self.tariff_options)
        ):
            raise ValueError("unsupported result requires unsupported capability or option")
        if self.state is WebEntitlementProjectionState.STALE and (
            self.freshness is not WebReadFreshness.STALE
        ):
            raise ValueError("stale result requires stale freshness")
        if self.freshness is WebReadFreshness.STALE and (
            self.state is not WebEntitlementProjectionState.STALE
        ):
            raise ValueError("only stale result may use stale freshness")
        ambiguous = any(
            item.access_state is WebEntitlementAccessState.AMBIGUOUS
            for item in self.capabilities
        ) or any(
            item.state is WebTariffOptionState.AMBIGUOUS for item in self.tariff_options
        )
        if self.state is WebEntitlementProjectionState.AMBIGUOUS:
            if (
                self.freshness is not WebReadFreshness.AMBIGUOUS
                or self.ambiguity_reference_id is None
                or not ambiguous
            ):
                raise ValueError(
                    "ambiguous result requires ambiguous freshness, reference and projection"
                )
        elif (
            self.freshness is WebReadFreshness.AMBIGUOUS
            or self.ambiguity_reference_id is not None
        ):
            raise ValueError("only ambiguous result may use ambiguous freshness or reference")
        if self.payment_upgrade_placeholder_reference_id is not None and (
            not self.query.include_tariff_options
            or not any(item.state is WebTariffOptionState.AVAILABLE for item in self.tariff_options)
        ):
            raise ValueError("payment placeholder requires requested available tariff option")
        return self


__all__ = [
    "RequestWebEntitlementProjectionQuery",
    "WebEntitlementAccessState",
    "WebEntitlementCapabilityProjection",
    "WebEntitlementProjectionResult",
    "WebEntitlementProjectionState",
    "WebTariffOptionProjection",
    "WebTariffOptionState",
]
