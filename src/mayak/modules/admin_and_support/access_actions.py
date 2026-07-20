"""Transport-neutral Admin & Support user-access action boundary."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts.metadata import ContractMetadata
from mayak.modules.admin_and_support.contracts import (
    SupportActionAuditRecord,
    SupportActionAuditState,
    SupportCommandEnvelope,
    SupportCommandPreparationState,
    SupportEvidenceReference,
    SupportSubjectKind,
)
from mayak.platform.boundaries import ENTITLEMENTS_AND_BILLING_MODULE_ID


class _AdminUserAccessContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class AdminUserAccessActionKind(str, Enum):
    ASSIGN_SUBSCRIPTION = "ASSIGN_SUBSCRIPTION"
    CHANGE_SUBSCRIPTION = "CHANGE_SUBSCRIPTION"
    EXTEND_SUBSCRIPTION = "EXTEND_SUBSCRIPTION"
    CANCEL_SUBSCRIPTION = "CANCEL_SUBSCRIPTION"
    CREATE_MANUAL_ACCESS_GRANT = "CREATE_MANUAL_ACCESS_GRANT"
    REVOKE_MANUAL_ACCESS_GRANT = "REVOKE_MANUAL_ACCESS_GRANT"


class AdminUserAccessOutcomeState(str, Enum):
    SUBSCRIPTION_ASSIGNED = "SUBSCRIPTION_ASSIGNED"
    SUBSCRIPTION_CHANGED = "SUBSCRIPTION_CHANGED"
    SUBSCRIPTION_EXTENDED = "SUBSCRIPTION_EXTENDED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"
    MANUAL_ACCESS_GRANTED = "MANUAL_ACCESS_GRANTED"
    MANUAL_ACCESS_REVOKED = "MANUAL_ACCESS_REVOKED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


_SUBSCRIPTION_ACTIONS = {
    AdminUserAccessActionKind.ASSIGN_SUBSCRIPTION,
    AdminUserAccessActionKind.CHANGE_SUBSCRIPTION,
    AdminUserAccessActionKind.EXTEND_SUBSCRIPTION,
    AdminUserAccessActionKind.CANCEL_SUBSCRIPTION,
}
_MANUAL_ACCESS_ACTIONS = {
    AdminUserAccessActionKind.CREATE_MANUAL_ACCESS_GRANT,
    AdminUserAccessActionKind.REVOKE_MANUAL_ACCESS_GRANT,
}
_SUBJECT_KIND_BY_ACTION = {
    **{kind: SupportSubjectKind.SUBSCRIPTION for kind in _SUBSCRIPTION_ACTIONS},
    **{kind: SupportSubjectKind.MANUAL_ACCESS_GRANT for kind in _MANUAL_ACCESS_ACTIONS},
}
_ACTION_FAMILY_BY_KIND = {
    AdminUserAccessActionKind.ASSIGN_SUBSCRIPTION: "ENTITLEMENTS_ASSIGN_SUBSCRIPTION",
    AdminUserAccessActionKind.CHANGE_SUBSCRIPTION: "ENTITLEMENTS_CHANGE_SUBSCRIPTION",
    AdminUserAccessActionKind.EXTEND_SUBSCRIPTION: (
        "ENTITLEMENTS_CHANGE_SUBSCRIPTION_EFFECTIVE_INTERVAL"
    ),
    AdminUserAccessActionKind.CANCEL_SUBSCRIPTION: "ENTITLEMENTS_CANCEL_SUBSCRIPTION",
    AdminUserAccessActionKind.CREATE_MANUAL_ACCESS_GRANT: (
        "ENTITLEMENTS_CREATE_MANUAL_ACCESS_GRANT"
    ),
    AdminUserAccessActionKind.REVOKE_MANUAL_ACCESS_GRANT: (
        "ENTITLEMENTS_REVOKE_MANUAL_ACCESS_GRANT"
    ),
}
_SUCCESSFUL_OUTCOME_BY_KIND = {
    AdminUserAccessActionKind.ASSIGN_SUBSCRIPTION: (
        AdminUserAccessOutcomeState.SUBSCRIPTION_ASSIGNED
    ),
    AdminUserAccessActionKind.CHANGE_SUBSCRIPTION: (
        AdminUserAccessOutcomeState.SUBSCRIPTION_CHANGED
    ),
    AdminUserAccessActionKind.EXTEND_SUBSCRIPTION: (
        AdminUserAccessOutcomeState.SUBSCRIPTION_EXTENDED
    ),
    AdminUserAccessActionKind.CANCEL_SUBSCRIPTION: (
        AdminUserAccessOutcomeState.SUBSCRIPTION_CANCELLED
    ),
    AdminUserAccessActionKind.CREATE_MANUAL_ACCESS_GRANT: (
        AdminUserAccessOutcomeState.MANUAL_ACCESS_GRANTED
    ),
    AdminUserAccessActionKind.REVOKE_MANUAL_ACCESS_GRANT: (
        AdminUserAccessOutcomeState.MANUAL_ACCESS_REVOKED
    ),
}
_AUDIT_STATE_BY_OUTCOME = {
    **{state: SupportActionAuditState.RECORDED for state in _SUCCESSFUL_OUTCOME_BY_KIND.values()},
    AdminUserAccessOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminUserAccessOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    AdminUserAccessOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminUserAccessOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    AdminUserAccessOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}


def _reject_empty_or_duplicate_evidence(
    evidence_references: tuple[SupportEvidenceReference, ...],
) -> None:
    identifiers = tuple(item.support_evidence_reference_id for item in evidence_references)
    if not identifiers or any(not identifier for identifier in identifiers):
        raise ValueError("evidence references must be non-empty")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate evidence references are not allowed")


class AdminUserAccessActionRequest(_AdminUserAccessContract):
    admin_user_access_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    action_kind: AdminUserAccessActionKind
    target_account_reference_id: str = Field(min_length=1)
    subscription_reference_id: str | None = Field(default=None, min_length=1)
    current_tariff_definition_reference_id: str | None = Field(default=None, min_length=1)
    requested_tariff_definition_reference_id: str | None = Field(default=None, min_length=1)
    manual_access_grant_reference_id: str | None = Field(default=None, min_length=1)
    capability_reference_id: str | None = Field(default=None, min_length=1)
    access_scope_reference_id: str = Field(min_length=1)
    effective_starts_at_reference_id: str = Field(min_length=1)
    effective_ends_at_reference_id: str = Field(min_length=1)
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    entitlements_access_authority: Literal[True] = True
    closed_effective_interval_required: Literal[True] = True
    open_interval_authority: Literal[False] = False
    payment_evidence_authority: Literal[False] = False
    provider_identity_authority: Literal[False] = False
    ui_flag_authority: Literal[False] = False
    direct_entitlements_write_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_matrix(self) -> "AdminUserAccessActionRequest":
        envelope = self.command_envelope
        if self.metadata != envelope.metadata:
            raise ValueError("request metadata must equal command envelope metadata")
        if self.metadata.causation_id is None:
            raise ValueError("request metadata requires causation id")
        if envelope.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("access envelope must be owned by Entitlements & Billing")
        if envelope.subject.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("access subject must be owned by Entitlements & Billing")
        if envelope.subject.subject_kind is not _SUBJECT_KIND_BY_ACTION[self.action_kind]:
            raise ValueError("subject kind does not match action kind")
        if envelope.subject.target_account_reference_id != self.target_account_reference_id:
            raise ValueError("subject target account must match request")
        expected_subject_reference = (
            self.subscription_reference_id
            if self.action_kind in _SUBSCRIPTION_ACTIONS
            else self.manual_access_grant_reference_id
        )
        if envelope.subject.safe_subject_reference_id != expected_subject_reference:
            raise ValueError("subject reference does not match action reference")
        if envelope.action_family_reference_id != _ACTION_FAMILY_BY_KIND[self.action_kind]:
            raise ValueError("action family does not match action kind")
        _reject_empty_or_duplicate_evidence(envelope.evidence_references)
        if self.effective_starts_at_reference_id == self.effective_ends_at_reference_id:
            raise ValueError("effective interval references must differ")
        if self.action_kind is AdminUserAccessActionKind.ASSIGN_SUBSCRIPTION:
            if (
                self.subscription_reference_id is None
                or self.requested_tariff_definition_reference_id is None
            ):
                raise ValueError("assign requires subscription and requested tariff references")
            if (
                self.current_tariff_definition_reference_id is not None
                or self.manual_access_grant_reference_id is not None
                or self.capability_reference_id is not None
            ):
                raise ValueError("assign has incompatible references")
        elif self.action_kind is AdminUserAccessActionKind.CHANGE_SUBSCRIPTION:
            if (
                self.subscription_reference_id is None
                or self.current_tariff_definition_reference_id is None
                or self.requested_tariff_definition_reference_id is None
            ):
                raise ValueError(
                    "change requires subscription and current/requested tariff references"
                )
            if (
                self.current_tariff_definition_reference_id
                == self.requested_tariff_definition_reference_id
            ):
                raise ValueError("change tariff references must differ")
            if (
                self.manual_access_grant_reference_id is not None
                or self.capability_reference_id is not None
            ):
                raise ValueError("change has incompatible references")
        elif self.action_kind in {
            AdminUserAccessActionKind.EXTEND_SUBSCRIPTION,
            AdminUserAccessActionKind.CANCEL_SUBSCRIPTION,
        }:
            if (
                self.subscription_reference_id is None
                or self.current_tariff_definition_reference_id is None
            ):
                raise ValueError(
                    "subscription action requires subscription and current tariff references"
                )
            if (
                self.requested_tariff_definition_reference_id is not None
                or self.manual_access_grant_reference_id is not None
                or self.capability_reference_id is not None
            ):
                raise ValueError("subscription action has incompatible references")
        else:
            if (
                self.manual_access_grant_reference_id is None
                or self.capability_reference_id is None
            ):
                raise ValueError("manual access action requires grant and capability references")
            if (
                self.subscription_reference_id is not None
                or self.current_tariff_definition_reference_id is not None
                or self.requested_tariff_definition_reference_id is not None
            ):
                raise ValueError("manual access action has incompatible references")
        return self


class AdminUserAccessActionOutcome(_AdminUserAccessContract):
    admin_user_access_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminUserAccessActionRequest
    state: AdminUserAccessOutcomeState
    entitlements_access_decision_reference_id: str = Field(min_length=1)
    authoritative_subscription_reference_id: str | None = Field(default=None, min_length=1)
    authoritative_manual_access_grant_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    entitlements_outcome_authority: Literal[True] = True
    admin_support_access_state_authority: Literal[False] = False
    open_interval_authority: Literal[False] = False
    payment_evidence_authority: Literal[False] = False
    provider_identity_authority: Literal[False] = False
    ui_flag_authority: Literal[False] = False
    direct_entitlements_write_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "AdminUserAccessActionOutcome":
        request = self.request
        envelope = request.command_envelope
        if envelope.state is not SupportCommandPreparationState.PREPARED:
            raise ValueError("outcome requires prepared request")
        if envelope.owning_command_reference_id is None:
            raise ValueError("outcome requires owning command reference")
        if self.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("outcome correlation must match request")
        if self.metadata.causation_id != request.metadata.message_id:
            raise ValueError("outcome causation must match request message id")
        successful = _SUCCESSFUL_OUTCOME_BY_KIND[request.action_kind]
        if self.state in _SUCCESSFUL_OUTCOME_BY_KIND.values() and self.state is not successful:
            raise ValueError("successful outcome does not match action kind")
        subscription_family = request.action_kind in _SUBSCRIPTION_ACTIONS
        if self.state in {successful, AdminUserAccessOutcomeState.UNCHANGED}:
            if subscription_family and self.authoritative_subscription_reference_id is None:
                raise ValueError(
                    "subscription outcome requires authoritative subscription reference"
                )
            if (
                not subscription_family
                and self.authoritative_manual_access_grant_reference_id is None
            ):
                raise ValueError("manual access outcome requires authoritative grant reference")
            if (
                subscription_family
                and self.authoritative_manual_access_grant_reference_id is not None
            ):
                raise ValueError("subscription outcome cannot carry grant reference")
            if not subscription_family and self.authoritative_subscription_reference_id is not None:
                raise ValueError("manual access outcome cannot carry subscription reference")
        if self.state in {
            AdminUserAccessOutcomeState.BLOCKED,
            AdminUserAccessOutcomeState.REJECTED,
            AdminUserAccessOutcomeState.CONFLICT,
            AdminUserAccessOutcomeState.AMBIGUOUS,
        } and (
            self.authoritative_subscription_reference_id is not None
            or self.authoritative_manual_access_grant_reference_id is not None
        ):
            raise ValueError("non-success outcome cannot carry authoritative reference")
        _reject_empty_or_duplicate_evidence(self.evidence_references)
        _reject_empty_or_duplicate_evidence(self.audit_record.evidence_references)
        outcome_ids = {item.support_evidence_reference_id for item in self.evidence_references}
        audit_ids = {
            item.support_evidence_reference_id for item in self.audit_record.evidence_references
        }
        if outcome_ids != audit_ids:
            raise ValueError("audit evidence must equal outcome evidence")
        audit = self.audit_record
        if (
            audit.support_action_id != envelope.support_action_id
            or audit.support_case_id != envelope.support_case_id
        ):
            raise ValueError("audit support references must match envelope")
        if audit.actor_context != envelope.actor_context or audit.subject != envelope.subject:
            raise ValueError("audit actor and subject must match envelope")
        if audit.action_family_reference_id != envelope.action_family_reference_id:
            raise ValueError("audit action family must match envelope")
        if audit.reason_code != envelope.reason_code:
            raise ValueError("audit reason must match envelope")
        if audit.requested_command_reference_id != envelope.owning_command_reference_id:
            raise ValueError("audit command reference must match envelope")
        if audit.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("audit owner must be Entitlements & Billing")
        if (
            audit.owning_module_outcome_reference_id
            != self.entitlements_access_decision_reference_id
        ):
            raise ValueError("audit outcome reference must match Entitlements decision")
        if audit.state is not _AUDIT_STATE_BY_OUTCOME[self.state]:
            raise ValueError("audit state does not match outcome state")
        if audit.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("audit correlation must match request")
        if audit.metadata.causation_id != self.metadata.message_id:
            raise ValueError("audit causation must match outcome message id")
        return self


__all__ = [
    "AdminUserAccessActionKind",
    "AdminUserAccessOutcomeState",
    "AdminUserAccessActionRequest",
    "AdminUserAccessActionOutcome",
]
