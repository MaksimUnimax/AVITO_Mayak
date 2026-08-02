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
    ParserOutcomePort,
    ParserOutcomeReference,
    ParserStatus,
    RunResult,
    ScheduleCommand,
    ScheduleResult,
    WorkClaim,
)
from .services import ScanRuntimeService, record_parser_outcome

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
    "ParserOutcomePort",
    "ParserOutcomeReference",
    "ParserStatus",
    "RunResult",
    "ScheduleCommand",
    "ScheduleResult",
    "WorkClaim",
    "ScanRuntimeService",
    "record_parser_outcome",
]
