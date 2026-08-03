"""Independent, identity-bound and fail-closed RF16 acceptance verifier."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MARKER = "RF16_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01"


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]


def _get(data: dict[str, object], path: str) -> object:
    value: object = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(path)
        value = value[part]
    return value


def _set(path: str, value: object) -> Callable[[dict[str, object]], None]:
    def tamper(data: dict[str, object]) -> None:
        target: dict[str, object] = data
        parts = path.split(".")
        for part in parts[:-1]:
            child = target.get(part)
            if not isinstance(child, dict):
                raise KeyError(path)
            target = child
        target[parts[-1]] = value

    return tamper


def _eq(path: str, expected: object) -> Callable[[dict[str, object]], bool]:
    def check(data: dict[str, object]) -> bool:
        try:
            return _get(data, path) == expected
        except KeyError:
            return False

    return check


def _predicate(
    path: str, predicate: Callable[[object], bool]
) -> Callable[[dict[str, object]], bool]:
    def check(data: dict[str, object]) -> bool:
        try:
            return predicate(_get(data, path))
        except KeyError, TypeError, ValueError:
            return False

    return check


def _registry(expected_sha: str, repository_head: str) -> tuple[Requirement, ...]:
    def exact_identity(value: object) -> bool:
        return (
            isinstance(value, dict)
            and value.get("technical_id") == TECHNICAL_ID
            and value.get("candidate_sha") == expected_sha
        )

    def head(value: object) -> bool:
        return (
            isinstance(value, dict)
            and value.get("db_head") == repository_head
            and value.get("repository_heads") == [repository_head]
        )

    return (
        Requirement(
            "candidate_identity",
            _predicate("identity", exact_identity),
            _set("identity.candidate_sha", "0" * 40),
        ),
        Requirement(
            "python_3_14_6",
            _eq("environment.python", "3.14.6"),
            _set("environment.python", "3.13.0"),
        ),
        Requirement(
            "postgresql_18",
            _predicate(
                "environment.postgres_version",
                lambda v: isinstance(v, str) and v.startswith("PostgreSQL 18."),
            ),
            _set("environment.postgres_version", "PostgreSQL 17"),
        ),
        Requirement(
            "alembic_current_head", _predicate("alembic", head), _set("alembic.db_head", "deadbeef")
        ),
        Requirement(
            "exact_four_egress_tables",
            _eq(
                "database.egress_tables",
                [
                    "egress_agent_heartbeats",
                    "egress_agents",
                    "egress_route_leases",
                    "egress_routes",
                ],
            ),
            _set("database.egress_tables", []),
        ),
        Requirement(
            "registration_durable",
            _predicate(
                "registration",
                lambda v: (
                    isinstance(v, dict)
                    and all(
                        isinstance(v.get(k), str) and v[k]
                        for k in ("agent_id", "route_id", "agent_state", "route_state")
                    )
                ),
            ),
            _set("registration.route_id", ""),
        ),
        Requirement(
            "heartbeat_durable",
            _predicate(
                "heartbeat",
                lambda v: (
                    isinstance(v, dict)
                    and all(v.get(k) for k in ("row_id", "observed_at", "state"))
                ),
            ),
            _set("heartbeat.row_id", ""),
        ),
        Requirement(
            "heartbeat_not_readiness",
            _predicate(
                "heartbeat",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("agent_state_before") == v.get("agent_state_after")
                    and v.get("route_state_before") == v.get("route_state_after")
                    and v.get("state") == "ONLINE"
                ),
            ),
            _set("heartbeat.route_state_after", "RESTRICTED"),
        ),
        Requirement(
            "selection_exact_physical_route",
            _predicate(
                "selection",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("status") == "SELECTED"
                    and v.get("selected_route_id") == v.get("eligible_route_id")
                    and v.get("physical_route_exists") is True
                ),
            ),
            _set("selection.selected_route_id", "absent"),
        ),
        Requirement(
            "selection_semantic_gates",
            _predicate(
                "selection",
                lambda v: (
                    isinstance(v, dict)
                    and all(
                        v.get(k) is True
                        for k in (
                            "purpose_match",
                            "capability_scope_match",
                            "registration",
                            "readiness",
                            "health",
                            "restriction_clear",
                            "evidence_current",
                            "reconciliation_eligible",
                        )
                    )
                ),
            ),
            _set("selection.evidence_current", False),
        ),
        Requirement(
            "selection_blocking_cases",
            _predicate(
                "selection_blocking",
                lambda v: (
                    isinstance(v, list)
                    and len(v) >= 7
                    and all(item.get("success") is False for item in v if isinstance(item, dict))
                ),
            ),
            _set("selection_blocking", []),
        ),
        Requirement(
            "multi_route_unapproved_policy_block",
            _eq("multi_route.status", "MULTIPLE_ROUTES_UNAPPROVED"),
            _set("multi_route.status", "SELECTED"),
        ),
        Requirement(
            "active_lease_exclusivity", _eq("lease.active_count", 1), _set("lease.active_count", 2)
        ),
        Requirement(
            "concurrent_lease_conflict",
            _predicate(
                "concurrency",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("distinct_backend_pids") == 2
                    and v.get("active_count") == 1
                    and sorted(x.get("reason") for x in v.get("sessions", []))
                    == ["GRANTED", "LEASE_CONFLICT"]
                    and v.get("windows_overlap") is True
                ),
            ),
            _set("concurrency.windows_overlap", False),
        ),
        Requirement(
            "same_identity_replay",
            _predicate(
                "replay",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("same_id") is True
                    and v.get("reason") == "REPLAY_ACTIVE"
                ),
            ),
            _set("replay.same_id", False),
        ),
        Requirement(
            "mismatch_conflict",
            _eq("mismatch.reason", "LEASE_CONFLICT"),
            _set("mismatch.reason", "GRANTED"),
        ),
        Requirement(
            "wrong_token_rejection",
            _eq("wrong_token.reason", "IDENTITY_MISMATCH"),
            _set("wrong_token.reason", "COMPLETED"),
        ),
        Requirement(
            "expiry_recovery",
            _predicate(
                "expiry",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("database_authoritative") is True
                    and v.get("state_after") == "EXPIRED"
                    and v.get("reason") == "LEASE_EXPIRED"
                ),
            ),
            _set("expiry.state_after", "ACTIVE"),
        ),
        Requirement(
            "restart_recovery",
            _predicate(
                "restart",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("session_a") != v.get("session_b")
                    and v.get("backend_pid_a") != v.get("backend_pid_b")
                    and v.get("state_before") == "ACTIVE"
                    and v.get("state_after") == "COMPLETED"
                    and v.get("result") == "COMPLETED"
                ),
            ),
            _set("restart.result", "GRANTED"),
        ),
        Requirement(
            "ambiguity_replay_block",
            _predicate(
                "ambiguity_replay",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("reason") in {"RECONCILIATION_REQUIRED", "REPLAY_AMBIGUOUS"}
                ),
            ),
            _set("ambiguity_replay.reason", "GRANTED"),
        ),
        Requirement(
            "foreign_state_unchanged",
            _eq("foreign_state.before_after_equal", True),
            _set("foreign_state.before_after_equal", False),
        ),
        Requirement(
            "safe_diagnostics",
            _predicate(
                "diagnostics",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("safe_metadata_only") is True
                    and v.get("secret_fields") == []
                ),
            ),
            _set("diagnostics.safe_metadata_only", False),
        ),
        Requirement(
            "protocol_strictness",
            _predicate(
                "protocol_cases",
                lambda v: (
                    isinstance(v, list)
                    and len(v) >= 10
                    and all(
                        item.get("accepted") is False
                        for item in v
                        if item.get("case_id") not in {"canonical_valid", "canonical_assignment"}
                    )
                ),
            ),
            _set("protocol_cases", []),
        ),
        Requirement(
            "simulator_runtime_parity",
            _predicate(
                "simulator_cases",
                lambda v: (
                    isinstance(v, list)
                    and len(v) >= 15
                    and all(item.get("classification") and item.get("message_type") for item in v)
                ),
            ),
            _set("simulator_cases", []),
        ),
        Requirement(
            "parser_fail_closed",
            _predicate(
                "parser_cases",
                lambda v: (
                    isinstance(v, list)
                    and len(v) >= 8
                    and all(
                        item.get("parser_success") is False
                        for item in v
                        if item.get("transport") != "VALIDATED_RESPONSE"
                    )
                ),
            ),
            _set("parser_cases", []),
        ),
        Requirement(
            "dedicated_agent_artifact_boundary",
            _predicate(
                "package",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("allowlisted_files") is True
                    and v.get("deterministic") is True
                    and v.get("forbidden_modules") == []
                ),
            ),
            _set("package.deterministic", False),
        ),
        Requirement(
            "no_secret_raw_provider_persistence",
            _predicate(
                "persistence_projection",
                lambda v: (
                    isinstance(v, dict)
                    and v.get("disallowed_classes") == []
                    and v.get("raw_provider_material") is False
                ),
            ),
            _set("persistence_projection.raw_provider_material", True),
        ),
    )


def _repository_head(repo_root: Path) -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    heads = ScriptDirectory.from_config(Config(str(repo_root / "alembic.ini"))).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"repository must have exactly one Alembic head, got {heads}")
    return heads[0]


def build_representative_evidence(expected_sha: str, repository_head: str) -> dict[str, object]:
    """Small deterministic raw fixture used only by verifier meta-tests."""
    return {
        "identity": {"technical_id": TECHNICAL_ID, "candidate_sha": expected_sha},
        "environment": {"python": "3.14.6", "postgres_version": "PostgreSQL 18.0"},
        "alembic": {"db_head": repository_head, "repository_heads": [repository_head]},
        "database": {
            "egress_tables": [
                "egress_agent_heartbeats",
                "egress_agents",
                "egress_route_leases",
                "egress_routes",
            ]
        },
        "registration": {
            "agent_id": "a",
            "route_id": "r",
            "agent_state": "READY",
            "route_state": "READY",
        },
        "heartbeat": {
            "row_id": "h",
            "observed_at": "now",
            "state": "ONLINE",
            "agent_state_before": "REGISTERED",
            "agent_state_after": "REGISTERED",
            "route_state_before": "REGISTERED",
            "route_state_after": "REGISTERED",
        },
        "selection": {
            "status": "SELECTED",
            "selected_route_id": "r",
            "eligible_route_id": "r",
            "physical_route_exists": True,
            "purpose_match": True,
            "capability_scope_match": True,
            "registration": True,
            "readiness": True,
            "health": True,
            "restriction_clear": True,
            "evidence_current": True,
            "reconciliation_eligible": True,
        },
        "selection_blocking": [{"case": str(i), "success": False} for i in range(8)],
        "multi_route": {"status": "MULTIPLE_ROUTES_UNAPPROVED"},
        "lease": {"active_count": 1},
        "concurrency": {
            "distinct_backend_pids": 2,
            "active_count": 1,
            "windows_overlap": True,
            "sessions": [{"reason": "GRANTED"}, {"reason": "LEASE_CONFLICT"}],
        },
        "replay": {"same_id": True, "reason": "REPLAY_ACTIVE"},
        "mismatch": {"reason": "LEASE_CONFLICT"},
        "wrong_token": {"reason": "IDENTITY_MISMATCH"},
        "expiry": {
            "database_authoritative": True,
            "state_after": "EXPIRED",
            "reason": "LEASE_EXPIRED",
        },
        "restart": {
            "session_a": "a",
            "session_b": "b",
            "backend_pid_a": 1,
            "backend_pid_b": 2,
            "state_before": "ACTIVE",
            "state_after": "COMPLETED",
            "result": "COMPLETED",
        },
        "ambiguity_replay": {"reason": "RECONCILIATION_REQUIRED"},
        "foreign_state": {"before_after_equal": True},
        "diagnostics": {"safe_metadata_only": True, "secret_fields": []},
        "protocol_cases": [{"case_id": "canonical_valid", "accepted": True}]
        + [{"case_id": str(i), "accepted": False} for i in range(10)],
        "simulator_cases": [
            {"message_type": "OUTCOME", "classification": str(i)} for i in range(15)
        ],
        "parser_cases": [{"transport": "VALIDATED_RESPONSE", "parser_success": False}]
        + [{"transport": str(i), "parser_success": False} for i in range(8)],
        "package": {"allowlisted_files": True, "deterministic": True, "forbidden_modules": []},
        "persistence_projection": {"disallowed_classes": [], "raw_provider_material": False},
    }


def verify(
    data: dict[str, object], *, expected_sha: str, repository_head: str, verify_tamper: bool = True
) -> tuple[list[str], list[str], tuple[Requirement, ...]]:
    registry = _registry(expected_sha, repository_head)
    ids = [item.requirement_id for item in registry]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate immutable requirement id")
    failing = [item.requirement_id for item in registry if item.check(data) is not True]
    rejected: list[str] = []
    if verify_tamper:
        for item in registry:
            tampered = copy.deepcopy(data)
            item.tamper(tampered)
            changed = [
                candidate.requirement_id
                for candidate in registry
                if candidate.check(tampered) != candidate.check(data)
            ]
            if (
                item.check(data) is not True
                or item.check(tampered) is not False
                or changed != [item.requirement_id]
            ):
                failing.append(f"tamper::{item.requirement_id}")
            else:
                rejected.append(item.requirement_id)
    return failing, rejected, registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--diagnostics", type=Path)
    parser.add_argument("--no-tamper", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
        if type(data) is not dict:
            raise ValueError("evidence root must be an object")
        if len(args.expected_sha) != 40 or any(
            c not in "0123456789abcdef" for c in args.expected_sha
        ):
            raise ValueError("expected SHA must be a 40-character lowercase commit SHA")
        repository_head = _repository_head(args.repo_root.resolve())
        failing, rejected, registry = verify(
            data,
            expected_sha=args.expected_sha,
            repository_head=repository_head,
            verify_tamper=not args.no_tamper,
        )
        result = {
            "requirement_count": len(registry),
            "requirement_ids": [x.requirement_id for x in registry],
            "original_pass_count": len(registry)
            - len([item for item in failing if not item.startswith("tamper::")]),
            "tamper_rejected_count": len(rejected),
            "tamper_ids": rejected,
            "failing_requirements": failing,
            "expected_sha": args.expected_sha,
            "repository_head": repository_head,
            "marker": MARKER,
        }
        if args.diagnostics:
            args.diagnostics.write_text(
                json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
            )
        print(json.dumps(result, sort_keys=True))
        if failing or (not args.no_tamper and len(rejected) != len(registry)):
            return 1
        print(MARKER)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {"error": str(exc), "failing_requirements": ["verifier_input"]}, sort_keys=True
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
