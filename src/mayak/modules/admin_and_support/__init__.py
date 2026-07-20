"""Admin and Support module package."""

from mayak.modules.admin_and_support.contracts import (
    SupportActionAuditRecord,
    SupportActionAuditState,
    SupportActorContext,
    SupportCase,
    SupportCaseState,
    SupportCommandEnvelope,
    SupportCommandPreparationState,
    SupportEscalationRecord,
    SupportEscalationState,
    SupportEvidenceKind,
    SupportEvidenceReference,
    SupportExplanationRecord,
    SupportExplanationState,
    SupportFreshnessState,
    SupportReadModel,
    SupportReadState,
    SupportSubjectKind,
    SupportSubjectReference,
    SupportWorkItem,
    SupportWorkItemState,
)
from mayak.platform.boundaries import ADMIN_AND_SUPPORT_MODULE_ID

MODULE_ID = ADMIN_AND_SUPPORT_MODULE_ID

__all__ = [
    "MODULE_ID",
    "SupportActionAuditRecord",
    "SupportActionAuditState",
    "SupportActorContext",
    "SupportCase",
    "SupportCaseState",
    "SupportCommandEnvelope",
    "SupportCommandPreparationState",
    "SupportEscalationRecord",
    "SupportEscalationState",
    "SupportEvidenceKind",
    "SupportEvidenceReference",
    "SupportExplanationRecord",
    "SupportExplanationState",
    "SupportFreshnessState",
    "SupportReadModel",
    "SupportReadState",
    "SupportSubjectKind",
    "SupportSubjectReference",
    "SupportWorkItem",
    "SupportWorkItemState",
]
