"""Pure semantic boundaries for multivalue, range, and dependency evaluation."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from .contracts import (
    FilterCapabilityProfile,
    FilterDefinition,
    FilterDependencyKind,
    FilterDependencyRule,
    FilterRangeDefinition,
    OpaqueReferenceId,
    SafeCode,
)


class MultivaluePreservationDecision(StrEnum):
    PRESERVED = "PRESERVED"
    BLOCKED = "BLOCKED"


class MultivaluePreservationReason(StrEnum):
    VALUES_PRESERVED = "VALUES_PRESERVED"
    VALUE_COUNT_CHANGED = "VALUE_COUNT_CHANGED"
    VALUE_SEQUENCE_CHANGED = "VALUE_SEQUENCE_CHANGED"
    VALUE_OCCURRENCE_CHANGED = "VALUE_OCCURRENCE_CHANGED"
    REPEATED_VALUE_COLLAPSE_DETECTED = "REPEATED_VALUE_COLLAPSE_DETECTED"


class RangeValueValidationDecision(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    BLOCKED = "BLOCKED"


class RangeValueValidationReason(StrEnum):
    RANGE_VALID = "RANGE_VALID"
    FILTER_DEFINITION_MISMATCH = "FILTER_DEFINITION_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    VALUE_BOUNDARY_MISSING = "VALUE_BOUNDARY_MISSING"
    VALUE_ORDER_INVALID = "VALUE_ORDER_INVALID"
    VALUE_INTERVAL_EMPTY = "VALUE_INTERVAL_EMPTY"
    LOWER_BOUND_OUT_OF_RANGE = "LOWER_BOUND_OUT_OF_RANGE"
    UPPER_BOUND_OUT_OF_RANGE = "UPPER_BOUND_OUT_OF_RANGE"
    LOWER_INCLUSIVITY_INCOMPATIBLE = "LOWER_INCLUSIVITY_INCOMPATIBLE"
    UPPER_INCLUSIVITY_INCOMPATIBLE = "UPPER_INCLUSIVITY_INCOMPATIBLE"
    STEP_ORIGIN_REQUIRED = "STEP_ORIGIN_REQUIRED"
    LOWER_STEP_MISMATCH = "LOWER_STEP_MISMATCH"
    UPPER_STEP_MISMATCH = "UPPER_STEP_MISMATCH"


class DependencyEvaluationState(StrEnum):
    SATISFIED = "SATISFIED"
    BLOCKED = "BLOCKED"
    NOT_EVALUATED = "NOT_EVALUATED"


class FilterSemanticExposureDecision(StrEnum):
    EXPOSED = "EXPOSED"
    BLOCKED = "BLOCKED"


class FilterSemanticExposureReason(StrEnum):
    FILTER_EXPOSED = "FILTER_EXPOSED"
    CATALOG_VERSION_MISMATCH = "CATALOG_VERSION_MISMATCH"
    CAPABILITY_PROFILE_NOT_LINKED = "CAPABILITY_PROFILE_NOT_LINKED"
    PROVIDER_SURFACE_MISMATCH = "PROVIDER_SURFACE_MISMATCH"
    CATEGORY_SCOPE_REQUIRED = "CATEGORY_SCOPE_REQUIRED"
    CATEGORY_SCOPE_MISMATCH = "CATEGORY_SCOPE_MISMATCH"
    GEOGRAPHY_SCOPE_REQUIRED = "GEOGRAPHY_SCOPE_REQUIRED"
    GEOGRAPHY_SCOPE_MISMATCH = "GEOGRAPHY_SCOPE_MISMATCH"
    GLOBAL_SCOPE_APPROVAL_REQUIRED = "GLOBAL_SCOPE_APPROVAL_REQUIRED"
    DEPENDENCY_RULE_SET_MISMATCH = "DEPENDENCY_RULE_SET_MISMATCH"
    DEPENDENCY_GRAPH_NOT_LINKED = "DEPENDENCY_GRAPH_NOT_LINKED"
    DEPENDENCY_RULE_ENDPOINT_UNKNOWN = "DEPENDENCY_RULE_ENDPOINT_UNKNOWN"
    DEPENDENCY_GRAPH_CYCLE = "DEPENDENCY_GRAPH_CYCLE"
    DEPENDENCY_EVALUATION_SET_MISMATCH = "DEPENDENCY_EVALUATION_SET_MISMATCH"
    DEPENDENCY_NOT_EVALUATED = "DEPENDENCY_NOT_EVALUATED"
    DEPENDENCY_BLOCKED = "DEPENDENCY_BLOCKED"


class _SemanticRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


def _unique(values: tuple[OpaqueReferenceId, ...], name: str, *, required: bool = False) -> None:
    if required and not values:
        raise ValueError(f"{name} must not be empty")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique references")


class MultivaluePreservationRequest(_SemanticRecord):
    filter_definition_id: OpaqueReferenceId
    source_value_reference_ids: tuple[OpaqueReferenceId, ...]
    candidate_value_reference_ids: tuple[OpaqueReferenceId, ...]


class MultivaluePreservationOutcome(_SemanticRecord):
    filter_definition_id: OpaqueReferenceId
    decision: MultivaluePreservationDecision
    reason_codes: tuple[MultivaluePreservationReason, ...]
    source_value_reference_ids: tuple[OpaqueReferenceId, ...]
    candidate_value_reference_ids: tuple[OpaqueReferenceId, ...]
    preserved_value_reference_ids: tuple[OpaqueReferenceId, ...]
    candidate_changed: bool
    normalization_performed: Literal[False] = False
    deduplication_performed: Literal[False] = False
    collapse_performed: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "MultivaluePreservationOutcome":
        _unique(tuple(self.reason_codes), "reason_codes", required=True)
        exact = self.source_value_reference_ids == self.candidate_value_reference_ids
        if self.decision is MultivaluePreservationDecision.PRESERVED:
            if not exact or self.preserved_value_reference_ids != self.source_value_reference_ids or self.candidate_changed:
                raise ValueError("preserved outcome must preserve the exact sequence")
            if self.reason_codes != (MultivaluePreservationReason.VALUES_PRESERVED,):
                raise ValueError("preserved outcome requires VALUES_PRESERVED")
        else:
            if exact or self.preserved_value_reference_ids or not self.candidate_changed:
                raise ValueError("blocked outcome must identify a changed candidate")
            if MultivaluePreservationReason.VALUES_PRESERVED in self.reason_codes:
                raise ValueError("blocked outcome must not contain VALUES_PRESERVED")
        return self


def _finite(value: Decimal | None, name: str) -> None:
    if value is not None and not value.is_finite():
        raise ValueError(f"{name} must be finite")


class RangeValueValidationRequest(_SemanticRecord):
    filter_definition_id: OpaqueReferenceId
    range_definition: FilterRangeDefinition
    candidate_unit_code: SafeCode
    lower_value: Decimal | None = None
    upper_value: Decimal | None = None
    lower_inclusive: bool
    upper_inclusive: bool
    step_origin: Decimal | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "RangeValueValidationRequest":
        _finite(self.lower_value, "lower_value")
        _finite(self.upper_value, "upper_value")
        _finite(self.step_origin, "step_origin")
        return self


class RangeValueValidationOutcome(_SemanticRecord):
    filter_definition_id: OpaqueReferenceId
    filter_range_definition_id: OpaqueReferenceId
    decision: RangeValueValidationDecision
    reason_codes: tuple[RangeValueValidationReason, ...]
    candidate_unit_code: SafeCode
    lower_value: Decimal | None = None
    upper_value: Decimal | None = None
    lower_inclusive: bool
    upper_inclusive: bool
    range_definition_mutated: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "RangeValueValidationOutcome":
        _unique(tuple(self.reason_codes), "reason_codes", required=True)
        if self.decision is RangeValueValidationDecision.VALID and self.reason_codes != (RangeValueValidationReason.RANGE_VALID,):
            raise ValueError("valid range outcome requires RANGE_VALID")
        if self.decision is not RangeValueValidationDecision.VALID and RangeValueValidationReason.RANGE_VALID in self.reason_codes:
            raise ValueError("non-valid range outcome forbids RANGE_VALID")
        if self.decision is RangeValueValidationDecision.BLOCKED and self.reason_codes != (RangeValueValidationReason.STEP_ORIGIN_REQUIRED,):
            raise ValueError("blocked range outcome requires STEP_ORIGIN_REQUIRED")
        if self.decision is RangeValueValidationDecision.INVALID and all(
            reason is RangeValueValidationReason.STEP_ORIGIN_REQUIRED for reason in self.reason_codes
        ):
            raise ValueError("invalid range outcome requires a defect reason")
        return self


class DependencyRuleEvaluation(_SemanticRecord):
    filter_dependency_rule_id: OpaqueReferenceId
    evaluation_state: DependencyEvaluationState
    evaluation_reference_id: OpaqueReferenceId | None = None

    @model_validator(mode="after")
    def validate_semantics(self) -> "DependencyRuleEvaluation":
        if self.evaluation_state in (DependencyEvaluationState.SATISFIED, DependencyEvaluationState.BLOCKED) and self.evaluation_reference_id is None:
            raise ValueError("evaluated dependency states require a reference")
        if self.evaluation_state is DependencyEvaluationState.NOT_EVALUATED and self.evaluation_reference_id is not None:
            raise ValueError("NOT_EVALUATED must not have a reference")
        return self


class FilterSemanticExposureRequest(_SemanticRecord):
    filter_catalog_version_id: OpaqueReferenceId
    filter_definition: FilterDefinition
    capability_profile: FilterCapabilityProfile
    provider_surface_reference_id: OpaqueReferenceId
    category_scope_reference_id: OpaqueReferenceId | None = None
    geography_scope_reference_id: OpaqueReferenceId | None = None
    global_scope_approval_reference_id: OpaqueReferenceId | None = None
    known_filter_definition_ids: tuple[OpaqueReferenceId, ...]
    dependency_rules: tuple[FilterDependencyRule, ...] = ()
    dependency_evaluations: tuple[DependencyRuleEvaluation, ...] = ()

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterSemanticExposureRequest":
        _unique(self.known_filter_definition_ids, "known_filter_definition_ids", required=True)
        if self.filter_definition.filter_definition_id not in self.known_filter_definition_ids:
            raise ValueError("subject filter definition must be known")
        _unique(tuple(rule.filter_dependency_rule_id for rule in self.dependency_rules), "dependency rule IDs")
        _unique(tuple(item.filter_dependency_rule_id for item in self.dependency_evaluations), "dependency evaluation rule IDs")
        if self.capability_profile.category_scope_reference_id is not None and self.capability_profile.geography_scope_reference_id is not None and self.global_scope_approval_reference_id is not None:
            raise ValueError("global approval is extraneous when both scopes are explicit")
        return self


class FilterSemanticExposureOutcome(_SemanticRecord):
    filter_definition_id: OpaqueReferenceId
    decision: FilterSemanticExposureDecision
    reason_codes: tuple[FilterSemanticExposureReason, ...]
    dependency_rule_ids: tuple[OpaqueReferenceId, ...]
    evaluated_dependency_rule_ids: tuple[OpaqueReferenceId, ...]
    blocked_dependency_rule_ids: tuple[OpaqueReferenceId, ...]
    global_scope_assumed: Literal[False] = False
    editability_granted: Literal[False] = False
    ui_render_performed: Literal[False] = False
    beacon_mutation_performed: Literal[False] = False
    override_candidate_prepared: Literal[False] = False

    @model_validator(mode="after")
    def validate_semantics(self) -> "FilterSemanticExposureOutcome":
        _unique(tuple(self.reason_codes), "reason_codes", required=True)
        _unique(self.dependency_rule_ids, "dependency_rule_ids")
        _unique(self.evaluated_dependency_rule_ids, "evaluated_dependency_rule_ids")
        _unique(self.blocked_dependency_rule_ids, "blocked_dependency_rule_ids")
        rule_ids = set(self.dependency_rule_ids)
        if not set(self.evaluated_dependency_rule_ids) <= rule_ids or not set(self.blocked_dependency_rule_ids) <= set(self.evaluated_dependency_rule_ids):
            raise ValueError("dependency result IDs must be ordered subsets")
        if self.decision is FilterSemanticExposureDecision.EXPOSED:
            if self.reason_codes != (FilterSemanticExposureReason.FILTER_EXPOSED,) or self.blocked_dependency_rule_ids:
                raise ValueError("exposed outcome must have no blockers")
        elif FilterSemanticExposureReason.FILTER_EXPOSED in self.reason_codes:
            raise ValueError("blocked outcome forbids FILTER_EXPOSED")
        return self


def _ordered_reasons(values: set[StrEnum], enum_type: type[StrEnum]) -> tuple[StrEnum, ...]:
    return tuple(reason for reason in enum_type if reason in values)


def evaluate_multivalue_preservation(request: MultivaluePreservationRequest) -> MultivaluePreservationOutcome:
    source = request.source_value_reference_ids
    candidate = request.candidate_value_reference_ids
    if source == candidate:
        return MultivaluePreservationOutcome(
            filter_definition_id=request.filter_definition_id, decision=MultivaluePreservationDecision.PRESERVED,
            reason_codes=(MultivaluePreservationReason.VALUES_PRESERVED,), source_value_reference_ids=source,
            candidate_value_reference_ids=candidate, preserved_value_reference_ids=source, candidate_changed=False,
        )
    reasons: set[MultivaluePreservationReason] = {MultivaluePreservationReason.VALUE_SEQUENCE_CHANGED}
    if len(source) != len(candidate):
        reasons.add(MultivaluePreservationReason.VALUE_COUNT_CHANGED)
    if Counter(source) != Counter(candidate):
        reasons.add(MultivaluePreservationReason.VALUE_OCCURRENCE_CHANGED)
    if (len(source) > 1 and len(candidate) <= 1) or any(candidate.count(value) < count for value, count in Counter(source).items()):
        reasons.add(MultivaluePreservationReason.REPEATED_VALUE_COLLAPSE_DETECTED)
    return MultivaluePreservationOutcome(
        filter_definition_id=request.filter_definition_id, decision=MultivaluePreservationDecision.BLOCKED,
        reason_codes=_ordered_reasons(reasons, MultivaluePreservationReason), source_value_reference_ids=source,
        candidate_value_reference_ids=candidate, preserved_value_reference_ids=(), candidate_changed=True,
    )


def validate_range_value(request: RangeValueValidationRequest) -> RangeValueValidationOutcome:
    definition = request.range_definition
    reasons: set[RangeValueValidationReason] = set()
    if definition.filter_definition_id != request.filter_definition_id:
        reasons.add(RangeValueValidationReason.FILTER_DEFINITION_MISMATCH)
    if definition.unit_code != request.candidate_unit_code:
        reasons.add(RangeValueValidationReason.UNIT_MISMATCH)
    lower, upper = request.lower_value, request.upper_value
    if lower is None and upper is None:
        reasons.add(RangeValueValidationReason.VALUE_BOUNDARY_MISSING)
    if lower is not None and upper is not None:
        if lower > upper:
            reasons.add(RangeValueValidationReason.VALUE_ORDER_INVALID)
        elif lower == upper and (not request.lower_inclusive or not request.upper_inclusive):
            reasons.add(RangeValueValidationReason.VALUE_INTERVAL_EMPTY)
    if lower is not None:
        if definition.lower_bound is not None and lower < definition.lower_bound or definition.upper_bound is not None and lower > definition.upper_bound:
            reasons.add(RangeValueValidationReason.LOWER_BOUND_OUT_OF_RANGE)
        if definition.lower_bound is not None and lower == definition.lower_bound and request.lower_inclusive and not definition.lower_inclusive:
            reasons.add(RangeValueValidationReason.LOWER_INCLUSIVITY_INCOMPATIBLE)
    if upper is not None:
        if definition.lower_bound is not None and upper < definition.lower_bound or definition.upper_bound is not None and upper > definition.upper_bound:
            reasons.add(RangeValueValidationReason.UPPER_BOUND_OUT_OF_RANGE)
        if definition.upper_bound is not None and upper == definition.upper_bound and request.upper_inclusive and not definition.upper_inclusive:
            reasons.add(RangeValueValidationReason.UPPER_INCLUSIVITY_INCOMPATIBLE)
    if definition.step is not None:
        if request.step_origin is None:
            reasons.add(RangeValueValidationReason.STEP_ORIGIN_REQUIRED)
        else:
            if lower is not None and (lower - request.step_origin) % definition.step != 0:
                reasons.add(RangeValueValidationReason.LOWER_STEP_MISMATCH)
            if upper is not None and (upper - request.step_origin) % definition.step != 0:
                reasons.add(RangeValueValidationReason.UPPER_STEP_MISMATCH)
    ordered = _ordered_reasons(reasons, RangeValueValidationReason)
    if any(reason is not RangeValueValidationReason.STEP_ORIGIN_REQUIRED for reason in ordered):
        decision = RangeValueValidationDecision.INVALID
    elif ordered:
        decision = RangeValueValidationDecision.BLOCKED
    else:
        decision, ordered = RangeValueValidationDecision.VALID, (RangeValueValidationReason.RANGE_VALID,)
    return RangeValueValidationOutcome(
        filter_definition_id=request.filter_definition_id, filter_range_definition_id=definition.filter_range_definition_id,
        decision=decision, reason_codes=ordered, candidate_unit_code=request.candidate_unit_code, lower_value=lower,
        upper_value=upper, lower_inclusive=request.lower_inclusive, upper_inclusive=request.upper_inclusive,
    )


def _has_cycle(rules: tuple[FilterDependencyRule, ...]) -> bool:
    graph: dict[str, tuple[str, ...]] = {}
    for rule in rules:
        if rule.dependency_kind in (FilterDependencyKind.REQUIRES, FilterDependencyKind.CONSTRAINS):
            graph[rule.source_filter_definition_id] = graph.get(rule.source_filter_definition_id, ()) + (rule.target_filter_definition_id,)
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False
    return any(visit(node) for node in graph)


def evaluate_filter_semantic_exposure(request: FilterSemanticExposureRequest) -> FilterSemanticExposureOutcome:
    definition = request.filter_definition
    profile = request.capability_profile
    required_ids = definition.dependency_rule_ids
    supplied_ids = tuple(rule.filter_dependency_rule_id for rule in request.dependency_rules)
    evaluation_map = {item.filter_dependency_rule_id: item for item in request.dependency_evaluations}
    reasons: set[FilterSemanticExposureReason] = set()
    if request.filter_catalog_version_id != definition.filter_catalog_version_id or request.filter_catalog_version_id != profile.filter_catalog_version_id:
        reasons.add(FilterSemanticExposureReason.CATALOG_VERSION_MISMATCH)
    if profile.filter_capability_profile_id not in definition.capability_profile_ids:
        reasons.add(FilterSemanticExposureReason.CAPABILITY_PROFILE_NOT_LINKED)
    if request.provider_surface_reference_id != profile.provider_surface_reference_id:
        reasons.add(FilterSemanticExposureReason.PROVIDER_SURFACE_MISMATCH)
    if profile.category_scope_reference_id is not None:
        if request.category_scope_reference_id is None:
            reasons.add(FilterSemanticExposureReason.CATEGORY_SCOPE_REQUIRED)
        elif request.category_scope_reference_id != profile.category_scope_reference_id:
            reasons.add(FilterSemanticExposureReason.CATEGORY_SCOPE_MISMATCH)
    if profile.geography_scope_reference_id is not None:
        if request.geography_scope_reference_id is None:
            reasons.add(FilterSemanticExposureReason.GEOGRAPHY_SCOPE_REQUIRED)
        elif request.geography_scope_reference_id != profile.geography_scope_reference_id:
            reasons.add(FilterSemanticExposureReason.GEOGRAPHY_SCOPE_MISMATCH)
    if profile.category_scope_reference_id is None or profile.geography_scope_reference_id is None:
        if request.global_scope_approval_reference_id is None:
            reasons.add(FilterSemanticExposureReason.GLOBAL_SCOPE_APPROVAL_REQUIRED)
    if set(supplied_ids) != set(required_ids):
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_RULE_SET_MISMATCH)
    if request.dependency_rules and not any(definition.filter_definition_id in (rule.source_filter_definition_id, rule.target_filter_definition_id) for rule in request.dependency_rules):
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_GRAPH_NOT_LINKED)
    known = set(request.known_filter_definition_ids)
    if any(rule.source_filter_definition_id not in known or rule.target_filter_definition_id not in known for rule in request.dependency_rules):
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_RULE_ENDPOINT_UNKNOWN)
    if _has_cycle(request.dependency_rules):
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_GRAPH_CYCLE)
    if set(evaluation_map) != set(required_ids):
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_EVALUATION_SET_MISMATCH)
    evaluated = tuple(rule_id for rule_id in required_ids if rule_id in evaluation_map and evaluation_map[rule_id].evaluation_state in (DependencyEvaluationState.SATISFIED, DependencyEvaluationState.BLOCKED))
    blocked = tuple(rule_id for rule_id in required_ids if rule_id in evaluation_map and evaluation_map[rule_id].evaluation_state is DependencyEvaluationState.BLOCKED)
    if any(item.evaluation_state is DependencyEvaluationState.NOT_EVALUATED for item in evaluation_map.values()):
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_NOT_EVALUATED)
    if blocked:
        reasons.add(FilterSemanticExposureReason.DEPENDENCY_BLOCKED)
    ordered = _ordered_reasons(reasons, FilterSemanticExposureReason)
    if not ordered:
        decision, ordered = FilterSemanticExposureDecision.EXPOSED, (FilterSemanticExposureReason.FILTER_EXPOSED,)
    else:
        decision = FilterSemanticExposureDecision.BLOCKED
    return FilterSemanticExposureOutcome(
        filter_definition_id=definition.filter_definition_id, decision=decision, reason_codes=ordered,
        dependency_rule_ids=required_ids, evaluated_dependency_rule_ids=evaluated, blocked_dependency_rule_ids=blocked,
    )


__all__ = (
    "MultivaluePreservationDecision", "MultivaluePreservationReason", "RangeValueValidationDecision",
    "RangeValueValidationReason", "DependencyEvaluationState", "FilterSemanticExposureDecision",
    "FilterSemanticExposureReason", "MultivaluePreservationRequest", "MultivaluePreservationOutcome",
    "RangeValueValidationRequest", "RangeValueValidationOutcome", "DependencyRuleEvaluation",
    "FilterSemanticExposureRequest", "FilterSemanticExposureOutcome", "evaluate_multivalue_preservation",
    "validate_range_value", "evaluate_filter_semantic_exposure",
)
