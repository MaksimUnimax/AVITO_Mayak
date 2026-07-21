"""Transport-neutral Web Cabinet read-model composition contracts."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.platform.boundaries import (
    ADMIN_AND_SUPPORT_MODULE_ID,
    BEACON_MANAGEMENT_MODULE_ID,
    ENTITLEMENTS_AND_BILLING_MODULE_ID,
    IDENTITY_AND_ACCESS_MODULE_ID,
    MAX_ADAPTER_MODULE_ID,
    NOTIFICATION_DELIVERY_MODULE_ID,
    SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
    TELEGRAM_ADAPTER_MODULE_ID,
    WEB_CABINET_MODULE_ID,
)


class _WebReadModelContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class WebViewAudience(str, Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN_AUTHORIZED = "ADMIN_AUTHORIZED"


class WebReadModelFamily(str, Enum):
    ACCOUNT_SUMMARY = "ACCOUNT_SUMMARY"
    ACTIVE_BEACONS = "ACTIVE_BEACONS"
    BEACON_HISTORY = "BEACON_HISTORY"
    TARIFF_ACCESS_LIMITS = "TARIFF_ACCESS_LIMITS"
    LAST_SCAN_STATUS = "LAST_SCAN_STATUS"
    MESSAGE_RESULT_HISTORY = "MESSAGE_RESULT_HISTORY"
    TELEGRAM_CHANNEL = "TELEGRAM_CHANNEL"
    MAX_CHANNEL = "MAX_CHANNEL"
    CUSTOMER_SUPPORT_STATUS = "CUSTOMER_SUPPORT_STATUS"
    ADMIN_ANALYTICS_PLACEHOLDER = "ADMIN_ANALYTICS_PLACEHOLDER"


class WebReadFreshness(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class WebSourceState(str, Enum):
    AVAILABLE = "AVAILABLE"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


class WebCabinetViewState(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"


_FAMILY_OWNERS: dict[WebReadModelFamily, str] = {
    WebReadModelFamily.ACCOUNT_SUMMARY: IDENTITY_AND_ACCESS_MODULE_ID,
    WebReadModelFamily.ACTIVE_BEACONS: BEACON_MANAGEMENT_MODULE_ID,
    WebReadModelFamily.BEACON_HISTORY: BEACON_MANAGEMENT_MODULE_ID,
    WebReadModelFamily.TARIFF_ACCESS_LIMITS: ENTITLEMENTS_AND_BILLING_MODULE_ID,
    WebReadModelFamily.LAST_SCAN_STATUS: SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
    WebReadModelFamily.MESSAGE_RESULT_HISTORY: NOTIFICATION_DELIVERY_MODULE_ID,
    WebReadModelFamily.TELEGRAM_CHANNEL: TELEGRAM_ADAPTER_MODULE_ID,
    WebReadModelFamily.MAX_CHANNEL: MAX_ADAPTER_MODULE_ID,
    WebReadModelFamily.CUSTOMER_SUPPORT_STATUS: ADMIN_AND_SUPPORT_MODULE_ID,
    WebReadModelFamily.ADMIN_ANALYTICS_PLACEHOLDER: WEB_CABINET_MODULE_ID,
}


def _reject_duplicate_ids(values: tuple[str, ...], label: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{label} identifiers must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} identifiers are not allowed")


def _reject_duplicate_families(values: tuple[WebReadModelFamily, ...]) -> None:
    if len(values) != len(set(values)):
        raise ValueError("duplicate read-model families are not allowed")


class WebReadModelSourceReference(_WebReadModelContract):
    web_source_reference_id: _NonEmptyReferenceId
    family: WebReadModelFamily
    owning_module_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    state: WebSourceState
    freshness: WebReadFreshness
    safe_projection_reference_id: _NonEmptyReferenceId | None = None
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    reason_code: _NonEmptyReferenceId
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    redaction_policy_reference_id: _NonEmptyReferenceId
    safe_reference_only: Literal[True] = True
    redacted: Literal[True] = True
    minimal_personal_data: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    full_private_message_retained: Literal[False] = False
    full_listing_archive_retained: Literal[False] = False
    mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_source(self) -> "WebReadModelSourceReference":
        if self.owning_module_id != _FAMILY_OWNERS[self.family]:
            raise ValueError("read-model family owning module does not match")
        if self.state in {
            WebSourceState.AVAILABLE,
            WebSourceState.REDACTED,
            WebSourceState.STALE,
        } and (self.safe_projection_reference_id is None or not self.provenance_reference_ids):
            raise ValueError(
                "available, redacted and stale sources require projection and provenance"
            )
        if self.state in {
            WebSourceState.FORBIDDEN,
            WebSourceState.NOT_FOUND_SAFE,
            WebSourceState.UNKNOWN,
            WebSourceState.POLICY_BLOCKED,
            WebSourceState.UNSUPPORTED,
        } and self.safe_projection_reference_id is not None:
            raise ValueError("this source state cannot carry a safe projection")
        if self.safe_projection_reference_id is not None and not self.provenance_reference_ids:
            raise ValueError("safe projection reference requires provenance")
        if self.state is WebSourceState.STALE and self.freshness is not WebReadFreshness.STALE:
            raise ValueError("stale source requires stale freshness")
        if self.state is WebSourceState.UNKNOWN and self.freshness is not WebReadFreshness.UNKNOWN:
            raise ValueError("unknown source requires unknown freshness")
        if self.state is WebSourceState.AMBIGUOUS:
            if self.ambiguity_reference_id is None:
                raise ValueError("ambiguous source requires ambiguity reference")
        elif self.ambiguity_reference_id is not None:
            raise ValueError("non-ambiguous source cannot carry ambiguity reference")
        if self.family is WebReadModelFamily.ADMIN_ANALYTICS_PLACEHOLDER and self.state not in {
            WebSourceState.POLICY_BLOCKED,
            WebSourceState.UNSUPPORTED,
        }:
            raise ValueError("analytics placeholder is policy-blocked or unsupported only")
        _reject_duplicate_ids(self.provenance_reference_ids, "provenance")
        return self


class RequestWebCabinetViewQuery(_WebReadModelContract):
    web_cabinet_view_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    audience: WebViewAudience
    requested_families: tuple[WebReadModelFamily, ...]
    view_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_actor_required: Literal[True] = True
    read_only: Literal[True] = True
    client_state_authority: Literal[False] = False
    direct_write_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    raw_resource_access_authority: Literal[False] = False
    foreign_host_access_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebCabinetViewQuery":
        if not self.requested_families:
            raise ValueError("requested families must be non-empty")
        _reject_duplicate_families(self.requested_families)
        if (
            WebReadModelFamily.ADMIN_ANALYTICS_PLACEHOLDER in self.requested_families
            and self.audience is not WebViewAudience.ADMIN_AUTHORIZED
        ):
            raise ValueError("analytics placeholder requires admin audience")
        return self


class WebCabinetViewResult(_WebReadModelContract):
    web_cabinet_view_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebCabinetViewQuery
    state: WebCabinetViewState
    freshness: WebReadFreshness
    sources: tuple[WebReadModelSourceReference, ...]
    composition_policy_reference_id: _NonEmptyReferenceId
    redaction_policy_reference_id: _NonEmptyReferenceId
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    provenance_aware: Literal[True] = True
    freshness_aware: Literal[True] = True
    ownership_scoped: Literal[True] = True
    authorization_required: Literal[True] = True
    redacted: Literal[True] = True
    minimal_personal_data: Literal[True] = True
    contains_secret_material: Literal[False] = False
    raw_provider_payload_retained: Literal[False] = False
    full_private_message_retained: Literal[False] = False
    full_listing_archive_retained: Literal[False] = False
    mutation_authority: Literal[False] = False
    provider_call_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebCabinetViewResult":
        source_ids = tuple(source.web_source_reference_id for source in self.sources)
        source_families = tuple(source.family for source in self.sources)
        _reject_duplicate_ids(source_ids, "source")
        _reject_duplicate_families(source_families)
        requested = set(self.query.requested_families)
        if any(source.family not in requested for source in self.sources):
            raise ValueError("source family was not requested")
        if any(
            source.account_id != self.query.account_id
            or source.tenant_scope_reference_id != self.query.tenant_scope_reference_id
            for source in self.sources
        ):
            raise ValueError("source account and tenant scope must match query")
        states = {source.state for source in self.sources}
        if self.state is WebCabinetViewState.AUTHORIZED and (
            not self.sources or states != {WebSourceState.AVAILABLE}
        ):
            raise ValueError("authorized result requires available sources")
        if self.state is WebCabinetViewState.REDACTED and (
            not self.sources
            or WebSourceState.REDACTED not in states
            or states & {
                WebSourceState.FORBIDDEN,
                WebSourceState.UNKNOWN,
                WebSourceState.AMBIGUOUS,
                WebSourceState.POLICY_BLOCKED,
                WebSourceState.UNSUPPORTED,
            }
        ):
            raise ValueError("redacted result requires safe redacted sources")
        if self.state is WebCabinetViewState.STALE and (
            self.freshness is not WebReadFreshness.STALE
            or not self.sources
            or WebSourceState.STALE not in states
        ):
            raise ValueError("stale result requires stale freshness and source")
        if self.state in {WebCabinetViewState.FORBIDDEN, WebCabinetViewState.NOT_FOUND_SAFE} and (
            self.sources or self.ambiguity_reference_id is not None
        ):
            raise ValueError("forbidden or not-found-safe result cannot carry sources")
        ambiguity_states = {
            WebSourceState.UNKNOWN,
            WebSourceState.AMBIGUOUS,
            WebSourceState.POLICY_BLOCKED,
            WebSourceState.UNSUPPORTED,
        }
        if self.state is WebCabinetViewState.AMBIGUOUS and (
            self.ambiguity_reference_id is None or not states & ambiguity_states
        ):
            raise ValueError("ambiguous result requires ambiguity reference and unresolved source")
        if (
            self.state is not WebCabinetViewState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("non-ambiguous result cannot carry ambiguity reference")
        if self.freshness is WebReadFreshness.FRESH and any(
            source.freshness is not WebReadFreshness.FRESH for source in self.sources
        ):
            raise ValueError("fresh result cannot contain non-fresh sources")
        if self.freshness is WebReadFreshness.STALE and WebSourceState.STALE not in states:
            raise ValueError("stale freshness requires stale source")
        if self.freshness is WebReadFreshness.UNKNOWN and not states & {
            WebSourceState.UNKNOWN,
            WebSourceState.POLICY_BLOCKED,
            WebSourceState.UNSUPPORTED,
        }:
            raise ValueError("unknown freshness requires unknown or blocked source")
        if self.freshness is WebReadFreshness.AMBIGUOUS and WebSourceState.AMBIGUOUS not in states:
            raise ValueError("ambiguous freshness requires ambiguous source")
        return self


__all__ = [
    "RequestWebCabinetViewQuery",
    "WebCabinetViewResult",
    "WebCabinetViewState",
    "WebReadFreshness",
    "WebReadModelFamily",
    "WebReadModelSourceReference",
    "WebSourceState",
    "WebViewAudience",
]
