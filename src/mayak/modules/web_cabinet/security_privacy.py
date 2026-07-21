"""Transport-neutral Web Cabinet security and privacy projections."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.web_cabinet.read_models import WebReadFreshness, WebViewAudience
from mayak.platform.boundaries import WEB_CABINET_MODULE_ID


class _WebSecurityPrivacyContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


_NonEmptyReferenceId = Annotated[str, Field(min_length=1)]
_OD_013 = "OD-013"
_OD_014 = "OD-014"


class WebPrivacySurfaceKind(str, Enum):
    BROWSER_VISIBLE_DATA = "BROWSER_VISIBLE_DATA"
    SAFE_ERROR = "SAFE_ERROR"
    ANALYTICS_COLLECTION = "ANALYTICS_COLLECTION"
    RETENTION_POLICY = "RETENTION_POLICY"
    DELETION_EXPORT_POLICY = "DELETION_EXPORT_POLICY"


class WebPrivacyProjectionState(str, Enum):
    SAFE = "SAFE"
    REDACTED = "REDACTED"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


class WebSecurityPrivacyResultState(str, Enum):
    SAFE = "SAFE"
    REDACTED = "REDACTED"
    FORBIDDEN = "FORBIDDEN"
    STALE = "STALE"
    AMBIGUOUS = "AMBIGUOUS"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


def _unique_non_empty(values: tuple[str, ...], label: str) -> None:
    if not values or any(not value for value in values):
        raise ValueError(f"{label} must be non-empty")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _valid_open_decisions(values: tuple[str, ...]) -> None:
    if len(values) != len(set(values)) or any(value not in {_OD_013, _OD_014} for value in values):
        raise ValueError("only unique OD-013 and OD-014 references are allowed")


def _required_open_decisions(surfaces: tuple[WebPrivacySurfaceKind, ...]) -> tuple[str, ...]:
    policy = set(surfaces) & {
        WebPrivacySurfaceKind.ANALYTICS_COLLECTION,
        WebPrivacySurfaceKind.RETENTION_POLICY,
        WebPrivacySurfaceKind.DELETION_EXPORT_POLICY,
    }
    if not policy:
        return ()
    return (
        (_OD_013, _OD_014) if WebPrivacySurfaceKind.ANALYTICS_COLLECTION in policy else (_OD_013,)
    )


class RequestWebSecurityPrivacyAssessmentQuery(_WebSecurityPrivacyContract):
    web_security_privacy_query_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    account_id: _NonEmptyReferenceId
    actor_context_reference_id: _NonEmptyReferenceId
    authorization_decision_reference_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    audience: WebViewAudience
    requested_surface_kinds: tuple[WebPrivacySurfaceKind, ...]
    open_decision_reference_ids: tuple[_NonEmptyReferenceId, ...]
    web_security_policy_reference_id: _NonEmptyReferenceId
    browser_minimization_policy_reference_id: _NonEmptyReferenceId
    redaction_policy_reference_id: _NonEmptyReferenceId
    safe_error_policy_reference_id: _NonEmptyReferenceId
    analytics_policy_gate_reference_id: _NonEmptyReferenceId
    retention_policy_gate_reference_id: _NonEmptyReferenceId
    deletion_export_policy_gate_reference_id: _NonEmptyReferenceId
    reason_code: _NonEmptyReferenceId
    verified_actor_required: Literal[True] = True
    read_only: Literal[True] = True
    untrusted_input: Literal[True] = True
    external_string_shell_authority: Literal[False] = False
    analytics_collection_requested: Literal[False] = False
    consent_assumed: Literal[False] = False
    retention_period_selected: Literal[False] = False
    deletion_export_policy_selected: Literal[False] = False
    raw_secret_requested: Literal[False] = False
    raw_provider_payload_requested: Literal[False] = False
    raw_personal_data_requested: Literal[False] = False
    runtime_authority: Literal[False] = False
    persistence_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_query(self) -> "RequestWebSecurityPrivacyAssessmentQuery":
        _unique_non_empty(self.requested_surface_kinds, "requested surfaces")
        _valid_open_decisions(self.open_decision_reference_ids)
        required = _required_open_decisions(self.requested_surface_kinds)
        if self.open_decision_reference_ids != required:
            raise ValueError("open decisions do not match policy-gated surfaces")
        return self


class WebPrivacyControlProjection(_WebSecurityPrivacyContract):
    web_privacy_control_projection_id: _NonEmptyReferenceId
    surface_kind: WebPrivacySurfaceKind
    state: WebPrivacyProjectionState
    freshness: WebReadFreshness
    account_id: _NonEmptyReferenceId
    tenant_scope_reference_id: _NonEmptyReferenceId
    web_security_policy_reference_id: _NonEmptyReferenceId
    browser_minimization_policy_reference_id: _NonEmptyReferenceId
    redaction_policy_reference_id: _NonEmptyReferenceId
    safe_error_policy_reference_id: _NonEmptyReferenceId
    policy_gate_reference_id: _NonEmptyReferenceId
    policy_decision_reference_id: _NonEmptyReferenceId | None = None
    safe_display_reference_id: _NonEmptyReferenceId | None = None
    redaction_evidence_reference_id: _NonEmptyReferenceId | None = None
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    provenance_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    open_decision_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    browser_visible: Literal[True] = True
    safe_reference_only: Literal[True] = True
    minimal_personal_data: Literal[True] = True
    redaction_enforced: Literal[True] = True
    safe_error_semantics: Literal[True] = True
    foreign_object_existence_disclosed: Literal[False] = False
    stack_trace_present: Literal[False] = False
    internal_exception_present: Literal[False] = False
    secret_material_present: Literal[False] = False
    password_present: Literal[False] = False
    one_time_code_present: Literal[False] = False
    token_present: Literal[False] = False
    cookie_present: Literal[False] = False
    session_material_present: Literal[False] = False
    private_key_present: Literal[False] = False
    environment_secret_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    raw_avito_payload_present: Literal[False] = False
    full_private_message_present: Literal[False] = False
    internal_support_note_present: Literal[False] = False
    private_audit_present: Literal[False] = False
    unnecessary_personal_data_present: Literal[False] = False
    shell_command_constructed: Literal[False] = False
    analytics_event_recorded: Literal[False] = False
    consent_assumed: Literal[False] = False
    retention_period_selected: Literal[False] = False
    deletion_export_policy_selected: Literal[False] = False
    runtime_authority: Literal[False] = False
    persistence_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_projection(self) -> "WebPrivacyControlProjection":
        for values, label in (
            (self.source_reference_ids, "source"),
            (self.provenance_reference_ids, "provenance"),
            (self.evidence_reference_ids, "evidence"),
        ):
            _unique_non_empty(values, label)
        _valid_open_decisions(self.open_decision_reference_ids)
        policy = self.surface_kind in {
            WebPrivacySurfaceKind.ANALYTICS_COLLECTION,
            WebPrivacySurfaceKind.RETENTION_POLICY,
            WebPrivacySurfaceKind.DELETION_EXPORT_POLICY,
        }
        if policy:
            required = (
                (_OD_013, _OD_014)
                if self.surface_kind is WebPrivacySurfaceKind.ANALYTICS_COLLECTION
                else (_OD_013,)
            )
            if (
                self.state is not WebPrivacyProjectionState.POLICY_BLOCKED
                or self.freshness is not WebReadFreshness.UNKNOWN
                or self.open_decision_reference_ids != required
            ):
                raise ValueError("policy projection must be blocked, unknown and open")
            if any(
                value is not None
                for value in (
                    self.policy_decision_reference_id,
                    self.safe_display_reference_id,
                    self.redaction_evidence_reference_id,
                    self.ambiguity_reference_id,
                )
            ):
                raise ValueError("policy projection cannot carry display or decision references")
        else:
            if (
                self.open_decision_reference_ids
                or self.state is WebPrivacyProjectionState.POLICY_BLOCKED
            ):
                raise ValueError("non-policy projection has invalid policy state")
            requirements = {
                WebPrivacyProjectionState.SAFE: (WebReadFreshness.FRESH, True, True, False),
                WebPrivacyProjectionState.REDACTED: (WebReadFreshness.FRESH, True, True, True),
                WebPrivacyProjectionState.STALE: (WebReadFreshness.STALE, True, True, False),
                WebPrivacyProjectionState.AMBIGUOUS: (
                    WebReadFreshness.AMBIGUOUS,
                    False,
                    False,
                    False,
                ),
                WebPrivacyProjectionState.UNSUPPORTED: (
                    WebReadFreshness.UNKNOWN,
                    False,
                    False,
                    False,
                ),
            }
            freshness, decision, display, redaction = requirements[self.state]
            if self.freshness is not freshness:
                raise ValueError("projection freshness does not match state")
            if (
                (self.policy_decision_reference_id is not None) != decision
                or (self.safe_display_reference_id is not None) != display
                or (self.redaction_evidence_reference_id is not None) != redaction
            ):
                raise ValueError("projection references do not match state")
            if self.state is WebPrivacyProjectionState.AMBIGUOUS:
                if self.ambiguity_reference_id is None:
                    raise ValueError("ambiguous projection requires ambiguity reference")
            elif self.ambiguity_reference_id is not None:
                raise ValueError("non-ambiguous projection cannot carry ambiguity")
        return self


class WebSecurityPrivacyAssessmentResult(_WebSecurityPrivacyContract):
    web_security_privacy_result_id: _NonEmptyReferenceId
    metadata: ContractMetadata
    query: RequestWebSecurityPrivacyAssessmentQuery
    state: WebSecurityPrivacyResultState
    freshness: WebReadFreshness
    owning_module_id: _NonEmptyReferenceId
    projections: tuple[WebPrivacyControlProjection, ...]
    projection_count: int = Field(ge=0)
    source_reference_ids: tuple[_NonEmptyReferenceId, ...]
    evidence_reference_ids: tuple[_NonEmptyReferenceId, ...]
    ambiguity_reference_id: _NonEmptyReferenceId | None = None
    reason_code: _NonEmptyReferenceId
    browser_minimized: Literal[True] = True
    redaction_enforced: Literal[True] = True
    safe_error_enforced: Literal[True] = True
    untrusted_input_preserved: Literal[True] = True
    secret_material_present: Literal[False] = False
    raw_provider_payload_present: Literal[False] = False
    raw_personal_data_present: Literal[False] = False
    internal_support_data_present: Literal[False] = False
    stack_trace_present: Literal[False] = False
    foreign_object_existence_disclosed: Literal[False] = False
    shell_command_constructed: Literal[False] = False
    analytics_event_recorded: Literal[False] = False
    consent_selected: Literal[False] = False
    retention_period_selected: Literal[False] = False
    deletion_export_policy_selected: Literal[False] = False
    runtime_authority: Literal[False] = False
    persistence_authority: Literal[False] = False
    route_or_ui_authority: Literal[False] = False
    business_success_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_result(self) -> "WebSecurityPrivacyAssessmentResult":
        if self.owning_module_id != WEB_CABINET_MODULE_ID:
            raise ValueError("result owner must be Web Cabinet")
        _unique_non_empty(self.source_reference_ids, "result sources")
        _unique_non_empty(self.evidence_reference_ids, "result evidence")
        if self.projection_count != len(self.projections):
            raise ValueError("projection count mismatch")
        ids = tuple(p.web_privacy_control_projection_id for p in self.projections)
        surfaces = tuple(p.surface_kind for p in self.projections)
        if len(ids) != len(set(ids)) or len(surfaces) != len(set(surfaces)):
            raise ValueError("projection identifiers and surfaces must be unique")
        q = self.query
        for p in self.projections:
            if (
                p.account_id != q.account_id
                or p.tenant_scope_reference_id != q.tenant_scope_reference_id
                or p.web_security_policy_reference_id != q.web_security_policy_reference_id
                or p.browser_minimization_policy_reference_id
                != q.browser_minimization_policy_reference_id
                or p.redaction_policy_reference_id != q.redaction_policy_reference_id
                or p.safe_error_policy_reference_id != q.safe_error_policy_reference_id
            ):
                raise ValueError("projection scope or policy mismatch")
            expected_gate = {
                WebPrivacySurfaceKind.ANALYTICS_COLLECTION: q.analytics_policy_gate_reference_id,
                WebPrivacySurfaceKind.RETENTION_POLICY: q.retention_policy_gate_reference_id,
                WebPrivacySurfaceKind.DELETION_EXPORT_POLICY: (
                    q.deletion_export_policy_gate_reference_id
                ),
            }.get(p.surface_kind, q.web_security_policy_reference_id)
            if p.policy_gate_reference_id != expected_gate:
                raise ValueError("projection policy gate mismatch")
        if self.state in {
            WebSecurityPrivacyResultState.FORBIDDEN,
            WebSecurityPrivacyResultState.UNSUPPORTED,
        }:
            expected = (WebReadFreshness.FRESH, WebReadFreshness.UNKNOWN)[
                self.state is WebSecurityPrivacyResultState.UNSUPPORTED
            ]
            if (
                self.projections
                or self.projection_count != 0
                or self.freshness is not expected
                or self.ambiguity_reference_id is not None
            ):
                raise ValueError("terminal result payload is invalid")
            return self
        if tuple(surfaces) != q.requested_surface_kinds:
            raise ValueError("result projections must cover requested surfaces in order")
        states = tuple(p.state for p in self.projections)
        allowed = {
            WebSecurityPrivacyResultState.SAFE: (
                {WebPrivacyProjectionState.SAFE},
                WebReadFreshness.FRESH,
                False,
            ),
            WebSecurityPrivacyResultState.REDACTED: (
                {WebPrivacyProjectionState.SAFE, WebPrivacyProjectionState.REDACTED},
                WebReadFreshness.FRESH,
                False,
            ),
            WebSecurityPrivacyResultState.STALE: (
                {
                    WebPrivacyProjectionState.SAFE,
                    WebPrivacyProjectionState.REDACTED,
                    WebPrivacyProjectionState.STALE,
                },
                WebReadFreshness.STALE,
                False,
            ),
            WebSecurityPrivacyResultState.AMBIGUOUS: (
                set(WebPrivacyProjectionState)
                - {WebPrivacyProjectionState.POLICY_BLOCKED, WebPrivacyProjectionState.UNSUPPORTED},
                WebReadFreshness.AMBIGUOUS,
                True,
            ),
            WebSecurityPrivacyResultState.POLICY_BLOCKED: (
                {
                    WebPrivacyProjectionState.SAFE,
                    WebPrivacyProjectionState.REDACTED,
                    WebPrivacyProjectionState.STALE,
                    WebPrivacyProjectionState.POLICY_BLOCKED,
                },
                WebReadFreshness.UNKNOWN,
                False,
            ),
        }[self.state]
        permitted, freshness, needs_ambiguity = allowed
        if self.freshness is not freshness or not states or any(s not in permitted for s in states):
            raise ValueError("result state composition is invalid")
        required_state = {
            WebSecurityPrivacyResultState.SAFE: WebPrivacyProjectionState.SAFE,
            WebSecurityPrivacyResultState.REDACTED: WebPrivacyProjectionState.REDACTED,
            WebSecurityPrivacyResultState.STALE: WebPrivacyProjectionState.STALE,
            WebSecurityPrivacyResultState.AMBIGUOUS: WebPrivacyProjectionState.AMBIGUOUS,
            WebSecurityPrivacyResultState.POLICY_BLOCKED: WebPrivacyProjectionState.POLICY_BLOCKED,
        }[self.state]
        if (
            required_state not in states
            or (needs_ambiguity and self.ambiguity_reference_id is None)
            or (not needs_ambiguity and self.ambiguity_reference_id is not None)
        ):
            raise ValueError("result does not contain required state or ambiguity")
        return self


__all__ = [
    "RequestWebSecurityPrivacyAssessmentQuery",
    "WebPrivacyControlProjection",
    "WebPrivacyProjectionState",
    "WebPrivacySurfaceKind",
    "WebSecurityPrivacyAssessmentResult",
    "WebSecurityPrivacyResultState",
]
