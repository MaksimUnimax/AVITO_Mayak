"""Scan Orchestration module package."""

from mayak.platform.boundaries import SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID

from .contracts import (
    AccessTier,
    BeaconSnapshot,
    ComparisonResult,
    DecisionStatus,
    EntitlementSnapshot,
    ListingCandidate,
    ParserOutcome,
    ParserStatus,
    RunResult,
    ScheduleCommand,
    ScheduleResult,
    WorkClaim,
)
from .services import (
    ScheduleService,
    claim_work,
    commit_comparison,
    materialize_due_work,
    start_run,
)

MODULE_ID = SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID

__all__ = [
    "MODULE_ID",
    "AccessTier",
    "BeaconSnapshot",
    "ComparisonResult",
    "DecisionStatus",
    "EntitlementSnapshot",
    "ListingCandidate",
    "ParserOutcome",
    "ParserStatus",
    "RunResult",
    "ScheduleCommand",
    "ScheduleResult",
    "ScheduleService",
    "WorkClaim",
    "claim_work",
    "commit_comparison",
    "materialize_due_work",
    "start_run",
]
