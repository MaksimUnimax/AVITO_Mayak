"""Contract constants for the RF24 scan-runtime resilience package."""

from __future__ import annotations

from typing import Final

TECHNICAL_ID: Final = "RF24-SCAN-RUNTIME-RESILIENCE-SCENARIOS-01"
SCENARIO_NAMES: Final = (
    "worker-restart",
    "scheduler-restart",
    "partial-parser",
    "captcha-restriction",
    "route-failure",
    "lost-lease",
    "duplicate-listing",
)
ACTION_BOUNDARIES: Final = {
    "worker-restart": "mayak.runtime.worker OS process",
    "scheduler-restart": "mayak.runtime.scheduler OS process",
    "partial-parser": "AvitoParserRuntime.run_synthetic + ScanRuntime.record_parser_outcome",
    "captcha-restriction": "AvitoParserRuntime.run_synthetic + ScanRuntime.record_parser_outcome",
    "route-failure": "EgressRoutingRuntime simulator + AvitoParserRuntime.consume_egress_transport",
    "lost-lease": "ScanRepository lease reclaim + ScanRuntime terminal guard",
    "duplicate-listing": "ScanRuntime.commit_comparison listing-state idempotency",
}


def expected_scenarios() -> tuple[str, ...]:
    return SCENARIO_NAMES
