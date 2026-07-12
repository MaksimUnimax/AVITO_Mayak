from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import (
    AgentLifecycleStatus,
    EgressAgent,
    EgressRoute,
    RouteEvidenceStatus,
    RouteFamily,
    RouteLifecycleStatus,
    SessionPolicyStatus,
)

ER03_TASK_ID = "ER-03-AGENT-ROUTE-REGISTRATION-20260712-004"

__all__ = (
    "ER03_TASK_ID",
    "AgentRegistrationStatus",
    "RouteRegistrationStatus",
    "AgentRouteAssociationStatus",
    "AgentRegistration",
    "RouteRegistration",
    "AgentRouteAssociation",
    "AgentRouteRegistrationBoundary",
)


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_text_tuple(value: object, field_name: str) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    for item in items:
        _require_text(item, field_name)
    return items  # type: ignore[return-value]


def _require_exact_enum(value: object, enum_cls: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_true(value: object, field_name: str) -> bool:
    validated = _require_bool(value, field_name)
    if validated is not True:
        raise ValueError(f"{field_name} must be True")
    return validated


def _require_false(value: object, field_name: str) -> bool:
    validated = _require_bool(value, field_name)
    if validated is not False:
        raise ValueError(f"{field_name} must be False")
    return validated


class AgentRegistrationStatus(str, Enum):
    REGISTERED = "REGISTERED"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class RouteRegistrationStatus(str, Enum):
    REGISTERED = "REGISTERED"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class AgentRouteAssociationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REGISTRATION_BLOCKED = "REGISTRATION_BLOCKED"
    CONFLICT = "CONFLICT"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class AgentRegistration:
    registration_id: str
    agent_id: str
    environment_id: str
    agent_class: str
    accountable_owner_reference: str
    purpose_scope: tuple[str, ...]
    trust_scope: tuple[str, ...]
    source_release_reference: str
    credential_reference: str | None
    connectivity_boundary_reference: str
    isolation_boundary_reference: str
    privacy_boundary_reference: str
    replaceable_execution_dependency: bool
    primary_database_access_allowed: bool
    business_state_ownership_allowed: bool
    public_unauthenticated_inbound_allowed: bool
    foreign_resource_reuse_allowed: bool
    arbitrary_command_execution_allowed: bool
    status: AgentRegistrationStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "registration_id", _require_text(self.registration_id, "registration_id")
        )
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(
            self, "environment_id", _require_text(self.environment_id, "environment_id")
        )
        object.__setattr__(self, "agent_class", _require_text(self.agent_class, "agent_class"))
        object.__setattr__(
            self,
            "accountable_owner_reference",
            _require_text(self.accountable_owner_reference, "accountable_owner_reference"),
        )
        object.__setattr__(
            self,
            "purpose_scope",
            _require_text_tuple(self.purpose_scope, "purpose_scope"),
        )
        object.__setattr__(
            self,
            "trust_scope",
            _require_text_tuple(self.trust_scope, "trust_scope"),
        )
        object.__setattr__(
            self,
            "source_release_reference",
            _require_text(self.source_release_reference, "source_release_reference"),
        )
        object.__setattr__(
            self,
            "credential_reference",
            _require_optional_text(self.credential_reference, "credential_reference"),
        )
        object.__setattr__(
            self,
            "connectivity_boundary_reference",
            _require_text(self.connectivity_boundary_reference, "connectivity_boundary_reference"),
        )
        object.__setattr__(
            self,
            "isolation_boundary_reference",
            _require_text(self.isolation_boundary_reference, "isolation_boundary_reference"),
        )
        object.__setattr__(
            self,
            "privacy_boundary_reference",
            _require_text(self.privacy_boundary_reference, "privacy_boundary_reference"),
        )
        object.__setattr__(
            self,
            "replaceable_execution_dependency",
            _require_true(
                self.replaceable_execution_dependency, "replaceable_execution_dependency"
            ),
        )
        object.__setattr__(
            self,
            "primary_database_access_allowed",
            _require_false(self.primary_database_access_allowed, "primary_database_access_allowed"),
        )
        object.__setattr__(
            self,
            "business_state_ownership_allowed",
            _require_false(
                self.business_state_ownership_allowed, "business_state_ownership_allowed"
            ),
        )
        object.__setattr__(
            self,
            "public_unauthenticated_inbound_allowed",
            _require_false(
                self.public_unauthenticated_inbound_allowed,
                "public_unauthenticated_inbound_allowed",
            ),
        )
        object.__setattr__(
            self,
            "foreign_resource_reuse_allowed",
            _require_false(self.foreign_resource_reuse_allowed, "foreign_resource_reuse_allowed"),
        )
        object.__setattr__(
            self,
            "arbitrary_command_execution_allowed",
            _require_false(
                self.arbitrary_command_execution_allowed,
                "arbitrary_command_execution_allowed",
            ),
        )
        object.__setattr__(
            self,
            "status",
            _require_exact_enum(self.status, AgentRegistrationStatus, "status"),
        )
        reason_codes = _require_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )
        if self.status is AgentRegistrationStatus.REGISTERED:
            if self.credential_reference is None:
                raise ValueError("credential_reference is required when status is REGISTERED")
            if not self.purpose_scope:
                raise ValueError("purpose_scope is required when status is REGISTERED")
            if not self.trust_scope:
                raise ValueError("trust_scope is required when status is REGISTERED")
            if not evidence_reference_ids:
                raise ValueError("evidence_reference_ids is required when status is REGISTERED")
        if (
            self.status
            in {
                AgentRegistrationStatus.REGISTRATION_BLOCKED,
                AgentRegistrationStatus.CONFLICT,
                AgentRegistrationStatus.REJECTED,
                AgentRegistrationStatus.SUSPENDED,
                AgentRegistrationStatus.RETIRED,
            }
            and not reason_codes
        ):
            raise ValueError("reason_codes are required for non-registered agent outcomes")
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)


@dataclass(frozen=True, slots=True)
class RouteRegistration:
    registration_id: str
    route_id: str
    agent_id: str
    agent_registration_id: str
    environment_id: str
    source_release_reference: str
    route_family: RouteFamily
    purpose_scope: tuple[str, ...]
    capability_ids: tuple[str, ...]
    unsupported_classes: tuple[str, ...]
    evidence_status: RouteEvidenceStatus
    session_policy_status: SessionPolicyStatus
    restriction_reference: str | None
    selection_policy_reference: str | None
    privacy_boundary_reference: str
    status: RouteRegistrationStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "registration_id", _require_text(self.registration_id, "registration_id")
        )
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(
            self,
            "agent_registration_id",
            _require_text(self.agent_registration_id, "agent_registration_id"),
        )
        object.__setattr__(
            self, "environment_id", _require_text(self.environment_id, "environment_id")
        )
        object.__setattr__(
            self,
            "source_release_reference",
            _require_text(self.source_release_reference, "source_release_reference"),
        )
        object.__setattr__(
            self,
            "route_family",
            _require_exact_enum(self.route_family, RouteFamily, "route_family"),
        )
        object.__setattr__(
            self,
            "purpose_scope",
            _require_text_tuple(self.purpose_scope, "purpose_scope"),
        )
        object.__setattr__(
            self,
            "capability_ids",
            _require_text_tuple(self.capability_ids, "capability_ids"),
        )
        object.__setattr__(
            self,
            "unsupported_classes",
            _require_text_tuple(self.unsupported_classes, "unsupported_classes"),
        )
        object.__setattr__(
            self,
            "evidence_status",
            _require_exact_enum(self.evidence_status, RouteEvidenceStatus, "evidence_status"),
        )
        object.__setattr__(
            self,
            "session_policy_status",
            _require_exact_enum(
                self.session_policy_status, SessionPolicyStatus, "session_policy_status"
            ),
        )
        object.__setattr__(
            self,
            "restriction_reference",
            _require_optional_text(self.restriction_reference, "restriction_reference"),
        )
        object.__setattr__(
            self,
            "selection_policy_reference",
            _require_optional_text(self.selection_policy_reference, "selection_policy_reference"),
        )
        object.__setattr__(
            self,
            "privacy_boundary_reference",
            _require_text(self.privacy_boundary_reference, "privacy_boundary_reference"),
        )
        object.__setattr__(
            self,
            "status",
            _require_exact_enum(self.status, RouteRegistrationStatus, "status"),
        )
        reason_codes = _require_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )
        if self.status is RouteRegistrationStatus.REGISTERED:
            if not self.purpose_scope:
                raise ValueError("purpose_scope is required when status is REGISTERED")
            if not self.capability_ids:
                raise ValueError("capability_ids is required when status is REGISTERED")
            if not evidence_reference_ids:
                raise ValueError("evidence_reference_ids is required when status is REGISTERED")
            if self.evidence_status is not RouteEvidenceStatus.CURRENT:
                raise ValueError("evidence_status must be CURRENT when status is REGISTERED")
        if self.status is RouteRegistrationStatus.UNSUPPORTED and not self.unsupported_classes:
            raise ValueError("unsupported_classes is required when status is UNSUPPORTED")
        if (
            self.status
            in {
                RouteRegistrationStatus.REGISTRATION_BLOCKED,
                RouteRegistrationStatus.UNSUPPORTED,
                RouteRegistrationStatus.CONFLICT,
                RouteRegistrationStatus.REJECTED,
                RouteRegistrationStatus.SUSPENDED,
                RouteRegistrationStatus.RETIRED,
            }
            and not reason_codes
        ):
            raise ValueError("reason_codes are required for non-registered route outcomes")
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)


@dataclass(frozen=True, slots=True)
class AgentRouteAssociation:
    association_id: str
    agent_id: str
    route_id: str
    environment_id: str
    agent_registration_id: str
    route_registration_id: str
    purpose_scope: tuple[str, ...]
    status: AgentRouteAssociationStatus
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "association_id", _require_text(self.association_id, "association_id")
        )
        object.__setattr__(self, "agent_id", _require_text(self.agent_id, "agent_id"))
        object.__setattr__(self, "route_id", _require_text(self.route_id, "route_id"))
        object.__setattr__(
            self, "environment_id", _require_text(self.environment_id, "environment_id")
        )
        object.__setattr__(
            self,
            "agent_registration_id",
            _require_text(self.agent_registration_id, "agent_registration_id"),
        )
        object.__setattr__(
            self,
            "route_registration_id",
            _require_text(self.route_registration_id, "route_registration_id"),
        )
        object.__setattr__(
            self,
            "purpose_scope",
            _require_text_tuple(self.purpose_scope, "purpose_scope"),
        )
        object.__setattr__(
            self,
            "status",
            _require_exact_enum(self.status, AgentRouteAssociationStatus, "status"),
        )
        reason_codes = _require_text_tuple(self.reason_codes, "reason_codes")
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids, "evidence_reference_ids"
        )
        if self.status is AgentRouteAssociationStatus.ACTIVE:
            if not self.purpose_scope:
                raise ValueError("purpose_scope is required when status is ACTIVE")
            if not evidence_reference_ids:
                raise ValueError("evidence_reference_ids is required when status is ACTIVE")
        if (
            self.status
            in {
                AgentRouteAssociationStatus.REGISTRATION_BLOCKED,
                AgentRouteAssociationStatus.CONFLICT,
                AgentRouteAssociationStatus.SUSPENDED,
                AgentRouteAssociationStatus.RETIRED,
            }
            and not reason_codes
        ):
            raise ValueError("reason_codes are required for non-active association outcomes")
        object.__setattr__(self, "reason_codes", reason_codes)
        object.__setattr__(self, "evidence_reference_ids", evidence_reference_ids)


@dataclass(frozen=True, slots=True)
class AgentRouteRegistrationBoundary:
    boundary_id: str
    agent: EgressAgent
    agent_registration: AgentRegistration
    route: EgressRoute
    route_registration: RouteRegistration
    association: AgentRouteAssociation

    def __post_init__(self) -> None:
        object.__setattr__(self, "boundary_id", _require_text(self.boundary_id, "boundary_id"))
        if not isinstance(self.agent, EgressAgent):
            raise ValueError("agent must be EgressAgent")
        if not isinstance(self.agent_registration, AgentRegistration):
            raise ValueError("agent_registration must be AgentRegistration")
        if not isinstance(self.route, EgressRoute):
            raise ValueError("route must be EgressRoute")
        if not isinstance(self.route_registration, RouteRegistration):
            raise ValueError("route_registration must be RouteRegistration")
        if not isinstance(self.association, AgentRouteAssociation):
            raise ValueError("association must be AgentRouteAssociation")

        if self.agent.agent_id != self.agent_registration.agent_id:
            raise ValueError("agent.agent_id must match agent_registration.agent_id")
        if self.agent.environment_id != self.agent_registration.environment_id:
            raise ValueError("agent.environment_id must match agent_registration.environment_id")
        if self.agent.agent_class != self.agent_registration.agent_class:
            raise ValueError("agent.agent_class must match agent_registration.agent_class")
        if self.agent.trust_scope != self.agent_registration.trust_scope:
            raise ValueError("agent.trust_scope must match agent_registration.trust_scope")
        if self.agent.source_release_reference != self.agent_registration.source_release_reference:
            raise ValueError(
                "agent.source_release_reference must match "
                "agent_registration.source_release_reference"
            )
        if self.agent.credential_reference != self.agent_registration.credential_reference:
            raise ValueError(
                "agent.credential_reference must match agent_registration.credential_reference"
            )

        if self.route.route_id != self.route_registration.route_id:
            raise ValueError("route.route_id must match route_registration.route_id")
        if self.route.agent_id != self.agent.agent_id:
            raise ValueError("route.agent_id must match agent.agent_id")
        if self.route_registration.agent_id != self.agent_registration.agent_id:
            raise ValueError(
                "route_registration.agent_id must match agent_registration.agent_id"
            )
        if self.route.agent_id != self.route_registration.agent_id:
            raise ValueError("route.agent_id must match route_registration.agent_id")
        if self.route.environment_id != self.route_registration.environment_id:
            raise ValueError("route.environment_id must match route_registration.environment_id")
        if self.route.route_family != self.route_registration.route_family:
            raise ValueError("route.route_family must match route_registration.route_family")
        if self.route.purpose_scope != self.route_registration.purpose_scope:
            raise ValueError("route.purpose_scope must match route_registration.purpose_scope")
        if self.route.capability_ids != self.route_registration.capability_ids:
            raise ValueError("route.capability_ids must match route_registration.capability_ids")
        if self.route_registration.agent_registration_id != self.agent_registration.registration_id:
            raise ValueError(
                "route_registration.agent_registration_id must match "
                "agent_registration.registration_id"
            )

        if self.association.agent_id != self.agent.agent_id:
            raise ValueError("association.agent_id must match agent.agent_id")
        if self.association.route_id != self.route.route_id:
            raise ValueError("association.route_id must match route.route_id")
        if self.association.environment_id != self.agent.environment_id:
            raise ValueError("association.environment_id must match agent.environment_id")
        if self.association.environment_id != self.route.environment_id:
            raise ValueError("association.environment_id must match route.environment_id")
        if self.association.agent_registration_id != self.agent_registration.registration_id:
            raise ValueError(
                "association.agent_registration_id must match agent_registration.registration_id"
            )
        if self.association.route_registration_id != self.route_registration.registration_id:
            raise ValueError(
                "association.route_registration_id must match route_registration.registration_id"
            )
        if self.association.purpose_scope != self.route.purpose_scope:
            raise ValueError("association.purpose_scope must match route.purpose_scope")

        if self.association.status is AgentRouteAssociationStatus.ACTIVE:
            if self.agent_registration.status is not AgentRegistrationStatus.REGISTERED:
                raise ValueError("active association requires registered agent registration")
            if self.route_registration.status is not RouteRegistrationStatus.REGISTERED:
                raise ValueError("active association requires registered route registration")
            if self.agent.lifecycle_status in {
                AgentLifecycleStatus.PROPOSED,
                AgentLifecycleStatus.REGISTRATION_BLOCKED,
                AgentLifecycleStatus.SUSPENDED,
                AgentLifecycleStatus.RETIRED,
            }:
                raise ValueError("active association requires an eligible agent lifecycle status")
            if self.route.lifecycle_status in {
                RouteLifecycleStatus.PROPOSED,
                RouteLifecycleStatus.REGISTRATION_BLOCKED,
                RouteLifecycleStatus.SUSPENDED,
                RouteLifecycleStatus.RETIRED,
            }:
                raise ValueError("active association requires an eligible route lifecycle status")
