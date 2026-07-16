from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from typing import Any, cast

import pytest

import mayak.modules.egress_routing as egress_routing
import mayak.modules.egress_routing.persistence_runtime_gate as persistence_runtime_gate_module
from mayak.modules.egress_routing import (
    ER14A_TASK_ID,
    EgressPersistenceRuntimeAuthority,
    EgressPersistenceRuntimeGateBoundary,
)

EXPECTED_TASK_ID = "ER-14A-PERSISTENCE-RUNTIME-FAIL-CLOSED-GATE-20260716-058"

EXPECTED_MODULE_EXPORTS = (
    "ER14A_TASK_ID",
    "EgressPersistenceRuntimeAuthority",
    "EgressPersistenceRuntimeGateBoundary",
)

EXPECTED_PACKAGE_EXPORT_SLICE = (
    "ER13A_TASK_ID",
    "EgressProofOnlyAuthority",
    "EgressProofOnlyGateBoundary",
    "ER14A_TASK_ID",
    "EgressPersistenceRuntimeAuthority",
    "EgressPersistenceRuntimeGateBoundary",
    "ER07E_TASK_ID",
)

EXPECTED_FIELD_NAMES = (
    "boundary_id",
    "authority",
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
    "reason_codes",
    "evidence_reference_ids",
)

EXPECTED_TRUE_BOOLEAN_FIELDS = (
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

EXPECTED_FALSE_BOOLEAN_FIELDS = (
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

EXPECTED_REASON_CODES = (
    "persistence-runtime-implementation-blocked",
    "required-decisions-unsatisfied",
    "exact-implementation-task-required",
    "semantic-only-work-allowed",
)

EXPECTED_EVIDENCE_REFERENCE_IDS = (
    "persistence-runtime-evidence-01",
    "persistence-runtime-evidence-02",
)

EXPECTED_BOUNDARY_ID = "persistence-runtime-boundary-01"
EXPECTED_AUTHORITY = EgressPersistenceRuntimeAuthority.EGRESS_ROUTING_SERVER
EXPECTED_BOOL_LOOKALIKE_ERROR_MESSAGE = (
    "physical_schema_and_migration_decisions_required must be a bool"
)
EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE = (
    "evidence_reference_ids must not contain URL, payload, credential, cookie, token, "
    "or secret values"
)


class TextLike(str):
    pass


class TupleLike(tuple):
    pass


class BoolLike(int):
    pass


class AuthorityLike(str):
    pass


def _snapshot(record: object) -> tuple[object, ...]:
    return tuple(getattr(record, field.name) for field in fields(cast(Any, record)))


def _boundary_kwargs(boundary: EgressPersistenceRuntimeGateBoundary) -> dict[str, object]:
    kwargs = {field.name: getattr(boundary, field.name) for field in fields(boundary)}
    return kwargs


def _build_boundary(
    *,
    boundary_id: object = EXPECTED_BOUNDARY_ID,
    authority: object = EXPECTED_AUTHORITY,
    **overrides: object,
) -> EgressPersistenceRuntimeGateBoundary:
    kwargs: dict[str, object] = {
        "boundary_id": boundary_id,
        "authority": authority,
        **{field_name: True for field_name in EXPECTED_TRUE_BOOLEAN_FIELDS},
        **{field_name: False for field_name in EXPECTED_FALSE_BOOLEAN_FIELDS},
        "reason_codes": EXPECTED_REASON_CODES,
        "evidence_reference_ids": EXPECTED_EVIDENCE_REFERENCE_IDS,
    }
    kwargs.update(overrides)
    boundary = cast(Any, EgressPersistenceRuntimeGateBoundary)(**kwargs)
    assert type(boundary) is EgressPersistenceRuntimeGateBoundary
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    return boundary


def _module_post_init_node() -> ast.FunctionDef:
    source = Path("src/mayak/modules/egress_routing/persistence_runtime_gate.py").read_text()
    tree = ast.parse(source)
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "EgressPersistenceRuntimeGateBoundary"
    )
    return next(
        node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "__post_init__"
    )


def test_exact_task_id_and_exports() -> None:
    assert ER14A_TASK_ID == EXPECTED_TASK_ID
    assert persistence_runtime_gate_module.ER14A_TASK_ID == EXPECTED_TASK_ID
    assert persistence_runtime_gate_module.__all__ == EXPECTED_MODULE_EXPORTS
    assert tuple(persistence_runtime_gate_module.__all__) == EXPECTED_MODULE_EXPORTS
    assert len(set(persistence_runtime_gate_module.__all__)) == len(EXPECTED_MODULE_EXPORTS)
    assert all(hasattr(persistence_runtime_gate_module, name) for name in EXPECTED_MODULE_EXPORTS)
    assert tuple((member.name, member.value) for member in EgressPersistenceRuntimeAuthority) == (
        ("EGRESS_ROUTING_SERVER", "EGRESS_ROUTING_SERVER"),
    )
    start = egress_routing.__all__.index("ER13A_TASK_ID")
    assert egress_routing.__all__[start : start + len(EXPECTED_PACKAGE_EXPORT_SLICE)] == (
        EXPECTED_PACKAGE_EXPORT_SLICE
    )


def test_exact_field_count_and_order() -> None:
    boundary = _build_boundary()
    assert is_dataclass(boundary)
    assert len(fields(boundary)) == 42
    assert tuple(field.name for field in fields(boundary)) == EXPECTED_FIELD_NAMES
    assert type(boundary).__slots__ == EXPECTED_FIELD_NAMES
    assert not hasattr(boundary, "__dict__")


def test_boundary_is_frozen_and_slots_based() -> None:
    boundary = _build_boundary()
    with pytest.raises(FrozenInstanceError):
        boundary.boundary_id = "changed"  # type: ignore[misc]


def test_canonical_boundary_matrix_is_exact() -> None:
    boundary = _build_boundary()
    duplicate_boundary = _build_boundary()

    assert boundary == duplicate_boundary
    assert hash(boundary) == hash(duplicate_boundary)
    assert boundary is not duplicate_boundary
    assert boundary.boundary_id == EXPECTED_BOUNDARY_ID
    assert boundary.authority is EXPECTED_AUTHORITY
    assert boundary.reason_codes == EXPECTED_REASON_CODES
    assert boundary.evidence_reference_ids == EXPECTED_EVIDENCE_REFERENCE_IDS
    assert _snapshot(boundary) == _snapshot(duplicate_boundary)
    assert "boundary_id=" in repr(boundary)

    for field_name in EXPECTED_TRUE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is True

    for field_name in EXPECTED_FALSE_BOOLEAN_FIELDS:
        value = getattr(boundary, field_name)
        assert type(value) is bool
        assert value is False

    for evidence_reference in boundary.evidence_reference_ids:
        assert type(evidence_reference) is str
        assert evidence_reference.strip()
        lowered = evidence_reference.lower()
        assert "http://" not in lowered
        assert "https://" not in lowered
        assert "://" not in lowered
        assert "payload" not in lowered
        assert "credential" not in lowered
        assert "cookie" not in lowered
        assert "token" not in lowered
        assert "secret" not in lowered


def test_exact_type_and_lookalike_guards() -> None:
    boundary = _build_boundary()
    kwargs = _boundary_kwargs(boundary)

    with pytest.raises(ValueError, match="boundary_id must be a non-blank string"):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(
            **{**kwargs, "boundary_id": TextLike(EXPECTED_BOUNDARY_ID)}
        )

    with pytest.raises(
        ValueError,
        match="authority must be EgressPersistenceRuntimeAuthority",
    ):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(
            **{**kwargs, "authority": AuthorityLike(EXPECTED_AUTHORITY.value)}
        )

    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(
            **{**kwargs, "reason_codes": TupleLike(EXPECTED_REASON_CODES)}
        )

    with pytest.raises(ValueError, match="evidence_reference_ids must be a tuple"):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(
            **{**kwargs, "evidence_reference_ids": TupleLike(EXPECTED_EVIDENCE_REFERENCE_IDS)}
        )

    with pytest.raises(ValueError, match=EXPECTED_BOOL_LOOKALIKE_ERROR_MESSAGE):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(
            **{**kwargs, "physical_schema_and_migration_decisions_required": BoolLike(1)}
        )


@pytest.mark.parametrize("field_name", EXPECTED_TRUE_BOOLEAN_FIELDS)
def test_required_true_fields_reject_false(field_name: str) -> None:
    kwargs = _boundary_kwargs(_build_boundary())
    kwargs[field_name] = False

    with pytest.raises(ValueError, match=f"{field_name} must be True"):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(**kwargs)


@pytest.mark.parametrize("field_name", EXPECTED_FALSE_BOOLEAN_FIELDS)
def test_blocked_false_fields_reject_true(field_name: str) -> None:
    kwargs = _boundary_kwargs(_build_boundary())
    kwargs[field_name] = True

    with pytest.raises(ValueError, match=f"{field_name} must be False"):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(**kwargs)


@pytest.mark.parametrize(
    ("reason_codes", "expected_message"),
    [
        (
            (
                "semantic-only-work-allowed",
                "required-decisions-unsatisfied",
                "exact-implementation-task-required",
                "persistence-runtime-implementation-blocked",
            ),
            "reason_codes must contain the required ER-14A codes",
        ),
        (
            (
                "persistence-runtime-implementation-blocked",
                "required-decisions-unsatisfied",
                "exact-implementation-task-required",
            ),
            "reason_codes must contain the required ER-14A codes",
        ),
        (
            (
                "persistence-runtime-implementation-blocked",
                "required-decisions-unsatisfied",
                "exact-implementation-task-required",
                "semantic-only-work-allowed",
                "extra-code",
            ),
            "reason_codes must contain the required ER-14A codes",
        ),
        (
            (
                "persistence-runtime-implementation-blocked",
                "required-decisions-unsatisfied",
                "required-decisions-unsatisfied",
                "semantic-only-work-allowed",
            ),
            "reason_codes must not contain duplicates",
        ),
    ],
)
def test_reason_code_variants_are_rejected(
    reason_codes: tuple[str, ...], expected_message: str
) -> None:
    kwargs = _boundary_kwargs(_build_boundary())
    kwargs["reason_codes"] = reason_codes

    with pytest.raises(ValueError, match=expected_message):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(**kwargs)


@pytest.mark.parametrize(
    ("evidence_reference_ids", "expected_message"),
    [
        ((), "evidence_reference_ids must not be empty"),
        (
            ("persistence-runtime-evidence-01", "persistence-runtime-evidence-01"),
            "evidence_reference_ids must not contain duplicates",
        ),
        (
            ("persistence-runtime-evidence-01", "https://example.invalid/path"),
            EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE,
        ),
        (
            ("persistence-runtime-evidence-01", "payload-summary"),
            EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE,
        ),
        (
            ("persistence-runtime-evidence-01", "credential-summary"),
            EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE,
        ),
        (
            ("persistence-runtime-evidence-01", "cookie-summary"),
            EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE,
        ),
        (
            ("persistence-runtime-evidence-01", "token-summary"),
            EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE,
        ),
        (
            ("persistence-runtime-evidence-01", "secret-summary"),
            EXPECTED_EVIDENCE_REFERENCE_ERROR_MESSAGE,
        ),
    ],
)
def test_evidence_reference_variants_are_rejected(
    evidence_reference_ids: tuple[str, ...], expected_message: str
) -> None:
    kwargs = _boundary_kwargs(_build_boundary())
    kwargs["evidence_reference_ids"] = evidence_reference_ids

    with pytest.raises(ValueError, match=expected_message):
        cast(Any, EgressPersistenceRuntimeGateBoundary)(**kwargs)


def test_validation_is_atomic_and_mutation_is_deferred() -> None:
    post_init = _module_post_init_node()
    raise_lines = [node.lineno for node in ast.walk(post_init) if isinstance(node, ast.Raise)]
    setattr_lines = [
        node.lineno
        for node in ast.walk(post_init)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "object"
        and node.func.attr == "__setattr__"
    ]

    assert raise_lines
    assert setattr_lines
    assert min(setattr_lines) > max(raise_lines)


def test_module_has_no_runtime_or_persistence_execution_semantics() -> None:
    source = Path("src/mayak/modules/egress_routing/persistence_runtime_gate.py").read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                assert root in {"__future__", "dataclasses", "enum", "typing"}
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                assert node.level > 0
                continue
            assert node.level == 0
            root = node.module.split(".", 1)[0]
            assert root in {"__future__", "dataclasses", "enum", "typing"}

    identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    } | {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    } | {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}

    assert {
        "connect",
        "connection",
        "create_all",
        "create_engine",
        "cursor",
        "declarative_base",
        "execute",
        "engine",
        "firewall",
        "httpx",
        "installer",
        "listener",
        "metadata",
        "op",
        "playwright",
        "psycopg",
        "requests",
        "selenium",
        "sessionmaker",
        "socket",
        "sqlalchemy",
        "subprocess",
        "systemd",
        "tunnel",
        "urlopen",
        "webdriver",
        "windows_service",
    }.isdisjoint(identifiers)

    assert {
        "ER14A_TASK_ID",
        "EgressPersistenceRuntimeAuthority",
        "EgressPersistenceRuntimeGateBoundary",
        "reason_codes",
        "evidence_reference_ids",
        "physical_schema_and_migration_decisions_required",
        "runtime_execution_authorized",
        "production_readiness_inferred",
    }.issubset(identifiers)


def test_frozen_instance_rejects_mutation_attempts() -> None:
    boundary = _build_boundary()

    with pytest.raises(FrozenInstanceError):
        boundary.reason_codes = EXPECTED_REASON_CODES  # type: ignore[misc]


def test_canonical_boundary_is_not_backed_by_dict() -> None:
    boundary = _build_boundary()
    assert not hasattr(boundary, "__dict__")
    assert _snapshot(boundary) == tuple(getattr(boundary, field.name) for field in fields(boundary))
