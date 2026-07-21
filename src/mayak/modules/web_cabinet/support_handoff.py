"""Transport-neutral customer-public support handoff projections."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebReadFreshness, WebViewAudience
from mayak.platform.boundaries import ADMIN_AND_SUPPORT_MODULE_ID, WEB_CABINET_MODULE_ID


class _WebSupportHandoffContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]


class WebSupportHandoffItemKind(str, Enum):
    SUPPORT_ENTRY = "SUPPORT_ENTRY"
    CASE_STATUS = "CASE_STATUS"
    PUBLIC_ANSWER = "PUBLIC_ANSWER"


class WebSupportHandoffItemState(str, Enum):
    AVAILABLE = "AVAILABLE"
    REDACTED = "REDACTED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"


class WebSupportHandoffResultState(str, Enum):
    AVAILABLE = "AVAILABLE"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND_SAFE = "NOT_FOUND_SAFE"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


def _unique_non_empty(values: tuple[str, ...], label: str) -> None:
    if not values or any(not value for value in values):
        raise ValueError(f"{label} references must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} references are not allowed")


def _required(value: str | None, label: str) -> None:
    if value is None:
        raise ValueError(f"{label} reference is required")


def _absent(value: str | None, label: str) -> None:
    if value is not None:
        raise ValueError(f"{label} reference is not allowed")


class RequestWebSupportHandoffQuery(_WebSupportHandoffContract):
    web_support_handoff_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    identity_authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    requested_audience: Literal[WebViewAudience.CUSTOMER] = WebViewAudience.CUSTOMER
    requested_item_kinds: tuple[WebSupportHandoffItemKind, ...]
    support_case_reference_id: _NonEmptyReferenceId | None = None
    web_support_handoff_policy_reference_id: _NonEmptyReferenceId
    admin_support_customer_read_policy_reference_id: _NonEmptyReferenceId
    customer_visibility_policy_reference_id: _NonEmptyReferenceId
    customer_publication_policy_reference_id: _NonEmptyReferenceId
    redaction_policy_reference_id: _NonEmptyReferenceId
    freshness_policy_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_customer_required: Literal[True] = True
    read_only: Literal[True] = True
    customer_publication_required: Literal[True] = True
    support_case_mutation_requested: Literal[False] = False
    operator_action_requested: Literal[False] = False
    internal_note_requested: Literal[False] = False
    private_audit_requested: Literal[False] = False
    raw_log_requested: Literal[False] = False
    provider_call_requested: Literal[False] = False
    raw_resource_access_requested: Literal[False] = False
    exact_customer_visibility_policy_invented: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebSupportHandoffQuery":
        if not self.requested_item_kinds:
            raise ValueError("requested item kinds must be non-empty")
        if len(self.requested_item_kinds) != len(set(self.requested_item_kinds)):
            raise ValueError("duplicate requested item kinds are not allowed")
        case_bound = {
            WebSupportHandoffItemKind.CASE_STATUS,
            WebSupportHandoffItemKind.PUBLIC_ANSWER,
        }
        if (
            case_bound.intersection(self.requested_item_kinds)
            and self.support_case_reference_id is None
        ):
            raise ValueError("case-bound kinds require a support case reference")
        if (
            self.requested_item_kinds == (WebSupportHandoffItemKind.SUPPORT_ENTRY,)
            and self.support_case_reference_id is not None
        ):
            raise ValueError("entry-only query cannot carry a support case reference")
        return self


class WebSupportHandoffProjection(_WebSupportHandoffContract):
    web_support_handoff_projection_id: _NonEmptyReferenceId
    item_kind: WebSupportHandoffItemKind
    state: WebSupportHandoffItemState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    account_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    support_case_reference_id: _NonEmptyReferenceId | None = None
    customer_visibility_policy_reference_id: _NonEmptyReferenceId
    customer_publication_policy_reference_id: _NonEmptyReferenceId
    customer_publication_decision_reference_id: _NonEmptyReferenceId | None = None
    support_entry_reference_id: _NonEmptyReferenceId | None = None
    customer_status_reference_id: _NonEmptyReferenceId | None = None
    customer_public_answer_reference_id: _NonEmptyReferenceId | None = None
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    redaction_policy_reference_id: _NonEmptyReferenceId
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    customer_visible: Literal[True] = True
    separate_customer_publication: Literal[True] = True
    admin_support_authoritative: Literal[True] = True
    web_presentation_boundary: Literal[True] = True
    safe_reference_only: Literal[True] = True
    redacted: Literal[True] = True
    minimal_personal_data: Literal[True] = True
    admin_support_safe_explanation_record_exposed: Literal[False] = False
    admin_support_internal_case_record_exposed: Literal[False] = False
    internal_note_present: Literal[False] = False
    private_audit_present: Literal[False] = False
    operator_only_field_present: Literal[False] = False
    raw_log_present: Literal[False] = False
    secret_material_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    full_private_message_present: Literal[False] = False
    mutation_authority: Literal[False] = False
    business_state_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_projection(self) -> "WebSupportHandoffProjection":
        if self.owning_module_id != ADMIN_AND_SUPPORT_MODULE_ID:
            raise ValueError("support handoff projections belong to Admin & Support")
        for values, label in (
            (self.source_reference_ids, "source"),
            (self.provenance_reference_ids, "provenance"),
            (self.evidence_reference_ids, "evidence"),
        ):
            _unique_non_empty(values, label)
        case_bound = self.item_kind is not WebSupportHandoffItemKind.SUPPORT_ENTRY
        if case_bound:
            _required(self.support_case_reference_id, "support case")
        else:
            _absent(self.support_case_reference_id, "support case")
        references = {
            WebSupportHandoffItemKind.SUPPORT_ENTRY: self.support_entry_reference_id,
            WebSupportHandoffItemKind.CASE_STATUS: self.customer_status_reference_id,
            WebSupportHandoffItemKind.PUBLIC_ANSWER: self.customer_public_answer_reference_id,
        }
        if self.state is WebSupportHandoffItemState.AMBIGUOUS:
            if (
                self.freshness is not WebReadFreshness.AMBIGUOUS
                or self.ambiguity_reference_id is None
            ):
                raise ValueError("ambiguous projection requires ambiguous freshness and reference")
            _absent(self.customer_publication_decision_reference_id, "publication decision")
            for reference in references.values():
                _absent(reference, "customer content")
        else:
            _required(references[self.item_kind], "item")
            for kind, reference in references.items():
                if kind is not self.item_kind:
                    _absent(reference, kind.value)
            expected_freshness = (
                WebReadFreshness.STALE
                if self.state is WebSupportHandoffItemState.STALE
                else WebReadFreshness.FRESH
            )
            if self.freshness is not expected_freshness:
                raise ValueError("projection state and freshness do not match")
            _required(self.customer_publication_decision_reference_id, "publication decision")
            _absent(self.ambiguity_reference_id, "ambiguity")
        return self


class WebSupportHandoffResult(_WebSupportHandoffContract):
    web_support_handoff_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebSupportHandoffQuery
    state: WebSupportHandoffResultState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    source_owner_module_id: _NonEmptyReferenceId
    projections: tuple[WebSupportHandoffProjection, ...]
    projection_count: int = Field(ge=0)
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    customer_only: Literal[True] = True
    admin_support_publication_authoritative: Literal[True] = True
    web_presentation_boundary: Literal[True] = True
    read_only: Literal[True] = True
    safe_reference_only: Literal[True] = True
    redacted: Literal[True] = True
    minimal_personal_data: Literal[True] = True
    internal_note_present: Literal[False] = False
    private_audit_present: Literal[False] = False
    operator_action_present: Literal[False] = False
    raw_log_present: Literal[False] = False
    secret_material_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    full_private_message_present: Literal[False] = False
    support_case_mutation_authority: Literal[False] = False
    operator_action_authority: Literal[False] = False
    route_or_ui_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebSupportHandoffResult":
        if self.owning_module_id != WEB_CABINET_MODULE_ID:
            raise ValueError("result belongs to Web Cabinet")
        if self.source_owner_module_id != ADMIN_AND_SUPPORT_MODULE_ID:
            raise ValueError("source owner is Admin & Support")
        _unique_non_empty(self.source_reference_ids, "source")
        _unique_non_empty(self.evidence_reference_ids, "evidence")
        if self.projection_count != len(self.projections):
            raise ValueError("projection count must match projections")
        if (
            len({projection.web_support_handoff_projection_id for projection in self.projections})
            != len(self.projections)
        ):
            raise ValueError("duplicate projection IDs are not allowed")
        if len({projection.item_kind for projection in self.projections}) != len(self.projections):
            raise ValueError("duplicate projection kinds are not allowed")
        terminal = {
            WebSupportHandoffResultState.FORBIDDEN,
            WebSupportHandoffResultState.NOT_FOUND_SAFE,
            WebSupportHandoffResultState.POLICY_BLOCKED,
            WebSupportHandoffResultState.UNSUPPORTED,
        }
        if self.state in terminal:
            if self.projections or self.projection_count or self.ambiguity_reference_id is not None:
                raise ValueError("terminal result cannot expose projection payload")
            expected = WebReadFreshness.UNKNOWN if self.state in {
                WebSupportHandoffResultState.POLICY_BLOCKED,
                WebSupportHandoffResultState.UNSUPPORTED,
            } else WebReadFreshness.FRESH
            if self.freshness is not expected:
                raise ValueError("terminal result freshness is invalid")
            return self
        if (
            tuple(projection.item_kind for projection in self.projections)
            != self.query.requested_item_kinds
        ):
            raise ValueError("non-terminal projections must cover requested kinds in order")
        for projection in self.projections:
            if (
                projection.account_id != self.query.account_id
                or projection.tenant_scope_reference_id != self.query.tenant_scope_reference_id
                or projection.customer_visibility_policy_reference_id
                != self.query.customer_visibility_policy_reference_id
                or projection.customer_publication_policy_reference_id
                != self.query.customer_publication_policy_reference_id
                or projection.redaction_policy_reference_id
                != self.query.redaction_policy_reference_id
            ):
                raise ValueError("projection scope or policy does not match query")
            if projection.item_kind is WebSupportHandoffItemKind.SUPPORT_ENTRY:
                if projection.support_case_reference_id is not None:
                    raise ValueError("entry projection cannot carry a case reference")
            elif projection.support_case_reference_id != self.query.support_case_reference_id:
                raise ValueError("case reference does not match query")
        states = tuple(projection.state for projection in self.projections)
        if self.state is WebSupportHandoffResultState.AVAILABLE:
            if self.freshness is not WebReadFreshness.FRESH or any(
                state is not WebSupportHandoffItemState.AVAILABLE for state in states
            ):
                raise ValueError("available result composition is invalid")
        elif self.state is WebSupportHandoffResultState.REDACTED:
            if (
                self.freshness is not WebReadFreshness.FRESH
                or WebSupportHandoffItemState.REDACTED not in states
                or any(
                    state
                    not in {
                        WebSupportHandoffItemState.AVAILABLE,
                        WebSupportHandoffItemState.REDACTED,
                    }
                    for state in states
                )
            ):
                raise ValueError("redacted result composition is invalid")
        elif self.state is WebSupportHandoffResultState.STALE:
            if (
                self.freshness is not WebReadFreshness.STALE
                or WebSupportHandoffItemState.STALE not in states
                or WebSupportHandoffItemState.AMBIGUOUS in states
            ):
                raise ValueError("stale result composition is invalid")
        elif self.state is WebSupportHandoffResultState.AMBIGUOUS:
            if (
                self.freshness is not WebReadFreshness.AMBIGUOUS
                or WebSupportHandoffItemState.AMBIGUOUS not in states
                or self.ambiguity_reference_id is None
            ):
                raise ValueError("ambiguous result composition is invalid")
        if (
            self.state is not WebSupportHandoffResultState.AMBIGUOUS
            and self.ambiguity_reference_id is not None
        ):
            raise ValueError("non-ambiguous result cannot carry ambiguity reference")
        return self


__all__ = [
    "RequestWebSupportHandoffQuery",
    "WebSupportHandoffItemKind",
    "WebSupportHandoffItemState",
    "WebSupportHandoffProjection",
    "WebSupportHandoffResult",
    "WebSupportHandoffResultState",
]
