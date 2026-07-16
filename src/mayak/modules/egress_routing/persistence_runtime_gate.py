from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast

ER14A_TASK_ID = "ER-14A-PERSISTENCE-RUNTIME-FAIL-CLOSED-GATE-20260716-058"

__all__ = (
    "ER14A_TASK_ID",
    "EgressPersistenceRuntimeAuthority",
    "EgressPersistenceRuntimeGateBoundary",
)

_REQUIRED_TRUE_FIELDS = (
    "physical_schema_and_migration_decisions_required",
    "operations_and_deploy_decision_required",
    "secret_storage_decision_required",
    "runtime_topology_decision_required",
    "exact_implementation_task_required",
    "semantic_contracts_allowed",
    "synthetic_fixtures_allowed",
    "docs_only_decisions_allowed",
    "architecture_static_checks_allowed",
    "evidence_handoff_allowed",
)

_REQUIRED_FALSE_FIELDS = (
    "physical_schema_and_migration_decisions_satisfied",
    "operations_and_deploy_decision_satisfied",
    "secret_storage_decision_satisfied",
    "runtime_topology_decision_satisfied",
    "exact_implementation_task_approved",
    "durable_route_state_authorized",
    "persistence_implementation_authorized",
    "postgresql_tables_authorized",
    "sqlalchemy_models_authorized",
    "psycopg_usage_authorized",
    "alembic_migrations_authorized",
    "direct_primary_database_access_by_agent_authorized",
    "agent_service_runtime_authorized",
    "windows_service_or_scheduled_task_authorized",
    "native_host_installer_authorized",
    "browser_worker_pool_runtime_authorized",
    "queue_broker_cache_authorized",
    "tunnel_proxy_vpn_config_authorized",
    "firewall_dns_certificate_port_authorized",
    "docker_cicd_deploy_authorized",
    "production_secret_store_authorized",
    "live_provider_traffic_authorized",
    "runtime_execution_authorized",
    "production_readiness_inferred",
    "provider_access_permission_inferred",
    "parser_success_inferred",
    "scan_success_inferred",
    "notification_delivery_inferred",
)

_REQUIRED_REASON_CODES = (
    "persistence-runtime-implementation-blocked",
    "required-decisions-unsatisfied",
    "exact-implementation-task-required",
    "semantic-only-work-allowed",
)

_UNSAFE_EVIDENCE_REFERENCE_FRAGMENTS = (
    "payload",
    "credential",
    "cookie",
    "token",
    "secret",
)

E = TypeVar("E", bound=Enum)
T = TypeVar("T")


def _require_text(value: object, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-blank string")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_tuple(value: object, field_name: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return value


def _require_exact_enum(value: object, enum_cls: type[E], field_name: str) -> E:
    if type(value) is not enum_cls:
        raise ValueError(f"{field_name} must be {enum_cls.__name__}")
    return cast(E, value)


def _require_exact_record(value: object, record_cls: type[T], field_name: str) -> T:
    if type(value) is not record_cls:
        raise ValueError(f"{field_name} must be {record_cls.__name__}")
    return cast(T, value)


def _require_text_tuple(
    value: object,
    field_name: str,
    *,
    non_empty: bool = False,
    require_unique: bool = False,
    safe_reference_ids: bool = False,
) -> tuple[str, ...]:
    items = _require_tuple(value, field_name)
    if non_empty and not items:
        raise ValueError(f"{field_name} must not be empty")

    validated: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _require_text(item, field_name)
        if require_unique and text in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        if safe_reference_ids:
            lowered = text.lower()
            if lowered.startswith("http:") or lowered.startswith("https:"):
                raise ValueError(
                    f"{field_name} must not contain URL, payload, credential, cookie, token, "
                    "or secret values"
                )
            if "://" in lowered:
                raise ValueError(
                    f"{field_name} must not contain URL, payload, credential, cookie, token, "
                    "or secret values"
                )
            if any(fragment in lowered for fragment in _UNSAFE_EVIDENCE_REFERENCE_FRAGMENTS):
                raise ValueError(
                    f"{field_name} must not contain URL, payload, credential, cookie, token, "
                    "or secret values"
                )
        seen.add(text)
        validated.append(text)
    return tuple(validated)


class EgressPersistenceRuntimeAuthority(str, Enum):
    EGRESS_ROUTING_SERVER = "EGRESS_ROUTING_SERVER"


@dataclass(frozen=True, slots=True)
class EgressPersistenceRuntimeGateBoundary:
    boundary_id: str
    authority: EgressPersistenceRuntimeAuthority
    physical_schema_and_migration_decisions_required: bool
    operations_and_deploy_decision_required: bool
    secret_storage_decision_required: bool
    runtime_topology_decision_required: bool
    exact_implementation_task_required: bool
    semantic_contracts_allowed: bool
    synthetic_fixtures_allowed: bool
    docs_only_decisions_allowed: bool
    architecture_static_checks_allowed: bool
    evidence_handoff_allowed: bool
    physical_schema_and_migration_decisions_satisfied: bool
    operations_and_deploy_decision_satisfied: bool
    secret_storage_decision_satisfied: bool
    runtime_topology_decision_satisfied: bool
    exact_implementation_task_approved: bool
    durable_route_state_authorized: bool
    persistence_implementation_authorized: bool
    postgresql_tables_authorized: bool
    sqlalchemy_models_authorized: bool
    psycopg_usage_authorized: bool
    alembic_migrations_authorized: bool
    direct_primary_database_access_by_agent_authorized: bool
    agent_service_runtime_authorized: bool
    windows_service_or_scheduled_task_authorized: bool
    native_host_installer_authorized: bool
    browser_worker_pool_runtime_authorized: bool
    queue_broker_cache_authorized: bool
    tunnel_proxy_vpn_config_authorized: bool
    firewall_dns_certificate_port_authorized: bool
    docker_cicd_deploy_authorized: bool
    production_secret_store_authorized: bool
    live_provider_traffic_authorized: bool
    runtime_execution_authorized: bool
    production_readiness_inferred: bool
    provider_access_permission_inferred: bool
    parser_success_inferred: bool
    scan_success_inferred: bool
    notification_delivery_inferred: bool
    reason_codes: tuple[str, ...]
    evidence_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        boundary_id = _require_text(self.boundary_id, "boundary_id")
        authority = _require_exact_enum(
            self.authority,
            EgressPersistenceRuntimeAuthority,
            "authority",
        )

        validated_bools: dict[str, bool] = {}
        for field_name in _REQUIRED_TRUE_FIELDS + _REQUIRED_FALSE_FIELDS:
            validated_bools[field_name] = _require_bool(getattr(self, field_name), field_name)

        reason_codes = _require_text_tuple(
            self.reason_codes,
            "reason_codes",
            non_empty=True,
            require_unique=True,
        )
        evidence_reference_ids = _require_text_tuple(
            self.evidence_reference_ids,
            "evidence_reference_ids",
            non_empty=True,
            require_unique=True,
            safe_reference_ids=True,
        )

        if authority is not EgressPersistenceRuntimeAuthority.EGRESS_ROUTING_SERVER:
            raise ValueError("authority must be EGRESS_ROUTING_SERVER")
        for field_name in _REQUIRED_TRUE_FIELDS:
            if validated_bools[field_name] is not True:
                raise ValueError(f"{field_name} must be True")
        for field_name in _REQUIRED_FALSE_FIELDS:
            if validated_bools[field_name] is not False:
                raise ValueError(f"{field_name} must be False")
        if reason_codes != _REQUIRED_REASON_CODES:
            raise ValueError("reason_codes must contain the required ER-14A codes")

        for field_name, value in (
            ("boundary_id", boundary_id),
            ("authority", authority),
            (
                "physical_schema_and_migration_decisions_required",
                validated_bools["physical_schema_and_migration_decisions_required"],
            ),
            (
                "operations_and_deploy_decision_required",
                validated_bools["operations_and_deploy_decision_required"],
            ),
            (
                "secret_storage_decision_required",
                validated_bools["secret_storage_decision_required"],
            ),
            (
                "runtime_topology_decision_required",
                validated_bools["runtime_topology_decision_required"],
            ),
            (
                "exact_implementation_task_required",
                validated_bools["exact_implementation_task_required"],
            ),
            ("semantic_contracts_allowed", validated_bools["semantic_contracts_allowed"]),
            ("synthetic_fixtures_allowed", validated_bools["synthetic_fixtures_allowed"]),
            ("docs_only_decisions_allowed", validated_bools["docs_only_decisions_allowed"]),
            (
                "architecture_static_checks_allowed",
                validated_bools["architecture_static_checks_allowed"],
            ),
            ("evidence_handoff_allowed", validated_bools["evidence_handoff_allowed"]),
            (
                "physical_schema_and_migration_decisions_satisfied",
                validated_bools["physical_schema_and_migration_decisions_satisfied"],
            ),
            (
                "operations_and_deploy_decision_satisfied",
                validated_bools["operations_and_deploy_decision_satisfied"],
            ),
            (
                "secret_storage_decision_satisfied",
                validated_bools["secret_storage_decision_satisfied"],
            ),
            (
                "runtime_topology_decision_satisfied",
                validated_bools["runtime_topology_decision_satisfied"],
            ),
            (
                "exact_implementation_task_approved",
                validated_bools["exact_implementation_task_approved"],
            ),
            ("durable_route_state_authorized", validated_bools["durable_route_state_authorized"]),
            (
                "persistence_implementation_authorized",
                validated_bools["persistence_implementation_authorized"],
            ),
            ("postgresql_tables_authorized", validated_bools["postgresql_tables_authorized"]),
            ("sqlalchemy_models_authorized", validated_bools["sqlalchemy_models_authorized"]),
            ("psycopg_usage_authorized", validated_bools["psycopg_usage_authorized"]),
            ("alembic_migrations_authorized", validated_bools["alembic_migrations_authorized"]),
            (
                "direct_primary_database_access_by_agent_authorized",
                validated_bools["direct_primary_database_access_by_agent_authorized"],
            ),
            (
                "agent_service_runtime_authorized",
                validated_bools["agent_service_runtime_authorized"],
            ),
            (
                "windows_service_or_scheduled_task_authorized",
                validated_bools["windows_service_or_scheduled_task_authorized"],
            ),
            (
                "native_host_installer_authorized",
                validated_bools["native_host_installer_authorized"],
            ),
            (
                "browser_worker_pool_runtime_authorized",
                validated_bools["browser_worker_pool_runtime_authorized"],
            ),
            ("queue_broker_cache_authorized", validated_bools["queue_broker_cache_authorized"]),
            (
                "tunnel_proxy_vpn_config_authorized",
                validated_bools["tunnel_proxy_vpn_config_authorized"],
            ),
            (
                "firewall_dns_certificate_port_authorized",
                validated_bools["firewall_dns_certificate_port_authorized"],
            ),
            ("docker_cicd_deploy_authorized", validated_bools["docker_cicd_deploy_authorized"]),
            (
                "production_secret_store_authorized",
                validated_bools["production_secret_store_authorized"],
            ),
            (
                "live_provider_traffic_authorized",
                validated_bools["live_provider_traffic_authorized"],
            ),
            ("runtime_execution_authorized", validated_bools["runtime_execution_authorized"]),
            ("production_readiness_inferred", validated_bools["production_readiness_inferred"]),
            (
                "provider_access_permission_inferred",
                validated_bools["provider_access_permission_inferred"],
            ),
            ("parser_success_inferred", validated_bools["parser_success_inferred"]),
            ("scan_success_inferred", validated_bools["scan_success_inferred"]),
            ("notification_delivery_inferred", validated_bools["notification_delivery_inferred"]),
            ("reason_codes", reason_codes),
            ("evidence_reference_ids", evidence_reference_ids),
        ):
            object.__setattr__(self, field_name, value)
