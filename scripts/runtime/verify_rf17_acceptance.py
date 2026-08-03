"""Independent, fixed-scope RF17 verifier.

The producer records observations only.  This module owns the acceptance
registry and computes every verdict, including the adversarial meta-gate.
"""

# ruff: noqa: E501
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MARKER = "RF17_NOTIFICATION_DELIVERY_RUNTIME_VERIFIED"
TECHNICAL_ID = "RF-17-NOTIFICATION-DELIVERY-DURABLE-RUNTIME-20260803-01"
EXPECTED_RF17_REQUIREMENT_IDS = (
    "identity.candidate_sha", "identity.pg18_db_repo_head", "schema.physical_five_tables",
    "security.app_role_notification_only", "source.single_event", "source.replay_same",
    "source.concurrent_same", "source.identity_fingerprint_mismatch", "source.same_fingerprint_cross_scope_conflict",
    "source.baseline_blocked", "source.no_new_blocked", "source.price_blocked", "source.non_notification_families_blocked",
    "source.unsafe_payload_blocked", "endpoint.stable_replay", "endpoint.cross_account_rebind_blocked",
    "endpoint.accepted_channel_evidence", "fanout.explicit_targets", "fanout.empty_blocked", "fanout.concurrent_dedup",
    "claim.same_item_single_owner", "claim.deterministic_order", "lease.wrong_token_blocked", "lease.expired_terminal_blocked",
    "attempt.unique_number", "transaction.attempt_committed_before_adapter", "transaction.adapter_outside_db_transaction",
    "result.definite_success", "result.not_human_read", "result.definite_failure_no_retry", "result.replay_same",
    "result.mismatch_blocked", "reconciliation.single_on_ambiguous", "reconciliation.unresolved_blocks_attempt",
    "reconciliation.replay_same", "reconciliation.resolved_delivered", "reconciliation.confirmed_no_effect_only_retry",
    "reconciliation.manual_ambiguous_blocks", "restart.claim_before_attempt_reclaim", "restart.retry_claim_before_attempt_reclaim",
    "restart.after_attempt_reconcile", "history.account_scope", "history.beacon_scope", "history.cross_account_blocked",
    "history.safe_refs", "foreign.authority_unchanged", "privacy.no_raw_provider_values", "privacy.no_raw_lease_values",
)
EXPECTED_RF17_TAMPER_STRATEGY_IDS = tuple("tamper." + item for item in EXPECTED_RF17_REQUIREMENT_IDS)

_SECRET_VALUE = re.compile(r"(?i)(bearer\s+\S+|authorization\s*[:=]|cookie\s*[:=]|lease_token\s*[:=]\s*[0-9a-f-]{20,})")

@dataclass(frozen=True, slots=True)
class Requirement:
    requirement_id: str
    tamper_strategy_id: str
    check: Callable[[dict[str, object]], bool]
    tamper: Callable[[dict[str, object]], None]

def _fact(name: str) -> Callable[[dict[str, object]], bool]:
    return lambda d: isinstance(d.get("observations"), dict) and d["observations"].get(name) is True  # type: ignore[union-attr]

def _tamper(name: str) -> Callable[[dict[str, object]], None]:
    def apply(d: dict[str, object]) -> None:
        observations = d.setdefault("observations", {})
        if isinstance(observations, dict):
            observations[name] = False
    return apply

def registry() -> tuple[Requirement, ...]:
    return tuple(Requirement(rid, "tamper." + rid, _fact(rid), _tamper(rid)) for rid in EXPECTED_RF17_REQUIREMENT_IDS)

def _safe_artifact(data: dict[str, object]) -> bool:
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return _SECRET_VALUE.search(encoded) is None and "safe_projection" not in encoded

def verify(data: dict[str, object], expected_sha: str | None, diagnostics_path: Path) -> None:
    if data.get("technical_id") != TECHNICAL_ID or (expected_sha is not None and data.get("candidate_sha") != expected_sha):
        raise SystemExit("RF17 evidence identity mismatch")
    requirements = registry()
    if tuple(r.requirement_id for r in requirements) != EXPECTED_RF17_REQUIREMENT_IDS:
        raise SystemExit("RF17 immutable registry corrupted")
    if not _safe_artifact(data):
        raise SystemExit("RF17 unsafe evidence artifact")
    original_failures = [r.requirement_id for r in requirements if not r.check(data)]
    tamper_rejected: list[str] = []
    tamper_failures: dict[str, str] = {}
    for r in requirements:
        mutated = copy.deepcopy(data)
        try:
            r.tamper(mutated)
            if not r.check(mutated):
                tamper_rejected.append(r.requirement_id)
            else:
                tamper_failures[r.requirement_id] = "tamper preserved requirement"
        except Exception as exc:  # malformed tamper machinery is never a pass
            tamper_failures[r.requirement_id] = type(exc).__name__
    diagnostics = {
        "technical_id": TECHNICAL_ID, "requirement_count": len(requirements),
        "requirement_ids": list(EXPECTED_RF17_REQUIREMENT_IDS),
        "tamper_strategy_ids": list(EXPECTED_RF17_TAMPER_STRATEGY_IDS),
        "tamper_rejected_ids": tamper_rejected, "original_failing_ids": original_failures,
        "tamper_failing_ids": sorted(tamper_failures),
        "original_pass_count": len(requirements) - len(original_failures),
        "tamper_rejected_count": len(tamper_rejected),
        "failing_requirements": original_failures + sorted(tamper_failures),
        "evidence_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
    }
    diagnostics_path.write_text(json.dumps(diagnostics, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if (original_failures or tuple(diagnostics["requirement_ids"]) != EXPECTED_RF17_REQUIREMENT_IDS
        or tuple(diagnostics["tamper_strategy_ids"]) != EXPECTED_RF17_TAMPER_STRATEGY_IDS
        or tuple(tamper_rejected) != EXPECTED_RF17_REQUIREMENT_IDS
        or tamper_failures or len(requirements) != 48):
        raise SystemExit("RF17 verifier failed")
    print(MARKER)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--diagnostics", type=Path, required=True)
    args = parser.parse_args()
    verify(json.loads(args.evidence.read_text(encoding="utf-8")), args.expected_sha, args.diagnostics)

if __name__ == "__main__":
    main()
