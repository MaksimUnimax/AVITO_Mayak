"""Independent, fail-closed RF16 acceptance verifier.

Acceptance predicates intentionally consume observations (or explicit package
artifacts), never producer-authored verdicts.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MARKER = "RF16_ACCEPTANCE_VERIFIED"
TECHNICAL_ID = "RF-16-EGRESS-ROUTING-DURABLE-RUNTIME-20260803-01"
BANNED = {
    "before_after_equal",
    "windows_overlap",
    "database_authoritative",
    "safe_metadata_only",
    "secret_fields",
    "allowlisted_files",
    "deterministic",
    "forbidden_modules",
    "disallowed_classes",
    "raw_provider_material",
    "parser_success",
    "purpose_match",
    "capability_scope_match",
    "restriction_clear",
    "evidence_current",
    "reconciliation_eligible",
    "physical_route_exists",
}
FORBIDDEN = re.compile(
    r"password|secret|authorization|cookie|credential|private.?key|raw.?body|raw.?payload|headers?|html|provider.?token",
    re.I,
)
ALLOWED_PACKAGE = {
    "mayak/modules/egress_routing/protocol.py",
    "mayak/modules/egress_routing/agent_entrypoint.py",
    "MANIFEST.json",
}


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]
    source: str
    source_kind: str


def _get(data: dict[str, object], path: str) -> object:
    value: object = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(path)
        value = value[part]
    return value


def _set(path: str, value: object) -> Callable[[dict[str, object]], None]:
    def tamper(data: dict[str, object]) -> None:
        target: object = data
        bits = path.split(".")
        for bit in bits[:-1]:
            if isinstance(target, dict):
                target = target.get(bit)
            elif isinstance(target, list) and bit.isdigit() and int(bit) < len(target):
                target = target[int(bit)]
            else:
                raise KeyError(path)
        if isinstance(target, dict):
            target[bits[-1]] = value
        elif isinstance(target, list) and bits[-1].isdigit():
            target[int(bits[-1])] = value
        else:
            raise KeyError(path)

    return tamper


def _check(fn: Callable[[dict[str, object]], bool]) -> Callable[[dict[str, object]], bool]:
    def wrapped(data: dict[str, object]) -> bool:
        try:
            return fn(data)
        except (KeyError, TypeError, ValueError, IndexError):
            return False

    return wrapped


def _r(
    rid: str,
    fn: Callable[[dict[str, object]], bool],
    tamper: Callable[[dict[str, object]], None],
    source: str,
    kind: str = "DB physical",
) -> Requirement:
    return Requirement(rid, _check(fn), tamper, source, kind)


def _raw_projection(value: object) -> bool:
    return isinstance(value, dict) and bool(value)


def _registry(expected_sha: str, repository_head: str) -> tuple[Requirement, ...]:
    exact_tables = [
        "egress_agent_heartbeats",
        "egress_agents",
        "egress_route_leases",
        "egress_routes",
    ]

    def selection(d: dict[str, object]) -> bool:
        s = d["selection"]
        candidates = s["candidate_observations"]
        if not isinstance(s, dict) or not isinstance(candidates, list):
            return False
        eligible = [
            c
            for c in candidates
            if isinstance(c, dict)
            and c.get("route_id")
            and c.get("purpose") == "scan"
            and c.get("capability_scope") == ["listing_read"]
            and c.get("registration_state") == "REGISTERED"
            and c.get("readiness_state") == "READY"
            and c.get("health_state") == "HEALTHY"
            and c.get("restriction_state") == "CLEAR"
            and c.get("evidence_current_state") == "CURRENT"
            and c.get("reconciliation_state") == "NOT_REQUIRED"
        ]
        return (
            len(eligible) == 1
            and s.get("status") == "SELECTED"
            and s.get("selected_route_id") == eligible[0]["route_id"]
        )

    def blocking(d: dict[str, object]) -> bool:
        rows = d["selection_blocking"]
        return (
            isinstance(rows, list)
            and len(rows) >= 7
            and all(
                isinstance(x, dict)
                and x.get("altered_fact")
                and x.get("result") is False
                and x.get("reason")
                for x in rows
            )
        )

    def foreign(d: dict[str, object]) -> bool:
        b, i, a = (
            d["foreign_witness_before"],
            d["foreign_witness_after_in_tx"],
            d["foreign_witness_after"],
        )
        return (
            _raw_projection(b)
            and b == i == a
            and set(b)
            == {"identity", "beacon", "schedule", "work", "parser_row_ids", "notification_rows"}
        )

    def overlap(d: dict[str, object]) -> bool:
        c = d["concurrency"]
        rows = c["sessions"]
        if not isinstance(rows, list) or len(rows) != 2:
            return False
        pids = {x.get("pid") for x in rows}
        reasons = sorted(x.get("reason") for x in rows)
        return (
            len(pids) == 2
            and reasons == ["GRANTED", "LEASE_CONFLICT"]
            and c.get("active_count") == 1
            and all(x.get("operation_started_at") and x.get("operation_finished_at") for x in rows)
            and rows[0]["operation_started_at"] < rows[1]["operation_finished_at"]
            and rows[1]["operation_started_at"] < rows[0]["operation_finished_at"]
        )

    def expiry(d: dict[str, object]) -> bool:
        e = d["expiry"]
        return (
            e.get("state_before") == "ACTIVE"
            and e.get("expires_at") <= e.get("decision_at")
            and e.get("reason") == "LEASE_EXPIRED"
            and e.get("state_after") == "EXPIRED"
        )

    def diagnostics(d: dict[str, object]) -> bool:
        x = d["diagnostics"]
        raw = x.get("observed") if isinstance(x, dict) else None

        def scan(v: object) -> bool:
            if isinstance(v, dict):
                return all(not FORBIDDEN.search(str(k)) and scan(val) for k, val in v.items())
            if isinstance(v, list):
                return all(scan(i) for i in v)
            return not (isinstance(v, str) and FORBIDDEN.search(v))

        return (
            isinstance(raw, dict)
            and scan(raw)
            and set(raw) <= {"route_id", "lease_id", "agent_id", "scenario", "protocol_version"}
        )

    def parser(d: dict[str, object]) -> bool:
        expected = {
            "NOT_SENT": {None, "NO_REQUEST"},
            "UNAVAILABLE": {"TRANSPORT_UNAVAILABLE"},
            "FAILURE": {"RESULT_AMBIGUOUS"},
            "RESTRICTED": {"RATE_OR_ACCESS_RESTRICTED", "UNCLASSIFIED"},
            "MALFORMED": {"MALFORMED_RESPONSE", "UNSUPPORTED_STRUCTURE"},
            "DISPATCH_AMBIGUOUS": {"RESULT_AMBIGUOUS"},
            "RESULT_AMBIGUOUS": {"RESULT_AMBIGUOUS"},
            "VALIDATED_RESPONSE": {"USABLE_RESPONSE"},
        }
        rows = d["parser_cases"]
        return (
            isinstance(rows, list)
            and len(rows) == len(expected)
            and all(
                x.get("parser_status") in expected.get(x.get("case_id"), set())
                and (
                    x.get("case_id") == "VALIDATED_RESPONSE"
                    or x.get("parser_status") != "USABLE_RESPONSE"
                )
                for x in rows
            )
        )

    def protocol(d: dict[str, object]) -> bool:
        rows = d["protocol_cases"]
        expected = {"canonical_valid": True, "canonical_assignment": True}
        return (
            isinstance(rows, list)
            and {x.get("case_id") for x in rows}
            == set(expected)
            | {
                "unknown_version",
                "unknown_type",
                "unknown_key",
                "malformed_uuid",
                "oversized",
                "forbidden_heartbeat_outcome",
                "missing_assignment_identity",
                "agent_outcome_server_shape",
            }
            and all(
                x.get("accepted") is expected[x["case_id"]]
                if x["case_id"] in expected
                else x.get("accepted") is False
                for x in rows
            )
        )

    def simulator(d: dict[str, object]) -> bool:
        expected = {
            "HEARTBEAT": ("HEARTBEAT", None),
            "ACCEPTED_ASSIGNMENT": ("RECEIPT", None),
            "NOT_SENT": ("OUTCOME", "NOT_SENT"),
            "UNAVAILABLE": ("OUTCOME", "UNAVAILABLE"),
            "FAILURE": ("OUTCOME", "FAILURE"),
            "SUCCESS_TRANSPORT": ("OUTCOME", "SUCCESS_TRANSPORT_ONLY"),
            "RESTRICTED": ("OUTCOME", "RESTRICTED"),
            "MALFORMED": ("OUTCOME", "MALFORMED_UNUSABLE"),
            "DISPATCH_AMBIGUOUS": ("OUTCOME", "DISPATCH_AMBIGUOUS"),
            "RESULT_AMBIGUOUS": ("OUTCOME", "RESULT_AMBIGUOUS"),
            "DUPLICATE": ("RECEIPT", None),
            "MISMATCHED_DUPLICATE": ("OUTCOME", "RESULT_AMBIGUOUS"),
            "EXPIRED_LEASE": ("OUTCOME", "RECONCILIATION_REQUIRED"),
            "REVOKED_LEASE": ("OUTCOME", "RECONCILIATION_REQUIRED"),
            "RESTART_REPLAY": ("RECEIPT", None),
            "restart_replay_after_restart": ("RECEIPT", None),
        }
        rows = d["simulator_cases"]
        return (
            isinstance(rows, list)
            and {x.get("scenario") for x in rows} == set(expected)
            and all(
                (x.get("message_type"), x.get("effect")) == expected[x["scenario"]] for x in rows
            )
        )

    def persistence(d: dict[str, object]) -> bool:
        p = d["persistence_projection"]
        allowed = {
            "id",
            "agent_id",
            "agent_code",
            "route_code",
            "state",
            "observed_at",
            "route_id",
            "work_item_id",
            "lease_expires_at",
        }
        return (
            isinstance(p, dict)
            and set(p.get("tables", {}))
            == {"egress_agents", "egress_routes", "egress_agent_heartbeats", "egress_route_leases"}
            and all(
                set(row) <= allowed
                and not any(
                    FORBIDDEN.search(str(k)) or (isinstance(v, str) and FORBIDDEN.search(v))
                    for k, v in row.items()
                )
                for rows in p["tables"].values()
                for row in rows
            )
        )

    def package(d: dict[str, object]) -> bool:
        p = d.get("package_external", d.get("package", {}))
        return isinstance(p, dict) and p.get("verified") is True

    return (
        _r(
            "candidate_identity",
            lambda d: (
                d["identity"].get("technical_id") == TECHNICAL_ID
                and d["identity"].get("candidate_sha") == expected_sha
            ),
            _set("identity.candidate_sha", "0" * 40),
            "identity.candidate_sha",
            "repository identity",
        ),
        _r(
            "python_3_14_6",
            lambda d: d["environment"].get("python") == "3.14.6",
            _set("environment.python", "3.13"),
            "environment.python",
            "runtime",
        ),
        _r(
            "postgresql_18",
            lambda d: str(d["environment"].get("postgres_version", "")).startswith(
                "PostgreSQL 18."
            ),
            _set("environment.postgres_version", "PostgreSQL 17"),
            "environment.postgres_version",
            "DB physical",
        ),
        _r(
            "alembic_current_head",
            lambda d: (
                d["alembic"].get("db_head") == repository_head
                and d["alembic"].get("repository_heads") == [repository_head]
            ),
            _set("alembic.db_head", "deadbeef"),
            "alembic.db_head/repository_heads",
        ),
        _r(
            "exact_four_egress_tables",
            lambda d: d["database"].get("egress_tables") == exact_tables,
            _set("database.egress_tables", []),
            "database.egress_tables",
        ),
        _r(
            "registration_durable",
            lambda d: (
                d["registration"].get("persisted_ids") == d["registration"].get("returned_ids")
                and d["registration"].get("new_connection") is True
                and d["registration"].get("route_agent_id") == d["registration"].get("agent_id")
            ),
            _set("registration.new_connection", False),
            "registration.persisted_ids/returned_ids/new_connection",
        ),
        _r(
            "heartbeat_durable",
            lambda d: (
                bool(d["heartbeat"].get("row_id")) and d["heartbeat"].get("new_connection") is True
            ),
            _set("heartbeat.row_id", ""),
            "heartbeat.row_id/new_connection",
        ),
        _r(
            "heartbeat_not_readiness",
            lambda d: (
                d["heartbeat"].get("agent_state_before") == d["heartbeat"].get("agent_state_after")
                and d["heartbeat"].get("route_state_before")
                == d["heartbeat"].get("route_state_after")
                and d["heartbeat"].get("state") == "ONLINE"
            ),
            _set("heartbeat.route_state_after", "RESTRICTED"),
            "heartbeat raw row and state projections",
        ),
        _r(
            "selection_exact_physical_route",
            lambda d: (
                d["selection"].get("status") == "SELECTED"
                and d["selection"].get("selected_route_id")
                == d["selection"].get("selected_route_db_id")
            ),
            _set("selection.selected_route_db_id", "absent"),
            "selection.selected_route_id/selected_route_db_id",
        ),
        _r(
            "selection_semantic_gates",
            selection,
            _set("selection.candidate_observations.0.evidence_current_state", "STALE"),
            "selection.candidate_observations",
            "runtime call result",
        ),
        _r(
            "selection_blocking_cases",
            blocking,
            _set("selection_blocking", []),
            "selection_blocking raw candidate facts/result",
            "runtime call result",
        ),
        _r(
            "multi_route_unapproved_policy_block",
            lambda d: (
                len(d["multi_route"].get("candidate_observations", [])) >= 2
                and d["multi_route"].get("result") is False
                and d["multi_route"].get("reason") == "MULTIPLE_ROUTES_UNAPPROVED"
            ),
            _set("multi_route.reason", "SELECTED"),
            "multi_route.candidate_observations/result/reason",
            "runtime call result",
        ),
        _r(
            "active_lease_exclusivity",
            lambda d: d["lease"].get("active_count") == 1,
            _set("lease.active_count", 2),
            "lease physical state/count",
        ),
        _r(
            "concurrent_lease_conflict",
            overlap,
            _set("concurrency.sessions.0.operation_started_at", "9999-01-01T00:00:00+00:00"),
            "concurrency.sessions timestamps/PIDs/results",
        ),
        _r(
            "same_identity_replay",
            lambda d: (
                d["replay"].get("returned_id") == d["replay"].get("original_id")
                and d["replay"].get("reason") == "REPLAY_ACTIVE"
            ),
            _set("replay.returned_id", "wrong"),
            "replay runtime result + IDs",
            "runtime call result",
        ),
        _r(
            "mismatch_conflict",
            lambda d: d["mismatch"].get("reason") == "LEASE_CONFLICT",
            _set("mismatch.reason", "GRANTED"),
            "mismatch runtime reason",
            "runtime call result",
        ),
        _r(
            "wrong_token_rejection",
            lambda d: d["wrong_token"].get("reason") == "IDENTITY_MISMATCH",
            _set("wrong_token.reason", "COMPLETED"),
            "wrong_token runtime reason",
            "runtime call result",
        ),
        _r(
            "expiry_recovery",
            expiry,
            _set("expiry.decision_at", "1970-01-01T00:00:00+00:00"),
            "expiry physical state/deadline/DB decision time",
            "DB physical",
        ),
        _r(
            "restart_recovery",
            lambda d: (
                d["restart"].get("session_a") != d["restart"].get("session_b")
                and d["restart"].get("backend_pid_a") != d["restart"].get("backend_pid_b")
                and d["restart"].get("state_before") == "ACTIVE"
                and d["restart"].get("state_after") == "COMPLETED"
                and d["restart"].get("result") == "COMPLETED"
            ),
            _set("restart.result", "GRANTED"),
            "restart session/PID/physical state/result",
            "DB physical",
        ),
        _r(
            "ambiguity_replay_block",
            lambda d: (
                d["ambiguity_replay"].get("reason")
                in {"RECONCILIATION_REQUIRED", "REPLAY_AMBIGUOUS"}
            ),
            _set("ambiguity_replay.reason", "GRANTED"),
            "ambiguity replay runtime reason",
            "runtime call result",
        ),
        _r(
            "foreign_state_unchanged",
            foreign,
            _set("foreign_witness_after.work", [{"state": "DONE"}]),
            "foreign_witness_before/after_in_tx/after",
            "DB physical",
        ),
        _r(
            "safe_diagnostics",
            diagnostics,
            _set("diagnostics.observed.injected", "password"),
            "diagnostics.observed",
            "protocol execution",
        ),
        _r(
            "protocol_strictness",
            protocol,
            _set("protocol_cases.2.accepted", True),
            "protocol_cases raw decoder result",
            "protocol execution",
        ),
        _r(
            "simulator_runtime_parity",
            simulator,
            _set("simulator_cases.0.effect", "FAILURE"),
            "simulator_cases message/effect/IDs",
            "simulator execution",
        ),
        _r(
            "parser_fail_closed",
            parser,
            _set("parser_cases.0.parser_status", "USABLE_RESPONSE"),
            "parser_cases.parser_status",
            "Parser execution",
        ),
        _r(
            "dedicated_agent_artifact_boundary",
            package,
            _set("package_external.verified", False),
            "external package manifests/ZIP",
            "external package artifact",
        ),
        _r(
            "no_secret_raw_provider_persistence",
            persistence,
            _set("persistence_projection.tables.egress_routes.0.provider_body", "secret"),
            "persistence_projection.tables",
            "DB physical",
        ),
    )


def source_map(registry: tuple[Requirement, ...]) -> list[dict[str, str]]:
    return [
        {
            "requirement_id": r.requirement_id,
            "authoritative_raw_path": r.source,
            "checker": r.requirement_id,
            "tamper_source": r.source,
            "source_kind": r.source_kind,
        }
        for r in registry
    ]


def _package_verify(build1: Path, build2: Path, agent_zip: Path) -> dict[str, object]:
    a, b = json.loads(build1.read_text()), json.loads(build2.read_text())
    digest = hashlib.sha256(agent_zip.read_bytes()).hexdigest()
    with zipfile.ZipFile(agent_zip) as z:
        names = z.namelist()
        manifest = json.loads(z.read("MANIFEST.json"))
    ok = (
        a.get("sha256") == b.get("sha256") == digest
        and set(names) == ALLOWED_PACKAGE
        and manifest.get("source_release") == "rf16-egress-routing-durable-runtime-20260803-01"
        and all(".." not in n and not n.startswith("/") for n in names)
    )
    return {
        "verified": ok,
        "build_1_sha256": a.get("sha256"),
        "build_2_sha256": b.get("sha256"),
        "zip_sha256": digest,
        "members": names,
    }


def build_representative_evidence(expected_sha: str, repository_head: str) -> dict[str, object]:
    """Deterministic raw fixture for verifier tests, including raw-corruption surfaces."""
    d: dict[str, object] = {
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
            "route_agent_id": "a",
            "returned_ids": {"agent": "a", "route": "r", "heartbeat": "h"},
            "persisted_ids": {"agent": "a", "route": "r", "heartbeat": "h"},
            "new_connection": True,
        },
        "heartbeat": {
            "row_id": "h",
            "state": "ONLINE",
            "agent_state_before": "READY",
            "agent_state_after": "READY",
            "route_state_before": "READY",
            "route_state_after": "READY",
            "new_connection": True,
        },
        "selection": {
            "status": "SELECTED",
            "selected_route_id": "r",
            "selected_route_db_id": "r",
            "candidate_observations": [
                {
                    "route_id": "r",
                    "purpose": "scan",
                    "capability_scope": ["listing_read"],
                    "registration_state": "REGISTERED",
                    "readiness_state": "READY",
                    "health_state": "HEALTHY",
                    "restriction_state": "CLEAR",
                    "evidence_current_state": "CURRENT",
                    "reconciliation_state": "NOT_REQUIRED",
                }
            ],
        },
        "selection_blocking": [
            {"altered_fact": "x", "result": False, "reason": "BLOCKED"} for _ in range(8)
        ],
        "multi_route": {
            "candidate_observations": [{"route_id": "r"}, {"route_id": "r2"}],
            "result": False,
            "reason": "MULTIPLE_ROUTES_UNAPPROVED",
        },
        "lease": {"active_count": 1},
        "concurrency": {
            "sessions": [
                {
                    "pid": 1,
                    "reason": "GRANTED",
                    "operation_started_at": "2026-01-01T00:00:00+00:00",
                    "operation_finished_at": "2026-01-01T00:00:02+00:00",
                },
                {
                    "pid": 2,
                    "reason": "LEASE_CONFLICT",
                    "operation_started_at": "2026-01-01T00:00:01+00:00",
                    "operation_finished_at": "2026-01-01T00:00:03+00:00",
                },
            ],
            "active_count": 1,
        },
        "replay": {"original_id": "l", "returned_id": "l", "reason": "REPLAY_ACTIVE"},
        "mismatch": {"reason": "LEASE_CONFLICT"},
        "wrong_token": {"reason": "IDENTITY_MISMATCH"},
        "expiry": {
            "state_before": "ACTIVE",
            "expires_at": "2025-01-01T00:00:00+00:00",
            "decision_at": "2026-01-01T00:00:00+00:00",
            "reason": "LEASE_EXPIRED",
            "state_after": "EXPIRED",
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
        "foreign_witness_before": {
            "identity": [],
            "beacon": [],
            "schedule": [],
            "work": [],
            "parser_row_ids": [],
            "notification_rows": [],
        },
        "foreign_witness_after_in_tx": {
            "identity": [],
            "beacon": [],
            "schedule": [],
            "work": [],
            "parser_row_ids": [],
            "notification_rows": [],
        },
        "foreign_witness_after": {
            "identity": [],
            "beacon": [],
            "schedule": [],
            "work": [],
            "parser_row_ids": [],
            "notification_rows": [],
        },
        "diagnostics": {"observed": {"route_id": "r", "lease_id": "l"}},
        "protocol_cases": [
            {"case_id": "canonical_valid", "accepted": True},
            {"case_id": "canonical_assignment", "accepted": True},
        ]
        + [
            {"case_id": x, "accepted": False}
            for x in [
                "unknown_version",
                "unknown_type",
                "unknown_key",
                "malformed_uuid",
                "oversized",
                "forbidden_heartbeat_outcome",
                "missing_assignment_identity",
                "agent_outcome_server_shape",
            ]
        ],
        "simulator_cases": [
            {"scenario": "HEARTBEAT", "message_type": "HEARTBEAT", "effect": None},
            {"scenario": "ACCEPTED_ASSIGNMENT", "message_type": "ASSIGNMENT", "effect": "ACCEPTED"},
        ]
        + [
            {
                "scenario": x,
                "message_type": "OUTCOME",
                "effect": (
                    {
                        "SUCCESS_TRANSPORT": "SUCCESS_TRANSPORT_ONLY",
                        "MALFORMED": "MALFORMED_UNUSABLE",
                    }.get(
                        x,
                        "RECONCILIATION_REQUIRED"
                        if x
                        in {
                            "EXPIRED_LEASE",
                            "REVOKED_LEASE",
                            "RESTART_REPLAY",
                            "restart_replay_after_restart",
                        }
                        else x,
                    )
                ),
            }
            for x in [
                "NOT_SENT",
                "UNAVAILABLE",
                "FAILURE",
                "SUCCESS_TRANSPORT",
                "RESTRICTED",
                "MALFORMED",
                "DISPATCH_AMBIGUOUS",
                "RESULT_AMBIGUOUS",
                "DUPLICATE",
                "MISMATCHED_DUPLICATE",
                "EXPIRED_LEASE",
                "REVOKED_LEASE",
                "RESTART_REPLAY",
                "restart_replay_after_restart",
            ]
        ],
        "parser_cases": [
            {"case_id": "NOT_SENT", "parser_status": None},
            {"case_id": "UNAVAILABLE", "parser_status": "TRANSPORT_UNAVAILABLE"},
            {"case_id": "FAILURE", "parser_status": "RESULT_AMBIGUOUS"},
            {"case_id": "RESTRICTED", "parser_status": "RATE_OR_ACCESS_RESTRICTED"},
            {"case_id": "MALFORMED", "parser_status": "MALFORMED_RESPONSE"},
            {"case_id": "DISPATCH_AMBIGUOUS", "parser_status": "RESULT_AMBIGUOUS"},
            {"case_id": "RESULT_AMBIGUOUS", "parser_status": "RESULT_AMBIGUOUS"},
            {"case_id": "VALIDATED_RESPONSE", "parser_status": "USABLE_RESPONSE"},
        ],
        "persistence_projection": {
            "tables": {
                x: [{"id": "x", "state": "READY"}]
                for x in [
                    "egress_agents",
                    "egress_routes",
                    "egress_agent_heartbeats",
                    "egress_route_leases",
                ]
            }
        },
        "package_external": {"verified": True},
    }
    d["simulator_cases"][1] = {
        "scenario": "ACCEPTED_ASSIGNMENT",
        "message_type": "RECEIPT",
        "effect": None,
    }
    for row in d["simulator_cases"]:
        if row["scenario"] in {"DUPLICATE", "RESTART_REPLAY", "restart_replay_after_restart"}:
            row["message_type"], row["effect"] = "RECEIPT", None
        if row["scenario"] == "MISMATCHED_DUPLICATE":
            row["effect"] = "RESULT_AMBIGUOUS"
    return d


def verify(
    data: dict[str, object],
    *,
    expected_sha: str,
    repository_head: str,
    verify_tamper: bool = True,
    package_inputs: tuple[Path, Path, Path] | None = None,
) -> tuple[list[str], list[str], tuple[Requirement, ...]]:
    if package_inputs:
        data = copy.deepcopy(data)
        data["package_external"] = _package_verify(*package_inputs)
    registry = _registry(expected_sha, repository_head)
    ids = [r.requirement_id for r in registry]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate immutable requirement id")
    failing = [r.requirement_id for r in registry if r.check(data) is not True]
    rejected: list[str] = []
    if verify_tamper:
        for r in registry:
            tampered = copy.deepcopy(data)
            r.tamper(tampered)
            changed = [x.requirement_id for x in registry if x.check(tampered) != x.check(data)]
            if (
                r.check(data) is not True
                or r.check(tampered) is not False
                or changed != [r.requirement_id]
            ):
                failing.append(f"tamper::{r.requirement_id}")
            else:
                rejected.append(r.requirement_id)
    return failing, rejected, registry


def _repository_head(repo_root: Path) -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    heads = ScriptDirectory.from_config(Config(str(repo_root / "alembic.ini"))).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"repository must have exactly one Alembic head, got {heads}")
    return heads[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("evidence", type=Path)
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--diagnostics", type=Path)
    p.add_argument("--package-build-1", type=Path)
    p.add_argument("--package-build-2", type=Path)
    p.add_argument("--agent-zip", type=Path)
    p.add_argument("--no-tamper", action="store_true")
    a = p.parse_args()
    try:
        data = json.loads(a.evidence.read_text())
        head = _repository_head(a.repo_root.resolve())
        package = (a.package_build_1, a.package_build_2, a.agent_zip)
        if any(package) and not all(package):
            raise ValueError("all external package inputs are required")
        failing, rejected, registry = verify(
            data,
            expected_sha=a.expected_sha,
            repository_head=head,
            verify_tamper=not a.no_tamper,
            package_inputs=package if all(package) else None,
        )
        result = {
            "requirement_count": len(registry),
            "requirement_ids": [r.requirement_id for r in registry],
            "tamper_ids": rejected,
            "original_pass_count": len(registry)
            - len([x for x in failing if not x.startswith("tamper::")]),
            "tamper_rejected_count": len(rejected),
            "failing_requirements": failing,
            "expected_sha": a.expected_sha,
            "repository_head": head,
            "raw_source_map": source_map(registry),
            "banned_summary_authority": sorted(BANNED),
            "marker": MARKER,
        }
        if a.diagnostics:
            a.diagnostics.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print(json.dumps(result, sort_keys=True))
        if failing or (not a.no_tamper and len(rejected) != len(registry)):
            return 1
        print(MARKER)
        return 0
    except (OSError, json.JSONDecodeError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print(
            json.dumps(
                {"error": str(exc), "failing_requirements": ["verifier_input"]}, sort_keys=True
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
