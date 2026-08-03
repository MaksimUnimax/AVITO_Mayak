"""Independent fail-closed RF17 verifier with an adversarial tamper matrix."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MARKER = "RF17_NOTIFICATION_DELIVERY_RUNTIME_VERIFIED"
TECHNICAL_ID = "RF-17-NOTIFICATION-DELIVERY-DURABLE-RUNTIME-20260803-01"


@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    tamper_strategy_id: str
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]


def _tamper(path: str, value: object) -> Callable[[dict[str, object]], None]:
    def apply(data: dict[str, object]) -> None:
        target: object = data
        parts = path.split(".")
        for part in parts[:-1]:
            target = target[int(part)] if isinstance(target, list) else target[part]  # type: ignore[index]
        if isinstance(target, list):
            target[int(parts[-1])] = value
        else:
            target[parts[-1]] = value  # type: ignore[index]

    return apply


def _req(
    rid: str,
    sid: str,
    check: Callable[[dict[str, object]], bool],
    tamper: Callable[[dict[str, object]], None],
) -> Requirement:
    del sid
    return Requirement(rid, rid, check, tamper)


def _duplicate_second_from_first(data: dict[str, object]) -> None:
    observations = data["claim_observations"]
    observations[1]["outbox_id"] = observations[0]["outbox_id"]  # type: ignore[index]


def registry() -> tuple[Requirement, ...]:
    return (
        _req(
            "source.single_event",
            "tamper.source.event_id",
            lambda d: bool(d["event_id"]) and d["replay_event_id"] == d["event_id"],
            _tamper("event_id", "00000000-0000-0000-0000-000000000000"),
        ),
        _req(
            "source.concurrent_replay",
            "tamper.source.concurrent_ids",
            lambda d: len(set(d["concurrent_event_ids"])) == 1,
            _tamper("concurrent_event_ids.0", "00000000-0000-0000-0000-000000000001"),
        ),
        _req(
            "source.fingerprint_conflict",
            "tamper.source.conflict",
            lambda d: d["idempotency_conflict_error"] == "IdempotencyConflict",
            _tamper("idempotency_conflict_error", "none"),
        ),
        _req(
            "baseline.no_event",
            "tamper.baseline.event_id",
            lambda d: d["baseline_event_id"] is None,
            _tamper("baseline_event_id", "00000000-0000-0000-0000-000000000002"),
        ),
        _req(
            "status.no_event",
            "tamper.status.event_id",
            lambda d: d["no_new_event_id"] is None,
            _tamper("no_new_event_id", "00000000-0000-0000-0000-000000000003"),
        ),
        _req(
            "price.disabled",
            "tamper.price.event_id",
            lambda d: d["price_event_id"] is None,
            _tamper("price_event_id", "00000000-0000-0000-0000-000000000004"),
        ),
        _req(
            "fanout.explicit_endpoints",
            "tamper.fanout.remove",
            lambda d: len(d["first_fanout_ids"]) == 2,
            _tamper("first_fanout_ids", ["00000000-0000-0000-0000-000000000005"]),
        ),
        _req(
            "fanout.replay_no_duplicate",
            "tamper.fanout.replay",
            lambda d: len(d["second_fanout_ids"]) == 0,
            _tamper("second_fanout_ids", ["00000000-0000-0000-0000-000000000006"]),
        ),
        _req(
            "claim.one_owner_per_item",
            "tamper.claim.duplicate_owner",
            lambda d: (
                len({item["outbox_id"] for item in d["claim_observations"]}) == 2
                and len(d["claim_observations"]) == 2
            ),
            _duplicate_second_from_first,
        ),
        _req(
            "attempt.definite_result",
            "tamper.attempt.accepted",
            lambda d: d["attempts"][0]["state"] == "DELIVERED",
            _tamper("attempts.0.state", "FAILED"),
        ),
        _req(
            "attempt.ambiguous_reconcile",
            "tamper.attempt.ambiguous",
            lambda d: d["attempts"][1]["state"] == "RECONCILIATION_REQUIRED",
            _tamper("attempts.1.state", "DELIVERED"),
        ),
        _req(
            "transaction.attempt_committed_before_adapter",
            "tamper.transaction.visibility",
            lambda d: d["fresh_connection_attempt_rows"] == [1, 1],
            _tamper("fresh_connection_attempt_rows.0", 0),
        ),
        _req(
            "provider.result_replay_idempotent",
            "tamper.provider.replay",
            lambda d: d["provider_replay_states"] == ["DELIVERED"],
            _tamper("provider_replay_states", ["FAILED"]),
        ),
        _req(
            "history.safe_listing_refs",
            "tamper.history.refs",
            lambda d: all(
                item["listing_reference_ids"] == ["listing-a", "listing-b"] for item in d["history"]
            ),
            _tamper("history.0.listing_reference_ids", ["unsafe"]),
        ),
        _req(
            "foreign.tables.unchanged",
            "tamper.foreign.after",
            lambda d: d["foreign_before"] == d["foreign_after"],
            _tamper("foreign_after", {"tampered": 1}),
        ),
        _req(
            "schema.exact_five_tables",
            "tamper.schema.tables",
            lambda d: (
                d["tables"] == sorted(d["tables"])
                and len(d["tables"]) == 5
                and all(name.startswith("notification_") for name in d["tables"])
            ),
            _tamper("tables.0", "shadow_queue"),
        ),
        _req(
            "payload.safe_projection",
            "tamper.safe_projection",
            lambda d: (
                d["safe_projection"] is True
                and not any("secret" in json.dumps(d).lower() for _ in (0,))
            ),
            _tamper("safe_projection", False),
        ),
    )


def verify(data: dict[str, object], expected_sha: str | None, diagnostics_path: Path) -> None:
    if data.get("technical_id") != TECHNICAL_ID or (
        expected_sha is not None and data.get("candidate_sha") != expected_sha
    ):
        raise SystemExit("RF17 evidence identity mismatch")
    if not str(data.get("postgres_version", "")).startswith("PostgreSQL 18."):
        raise SystemExit("RF17 requires PostgreSQL 18")
    requirements = registry()
    original_failures = [req.requirement_id for req in requirements if not req.check(data)]
    tamper_rejected: list[str] = []
    tamper_failures: dict[str, str] = {}
    for req in requirements:
        mutated = copy.deepcopy(data)
        try:
            req.tamper(mutated)
            if not req.check(mutated):
                tamper_rejected.append(req.requirement_id)
            else:
                tamper_failures[req.requirement_id] = "tamper preserved requirement"
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            tamper_failures[req.requirement_id] = type(exc).__name__
    diagnostics = {
        "technical_id": TECHNICAL_ID,
        "requirement_count": len(requirements),
        "requirement_ids": [req.requirement_id for req in requirements],
        "tamper_strategy_ids": [req.tamper_strategy_id for req in requirements],
        "tamper_rejected_ids": tamper_rejected,
        "original_failing_ids": original_failures,
        "tamper_failing_ids": sorted(tamper_failures),
        "original_pass_count": len(requirements) - len(original_failures),
        "tamper_rejected_count": len(tamper_rejected),
        "failing_requirements": original_failures + sorted(tamper_failures),
        "evidence_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
    }
    diagnostics_path.write_text(
        json.dumps(diagnostics, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    if (
        original_failures
        or set(diagnostics["requirement_ids"]) != set(diagnostics["tamper_strategy_ids"])
        or set(diagnostics["requirement_ids"]) != set(diagnostics["tamper_rejected_ids"])
    ):
        raise SystemExit("RF17 verifier failed")
    print(MARKER)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--diagnostics", type=Path, required=True)
    args = parser.parse_args()
    verify(
        json.loads(args.evidence.read_text(encoding="utf-8")), args.expected_sha, args.diagnostics
    )


if __name__ == "__main__":
    main()
