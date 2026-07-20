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


class _AdminTariffCatalogContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class AdminTariffCatalogActionKind(str, Enum):
    CREATE = "CREATE"
    EDIT = "EDIT"
    PUBLISH = "PUBLISH"
    DEACTIVATE = "DEACTIVATE"


class AdminTariffPopulationEffect(str, Enum):
    FUTURE_ASSIGNMENTS_ONLY = "FUTURE_ASSIGNMENTS_ONLY"
    EXISTING_SUBSCRIPTIONS_INCLUDED = "EXISTING_SUBSCRIPTIONS_INCLUDED"
    MANUAL_MIGRATION_REQUIRED = "MANUAL_MIGRATION_REQUIRED"
    UNRESOLVED = "UNRESOLVED"


class AdminTariffCatalogOutcomeState(str, Enum):
    CREATED = "CREATED"
    EDITED = "EDITED"
    PUBLISHED = "PUBLISHED"
    DEACTIVATED = "DEACTIVATED"
    UNCHANGED = "UNCHANGED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


_ACTION_FAMILY_BY_KIND = {
    AdminTariffCatalogActionKind.CREATE: "ENTITLEMENTS_CREATE_TARIFF_DEFINITION",
    AdminTariffCatalogActionKind.EDIT: "ENTITLEMENTS_EDIT_TARIFF_DEFINITION",
    AdminTariffCatalogActionKind.PUBLISH: "ENTITLEMENTS_PUBLISH_TARIFF_DEFINITION",
    AdminTariffCatalogActionKind.DEACTIVATE: "ENTITLEMENTS_DEACTIVATE_TARIFF_DEFINITION",
}

_SUCCESSFUL_OUTCOME_BY_KIND = {
    AdminTariffCatalogActionKind.CREATE: AdminTariffCatalogOutcomeState.CREATED,
    AdminTariffCatalogActionKind.EDIT: AdminTariffCatalogOutcomeState.EDITED,
    AdminTariffCatalogActionKind.PUBLISH: AdminTariffCatalogOutcomeState.PUBLISHED,
    AdminTariffCatalogActionKind.DEACTIVATE: AdminTariffCatalogOutcomeState.DEACTIVATED,
}

_AUDIT_STATE_BY_OUTCOME = {
    AdminTariffCatalogOutcomeState.CREATED: SupportActionAuditState.RECORDED,
    AdminTariffCatalogOutcomeState.EDITED: SupportActionAuditState.RECORDED,
    AdminTariffCatalogOutcomeState.PUBLISHED: SupportActionAuditState.RECORDED,
    AdminTariffCatalogOutcomeState.DEACTIVATED: SupportActionAuditState.RECORDED,
    AdminTariffCatalogOutcomeState.UNCHANGED: SupportActionAuditState.REPLAYED,
    AdminTariffCatalogOutcomeState.BLOCKED: SupportActionAuditState.REJECTED,
    AdminTariffCatalogOutcomeState.REJECTED: SupportActionAuditState.REJECTED,
    AdminTariffCatalogOutcomeState.CONFLICT: SupportActionAuditState.CONFLICT,
    AdminTariffCatalogOutcomeState.AMBIGUOUS: SupportActionAuditState.MANUAL_REVIEW_REQUIRED,
}


def _reject_duplicate_evidence_references(
    evidence_references: tuple[SupportEvidenceReference, ...],
) -> None:
    identifiers = tuple(item.support_evidence_reference_id for item in evidence_references)
    if not identifiers:
        raise ValueError("evidence references must be non-empty")
    if any(not identifier for identifier in identifiers):
        raise ValueError("evidence references must be non-empty")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate evidence references are not allowed")


class AdminTariffCatalogActionRequest(_AdminTariffCatalogContract):
    admin_tariff_catalog_action_request_id: str = Field(min_length=1)
    metadata: ContractMetadata
    command_envelope: SupportCommandEnvelope
    action_kind: AdminTariffCatalogActionKind
    target_tariff_definition_reference_id: str = Field(min_length=1)
    prior_tariff_definition_reference_id: str | None = Field(default=None, min_length=1)
    semantic_version_reference_id: str = Field(min_length=1)
    effective_interval_reference_id: str = Field(min_length=1)
    population_effect: AdminTariffPopulationEffect
    existing_subscription_effect_policy_reference_id: str | None = Field(
        default=None, min_length=1
    )
    timestamp_policy_reference_id: str = Field(min_length=1)
    server_authorization_required: Literal[True] = True
    entitlements_tariff_authority: Literal[True] = True
    published_history_preserved: Literal[True] = True
    unresolved_product_values_authority: Literal[False] = False
    retroactive_effect_authority: Literal[False] = False
    direct_entitlements_write_authority: Literal[False] = False
    payment_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_request_matrix(self) -> "AdminTariffCatalogActionRequest":
        envelope = self.command_envelope
        if self.metadata != envelope.metadata:
            raise ValueError("request metadata must equal command envelope metadata")
        if self.metadata.causation_id is None:
            raise ValueError("request metadata requires causation id")
        if envelope.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("tariff envelope must be owned by Entitlements & Billing")
        if envelope.subject.subject_kind is not SupportSubjectKind.TARIFF_DEFINITION:
            raise ValueError("tariff subject must be a tariff definition")
        if envelope.subject.owning_module_id != ENTITLEMENTS_AND_BILLING_MODULE_ID:
            raise ValueError("tariff subject must be owned by Entitlements & Billing")
        if envelope.subject.safe_subject_reference_id != self.target_tariff_definition_reference_id:
            raise ValueError("subject reference must match target reference")
        if envelope.subject.target_account_reference_id is not None:
            raise ValueError("tariff subject cannot carry target account reference")
        if envelope.action_family_reference_id != _ACTION_FAMILY_BY_KIND[self.action_kind]:
            raise ValueError("action family does not match action kind")
        _reject_duplicate_evidence_references(envelope.evidence_references)
        if self.action_kind is AdminTariffCatalogActionKind.CREATE:
            if self.prior_tariff_definition_reference_id is not None:
                raise ValueError("create cannot carry prior reference")
        elif self.action_kind is AdminTariffCatalogActionKind.EDIT:
            if self.prior_tariff_definition_reference_id is None:
                raise ValueError("edit requires prior reference")
            if (
                self.prior_tariff_definition_reference_id
                == self.target_tariff_definition_reference_id
            ):
                raise ValueError("edit prior and target references must differ")
        elif self.prior_tariff_definition_reference_id is not None:
            raise ValueError("publish or deactivate cannot carry prior reference")
        if envelope.state is SupportCommandPreparationState.PREPARED and (
            self.population_effect is not AdminTariffPopulationEffect.FUTURE_ASSIGNMENTS_ONLY
        ):
            raise ValueError("prepared request requires future assignments only")
        if self.population_effect in {
            AdminTariffPopulationEffect.EXISTING_SUBSCRIPTIONS_INCLUDED,
            AdminTariffPopulationEffect.MANUAL_MIGRATION_REQUIRED,
        }:
            if envelope.state is not SupportCommandPreparationState.POLICY_BLOCKED:
                raise ValueError("subscription effect must be policy blocked")
            if self.existing_subscription_effect_policy_reference_id is None:
                raise ValueError("subscription effect requires policy reference")
        elif self.population_effect is AdminTariffPopulationEffect.UNRESOLVED:
            if envelope.state is not SupportCommandPreparationState.POLICY_BLOCKED:
                raise ValueError("unresolved effect must be policy blocked")
            if self.existing_subscription_effect_policy_reference_id is not None:
                raise ValueError("unresolved effect cannot carry policy reference")
        elif self.existing_subscription_effect_policy_reference_id is not None:
            raise ValueError("future-only effect cannot carry policy reference")
        return self


class AdminTariffCatalogActionOutcome(_AdminTariffCatalogContract):
    admin_tariff_catalog_action_outcome_id: str = Field(min_length=1)
    metadata: ContractMetadata
    request: AdminTariffCatalogActionRequest
    state: AdminTariffCatalogOutcomeState
    entitlements_tariff_definition_decision_reference_id: str = Field(min_length=1)
    authoritative_tariff_definition_reference_id: str | None = Field(default=None, min_length=1)
    audit_record: SupportActionAuditRecord
    evidence_references: tuple[SupportEvidenceReference, ...]
    entitlements_outcome_authority: Literal[True] = True
    admin_support_tariff_state_authority: Literal[False] = False
    unresolved_product_values_authority: Literal[False] = False
    retroactive_effect_authority: Literal[False] = False
    direct_entitlements_write_authority: Literal[False] = False
    payment_authority: Literal[False] = False
    business_execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def _validate_outcome_matrix(self) -> "AdminTariffCatalogActionOutcome":
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
        if self.state in _SUCCESSFUL_OUTCOME_BY_KIND.values() and (
            self.state is not _SUCCESSFUL_OUTCOME_BY_KIND[request.action_kind]
        ):
            raise ValueError("successful outcome does not match action kind")
        if self.state in {
            AdminTariffCatalogOutcomeState.CREATED,
            AdminTariffCatalogOutcomeState.EDITED,
            AdminTariffCatalogOutcomeState.PUBLISHED,
            AdminTariffCatalogOutcomeState.DEACTIVATED,
            AdminTariffCatalogOutcomeState.UNCHANGED,
        } and self.authoritative_tariff_definition_reference_id is None:
            raise ValueError("successful or unchanged outcome requires authoritative reference")
        if self.state in {
            AdminTariffCatalogOutcomeState.BLOCKED,
            AdminTariffCatalogOutcomeState.REJECTED,
            AdminTariffCatalogOutcomeState.CONFLICT,
            AdminTariffCatalogOutcomeState.AMBIGUOUS,
        } and self.authoritative_tariff_definition_reference_id is not None:
            raise ValueError("blocked outcome cannot carry authoritative reference")
        _reject_duplicate_evidence_references(self.evidence_references)
        _reject_duplicate_evidence_references(self.audit_record.evidence_references)
        outcome_ids = {item.support_evidence_reference_id for item in self.evidence_references}
        audit_ids = {
            item.support_evidence_reference_id for item in self.audit_record.evidence_references
        }
        if outcome_ids != audit_ids:
            raise ValueError("audit evidence must equal outcome evidence")
        audit = self.audit_record
        if audit.support_action_id != envelope.support_action_id:
            raise ValueError("audit support action must match envelope")
        if audit.support_case_id != envelope.support_case_id:
            raise ValueError("audit support case must match envelope")
        if audit.actor_context != envelope.actor_context:
            raise ValueError("audit actor must match envelope")
        if audit.subject != envelope.subject:
            raise ValueError("audit subject must match envelope")
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
            != self.entitlements_tariff_definition_decision_reference_id
        ):
            raise ValueError("audit outcome must match Entitlements decision reference")
        if audit.state is not _AUDIT_STATE_BY_OUTCOME[self.state]:
            raise ValueError("audit state does not match outcome state")
        if audit.metadata.correlation_id != request.metadata.correlation_id:
            raise ValueError("audit correlation must match request")
        if audit.metadata.causation_id != self.metadata.message_id:
            raise ValueError("audit causation must match outcome message id")
        return self


__all__ = [
    "AdminTariffCatalogActionKind",
    "AdminTariffPopulationEffect",
    "AdminTariffCatalogOutcomeState",
    "AdminTariffCatalogActionRequest",
    "AdminTariffCatalogActionOutcome",
]
