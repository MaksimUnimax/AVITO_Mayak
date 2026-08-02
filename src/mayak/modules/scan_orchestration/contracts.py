"""Public, transport-neutral contracts for the durable Scan runtime."""

from __future__ import annotations

import json
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AccessTier(StrEnum):
    BASIC = "BASIC"
    FREE = "FREE"


class DecisionStatus(StrEnum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    AMBIGUOUS = "AMBIGUOUS"


class ParserStatus(StrEnum):
    CLEAN = "CLEAN"
    NOT_SENT = "NOT_SENT"
    TRANSPORT_UNAVAILABLE = "TRANSPORT_UNAVAILABLE"
    TRANSPORT_AMBIGUOUS = "TRANSPORT_AMBIGUOUS"
    EXPLICIT_REJECTION = "EXPLICIT_REJECTION"
    RATE_OR_ACCESS_RESTRICTED = "RATE_OR_ACCESS_RESTRICTED"
    CAPTCHA_OR_CHALLENGE = "CAPTCHA_OR_CHALLENGE"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    INCOMPLETE_RESPONSE = "INCOMPLETE_RESPONSE"
    UNSUPPORTED_STRUCTURE = "UNSUPPORTED_STRUCTURE"
    REFERENCE_STALE = "REFERENCE_STALE"
    REFERENCE_MISSING = "REFERENCE_MISSING"
    REFERENCE_DISPUTED = "REFERENCE_DISPUTED"
    PARTIAL = "PARTIAL"
    RESULT_AMBIGUOUS = "RESULT_AMBIGUOUS"


class ScanError(RuntimeError):
    """Base class for explicit fail-closed Scan errors."""


class IdempotencyMismatch(ScanError):
    pass


class LeaseConflict(ScanError):
    pass


class RevisionConflict(ScanError):
    pass


class CadenceRejected(ScanError):
    pass


class DependencyBlocked(ScanError):
    pass


class ScanModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class BeaconSnapshot(ScanModel):
    beacon_id: UUID
    account_id: UUID | None = None
    revision_no: int = Field(gt=0)
    lifecycle_eligible: bool


class EntitlementSnapshot(ScanModel):
    status: DecisionStatus
    tier: AccessTier
    minimum_seconds: int = Field(gt=0)
    step_seconds: int = Field(gt=0)


class ListingCandidate(ScanModel):
    identity_key: str = Field(min_length=1, max_length=255)
    snapshot: dict[str, object]

    @model_validator(mode="after")
    def safe_snapshot(self) -> "ListingCandidate":
        forbidden = {
            "html",
            "raw_body",
            "headers",
            "cookies",
            "token",
            "seller",
            "phone",
            "description",
            "views",
        }
        if forbidden.intersection(self.snapshot):
            raise ValueError("provider-shaped or private fields are not authoritative Scan data")
        _validate_snapshot(self.snapshot)
        encoded = json.dumps(
            self.snapshot,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        if len(encoded) > 32768:
            raise ValueError("listing snapshot exceeds 32 KiB")
        return self


_FORBIDDEN_SNAPSHOT_NAMES = {
    "body",
    "raw",
    "raw_body",
    "html",
    "headers",
    "cookies",
    "token",
    "tokens",
    "seller",
    "phone",
    "description",
    "full_description",
    "views",
    "private_route",
}
_SCALAR_TYPES = (str, int, float, bool)


def _validate_snapshot(value: Any, *, path: str = "snapshot") -> None:
    if value is None or isinstance(value, _SCALAR_TYPES):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValueError(f"{path} contains a non-JSON number")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or key.lower() in _FORBIDDEN_SNAPSHOT_NAMES:
                raise ValueError(f"{path} contains an unsafe provider-shaped field")
            _validate_snapshot(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_snapshot(item, path=f"{path}[{index}]")
        return
    raise ValueError(f"{path} contains a non-JSON-serializable value")


class ParserOutcome(ScanModel):
    outcome_id: UUID
    status: ParserStatus
    candidates: tuple[ListingCandidate, ...] = ()
    sort_context: str | None = None
    provenance_fingerprint: str = Field(min_length=64, max_length=64, pattern="^[0-9a-f]{64}$")

    @property
    def comparison_eligible(self) -> bool:
        return self.status is ParserStatus.CLEAN and self.sort_context == "NEWEST_FIRST_PROVEN"


class ScheduleCommand(ScanModel):
    beacon_id: UUID
    interval_seconds: int = Field(gt=0)
    next_due_at: datetime


class ScheduleResult(ScanModel):
    schedule_id: UUID
    beacon_id: UUID
    interval_seconds: int
    next_due_at: datetime
    state: str


class WorkClaim(ScanModel):
    work_item_id: UUID
    beacon_id: UUID
    schedule_id: UUID
    due_at: datetime
    lease_token: UUID
    lease_started_at: datetime
    lease_expires_at: datetime


class RunResult(ScanModel):
    run_id: UUID
    work_item_id: UUID
    beacon_id: UUID
    revision_no: int
    state: str
    lease_token: UUID
    replayed: bool = False


class ComparisonResult(ScanModel):
    run_id: UUID
    baseline_established: bool
    new_listing_keys: tuple[str, ...]
    event_ids: tuple[UUID, ...]
    replayed: bool = False


class BeaconPort(Protocol):
    def current(self, beacon_id: UUID) -> BeaconSnapshot: ...


class EntitlementPort(Protocol):
    def current(self, beacon_id: UUID, account_id: UUID | None) -> EntitlementSnapshot: ...


class ParserOutcomePort(Protocol):
    """Server-owned reader for normalized Parser evidence."""

    def resolve(self, outcome_id: UUID, *, run_id: UUID, beacon_id: UUID) -> ParserOutcome: ...


class ParserOutcomeReference(ScanModel):
    outcome_id: UUID


__all__ = [
    "AccessTier",
    "BeaconPort",
    "BeaconSnapshot",
    "CadenceRejected",
    "ComparisonResult",
    "DecisionStatus",
    "DependencyBlocked",
    "EntitlementPort",
    "EntitlementSnapshot",
    "IdempotencyMismatch",
    "LeaseConflict",
    "ListingCandidate",
    "ParserOutcome",
    "ParserOutcomePort",
    "ParserOutcomeReference",
    "ParserStatus",
    "RevisionConflict",
    "RunResult",
    "ScheduleCommand",
    "ScheduleResult",
    "ScanError",
    "WorkClaim",
]
