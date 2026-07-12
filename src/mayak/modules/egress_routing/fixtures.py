from __future__ import annotations

from dataclasses import dataclass

from .contracts import RouteFamily, _require_text, _require_text_tuple

ER02_TASK_ID = "ER-02-SEMANTIC-CONTRACTS-20260712-001"

__all__ = (
    "ER02_TASK_ID",
    "EgressSyntheticFixture",
    "EGRESS_SYNTHETIC_FIXTURE_IDS",
    "EGRESS_SYNTHETIC_FIXTURES",
)


@dataclass(frozen=True, slots=True)
class EgressSyntheticFixture:
    fixture_id: str
    summary: str
    route_family: RouteFamily | None
    expected_status_code: str
    reason_codes: tuple[str, ...]
    safe_reference_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixture_id", _require_text(self.fixture_id, "fixture_id"))
        object.__setattr__(self, "summary", _require_text(self.summary, "summary"))
        if self.route_family is not None and not isinstance(self.route_family, RouteFamily):
            raise ValueError("route_family must be RouteFamily or None")
        object.__setattr__(
            self,
            "expected_status_code",
            _require_text(self.expected_status_code, "expected_status_code"),
        )
        object.__setattr__(
            self, "reason_codes", _require_text_tuple(self.reason_codes, "reason_codes")
        )
        object.__setattr__(
            self,
            "safe_reference_ids",
            _require_text_tuple(self.safe_reference_ids, "safe_reference_ids"),
        )


def _fixture(
    fixture_id: str,
    summary: str,
    route_family: RouteFamily | None,
    expected_status_code: str,
    reason_codes: tuple[str, ...],
    safe_reference_ids: tuple[str, ...],
) -> EgressSyntheticFixture:
    return EgressSyntheticFixture(
        fixture_id=fixture_id,
        summary=summary,
        route_family=route_family,
        expected_status_code=expected_status_code,
        reason_codes=reason_codes,
        safe_reference_ids=safe_reference_ids,
    )


EGRESS_SYNTHETIC_FIXTURE_IDS = (
    "FX-ER-AGENT-REGISTRATION-BLOCKED-001",
    "FX-ER-REGISTERED-NOT-READY-001",
    "FX-ER-HEARTBEAT-NOT-READINESS-001",
    "FX-ER-RELEASE-MISMATCH-BLOCKS-001",
    "FX-ER-CAPABILITY-UNSUPPORTED-001",
    "FX-ER-CAPABILITY-EVIDENCE-STALE-001",
    "FX-ER-NO-POLICY-NO-ARBITRARY-SELECTION-001",
    "FX-ER-LEASE-GRANTED-001",
    "FX-ER-LEASE-REPLAY-NO-EXTENSION-001",
    "FX-ER-LEASE-IDEMPOTENCY-MISMATCH-001",
    "FX-ER-LEASE-EXPIRED-NO-DISPATCH-001",
    "FX-ER-LEASE-REVOKED-NO-DISPATCH-001",
    "FX-ER-DISPATCH-NOT-SENT-001",
    "FX-ER-DISPATCH-AMBIGUOUS-RECONCILE-001",
    "FX-ER-RECEIVED-NOT-SENT-001",
    "FX-ER-SENT-RESPONSE-NOT-PARSER-SUCCESS-001",
    "FX-ER-EXPLICIT-REJECTION-NOT-EMPTY-001",
    "FX-ER-CAPTCHA-NOT-EMPTY-001",
    "FX-ER-MALFORMED-NOT-PARSER-SUCCESS-001",
    "FX-ER-ROUTE-FAILURE-NOT-PARSER-SUCCESS-001",
    "FX-ER-QUARANTINE-BLOCKS-NEW-LEASE-001",
    "FX-ER-NO-AUTO-UNQUARANTINE-001",
    "FX-ER-NO-AGENT-FALLBACK-001",
    "FX-ER-AMBIGUOUS-NO-FALLBACK-001",
    "FX-ER-CROSS-ENVIRONMENT-REJECT-001",
    "FX-ER-FOREIGN-RESOURCE-REJECT-001",
    "FX-ER-NO-PUBLIC-INBOUND-001",
    "FX-ER-NO-PRIMARY-DATABASE-001",
    "FX-ER-MINIMUM-ASSIGNMENT-PAYLOAD-001",
    "FX-ER-SECRET-REFERENCE-ONLY-001",
    "FX-ER-BATCH-PER-ASSIGNMENT-OUTCOME-001",
    "FX-ER-RECONCILIATION-REMAINS-AMBIGUOUS-001",
    "FX-ER-OD011-NO-CADENCE-DEFAULT-001",
    "FX-ER-OD013-RETENTION-BLOCKED-001",
)

EGRESS_SYNTHETIC_FIXTURES = (
    _fixture(
        "FX-ER-AGENT-REGISTRATION-BLOCKED-001",
        "Linux reference-style candidate is proof-gated and not production-ready",
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        "AGENT_REGISTRATION_BLOCKED",
        ("proof-gated", "not-production-ready"),
        ("SAFE-ER-AGENT-001",),
    ),
    _fixture(
        "FX-ER-REGISTERED-NOT-READY-001",
        "Russian residential route is provider-unselected",
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE,
        "REGISTERED_NOT_READY",
        ("provider-unselected",),
        ("SAFE-ER-REGISTERED-001",),
    ),
    _fixture(
        "FX-ER-HEARTBEAT-NOT-READINESS-001",
        "Owner development bridge is development-only; heartbeat does not imply readiness",
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        "HEARTBEAT_ONLY",
        ("development-only", "heartbeat-not-readiness"),
        ("SAFE-ER-HEARTBEAT-001",),
    ),
    _fixture(
        "FX-ER-RELEASE-MISMATCH-BLOCKS-001",
        "Windows browser agent fallback is proof-gated",
        RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE,
        "RELEASE_MISMATCH_BLOCKED",
        ("proof-gated", "fallback-blocked"),
        ("SAFE-ER-RELEASE-001",),
    ),
    _fixture(
        "FX-ER-CAPABILITY-UNSUPPORTED-001",
        "Windows VM browser worker fallback is proof-gated",
        RouteFamily.WINDOWS_VM_BROWSER_WORKER_ROUTE,
        "CAPABILITY_UNSUPPORTED",
        ("proof-gated", "capability-unsupported"),
        ("SAFE-ER-CAPABILITY-001",),
    ),
    _fixture(
        "FX-ER-CAPABILITY-EVIDENCE-STALE-001",
        "Browser-extension route is owner-evidence-only and not production-scale proof",
        RouteFamily.BROWSER_EXTENSION_ROUTE,
        "EVIDENCE_STALE",
        ("owner-evidence-only", "not-production-scale-proof"),
        ("SAFE-ER-EXTENSION-001",),
    ),
    _fixture(
        "FX-ER-NO-POLICY-NO-ARBITRARY-SELECTION-001",
        "No policy means no arbitrary selection",
        None,
        "NO_POLICY",
        ("no-policy", "no-arbitrary-selection"),
        ("SAFE-ER-SELECTION-001",),
    ),
    _fixture(
        "FX-ER-LEASE-GRANTED-001",
        "Owner development bridge lease is development-only and bounded",
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        "LEASE_GRANTED",
        ("development-only", "bounded-authorization"),
        ("SAFE-ER-LEASE-001",),
    ),
    _fixture(
        "FX-ER-LEASE-REPLAY-NO-EXTENSION-001",
        "Lease replay does not extend the bounded authorization",
        None,
        "LEASE_REPLAY_NO_EXTENSION",
        ("replay-blocked", "no-extension"),
        ("SAFE-ER-REPLAY-001",),
    ),
    _fixture(
        "FX-ER-LEASE-IDEMPOTENCY-MISMATCH-001",
        "Lease idempotency mismatch blocks renewal",
        None,
        "LEASE_IDEMPOTENCY_MISMATCH",
        ("idempotency-mismatch",),
        ("SAFE-ER-IDEMPOTENCY-001",),
    ),
    _fixture(
        "FX-ER-LEASE-EXPIRED-NO-DISPATCH-001",
        "Lease expired; unavailable outcome and no dispatch",
        None,
        "TRANSPORT_UNAVAILABLE",
        ("expired", "unavailable"),
        ("SAFE-ER-EXPIRED-001",),
    ),
    _fixture(
        "FX-ER-LEASE-REVOKED-NO-DISPATCH-001",
        "Lease revoked; restricted outcome and no dispatch",
        None,
        "RATE_OR_ACCESS_RESTRICTED",
        ("revoked", "restricted"),
        ("SAFE-ER-REVOKED-001",),
    ),
    _fixture(
        "FX-ER-DISPATCH-NOT-SENT-001",
        "Dispatch not sent outcome remains explicit",
        None,
        "NOT_SENT",
        ("dispatch-not-sent",),
        ("SAFE-ER-DISPATCH-001",),
    ),
    _fixture(
        "FX-ER-DISPATCH-AMBIGUOUS-RECONCILE-001",
        "Ambiguous dispatch blocks fallback and requires reconciliation; ambiguous outcome",
        None,
        "AMBIGUOUS",
        ("ambiguous-dispatch", "reconciliation-required"),
        ("SAFE-ER-AMBIGUOUS-001",),
    ),
    _fixture(
        "FX-ER-RECEIVED-NOT-SENT-001",
        "Received response but dispatch was not sent",
        None,
        "SENT_NO_RESPONSE",
        ("received-not-sent",),
        ("SAFE-ER-RECEIVED-001",),
    ),
    _fixture(
        "FX-ER-SENT-RESPONSE-NOT-PARSER-SUCCESS-001",
        "Sent response is not parser success",
        None,
        "RESPONSE_RECEIVED_UNCLASSIFIED",
        ("transport-not-parser-success",),
        ("SAFE-ER-TRANSPORT-001",),
    ),
    _fixture(
        "FX-ER-EXPLICIT-REJECTION-NOT-EMPTY-001",
        "Explicit rejection is not an empty result",
        None,
        "PROVIDER_REJECTED",
        ("explicit-rejection", "not-empty"),
        ("SAFE-ER-REJECTION-001",),
    ),
    _fixture(
        "FX-ER-CAPTCHA-NOT-EMPTY-001",
        "CAPTCHA is explicit and not success or empty",
        RouteFamily.BROWSER_EXTENSION_ROUTE,
        "CAPTCHA_OR_CHALLENGE",
        ("captcha", "not-success", "not-empty"),
        ("SAFE-ER-CAPTCHA-001",),
    ),
    _fixture(
        "FX-ER-MALFORMED-NOT-PARSER-SUCCESS-001",
        "Malformed transport response is not parser success",
        None,
        "MALFORMED_RESPONSE_TRANSPORT_LAYER",
        ("malformed", "transport-not-parser-success"),
        ("SAFE-ER-MALFORMED-001",),
    ),
    _fixture(
        "FX-ER-ROUTE-FAILURE-NOT-PARSER-SUCCESS-001",
        "Route failure is not parser success",
        None,
        "ROUTE_DEGRADED",
        ("route-failure", "not-parser-success"),
        ("SAFE-ER-FAILURE-001",),
    ),
    _fixture(
        "FX-ER-QUARANTINE-BLOCKS-NEW-LEASE-001",
        "Quarantined outcome blocks new assignments and stays quarantined",
        None,
        "ROUTE_QUARANTINED",
        ("quarantined-outcome", "no-new-lease"),
        ("SAFE-ER-QUARANTINE-001",),
    ),
    _fixture(
        "FX-ER-NO-AUTO-UNQUARANTINE-001",
        "No auto-unquarantine",
        None,
        "NO_AUTO_UNQUARANTINE",
        ("no-auto-unquarantine",),
        ("SAFE-ER-UNQUARANTINE-001",),
    ),
    _fixture(
        "FX-ER-NO-AGENT-FALLBACK-001",
        "No agent fallback; Egress remains the selection authority",
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        "NO_AGENT_FALLBACK",
        ("no-agent-fallback", "egress-only"),
        ("SAFE-ER-FALLBACK-001",),
    ),
    _fixture(
        "FX-ER-AMBIGUOUS-NO-FALLBACK-001",
        "Ambiguous state means no fallback",
        None,
        "AMBIGUOUS_NO_FALLBACK",
        ("ambiguous", "no-fallback"),
        ("SAFE-ER-NO-FALLBACK-001",),
    ),
    _fixture(
        "FX-ER-CROSS-ENVIRONMENT-REJECT-001",
        "Cross-environment reject is proof-gated",
        RouteFamily.WINDOWS_BROWSER_AGENT_ROUTE,
        "CROSS_ENVIRONMENT_REJECTED",
        ("cross-environment", "proof-gated"),
        ("SAFE-ER-CROSS-ENV-001",),
    ),
    _fixture(
        "FX-ER-FOREIGN-RESOURCE-REJECT-001",
        "Foreign resource reject remains blocked",
        None,
        "FOREIGN_RESOURCE_REJECTED",
        ("foreign-resource", "blocked"),
        ("SAFE-ER-FOREIGN-001",),
    ),
    _fixture(
        "FX-ER-NO-PUBLIC-INBOUND-001",
        "No public inbound exposure",
        RouteFamily.LINUX_REFERENCE_STYLE_ROUTE,
        "NO_PUBLIC_INBOUND",
        ("no-public-inbound",),
        ("SAFE-ER-INBOUND-001",),
    ),
    _fixture(
        "FX-ER-NO-PRIMARY-DATABASE-001",
        "No primary database access",
        RouteFamily.OWNER_DEVELOPMENT_BRIDGE_ROUTE,
        "NO_PRIMARY_DATABASE",
        ("no-primary-database",),
        ("SAFE-ER-NO-DB-001",),
    ),
    _fixture(
        "FX-ER-MINIMUM-ASSIGNMENT-PAYLOAD-001",
        "Minimum bounded assignment payload only",
        RouteFamily.RUSSIAN_RESIDENTIAL_ROUTE,
        "MINIMUM_ASSIGNMENT_PAYLOAD",
        ("minimum-assignment", "bounded"),
        ("SAFE-ER-MIN-001",),
    ),
    _fixture(
        "FX-ER-SECRET-REFERENCE-ONLY-001",
        "Secret reference only; no secret values",
        RouteFamily.BROWSER_EXTENSION_ROUTE,
        "SECRET_REFERENCE_ONLY",
        ("secret-reference-only",),
        ("SAFE-ER-SECRET-REF-001",),
    ),
    _fixture(
        "FX-ER-BATCH-PER-ASSIGNMENT-OUTCOME-001",
        "One outcome per assignment per batch",
        None,
        "BATCH_PER_ASSIGNMENT_OUTCOME",
        ("batch", "one-outcome"),
        ("SAFE-ER-BATCH-001",),
    ),
    _fixture(
        "FX-ER-RECONCILIATION-REMAINS-AMBIGUOUS-001",
        "Reconciliation remains ambiguous",
        None,
        "RECONCILIATION_AMBIGUOUS",
        ("reconciliation", "ambiguous"),
        ("SAFE-ER-RECON-001",),
    ),
    _fixture(
        "FX-ER-OD011-NO-CADENCE-DEFAULT-001",
        "OD-011 has no cadence value",
        None,
        "OD011_NO_CADENCE",
        ("od-011", "no-cadence"),
        ("SAFE-ER-OD011-001",),
    ),
    _fixture(
        "FX-ER-OD013-RETENTION-BLOCKED-001",
        "OD-013 has no retention value",
        None,
        "OD013_NO_RETENTION",
        ("od-013", "no-retention"),
        ("SAFE-ER-OD013-001",),
    ),
)
