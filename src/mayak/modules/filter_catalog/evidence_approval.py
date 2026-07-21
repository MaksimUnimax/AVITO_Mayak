"""Pure evidence approval-boundary semantics for one candidate definition."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .contracts import (
    FilterDefinitionState,
    FilterEvidenceReference,
    FilterEvidenceState,
    OpaqueReferenceId,
    SafeCode,
)


class EvidenceAuthorityClass(StrEnum):
    OFFICIAL_REFERENCE = "OFFICIAL_REFERENCE"
    ACCEPTED_PRIMARY_REFERENCE = "ACCEPTED_PRIMARY_REFERENCE"
    PARSER_OBSERVATION = "PARSER_OBSERVATION"
    UNVERIFIED_REFERENCE = "UNVERIFIED_REFERENCE"
    INTERNAL_PROVIDER_SURFACE = "INTERNAL_PROVIDER_SURFACE"


class FilterEvidenceTransition(StrEnum):
    PROPOSE = "PROPOSE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    DEPRECATE = "DEPRECATE"


class FilterEvidenceApprovalDecision(StrEnum):
    PROPOSABLE = "PROPOSABLE"
    APPROVABLE = "APPROVABLE"
    REJECTED = "REJECTED"
    DEPRECATION_REQUIRED = "DEPRECATION_REQUIRED"
    BLOCKED = "BLOCKED"


class ExactFilterApprovalGateState(StrEnum):
    BLOCKED_OPEN_DECISION = "BLOCKED_OPEN_DECISION"
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"


class FilterEvidenceApprovalReason(StrEnum):
    EVIDENCE_CURRENT = "EVIDENCE_CURRENT"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    EVIDENCE_CONTRADICTORY = "EVIDENCE_CONTRADICTORY"
    EVIDENCE_UNSUPPORTED = "EVIDENCE_UNSUPPORTED"
    EVIDENCE_AMBIGUOUS = "EVIDENCE_AMBIGUOUS"
    EVIDENCE_RESTRICTED = "EVIDENCE_RESTRICTED"
    EVIDENCE_REFRESH_REQUIRED = "EVIDENCE_REFRESH_REQUIRED"
    REQUIRED_SCOPE_MISSING = "REQUIRED_SCOPE_MISSING"
    AUTHORITATIVE_EVIDENCE_MISSING = "AUTHORITATIVE_EVIDENCE_MISSING"
    PARSER_OBSERVATION_NOT_AUTHORITY = "PARSER_OBSERVATION_NOT_AUTHORITY"
    EXACT_FILTER_GATE_BLOCKED = "EXACT_FILTER_GATE_BLOCKED"
    EXACT_FILTER_GATE_REVOKED = "EXACT_FILTER_GATE_REVOKED"
    EXPLICIT_REJECTION = "EXPLICIT_REJECTION"
    DEPRECATION_TRIGGER_MISSING = "DEPRECATION_TRIGGER_MISSING"
    DEPRECATION_STATE_INVALID = "DEPRECATION_STATE_INVALID"


class _EvidenceApprovalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class EvidenceAuthorityReference(_EvidenceApprovalModel):
    evidence_reference_id: OpaqueReferenceId
    authority_class: EvidenceAuthorityClass
    accepted_reference_policy_id: OpaqueReferenceId | None = None
    limitation_codes: tuple[SafeCode, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "EvidenceAuthorityReference":
        if len(self.limitation_codes) != len(set(self.limitation_codes)):
            raise ValueError("limitation_codes must contain unique codes")
        authoritative = self.authority_class in (
            EvidenceAuthorityClass.OFFICIAL_REFERENCE,
            EvidenceAuthorityClass.ACCEPTED_PRIMARY_REFERENCE,
        )
        if authoritative and self.accepted_reference_policy_id is None:
            raise ValueError("authoritative references require an accepted policy")
        if not authoritative and self.accepted_reference_policy_id is not None:
            raise ValueError("non-authoritative references must not have an accepted policy")
        return self


class FilterEvidenceApprovalRequest(_EvidenceApprovalModel):
    filter_definition_id: OpaqueReferenceId
    current_definition_state: FilterDefinitionState
    requested_transition: FilterEvidenceTransition
    required_scope_reference_ids: tuple[OpaqueReferenceId, ...]
    evidence_references: tuple[FilterEvidenceReference, ...] = ()
    authority_references: tuple[EvidenceAuthorityReference, ...] = ()
    exact_filter_gate_state: ExactFilterApprovalGateState = ExactFilterApprovalGateState.BLOCKED_OPEN_DECISION
    exact_filter_gate_reference_id: OpaqueReferenceId | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterEvidenceApprovalRequest":
        if not self.required_scope_reference_ids:
            raise ValueError("required_scope_reference_ids must not be empty")
        if len(self.required_scope_reference_ids) != len(set(self.required_scope_reference_ids)):
            raise ValueError("required_scope_reference_ids must contain unique references")
        evidence_ids = tuple(item.evidence_reference_id for item in self.evidence_references)
        authority_ids = tuple(item.evidence_reference_id for item in self.authority_references)
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence reference IDs must be unique")
        if len(authority_ids) != len(set(authority_ids)):
            raise ValueError("authority reference IDs must be unique")
        if set(evidence_ids) != set(authority_ids):
            raise ValueError("evidence and authority reference ID sets must match")
        if self.exact_filter_gate_state in (
            ExactFilterApprovalGateState.GRANTED,
            ExactFilterApprovalGateState.REVOKED,
        ) and self.exact_filter_gate_reference_id is None:
            raise ValueError("this gate state requires a gate reference")
        if self.exact_filter_gate_state is ExactFilterApprovalGateState.BLOCKED_OPEN_DECISION and self.exact_filter_gate_reference_id is not None:
            raise ValueError("blocked open-decision gate must not have a gate reference")
        return self


class FilterEvidenceApprovalOutcome(_EvidenceApprovalModel):
    filter_definition_id: OpaqueReferenceId
    requested_transition: FilterEvidenceTransition
    decision: FilterEvidenceApprovalDecision
    suggested_definition_state: FilterDefinitionState
    reason_codes: tuple[FilterEvidenceApprovalReason, ...]
    evidence_reference_ids: tuple[OpaqueReferenceId, ...]
    authoritative_evidence_reference_ids: tuple[OpaqueReferenceId, ...] = ()
    parser_observation_reference_ids: tuple[OpaqueReferenceId, ...] = ()
    catalog_mutation_performed: Literal[False] = False
    editability_granted: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterEvidenceApprovalOutcome":
        fields = (self.evidence_reference_ids, self.authoritative_evidence_reference_ids, self.parser_observation_reference_ids, self.reason_codes)
        if any(len(values) != len(set(values)) for values in fields):
            raise ValueError("outcome references and reasons must be unique")
        evidence_ids = set(self.evidence_reference_ids)
        authoritative_ids = set(self.authoritative_evidence_reference_ids)
        parser_ids = set(self.parser_observation_reference_ids)
        if not authoritative_ids <= evidence_ids or not parser_ids <= evidence_ids:
            raise ValueError("classified IDs must be subsets of evidence IDs")
        if authoritative_ids & parser_ids:
            raise ValueError("authoritative and parser IDs must not overlap")
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        expected_states = {
            FilterEvidenceApprovalDecision.PROPOSABLE: FilterDefinitionState.PROPOSED,
            FilterEvidenceApprovalDecision.APPROVABLE: FilterDefinitionState.APPROVED,
            FilterEvidenceApprovalDecision.REJECTED: FilterDefinitionState.REJECTED,
            FilterEvidenceApprovalDecision.DEPRECATION_REQUIRED: FilterDefinitionState.DEPRECATED,
            FilterEvidenceApprovalDecision.BLOCKED: FilterDefinitionState.BLOCKED,
        }
        if self.suggested_definition_state is not expected_states[self.decision]:
            raise ValueError("decision and suggested state do not match")
        return self


_STATE_REASONS = {
    FilterEvidenceState.MISSING: FilterEvidenceApprovalReason.EVIDENCE_MISSING,
    FilterEvidenceState.STALE: FilterEvidenceApprovalReason.EVIDENCE_STALE,
    FilterEvidenceState.CONTRADICTORY: FilterEvidenceApprovalReason.EVIDENCE_CONTRADICTORY,
    FilterEvidenceState.UNSUPPORTED: FilterEvidenceApprovalReason.EVIDENCE_UNSUPPORTED,
    FilterEvidenceState.AMBIGUOUS: FilterEvidenceApprovalReason.EVIDENCE_AMBIGUOUS,
    FilterEvidenceState.RESTRICTED: FilterEvidenceApprovalReason.EVIDENCE_RESTRICTED,
}
_PROPOSAL_BLOCKERS = frozenset(_STATE_REASONS.values()) | frozenset({
    FilterEvidenceApprovalReason.EVIDENCE_REFRESH_REQUIRED,
    FilterEvidenceApprovalReason.REQUIRED_SCOPE_MISSING,
    FilterEvidenceApprovalReason.AUTHORITATIVE_EVIDENCE_MISSING,
    FilterEvidenceApprovalReason.PARSER_OBSERVATION_NOT_AUTHORITY,
})


def _ordered_reasons(reasons: set[FilterEvidenceApprovalReason]) -> tuple[FilterEvidenceApprovalReason, ...]:
    return tuple(reason for reason in FilterEvidenceApprovalReason if reason in reasons)


def evaluate_filter_evidence_approval(request: FilterEvidenceApprovalRequest) -> FilterEvidenceApprovalOutcome:
    evidence = request.evidence_references
    authority_by_id = {item.evidence_reference_id: item for item in request.authority_references}
    evidence_ids = tuple(item.evidence_reference_id for item in evidence)
    authoritative_ids = tuple(item.evidence_reference_id for item in evidence if authority_by_id[item.evidence_reference_id].authority_class in (EvidenceAuthorityClass.OFFICIAL_REFERENCE, EvidenceAuthorityClass.ACCEPTED_PRIMARY_REFERENCE))
    parser_ids = tuple(item.evidence_reference_id for item in evidence if authority_by_id[item.evidence_reference_id].authority_class is EvidenceAuthorityClass.PARSER_OBSERVATION)
    reasons: set[FilterEvidenceApprovalReason] = set()
    if not evidence:
        reasons.add(FilterEvidenceApprovalReason.EVIDENCE_MISSING)
    if any(item.evidence_state is FilterEvidenceState.CURRENT for item in evidence):
        reasons.add(FilterEvidenceApprovalReason.EVIDENCE_CURRENT)
    for item in evidence:
        if item.evidence_state in _STATE_REASONS:
            reasons.add(_STATE_REASONS[item.evidence_state])
        if item.refresh_required:
            reasons.add(FilterEvidenceApprovalReason.EVIDENCE_REFRESH_REQUIRED)
    covered_scopes = {scope_id for item in evidence for scope_id in item.scope_reference_ids}
    if any(scope_id not in covered_scopes for scope_id in request.required_scope_reference_ids):
        reasons.add(FilterEvidenceApprovalReason.REQUIRED_SCOPE_MISSING)
    if not authoritative_ids:
        reasons.add(FilterEvidenceApprovalReason.AUTHORITATIVE_EVIDENCE_MISSING)
        if parser_ids:
            reasons.add(FilterEvidenceApprovalReason.PARSER_OBSERVATION_NOT_AUTHORITY)
    defects = reasons & _PROPOSAL_BLOCKERS
    if request.requested_transition is FilterEvidenceTransition.REJECT:
        decision, state = FilterEvidenceApprovalDecision.REJECTED, FilterDefinitionState.REJECTED
        if not defects:
            reasons.add(FilterEvidenceApprovalReason.EXPLICIT_REJECTION)
    elif request.requested_transition is FilterEvidenceTransition.DEPRECATE:
        if request.current_definition_state is not FilterDefinitionState.APPROVED:
            decision, state = FilterEvidenceApprovalDecision.BLOCKED, FilterDefinitionState.BLOCKED
            reasons.add(FilterEvidenceApprovalReason.DEPRECATION_STATE_INVALID)
        elif defects & {
            FilterEvidenceApprovalReason.EVIDENCE_MISSING, FilterEvidenceApprovalReason.EVIDENCE_STALE,
            FilterEvidenceApprovalReason.EVIDENCE_CONTRADICTORY, FilterEvidenceApprovalReason.EVIDENCE_UNSUPPORTED,
            FilterEvidenceApprovalReason.EVIDENCE_AMBIGUOUS, FilterEvidenceApprovalReason.EVIDENCE_RESTRICTED,
            FilterEvidenceApprovalReason.EVIDENCE_REFRESH_REQUIRED, FilterEvidenceApprovalReason.REQUIRED_SCOPE_MISSING,
        }:
            decision, state = FilterEvidenceApprovalDecision.DEPRECATION_REQUIRED, FilterDefinitionState.DEPRECATED
        else:
            decision, state = FilterEvidenceApprovalDecision.BLOCKED, FilterDefinitionState.BLOCKED
            reasons.add(FilterEvidenceApprovalReason.DEPRECATION_TRIGGER_MISSING)
    else:
        if request.requested_transition is FilterEvidenceTransition.APPROVE:
            if request.exact_filter_gate_state is ExactFilterApprovalGateState.BLOCKED_OPEN_DECISION:
                reasons.add(FilterEvidenceApprovalReason.EXACT_FILTER_GATE_BLOCKED)
            elif request.exact_filter_gate_state is ExactFilterApprovalGateState.REVOKED:
                reasons.add(FilterEvidenceApprovalReason.EXACT_FILTER_GATE_REVOKED)
        if defects or (request.requested_transition is FilterEvidenceTransition.APPROVE and request.exact_filter_gate_state is not ExactFilterApprovalGateState.GRANTED):
            decision, state = FilterEvidenceApprovalDecision.BLOCKED, FilterDefinitionState.BLOCKED
        elif request.requested_transition is FilterEvidenceTransition.APPROVE:
            decision, state = FilterEvidenceApprovalDecision.APPROVABLE, FilterDefinitionState.APPROVED
        else:
            decision, state = FilterEvidenceApprovalDecision.PROPOSABLE, FilterDefinitionState.PROPOSED
    return FilterEvidenceApprovalOutcome(
        filter_definition_id=request.filter_definition_id,
        requested_transition=request.requested_transition,
        decision=decision,
        suggested_definition_state=state,
        reason_codes=_ordered_reasons(reasons),
        evidence_reference_ids=evidence_ids,
        authoritative_evidence_reference_ids=authoritative_ids,
        parser_observation_reference_ids=parser_ids,
    )


__all__ = (
    "EvidenceAuthorityClass", "FilterEvidenceTransition", "FilterEvidenceApprovalDecision",
    "ExactFilterApprovalGateState", "FilterEvidenceApprovalReason", "EvidenceAuthorityReference",
    "FilterEvidenceApprovalRequest", "FilterEvidenceApprovalOutcome", "evaluate_filter_evidence_approval",
)
