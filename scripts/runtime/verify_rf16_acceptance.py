"""Strict, fail-closed RF16 verifier over raw producer observations."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MARKER = "RF16_ACCEPTANCE_VERIFIED"


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]


def _eq(path: str, expected: object) -> Callable[[dict[str, object]], bool]:
    def check(data: dict[str, object]) -> bool:
        value: object = data
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                return False
            value = value[part]
        return value == expected

    return check


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


def _same(path_a: str, path_b: str) -> Callable[[dict[str, object]], bool]:
    def check(data: dict[str, object]) -> bool:
        def get(path: str) -> object:
            value: object = data
            for part in path.split("."):
                if not isinstance(value, dict) or part not in value:
                    raise KeyError(path)
                value = value[part]
            return value

        try:
            return get(path_a) == get(path_b)
        except KeyError:
            return False

    return check


def _registry() -> tuple[Requirement, ...]:
    return (
        Requirement(
            "candidate_identity",
            _eq("technical_id", "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01"),
            _set("technical_id", "tampered"),
        ),
        Requirement("python_3_14_6", _eq("python", "3.14.6"), _set("python", "3.13.0")),
        Requirement(
            "postgresql_18",
            lambda d: "PostgreSQL 18." in str(d.get("postgres_version", "")),
            _set("postgres_version", "PostgreSQL 17"),
        ),
        Requirement(
            "alembic_current_head",
            lambda d: bool(d.get("alembic_head")),
            _set("alembic_head", None),
        ),
        Requirement(
            "exact_four_egress_tables",
            _eq(
                "egress_tables",
                [
                    "egress_agent_heartbeats",
                    "egress_agents",
                    "egress_route_leases",
                    "egress_routes",
                ],
            ),
            _set("egress_tables", []),
        ),
        Requirement(
            "registry_durability",
            lambda d: (
                bool(d.get("registration", {}).get("agent"))
                and bool(d.get("registration", {}).get("route"))
            ),
            _set("registration", {"agent": "", "route": "r", "heartbeat": "h"}),
        ),
        Requirement(
            "heartbeat_durability",
            lambda d: bool(d.get("registration", {}).get("heartbeat")),
            _set("registration", {"agent": "a", "route": "r", "heartbeat": ""}),
        ),
        Requirement(
            "heartbeat_not_readiness",
            _eq("heartbeat_state_is_not_readiness", True),
            _set("heartbeat_state_is_not_readiness", False),
        ),
        Requirement(
            "accepted_semantic_selection",
            _eq("selection.reason", "SELECTED"),
            _set("selection.reason", "READY_ONLY"),
        ),
        Requirement(
            "capability_fail_closed",
            _eq("selection_unsupported.reason", "CAPABILITY_OR_PURPOSE_BLOCKED"),
            _set("selection_unsupported.reason", "SELECTED"),
        ),
        Requirement(
            "multi_route_unapproved_policy_block",
            _eq("multi_route.reason", "MULTIPLE_ROUTES_UNAPPROVED"),
            _set("multi_route.reason", "SELECTED"),
        ),
        Requirement(
            "active_lease_exclusivity", _eq("active_lease_count", 1), _set("active_lease_count", 2)
        ),
        Requirement(
            "concurrent_lease_conflict",
            lambda d: (
                d.get("concurrency", {}).get("distinct_backend_pids") == 2
                and d.get("concurrency", {}).get("active_count") == 1
                and sorted(
                    row.get("reason") for row in d.get("concurrency", {}).get("sessions", [])
                )
                == ["GRANTED", "LEASE_CONFLICT"]
            ),
            _set("concurrency", {}),
        ),
        Requirement(
            "same_identity_replay",
            lambda d: (
                d.get("same_identity_replay", {}).get("id") == d.get("lease", {}).get("id")
                and d.get("same_identity_replay", {}).get("reason") == "REPLAY_ACTIVE"
            ),
            _set("same_identity_replay", {}),
        ),
        Requirement(
            "mismatch_conflict",
            _eq("mismatch_conflict.reason", "LEASE_CONFLICT"),
            _set("mismatch_conflict.reason", "GRANTED"),
        ),
        Requirement(
            "wrong_token_rejection",
            _eq("wrong_token.reason", "IDENTITY_MISMATCH"),
            _set("wrong_token.reason", "COMPLETED"),
        ),
        Requirement(
            "expiry", _eq("expiry.reason", "LEASE_EXPIRED"), _set("expiry.reason", "GRANTED")
        ),
        Requirement(
            "restart_recovery",
            _eq("restart_recovery.durable", True),
            _set("restart_recovery.durable", False),
        ),
        Requirement(
            "ambiguity_replay_block",
            _eq("ambiguity_replay.reason", "RECONCILIATION_REQUIRED"),
            _set("ambiguity_replay.reason", "GRANTED"),
        ),
        Requirement(
            "foreign_state_unchanged",
            _same("foreign_witness_before", "foreign_witness_after"),
            _set("foreign_witness_after", {}),
        ),
        Requirement(
            "safe_diagnostics",
            _eq("safe_diagnostics.safe", True),
            _set("safe_diagnostics.safe", False),
        ),
        Requirement(
            "protocol_strictness",
            _eq("protocol_strictness", True),
            _set("protocol_strictness", False),
        ),
        Requirement(
            "simulator_runtime_parity",
            _eq("simulator_runtime_parity", True),
            _set("simulator_runtime_parity", False),
        ),
        Requirement(
            "dedicated_agent_artifact_boundary",
            _eq("package_boundary", True),
            _set("package_boundary", False),
        ),
        Requirement(
            "parser_fail_closed", _eq("parser_fail_closed", True), _set("parser_fail_closed", False)
        ),
        Requirement(
            "no_secret_raw_provider_persistence",
            _eq("no_secret_raw_provider_persistence", True),
            _set("no_secret_raw_provider_persistence", False),
        ),
    )


REQUIREMENTS = _registry()


def verify(data: dict[str, object], *, verify_tamper: bool = True) -> tuple[list[str], list[str]]:
    if len({item.requirement_id for item in REQUIREMENTS}) != len(REQUIREMENTS):
        raise RuntimeError("duplicate immutable requirement id")
    failing = [item.requirement_id for item in REQUIREMENTS if not item.check(data)]
    rejected: list[str] = []
    if verify_tamper:
        for item in REQUIREMENTS:
            tampered = copy.deepcopy(data)
            try:
                item.tamper(tampered)
            except (KeyError, TypeError):
                raise RuntimeError(f"unknown tamper strategy: {item.requirement_id}") from None
            changed = [
                candidate.requirement_id
                for candidate in REQUIREMENTS
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
    return failing, rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--no-tamper", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.evidence.read_text(encoding="utf-8"))
        if type(data) is not dict:
            raise ValueError("evidence root must be an object")
        failing, rejected = verify(data, verify_tamper=not args.no_tamper)
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {"error": str(exc), "failing_requirements": ["verifier_input"]}, sort_keys=True
            ),
            file=sys.stderr,
        )
        return 2
    result = {
        "requirement_count": len(REQUIREMENTS),
        "original_pass_count": len(REQUIREMENTS)
        - sum(not item.check(data) for item in REQUIREMENTS),
        "tamper_rejected_count": len(rejected),
        "failing_requirements": failing,
    }
    print(json.dumps(result, sort_keys=True))
    if failing or (not args.no_tamper and len(rejected) != len(REQUIREMENTS)):
        return 1
    print(MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
