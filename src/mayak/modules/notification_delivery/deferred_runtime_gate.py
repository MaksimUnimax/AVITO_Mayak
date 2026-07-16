"""Deferred runtime gate for Notification Delivery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

ND14_TASK_ID = "MAYAK-ND-14-DEFERRED-RUNTIME-GATES-20260716-010"


class NotificationDeferredRuntimeAuthority(str, Enum):
    NOTIFICATION_DELIVERY_SERVER = "NOTIFICATION_DELIVERY_SERVER"


class NotificationDeferredRuntimeGateStatus(str, Enum):
    BLOCKED_PENDING_EXPLICIT_GATES = "BLOCKED_PENDING_EXPLICIT_GATES"


class NotificationDeferredRuntimeRequirement(str, Enum):
    PHYSICAL_SCHEMA_AND_MIGRATIONS = "PHYSICAL_SCHEMA_AND_MIGRATIONS"
    QUEUE_WORKER_BROKER = "QUEUE_WORKER_BROKER"
    PROVIDER_ADAPTER_PLAYBOOKS = "PROVIDER_ADAPTER_PLAYBOOKS"
    PROVIDER_CREDENTIALS_POLICY = "PROVIDER_CREDENTIALS_POLICY"
    RETRY_RATE_TIME_POLICY = "RETRY_RATE_TIME_POLICY"
    OPERATIONS_DEPLOY_RUNTIME_TOPOLOGY = "OPERATIONS_DEPLOY_RUNTIME_TOPOLOGY"
    EXACT_IMPLEMENTATION_TASK = "EXACT_IMPLEMENTATION_TASK"


class NotificationPreRuntimeAllowedWork(str, Enum):
    SEMANTIC_CONTRACTS = "SEMANTIC_CONTRACTS"
    SYNTHETIC_DETERMINISTIC_FAKES = "SYNTHETIC_DETERMINISTIC_FAKES"
    ARCHITECTURE_STATIC_CHECKS = "ARCHITECTURE_STATIC_CHECKS"
    DOCS_ONLY_DECISIONS = "DOCS_ONLY_DECISIONS"
    EVIDENCE_HANDOFF = "EVIDENCE_HANDOFF"


class NotificationDeferredRuntimeCapability(str, Enum):
    POSTGRESQL_TABLES = "POSTGRESQL_TABLES"
    SQLALCHEMY_MODELS = "SQLALCHEMY_MODELS"
    PSYCOPG_USAGE = "PSYCOPG_USAGE"
    ALEMBIC_MIGRATIONS = "ALEMBIC_MIGRATIONS"
    QUEUE = "QUEUE"
    WORKER = "WORKER"
    BROKER_OR_CACHE = "BROKER_OR_CACHE"
    SCHEDULER_OR_POLLING = "SCHEDULER_OR_POLLING"
    TELEGRAM_PROVIDER_ADAPTER = "TELEGRAM_PROVIDER_ADAPTER"
    MAX_PROVIDER_ADAPTER = "MAX_PROVIDER_ADAPTER"
    WEB_PUSH_DELIVERY = "WEB_PUSH_DELIVERY"
    WEBHOOK = "WEBHOOK"
    MINI_APP = "MINI_APP"
    PROVIDER_API_CALLS = "PROVIDER_API_CALLS"
    MESSAGE_TEMPLATES = "MESSAGE_TEMPLATES"
    PROVIDER_CREDENTIALS = "PROVIDER_CREDENTIALS"
    PROVIDER_RETRY_OR_BACKOFF = "PROVIDER_RETRY_OR_BACKOFF"
    PROVIDER_RATE_LIMITS = "PROVIDER_RATE_LIMITS"
    QUIET_HOURS = "QUIET_HOURS"
    DIGEST_OR_TIME_BATCHING = "DIGEST_OR_TIME_BATCHING"
    RETENTION_TOOLING = "RETENTION_TOOLING"
    RUNTIME_SERVICES = "RUNTIME_SERVICES"
    DOCKER_CICD_DEPLOY = "DOCKER_CICD_DEPLOY"
    LIVE_DELIVERY = "LIVE_DELIVERY"


_CANONICAL_REQUIRED_GATE_CLASSES = (
    NotificationDeferredRuntimeRequirement.PHYSICAL_SCHEMA_AND_MIGRATIONS,
    NotificationDeferredRuntimeRequirement.QUEUE_WORKER_BROKER,
    NotificationDeferredRuntimeRequirement.PROVIDER_ADAPTER_PLAYBOOKS,
    NotificationDeferredRuntimeRequirement.PROVIDER_CREDENTIALS_POLICY,
    NotificationDeferredRuntimeRequirement.RETRY_RATE_TIME_POLICY,
    NotificationDeferredRuntimeRequirement.OPERATIONS_DEPLOY_RUNTIME_TOPOLOGY,
    NotificationDeferredRuntimeRequirement.EXACT_IMPLEMENTATION_TASK,
)

_CANONICAL_ALLOWED_PRE_RUNTIME_WORK = (
    NotificationPreRuntimeAllowedWork.SEMANTIC_CONTRACTS,
    NotificationPreRuntimeAllowedWork.SYNTHETIC_DETERMINISTIC_FAKES,
    NotificationPreRuntimeAllowedWork.ARCHITECTURE_STATIC_CHECKS,
    NotificationPreRuntimeAllowedWork.DOCS_ONLY_DECISIONS,
    NotificationPreRuntimeAllowedWork.EVIDENCE_HANDOFF,
)

_CANONICAL_BLOCKED_RUNTIME_CAPABILITIES = (
    NotificationDeferredRuntimeCapability.POSTGRESQL_TABLES,
    NotificationDeferredRuntimeCapability.SQLALCHEMY_MODELS,
    NotificationDeferredRuntimeCapability.PSYCOPG_USAGE,
    NotificationDeferredRuntimeCapability.ALEMBIC_MIGRATIONS,
    NotificationDeferredRuntimeCapability.QUEUE,
    NotificationDeferredRuntimeCapability.WORKER,
    NotificationDeferredRuntimeCapability.BROKER_OR_CACHE,
    NotificationDeferredRuntimeCapability.SCHEDULER_OR_POLLING,
    NotificationDeferredRuntimeCapability.TELEGRAM_PROVIDER_ADAPTER,
    NotificationDeferredRuntimeCapability.MAX_PROVIDER_ADAPTER,
    NotificationDeferredRuntimeCapability.WEB_PUSH_DELIVERY,
    NotificationDeferredRuntimeCapability.WEBHOOK,
    NotificationDeferredRuntimeCapability.MINI_APP,
    NotificationDeferredRuntimeCapability.PROVIDER_API_CALLS,
    NotificationDeferredRuntimeCapability.MESSAGE_TEMPLATES,
    NotificationDeferredRuntimeCapability.PROVIDER_CREDENTIALS,
    NotificationDeferredRuntimeCapability.PROVIDER_RETRY_OR_BACKOFF,
    NotificationDeferredRuntimeCapability.PROVIDER_RATE_LIMITS,
    NotificationDeferredRuntimeCapability.QUIET_HOURS,
    NotificationDeferredRuntimeCapability.DIGEST_OR_TIME_BATCHING,
    NotificationDeferredRuntimeCapability.RETENTION_TOOLING,
    NotificationDeferredRuntimeCapability.RUNTIME_SERVICES,
    NotificationDeferredRuntimeCapability.DOCKER_CICD_DEPLOY,
    NotificationDeferredRuntimeCapability.LIVE_DELIVERY,
)

_CANONICAL_REASON_CODES = (
    "notification-runtime-implementation-blocked",
    "required-decisions-unsatisfied",
    "exact-implementation-task-required",
    "semantic-only-work-allowed",
    "od-013-remains-open",
)

_FORBIDDEN_EVIDENCE_REFERENCE_TOKENS = (
    "http://",
    "https://",
    "://",
    "cookie",
    "token",
    "secret",
    "credential",
    "private key",
    "session",
    "one-time code",
)


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_exact_enum(value: object, enum_type: type[Enum], field_name: str) -> Enum:
    if type(value) is not enum_type:
        raise ValueError(f"{field_name} must be {enum_type.__name__}")
    return value


def _require_exact_tuple(
    value: object,
    field_name: str,
    expected: tuple[object, ...],
) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if value != expected:
        raise ValueError(f"{field_name} must match the canonical blocked boundary")
    return value


def _require_safe_evidence_reference_ids(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")

    validated = tuple(_require_text(item, field_name) for item in value)
    if len(set(validated)) != len(validated):
        raise ValueError(f"{field_name} must not contain duplicate values")

    for item in validated:
        lowered = item.lower()
        for token in _FORBIDDEN_EVIDENCE_REFERENCE_TOKENS:
            if token in lowered:
                raise ValueError(f"{field_name} must contain only safe internal references")
    return validated


@dataclass(frozen=True, slots=True)
class NotificationDeferredRuntimeGateBoundary:
    boundary_id: str
    authority: NotificationDeferredRuntimeAuthority
    status: NotificationDeferredRuntimeGateStatus
    required_gate_classes: tuple[NotificationDeferredRuntimeRequirement, ...]
    satisfied_gate_classes: tuple[NotificationDeferredRuntimeRequirement, ...]
    allowed_pre_runtime_work: tuple[NotificationPreRuntimeAllowedWork, ...]
    blocked_runtime_capabilities: tuple[NotificationDeferredRuntimeCapability, ...]
    runtime_execution_authorized: bool
    persistence_implementation_authorized: bool
    provider_adapter_implementation_authorized: bool
    production_readiness_inferred: bool
    provider_permission_inferred: bool
    retention_policy_resolved: bool
    od013_closed: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text(self.boundary_id, "boundary_id")
        _require_exact_enum(
            self.authority,
            NotificationDeferredRuntimeAuthority,
            "authority",
        )
        _require_exact_enum(
            self.status,
            NotificationDeferredRuntimeGateStatus,
            "status",
        )
        _require_exact_tuple(
            self.required_gate_classes,
            "required_gate_classes",
            _CANONICAL_REQUIRED_GATE_CLASSES,
        )
        _require_exact_tuple(
            self.satisfied_gate_classes,
            "satisfied_gate_classes",
            (),
        )
        _require_exact_tuple(
            self.allowed_pre_runtime_work,
            "allowed_pre_runtime_work",
            _CANONICAL_ALLOWED_PRE_RUNTIME_WORK,
        )
        _require_exact_tuple(
            self.blocked_runtime_capabilities,
            "blocked_runtime_capabilities",
            _CANONICAL_BLOCKED_RUNTIME_CAPABILITIES,
        )
        if _require_bool(self.runtime_execution_authorized, "runtime_execution_authorized"):
            raise ValueError("runtime_execution_authorized must be False")
        if _require_bool(
            self.persistence_implementation_authorized,
            "persistence_implementation_authorized",
        ):
            raise ValueError("persistence_implementation_authorized must be False")
        if _require_bool(
            self.provider_adapter_implementation_authorized,
            "provider_adapter_implementation_authorized",
        ):
            raise ValueError("provider_adapter_implementation_authorized must be False")
        if _require_bool(self.production_readiness_inferred, "production_readiness_inferred"):
            raise ValueError("production_readiness_inferred must be False")
        if _require_bool(self.provider_permission_inferred, "provider_permission_inferred"):
            raise ValueError("provider_permission_inferred must be False")
        if _require_bool(self.retention_policy_resolved, "retention_policy_resolved"):
            raise ValueError("retention_policy_resolved must be False")
        if _require_bool(self.od013_closed, "od013_closed"):
            raise ValueError("od013_closed must be False")
        _require_exact_tuple(self.reason_codes, "reason_codes", _CANONICAL_REASON_CODES)
        _require_safe_evidence_reference_ids(self.evidence_reference_ids, "evidence_reference_ids")


def build_notification_deferred_runtime_gate(
    *,
    boundary_id: str,
    evidence_reference_ids: tuple[str, ...],
) -> NotificationDeferredRuntimeGateBoundary:
    return NotificationDeferredRuntimeGateBoundary(
        boundary_id=boundary_id,
        authority=NotificationDeferredRuntimeAuthority.NOTIFICATION_DELIVERY_SERVER,
        status=NotificationDeferredRuntimeGateStatus.BLOCKED_PENDING_EXPLICIT_GATES,
        required_gate_classes=_CANONICAL_REQUIRED_GATE_CLASSES,
        satisfied_gate_classes=(),
        allowed_pre_runtime_work=_CANONICAL_ALLOWED_PRE_RUNTIME_WORK,
        blocked_runtime_capabilities=_CANONICAL_BLOCKED_RUNTIME_CAPABILITIES,
        runtime_execution_authorized=False,
        persistence_implementation_authorized=False,
        provider_adapter_implementation_authorized=False,
        production_readiness_inferred=False,
        provider_permission_inferred=False,
        retention_policy_resolved=False,
        od013_closed=False,
        reason_codes=_CANONICAL_REASON_CODES,
        evidence_reference_ids=evidence_reference_ids,
    )


__all__ = (
    "ND14_TASK_ID",
    "NotificationDeferredRuntimeAuthority",
    "NotificationDeferredRuntimeGateStatus",
    "NotificationDeferredRuntimeRequirement",
    "NotificationPreRuntimeAllowedWork",
    "NotificationDeferredRuntimeCapability",
    "NotificationDeferredRuntimeGateBoundary",
    "build_notification_deferred_runtime_gate",
)
