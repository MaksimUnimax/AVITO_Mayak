from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mayak.contracts import ContractMetadata
from mayak.modules.admin_and_support.contracts import (
    SupportActionAuditRecord,
    SupportActionAuditState,
    SupportCommandEnvelope,
    SupportCommandPreparationState,
    SupportEvidenceReference,
    SupportSubjectKind,
)
from mayak.platform.boundaries import IDENTITY_AND_ACCESS_MODULE_ID


class _AdminRoleActionContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class AdminRoleActionKind(str, Enum):
    ASSIGN = "ASSIGN"
    CHANGE = "CHANGE"
    REVOKE = "REVOKE"


class AdminRoleActionOutcomeState(str, Enum):
    ASSIGNED = "ASSIGNED"
    REVOKED = "REVOKED"
    UNCHANGED = "UNCHANGED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"


_ACTION_FAMILY_BY_KIND = {
    AdminRoleActionKind.ASSIGN: "IDENTITY_ASSIGN_ROLE",
    AdminRoleActionKind.CHANGE: "IDENTITY_CHANGE_ROLE",
    AdminRoleActionKind.REVOKE: "IDENTITY_REVOKE_ROLE",
}

_AUDIT_STATE_BY_OUTCOME = {
    AdminRoleActionOutcomeState.ASSIGNED: SupportActionAuditState.RECORDED,
    AdminRoleActionOutcomeState.REVOKED: SupportActionAuditState.RECORDED,
    AdminRoleActionOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminRoleActionOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminRoleActionOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
}


def _reject_duplicate_evidence_references(
    evidence_references: tuple[SupportEvidenceReference, ...],
) -> None:
    identifiers = tuple(item.support_evidence_reference_id for item in evidence_references)
    if not identifiers:
        raise ValueError("evidence references must be non-empty")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate evidence references are not allowed")


class AdminRoleActionRequest(_AdminRoleActionContract):
    admin_role_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    action_kind: AdminRoleActionKind
    target_account_reference_id: str = Field(min_length=1)
    old_role_reference_id: str | None = Field(default=None, min_length=1)
    new_role_reference_id: str | None = Field(default=None, min_length=1)
    identity_role_scope_reference_id: str = Field(min_length=1)
    identity_target_scope_reference_id: str = Field(min_length=1)
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    identity_role_taxonomy_authority: Literal[True] = True
    client_role_authority: Literal[False] = False
    provider_identity_role_authority: Literal[False] = False
    ui_role_flag_authority: Literal[False] = False
    direct_identity_write_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_matrix(self) -> "AdminRoleActionRequest":
        envelope = self.command_envelope
        if self.metadata != envelope.metadata:
            raise ValueError("request metadata must equal command envelope metadata")
        if self.metadata.causation_id is None:
            raise ValueError("request metadata requires causation id")
        if envelope.owning_module_id != IDENTITY_AND_ACCESS_MODULE_ID:
            raise ValueError("role action envelope must be owned by Identity & Access")
        if envelope.subject.subject_kind is not SupportSubjectKind.ACCOUNT:
            raise ValueError("role action subject must be an account")
        if envelope.subject.owning_module_id != IDENTITY_AND_ACCESS_MODULE_ID:
            raise ValueError("role action subject must be owned by Identity & Access")
        if envelope.subject.target_account_reference_id != self.target_account_reference_id:
            raise ValueError("target account reference must match subject")
        if envelope.action_family_reference_id != _ACTION_FAMILY_BY_KIND[self.action_kind]:
            raise ValueError("action family does not match action kind")
        _reject_duplicate_evidence_references(envelope.evidence_references)
        if self.action_kind is AdminRoleActionKind.ASSIGN:
            if self.old_role_reference_id is not None or self.new_role_reference_id is None:
                raise ValueError("assign requires new role and no old role")
        elif self.action_kind is AdminRoleActionKind.CHANGE:
            if (
                self.old_role_reference_id is None
                or self.new_role_reference_id is None
                or self.old_role_reference_id == self.new_role_reference_id
            ):
                raise ValueError("change requires different old and new roles")
        elif self.old_role_reference_id is None or self.new_role_reference_id is not None:
            raise ValueError("revoke requires old role and no new role")
        return self


class AdminRoleActionOutcome(_AdminRoleActionContract):
    admin_role_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminRoleActionRequest
    state: AdminRoleActionOutcomeState
    identity_role_assignment_decision_reference_id: str = Field(min_length=1)
    identity_role_assignment_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    identity_outcome_authority: Literal[True] = True
    admin_support_role_state_authority: Literal[False] = False
    direct_identity_write_authority: Literal[False] = False
    provider_role_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "AdminRoleActionOutcome":
        request = self.request
        envelope = request.command_envelope
        if envelope.state is not SupportCommandPreparationState.PREPARED:
            raise ValueError("outcome requires prepared request")
        if envelope.owning_command_reference_id is None:
            raise ValueError("outcome requires owning command reference")
        if self.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("outcome correlation must equal request correlation")
        if self.metadata.causation_id != request.metadata.message_id:
            raise ValueError("outcome causation must equal request message id")
        if self.state is AdminRoleActionOutcomeState.ASSIGNED and request.action_kind not in {
            AdminRoleActionKind.ASSIGN,
            AdminRoleActionKind.CHANGE,
        }:
            raise ValueError("assigned outcome is invalid for revoke")
        if (
            self.state is AdminRoleActionOutcomeState.REVOKED
            and request.action_kind is not AdminRoleActionKind.REVOKE
        ):
            raise ValueError("revoked outcome is invalid for assign or change")
        if self.state in {
            AdminRoleActionOutcomeState.ASSIGNED,
            AdminRoleActionOutcomeState.REVOKED,
            AdminRoleActionOutcomeState.UNCHANGED,
        } and self.identity_role_assignment_reference_id is None:
            raise ValueError("successful or unchanged outcome requires assignment reference")
        if self.state in {
            AdminRoleActionOutcomeState.REJECTED,
            AdminRoleActionOutcomeState.CONFLICT,
        } and self.identity_role_assignment_reference_id is not None:
            raise ValueError("rejected or conflict outcome cannot carry assignment reference")
        _reject_duplicate_evidence_references(self.evidence_references)
        _reject_duplicate_evidence_references(self.audit_record.evidence_references)
        outcome_ids = {
            item.support_evidence_reference_id for item in self.evidence_references
        }
        audit_ids = {
            item.support_evidence_reference_id for item in self.audit_record.evidence_references
        }
        if outcome_ids != audit_ids:
            raise ValueError("audit evidence must equal outcome evidence")
        if self.audit_record.support_action_id != envelope.support_action_id:
            raise ValueError("audit support action must match envelope")
        if self.audit_record.support_case_id != envelope.support_case_id:
            raise ValueError("audit support case must match envelope")
        if self.audit_record.actor_context != envelope.actor_context:
            raise ValueError("audit actor must match envelope")
        if self.audit_record.subject != envelope.subject:
            raise ValueError("audit subject must match envelope")
        if self.audit_record.action_family_reference_id != envelope.action_family_reference_id:
            raise ValueError("audit action family must match envelope")
        if self.audit_record.reason_code != envelope.reason_code:
            raise ValueError("audit reason must match envelope")
        if self.audit_record.requested_command_reference_id != envelope.owning_command_reference_id:
            raise ValueError("audit command reference must match envelope")
        if self.audit_record.owning_module_id != IDENTITY_AND_ACCESS_MODULE_ID:
            raise ValueError("audit owner must be Identity & Access")
        if (
            self.audit_record.owning_module_outcome_reference_id
            != self.identity_role_assignment_decision_reference_id
        ):
            raise ValueError("audit outcome must match Identity decision reference")
        if self.audit_record.state is not _AUDIT_STATE_BY_OUTCOME[self.state]:
            raise ValueError("audit state does not match outcome state")
        if self.audit_record.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("audit correlation must match request")
        if self.audit_record.metadata.causation_id != self.metadata.message_id:
            raise ValueError("audit causation must match outcome message id")
        return self


__all__ = [
    "AdminRoleActionKind",
    "AdminRoleActionOutcomeState",
    "AdminRoleActionRequest",
    "AdminRoleActionOutcome",
]
