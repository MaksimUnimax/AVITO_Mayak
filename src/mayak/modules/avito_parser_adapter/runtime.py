"""RF-14 runtime for the Avito Parser Adapter.

The runtime deliberately owns only parser facts.  It accepts safe references and
already-classified transport outcomes; it never resolves Beacon, Scan or Egress
authority itself.  The small synthetic provider is an acceptance provider, not a
fixture reader and not a claim about the live Avito surface.
"""

# Contract constructors intentionally keep semantic arguments visible at this
# boundary; the repository's 100-column rule is not useful for those calls.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx
from sqlalchemy import insert, select, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .contracts import (
    CompatibilityProfileAuthorityClass,
    CompatibilityProfileLifecycleStatus,
    ListingCandidateStatus,
    ListingCardCandidate,
    ListingFieldAvailability,
    ListingFieldCandidate,
    ListingFieldFamily,
    ListingFieldQuality,
    ListingFieldTier,
    ListingOrderingEvidence,
    ListingPageParseOutcome,
    ListingSortContextStatus,
    MultivalueNormalizationOutcome,
    MultivalueNormalizationRule,
    MultivalueNormalizationStatus,
    MultivaluePreservationMode,
    NormalizedListingCandidate,
    ObservedListingPosition,
    ParserAttemptOutcome,
    ParserCompatibilityOutcome,
    ParserCompatibilityProfile,
    ParserEvidenceReference,
    ParserOutcomeExplanation,
    ParserOutcomeStatus,
    ParserRequestEnvelope,
    ParserSourceReference,
    ParserWarning,
    ParserWarningCode,
    ProviderResponseEvidenceClass,
    ResponseCompletenessStatus,
    ResponseRestrictionSignal,
    SearchConfigurationCandidate,
    SearchConfigurationExtractionField,
    SearchConfigurationExtractionOutcome,
    SearchConfigurationFieldStatus,
    SearchConfigurationParameterCandidate,
    SearchConfigurationValueKind,
    SearchConfigurationWarningCode,
    SearchSourceAnalysisOutcome,
    SourceReferenceKind,
    TransportOutcomeReference,
    TransportOutcomeStatus,
    TransportResponseClassificationOutcome,
)


class SyntheticScenario(StrEnum):
    USABLE_CONFIGURATION = "usable_configuration"
    USABLE_LISTING_PAGE = "usable_listing_page"
    CLEAN_EMPTY = "clean_empty"
    EMPTY_WITHOUT_PROOF = "empty_without_proof"
    CAPTCHA = "captcha"
    RATE_RESTRICTED = "rate_restricted"
    EXPLICIT_REJECTION = "explicit_rejection"
    MALFORMED = "malformed"
    INCOMPLETE = "incomplete"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    TRANSPORT_UNAVAILABLE = "transport_unavailable"
    TRANSPORT_AMBIGUOUS = "transport_ambiguous"
    STALE_PROFILE = "stale_profile"
    MISSING_PROFILE = "missing_profile"
    DISPUTED_PROFILE = "disputed_profile"


@dataclass(frozen=True, slots=True)
class TrustedDispatchBinding:
    """Server-owned, immutable binding used as the only network target."""

    source_reference_id: str
    beacon_source_reference: str
    profile_id: str
    profile_version: str
    authority_reference: str
    proof_reference: str
    target: str
    response_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        parts = urlsplit(self.target)
        if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
            raise ValueError("trusted target must be an absolute https URL without credentials")
        for field in ("source_reference_id", "beacon_source_reference", "profile_id",
                      "profile_version", "authority_reference", "proof_reference"):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must not be blank")


class TrustedDispatchAuthorityPort(Protocol):
    def resolve(
        self, source: ParserSourceReference, profile: ParserCompatibilityProfile
    ) -> TrustedDispatchBinding | None: ...

    def resolve_with_reason(
        self, source: ParserSourceReference, profile: ParserCompatibilityProfile
    ) -> tuple[TrustedDispatchBinding | None, str]: ...


class TrustedDispatchAuthority:
    """Exact server-owned resolver; caller data cannot create a binding."""

    def __init__(
        self,
        bindings: tuple[TrustedDispatchBinding, ...] = (),
        *,
        expected_bindings: tuple[TrustedDispatchBinding, ...] | None = None,
    ) -> None:
        self._bindings = bindings
        self._expected_bindings = expected_bindings if expected_bindings is not None else bindings

    def resolve(self, source: ParserSourceReference, profile: ParserCompatibilityProfile) -> TrustedDispatchBinding | None:
        return self.resolve_with_reason(source, profile)[0]

    def resolve_with_reason(
        self, source: ParserSourceReference, profile: ParserCompatibilityProfile
    ) -> tuple[TrustedDispatchBinding | None, str]:
        expected = next(
            (
                item for item in self._expected_bindings
                if item.source_reference_id == source.source_reference_id
                and item.beacon_source_reference == source.beacon_source_reference
                and item.profile_id == profile.profile_id
                and item.profile_version == profile.profile_version
            ),
            None,
        )
        if expected is None:
            for item in self._expected_bindings:
                if item.source_reference_id != source.source_reference_id:
                    return None, "SOURCE_IDENTITY_MISMATCH"
                if item.beacon_source_reference != source.beacon_source_reference:
                    return None, "PROVENANCE_MISMATCH"
                if item.profile_id != profile.profile_id or item.profile_version != profile.profile_version:
                    return None, "PROFILE_IDENTITY_VERSION_MISMATCH"
            return None, "LIVE_AUTHORITY_MISSING"
        candidate = next(
            (
                item for item in self._bindings
                if item.source_reference_id == source.source_reference_id
                and item.beacon_source_reference == source.beacon_source_reference
                and item.profile_id == profile.profile_id
                and item.profile_version == profile.profile_version
            ),
            None,
        )
        if candidate is None:
            return None, "LIVE_AUTHORITY_MISSING"
        if candidate.authority_reference != expected.authority_reference:
            return None, "AUTHORITY_IDENTITY_MISMATCH"
        if candidate.proof_reference != expected.proof_reference:
            return None, "PROOF_IDENTITY_MISMATCH"
        if candidate.target != expected.target:
            return None, "TRUSTED_TARGET_POLICY_MISMATCH"
        return candidate, "AUTHORIZED"


class DisabledLiveAuthority:
    """Default production authority: fail closed and issue no grant."""

    def resolve(self, source: ParserSourceReference, profile: ParserCompatibilityProfile) -> None:
        return None

    def resolve_with_reason(
        self, source: ParserSourceReference, profile: ParserCompatibilityProfile
    ) -> tuple[None, str]:
        return None, "LIVE_AUTHORITY_MISSING"


@dataclass(frozen=True, slots=True)
class RawHttpResponseObservation:
    """Transport facts only; it contains no semantic parser decision."""

    status_code: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    request_target: str


class HttpxTransport:
    """HTTP mechanics isolated from provider/semantic classification."""

    def __init__(self, settings: HttpxAdapterSettings, transport: httpx.BaseTransport | None) -> None:
        self.settings = settings
        self.transport = transport

    def request(self, target: str) -> RawHttpResponseObservation:
        timeout = httpx.Timeout(
            connect=self.settings.connect_timeout_seconds,
            read=self.settings.read_timeout_seconds,
            write=self.settings.write_timeout_seconds,
            pool=self.settings.pool_timeout_seconds,
        )
        with httpx.Client(transport=self.transport, timeout=timeout, follow_redirects=False,
                          cookies=None, trust_env=False) as client:
            with client.stream("GET", target) as response:
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > self.settings.max_response_bytes:
                        raise ValueError("response exceeds configured bound")
                return RawHttpResponseObservation(
                    response.status_code, tuple(response.headers.multi_items()), bytes(body), target
                )


@dataclass(frozen=True, slots=True)
class ParserTransportPort(Protocol):
    def dispatch(self, source_reference: str) -> TransportOutcomeReference: ...


@dataclass(frozen=True, slots=True)
class SyntheticRuntimeResult:
    scenario: str
    attempt: ParserAttemptOutcome
    configuration: SearchConfigurationExtractionOutcome | None = None
    page: ListingPageParseOutcome | None = None


@dataclass(frozen=True, slots=True)
class NormalizedListingSnapshot:
    """The only listing representation accepted by parser persistence.

    It contains normalized semantic fields only; provider bodies, headers,
    cookies, tokens and unknown fields have no slot in this DTO.
    """

    candidates: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        allowed_fields = {item.value for item in ListingFieldFamily}
        for candidate in self.candidates:
            if set(candidate) != {"listing_candidate_id", "status", "fields"}:
                raise ValueError("snapshot contains an unapproved normalized field")
            if not isinstance(candidate["listing_candidate_id"], str) or not candidate[
                "listing_candidate_id"
            ].strip():
                raise ValueError("snapshot listing identity must be non-empty")
            if candidate["status"] not in {item.value for item in ListingCandidateStatus}:
                raise ValueError("snapshot contains an unapproved candidate status")
            fields = candidate["fields"]
            if not isinstance(fields, dict) or not set(fields).issubset(allowed_fields):
                raise ValueError("snapshot contains an unapproved normalized field")
            if any(
                not isinstance(value, (str, int, float, bool)) and value is not None
                for value in fields.values()
            ):
                raise ValueError("snapshot fields must be scalar normalized values")

    @classmethod
    def from_page(cls, page: ListingPageParseOutcome) -> "NormalizedListingSnapshot":
        candidates: list[dict[str, object]] = []
        for candidate in page.normalized_listing_candidates:
            fields = {
                field.field_family.value: field.value
                for field in candidate.card_candidate.field_candidates
                if isinstance(field.value, (str, int, float, bool)) or field.value is None
            }
            candidates.append(
                {
                    "listing_candidate_id": candidate.listing_candidate_id,
                    "status": candidate.status.value,
                    "fields": fields,
                }
            )
        return cls(tuple(candidates))

    def as_dict(self) -> dict[str, object]:
        return {"candidates": [dict(item) for item in self.candidates]}


@dataclass(frozen=True, slots=True)
class ParserBatchRuntimeResult:
    """Ordered per-page batch result; parser owns no scan/newness decisions."""

    outcomes: tuple[SyntheticRuntimeResult, ...]
    succeeded_count: int
    failed_count: int
    ambiguous_count: int
    duplicate_observations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParserPersistenceResult:
    outcome_id: UUID
    fingerprint: str
    replayed: bool
    outcome_code: str


@dataclass(frozen=True, slots=True)
class ParserOutcomeReadback:
    outcome_id: UUID
    beacon_id: UUID
    run_id: UUID | None
    route_id: UUID | None
    outcome_code: str
    listing_snapshot: dict[str, object] | None
    observed_at: datetime
    fingerprint: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class HttpxAdapterSettings:
    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 5.0
    write_timeout_seconds: float = 3.0
    pool_timeout_seconds: float = 2.0
    max_response_bytes: int = 256 * 1024

    def __post_init__(self) -> None:
        if any(
            value <= 0
            for value in (
                self.connect_timeout_seconds,
                self.read_timeout_seconds,
                self.write_timeout_seconds,
                self.pool_timeout_seconds,
            )
        ):
            raise ValueError("HTTPX timeouts must be positive")
        if not 1024 <= self.max_response_bytes <= 8 * 1024 * 1024:
            raise ValueError("max_response_bytes must be between 1 KiB and 8 MiB")


class HttpxLiveAdapter:
    """Production-shaped, GET-only HTTPX adapter with disabled-by-default traffic."""

    def __init__(
        self,
        *,
        settings: HttpxAdapterSettings | None = None,
        enabled: bool = False,
        transport: httpx.BaseTransport | None = None,
        authority: TrustedDispatchAuthorityPort | None = None,
    ) -> None:
        self.settings = settings or HttpxAdapterSettings()
        self.enabled = enabled
        self._transport = transport
        self._authority = authority or DisabledLiveAuthority()
        self.calls = 0

    def fetch(
        self,
        source: ParserSourceReference,
        *,
        profile: ParserCompatibilityProfile | None,
    ) -> TransportResponseClassificationOutcome:
        ref = _evidence("httpx", "adapter")
        if not isinstance(source, ParserSourceReference) or source.source_reference_kind not in (
            SourceReferenceKind.BEACON_OWNED_SUBMISSION,
            SourceReferenceKind.SAFE_REFERENCE,
        ):
            return _classification(
                "live-source-boundary-blocked",
                TransportOutcomeStatus.NOT_SENT,
                explanation="SOURCE_URL_POLICY_MISSING",
                evidence=(ref,),
            )
        if not self.enabled:
            return _classification(
                "live-disabled",
                TransportOutcomeStatus.NOT_SENT,
                evidence_class=ProviderResponseEvidenceClass.UNCLASSIFIED,
                explanation="PROVIDER_DISABLED_CONTINUE",
                evidence=(ref,),
            )
        if profile is None or profile.lifecycle_status is not CompatibilityProfileLifecycleStatus.CURRENT:
            return _classification(
                "live-profile-missing",
                TransportOutcomeStatus.NOT_SENT,
                explanation="REFERENCE_MISSING_OR_NOT_CURRENT",
                evidence=(ref,),
            )
        if profile.authority_class is CompatibilityProfileAuthorityClass.SYNTHETIC:
            return _classification(
                "live-synthetic-profile-rejected",
                TransportOutcomeStatus.NOT_SENT,
                explanation="SYNTHETIC_PROFILE_CANNOT_AUTHORIZE_LIVE",
                evidence=(ref,),
            )
        binding, authority_reason = self._authority.resolve_with_reason(source, profile)
        if binding is None:
            return _classification(
                authority_reason,
                TransportOutcomeStatus.NOT_SENT,
                explanation=authority_reason,
                evidence=(ref,),
            )
        self.calls += 1
        try:
            response = HttpxTransport(self.settings, self._transport).request(binding.target)
            if 300 <= response.status_code < 400:
                return _classification("httpx-redirect", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                                        parser_status=ParserOutcomeStatus.RESULT_AMBIGUOUS,
                                        evidence_class=ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,
                                        explanation="REDIRECT_POLICY_BLOCKED", evidence=(ref,))
            if response.status_code in (403, 429):
                return _classification("httpx-restricted", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                                        parser_status=ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
                                        evidence_class=ProviderResponseEvidenceClass.RATE_OR_ACCESS_RESTRICTED,
                                        restriction=ResponseRestrictionSignal.ACCESS_RESTRICTED, evidence=(ref,))
            if response.status_code >= 400:
                return _classification("httpx-rejected", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                                        parser_status=ParserOutcomeStatus.EXPLICIT_REJECTION,
                                        evidence_class=ProviderResponseEvidenceClass.EXPLICIT_REJECTION, evidence=(ref,))
            try:
                decoded = json.loads(response.body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _classification("httpx-malformed", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                                        parser_status=ParserOutcomeStatus.MALFORMED_RESPONSE,
                                        evidence_class=ProviderResponseEvidenceClass.MALFORMED_RESPONSE, evidence=(ref,))
            # The current accepted evidence contains no live Avito response schema.
            # Parseability and generic keys are therefore never semantic authority.
            del decoded, binding
            return _classification("httpx-unproven-schema", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED,
                                    parser_status=ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
                                    evidence_class=ProviderResponseEvidenceClass.UNSUPPORTED_STRUCTURE,
                                    completeness=ResponseCompletenessStatus.AMBIGUOUS,
                                    explanation="LIVE_RESPONSE_SCHEMA_UNPROVEN", evidence=(ref,))
        except ValueError:
            return _classification("httpx-response-too-large", TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
                                    parser_status=ParserOutcomeStatus.INCOMPLETE_RESPONSE,
                                    evidence_class=ProviderResponseEvidenceClass.INCOMPLETE_RESPONSE, evidence=(ref,))
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError):
            return _classification(
                "httpx-transport-failure",
                TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
                evidence=(ref,),
                explanation="TRANSPORT_UNAVAILABLE",
            )


class SyntheticParserProvider:
    """Deterministic provider with explicit scenario classifications."""

    def execute(
        self, scenario: str | SyntheticScenario, *, request_id: str = "synthetic"
    ) -> SyntheticRuntimeResult:
        name = str(scenario.value if isinstance(scenario, SyntheticScenario) else scenario)
        if name not in {item.value for item in SyntheticScenario}:
            raise ValueError(f"unsupported synthetic scenario: {name}")
        profile_status = CompatibilityProfileLifecycleStatus.CURRENT
        if name == SyntheticScenario.STALE_PROFILE:
            profile_status = CompatibilityProfileLifecycleStatus.STALE
        elif name == SyntheticScenario.DISPUTED_PROFILE:
            profile_status = CompatibilityProfileLifecycleStatus.DISPUTED
        profile = _profile("synthetic-avito-v1", profile_status)
        request = _request(request_id, profile)
        transport_status = TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
        parser_status: ParserOutcomeStatus | None = ParserOutcomeStatus.USABLE_RESPONSE
        _evidence_class = ProviderResponseEvidenceClass.USABLE_RESPONSE
        _completeness = ResponseCompletenessStatus.COMPLETE
        _restriction = ResponseRestrictionSignal.NONE
        explanation = "SYNTHETIC_SCENARIO"
        if name in ("missing_profile",):
            profile = _profile("synthetic-missing", CompatibilityProfileLifecycleStatus.UNAVAILABLE)
            request = _request(request_id, profile)
            parser_status, _evidence_class, explanation = (
                None,
                ProviderResponseEvidenceClass.UNCLASSIFIED,
                "REFERENCE_MISSING",
            )
        elif name == "transport_unavailable":
            transport_status, parser_status, _evidence_class = (
                TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
                None,
                ProviderResponseEvidenceClass.UNCLASSIFIED,
            )
        elif name == "transport_ambiguous":
            transport_status, parser_status, _evidence_class = (
                TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
                ParserOutcomeStatus.RESULT_AMBIGUOUS,
                ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,
            )
        else:
            mapping: dict[
                str,
                tuple[
                    ParserOutcomeStatus, ProviderResponseEvidenceClass, ResponseRestrictionSignal
                ],
            ] = {
                "empty_without_proof": (
                    ParserOutcomeStatus.RESULT_AMBIGUOUS,
                    ProviderResponseEvidenceClass.EMPTY_WITHOUT_PROOF,
                    ResponseRestrictionSignal.NONE,
                ),
                "captcha": (
                    ParserOutcomeStatus.CAPTCHA_OR_CHALLENGE,
                    ProviderResponseEvidenceClass.CAPTCHA_OR_CHALLENGE,
                    ResponseRestrictionSignal.CAPTCHA,
                ),
                "rate_restricted": (
                    ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
                    ProviderResponseEvidenceClass.RATE_OR_ACCESS_RESTRICTED,
                    ResponseRestrictionSignal.RATE_LIMIT,
                ),
                "explicit_rejection": (
                    ParserOutcomeStatus.EXPLICIT_REJECTION,
                    ProviderResponseEvidenceClass.EXPLICIT_REJECTION,
                    ResponseRestrictionSignal.NONE,
                ),
                "malformed": (
                    ParserOutcomeStatus.MALFORMED_RESPONSE,
                    ProviderResponseEvidenceClass.MALFORMED_RESPONSE,
                    ResponseRestrictionSignal.NONE,
                ),
                "incomplete": (
                    ParserOutcomeStatus.INCOMPLETE_RESPONSE,
                    ProviderResponseEvidenceClass.INCOMPLETE_RESPONSE,
                    ResponseRestrictionSignal.NONE,
                ),
                "partial": (
                    ParserOutcomeStatus.PARTIAL,
                    ProviderResponseEvidenceClass.PARTIAL,
                    ResponseRestrictionSignal.NONE,
                ),
                "unsupported": (
                    ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
                    ProviderResponseEvidenceClass.UNSUPPORTED_STRUCTURE,
                    ResponseRestrictionSignal.NONE,
                ),
                "ambiguous": (
                    ParserOutcomeStatus.RESULT_AMBIGUOUS,
                    ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,
                    ResponseRestrictionSignal.NONE,
                ),
                "stale_profile": (
                    ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
                    ProviderResponseEvidenceClass.UNSUPPORTED_STRUCTURE,
                    ResponseRestrictionSignal.NONE,
                ),
                "disputed_profile": (
                    ParserOutcomeStatus.RESULT_AMBIGUOUS,
                    ProviderResponseEvidenceClass.RESULT_AMBIGUOUS,
                    ResponseRestrictionSignal.NONE,
                ),
            }
            if name in mapping:
                parser_status, _evidence_class, _restriction = mapping[name]
            if name == "clean_empty":
                parser_status = ParserOutcomeStatus.USABLE_RESPONSE
        transport = _transport(request_id, transport_status)
        attempt = ParserAttemptOutcome(
            attempt_id=f"attempt::{request_id}::{name}",
            transport_status=transport_status,
            parser_status=parser_status,
            reference_status=profile.lifecycle_status,
            request_envelope=request,
            transport_outcome=transport,
            response_reference=f"synthetic-response::{name}",
            warnings=(_warning(ParserWarningCode.EMPTY_RESULT_PROVEN),)
            if name == "clean_empty"
            else (),
            explanation=ParserOutcomeExplanation(explanation, reason_code=name),
        )
        page = None
        if name in (
            "usable_listing_page",
            "clean_empty",
            "empty_without_proof",
            "captcha",
            "rate_restricted",
            "malformed",
            "incomplete",
            "partial",
            "unsupported",
            "ambiguous",
        ):
            page = _synthetic_page(request, transport, profile, name, parser_status)
        configuration = (
            _synthetic_configuration(request, transport, profile)
            if name == "usable_configuration"
            else None
        )
        return SyntheticRuntimeResult(name, attempt, configuration, page)


class AvitoParserRuntime:
    """Public Module05 runtime facade."""

    def __init__(
        self,
        *,
        synthetic_provider: SyntheticParserProvider | None = None,
        live_adapter: HttpxLiveAdapter | None = None,
    ) -> None:
        self.synthetic_provider = synthetic_provider or SyntheticParserProvider()
        self.live_adapter = live_adapter or HttpxLiveAdapter()

    def run_synthetic(
        self, scenario: str | SyntheticScenario, *, request_id: str = "synthetic"
    ) -> SyntheticRuntimeResult:
        return self.synthetic_provider.execute(scenario, request_id=request_id)

    def run_page(
        self, scenario: str | SyntheticScenario, *, request_id: str = "synthetic-page"
    ) -> ListingPageParseOutcome:
        result = self.run_synthetic(scenario, request_id=request_id)
        if result.page is None:
            raise ValueError(f"scenario does not produce a listing page: {result.scenario}")
        return result.page

    def run_batch(
        self, scenarios: tuple[str | SyntheticScenario, ...], *, request_id: str = "synthetic-batch"
    ) -> ParserBatchRuntimeResult:
        if not scenarios:
            raise ValueError("batch must not be empty")
        outcomes = tuple(
            self.run_synthetic(scenario, request_id=f"{request_id}::{index}")
            for index, scenario in enumerate(scenarios, 1)
        )
        statuses = tuple(item.attempt.parser_status for item in outcomes)
        succeeded = sum(status is ParserOutcomeStatus.USABLE_RESPONSE for status in statuses)
        ambiguous = sum(status is ParserOutcomeStatus.RESULT_AMBIGUOUS for status in statuses)
        seen: set[str] = set()
        duplicates: list[str] = []
        for item in outcomes:
            if item.page is None:
                continue
            for candidate in item.page.normalized_listing_candidates:
                if candidate.listing_candidate_id in seen:
                    duplicates.append(candidate.listing_candidate_id)
                seen.add(candidate.listing_candidate_id)
        return ParserBatchRuntimeResult(
            outcomes=outcomes,
            succeeded_count=succeeded,
            failed_count=len(outcomes) - succeeded - ambiguous,
            ambiguous_count=ambiguous,
            duplicate_observations=tuple(duplicates),
        )

    def analyze_source(
        self, request: ParserRequestEnvelope, transport: TransportOutcomeReference | None
    ) -> Any:
        status: Any = _status_for_transport(request.compatibility_profile, transport)
        return SearchSourceAnalysisOutcome(
            analysis_id=f"analysis::{request.request_id}",
            request_envelope=request,
            transport_outcome=transport,
            status=status,
            compatibility_profile=request.compatibility_profile,
            warnings=(_warning(ParserWarningCode.SOURCE_URL_UNTRUSTED),),
            explanation=ParserOutcomeExplanation(
                "source remains Beacon-owned and untrusted",
                reason_code="SOURCE_REFERENCE_UNCHANGED",
            ),
        )

    def compatibility(
        self, profile: ParserCompatibilityProfile | None
    ) -> ParserCompatibilityOutcome:
        if profile is None:
            profile = _profile("missing", CompatibilityProfileLifecycleStatus.UNAVAILABLE)
        lifecycle = profile.lifecycle_status or CompatibilityProfileLifecycleStatus.UNAVAILABLE
        change = (
            "COMPATIBLE"
            if lifecycle is CompatibilityProfileLifecycleStatus.CURRENT
            else "UNAVAILABLE"
        )
        from .contracts import CompatibilityChangeClass

        return ParserCompatibilityOutcome(
            outcome_id=f"compat::{profile.profile_id}",
            compatibility_profile=profile,
            lifecycle_status=lifecycle,
            change_class=CompatibilityChangeClass(change),
            status=lifecycle,
            error_messages=()
            if lifecycle is CompatibilityProfileLifecycleStatus.CURRENT
            else ("profile is not current",),
        )

    def explain(self, outcome: ParserAttemptOutcome) -> ParserOutcomeExplanation:
        return outcome.explanation or ParserOutcomeExplanation(
            "safe parser outcome", reason_code=outcome.attempt_id
        )

    def persist_outcome(
        self,
        session: Session | Connection,
        *,
        beacon_id: UUID,
        attempt: ParserAttemptOutcome,
        normalized_snapshot: NormalizedListingSnapshot | ListingPageParseOutcome | None = None,
        run_id: UUID | None = None,
        route_id: UUID | None = None,
        purpose: str = "scan",
        observed_at: datetime | None = None,
    ) -> ParserPersistenceResult:
        snapshot = _snapshot_for_persistence(normalized_snapshot)
        code = (attempt.parser_status or attempt.transport_status).value
        fingerprint = _fingerprint(beacon_id, purpose, attempt, snapshot)
        from mayak.persistence.metadata import metadata

        table = metadata.tables["mayak.parser_outcomes"]
        db: Any = session
        # PostgreSQL is the replay authority even when a caller has no run_id.
        # This is a database transaction lock, never a process-local mutex.
        lock_key = int.from_bytes(hashlib.sha256(f"parser-replay:{fingerprint}".encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})
        existing = (
            db.execute(
                select(table).where(table.c.run_id == run_id, table.c.fingerprint == fingerprint)
            )
            .mappings()
            .first()
        )
        if existing is not None:
            if existing["outcome_code"] != code or existing["listing_snapshot"] != snapshot:
                raise ValueError("contradictory immutable parser replay")
            return ParserPersistenceResult(existing["id"], fingerprint, True, code)
        outcome_id = uuid4()
        values = dict(
            id=outcome_id, beacon_id=beacon_id, run_id=run_id, route_id=route_id,
            outcome_code=code, listing_snapshot=snapshot,
            observed_at=observed_at or datetime.now(UTC), fingerprint=fingerprint,
            created_at=observed_at or datetime.now(UTC),
        )
        try:
            with db.begin_nested():
                db.execute(insert(table).values(**values))
        except IntegrityError:
            existing = db.execute(
                select(table).where(table.c.run_id == run_id, table.c.fingerprint == fingerprint)
            ).mappings().first()
            if existing is None:
                raise
            if existing["outcome_code"] != code or existing["listing_snapshot"] != snapshot:
                raise ValueError("contradictory immutable parser replay")
            return ParserPersistenceResult(existing["id"], fingerprint, True, code)
        return ParserPersistenceResult(outcome_id, fingerprint, False, code)

    def read_outcome(
        self, session: Session | Connection, outcome_id: UUID
    ) -> ParserOutcomeReadback | None:
        from mayak.persistence.metadata import metadata

        table = metadata.tables["mayak.parser_outcomes"]
        db: Any = session
        row = db.execute(select(table).where(table.c.id == outcome_id)).mappings().first()
        if row is None:
            return None
        values = dict(row)
        values["outcome_id"] = values.pop("id")
        return ParserOutcomeReadback(**values)


# Explicit aliases make the public boundary discoverable without a second package.
ParserRuntime = AvitoParserRuntime
HTTPXLiveAdapter = HttpxLiveAdapter


def _evidence(kind: str, value: str) -> ParserEvidenceReference:
    return ParserEvidenceReference(
        f"safe::{kind}::{value}", kind, fingerprint=hashlib.sha256(value.encode()).hexdigest()
    )


def _warning(code: ParserWarningCode | SearchConfigurationWarningCode) -> ParserWarning:
    return ParserWarning(code, code.value.lower().replace("_", " "))


def _profile(
    profile_id: str,
    lifecycle: CompatibilityProfileLifecycleStatus = CompatibilityProfileLifecycleStatus.CURRENT,
) -> ParserCompatibilityProfile:
    return ParserCompatibilityProfile(
        profile_id=profile_id,
        semantic_version="synthetic-1",
        profile_version="synthetic-1",
        lifecycle_status=lifecycle,
        authority_class=CompatibilityProfileAuthorityClass.SYNTHETIC,
        authority_scope=("synthetic",),
        reference_ids=("RF14-SYNTHETIC",),
        evidence_reference=_evidence("profile", profile_id),
        supported_extraction_claims=("tier-1 listing", "bounded search parameters"),
        unsupported_extraction_claims=(
            "live Avito capability",
            "filter editability",
            "country-wide support",
        ),
        required_fields=("profile_id", "items"),
        completeness_rules=("clean empty requires explicit proof",),
    )


def _request(request_id: str, profile: ParserCompatibilityProfile) -> ParserRequestEnvelope:
    return ParserRequestEnvelope(
        request_id,
        "mayak.avito.parser.request",
        "1.0",
        "mayak.synthetic",
        "scan",
        profile,
        safe_source_reference="safe-source::synthetic",
        correlation_id=f"corr::{request_id}",
        idempotency_key=f"idem::{request_id}",
    )


def _transport(request_id: str, status: TransportOutcomeStatus) -> TransportOutcomeReference:
    return TransportOutcomeReference(
        f"transport::{request_id}", status, request_reference=f"request::{request_id}"
    )


def _classification(
    classification_id: str,
    transport_status: TransportOutcomeStatus,
    *,
    parser_status: ParserOutcomeStatus | None = None,
    evidence_class: ProviderResponseEvidenceClass = ProviderResponseEvidenceClass.UNCLASSIFIED,
    completeness: ResponseCompletenessStatus = ResponseCompletenessStatus.UNVERIFIED,
    restriction: ResponseRestrictionSignal = ResponseRestrictionSignal.NONE,
    explanation: str | None = None,
    evidence: tuple[ParserEvidenceReference, ...] = (),
) -> TransportResponseClassificationOutcome:
    return TransportResponseClassificationOutcome(
        classification_id,
        parser_status or transport_status,
        transport_status=transport_status,
        parser_status=parser_status,
        provider_response_evidence_class=evidence_class,
        response_completeness_status=completeness,
        response_restriction_signal=restriction,
        evidence_references=evidence,
        explanation=ParserOutcomeExplanation(explanation, reason_code=classification_id)
        if explanation
        else None,
    )


def _status_for_transport(
    profile: ParserCompatibilityProfile, transport: TransportOutcomeReference | None
) -> Any:
    if profile.lifecycle_status is not CompatibilityProfileLifecycleStatus.CURRENT:
        return profile.lifecycle_status
    if transport is None:
        return TransportOutcomeStatus.NOT_SENT
    if transport.transport_status is not TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED:
        return transport.transport_status
    return ParserOutcomeStatus.RESULT_AMBIGUOUS


def _synthetic_configuration(
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
) -> SearchConfigurationExtractionOutcome:
    evidence = _evidence("config", request.request_id)
    values = ("city=synthetic", "city=synthetic", "price_from=100")
    rule = MultivalueNormalizationRule(
        "synthetic-repeat",
        MultivalueNormalizationStatus.PRESERVED,
        MultivaluePreservationMode.ORDERED_TUPLE,
    )
    multi = MultivalueNormalizationOutcome(
        "multi::city",
        "city",
        ("synthetic", "synthetic"),
        rule,
        MultivalueNormalizationStatus.PRESERVED,
        MultivaluePreservationMode.ORDERED_TUPLE,
        ("synthetic", "synthetic"),
        compatibility_profile=profile,
    )
    params = (
        SearchConfigurationParameterCandidate(
            "city",
            repeated_values=("synthetic", "synthetic"),
            multivalue_normalization=multi,
            value_kind=SearchConfigurationValueKind.COLLECTION,
            evidence_references=(evidence,),
        ),
        SearchConfigurationParameterCandidate(
            "price_from", parameter_value="100", evidence_references=(evidence,)
        ),
    )
    candidates = (
        SearchConfigurationCandidate(
            "geo",
            SearchConfigurationExtractionField.GEOGRAPHY_CONTEXT,
            SearchConfigurationFieldStatus.EVIDENCE_BOUND,
            SearchConfigurationValueKind.KEY_VALUE_PAIR,
            (params[0],),
            (evidence,),
        ),
        SearchConfigurationCandidate(
            "price",
            SearchConfigurationExtractionField.PRICE_LOWER_BOUND,
            SearchConfigurationFieldStatus.EVIDENCE_BOUND,
            SearchConfigurationValueKind.KEY_VALUE_PAIR,
            (params[1],),
            (evidence,),
        ),
    )
    return SearchConfigurationExtractionOutcome(
        f"config::{request.request_id}",
        request,
        transport,
        ParserOutcomeStatus.USABLE_RESPONSE,
        profile,
        search_configuration_candidates=candidates,
        parameter_candidates=params,
        normalized_geography_candidates=("synthetic",),
        normalized_filter_candidates=values,
        warnings=(_warning(SearchConfigurationWarningCode.MULTIVALUE_PARAMETER_PRESERVED),),
        evidence_references=(evidence,),
    )


def _synthetic_page(
    request: ParserRequestEnvelope,
    transport: TransportOutcomeReference,
    profile: ParserCompatibilityProfile,
    name: str,
    status: ParserOutcomeStatus | None,
) -> ListingPageParseOutcome:
    final_status = status or ParserOutcomeStatus.RESULT_AMBIGUOUS
    candidates: tuple[NormalizedListingCandidate, ...] = ()
    cards: tuple[ListingCardCandidate, ...] = ()
    if name == "usable_listing_page":
        evidence = _evidence("listing", "synthetic-1")
        fields = tuple(
            ListingFieldCandidate(
                f"field::{family.value.lower()}",
                family,
                ListingFieldTier.TIER_1_SEARCH_RESULT,
                ListingFieldAvailability.PROVEN_AVAILABLE,
                ListingFieldQuality.SYNTHETIC_ONLY,
                value,
                profile,
                evidence_references=(evidence,),
            )
            for family, value in (
                (ListingFieldFamily.TITLE, "Synthetic listing"),
                (ListingFieldFamily.LISTING_URL, "https://synthetic.invalid/item/1"),
                (ListingFieldFamily.NORMALIZED_PRICE, "100"),
            )
        )
        card = ListingCardCandidate("card::1", fields, evidence_references=(evidence,))
        candidates = (
            NormalizedListingCandidate(
                "listing::1", ListingCandidateStatus.USABLE, card, evidence_references=(evidence,)
            ),
        )
        cards = (card,)
    positions = tuple(
        ObservedListingPosition(f"position::{i}", item.listing_candidate_id, i)
        for i, item in enumerate(candidates, 1)
    )
    ordering = (
        ListingOrderingEvidence(
            "ordering::synthetic",
            ListingSortContextStatus.MISSING,
            positions,
        )
        if positions
        else None
    )
    return ListingPageParseOutcome(
        f"page::{request.request_id}",
        request,
        transport,
        final_status,
        profile,
        candidates,
        cards,
        ordering_evidence=ordering,
        warnings=(_warning(ParserWarningCode.EMPTY_RESULT_PROVEN),)
        if name == "clean_empty"
        else (),
    )


def _snapshot_for_persistence(
    value: NormalizedListingSnapshot | ListingPageParseOutcome | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    if isinstance(value, ListingPageParseOutcome):
        value = NormalizedListingSnapshot.from_page(value)
    if not isinstance(value, NormalizedListingSnapshot):
        raise TypeError("persistence requires NormalizedListingSnapshot or ListingPageParseOutcome")
    snapshot = value.as_dict()
    encoded = json.dumps(snapshot, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode()) > 32768:
        raise ValueError("normalized listing snapshot exceeds 32 KiB")
    return json.loads(encoded)


def _fingerprint(
    beacon_id: UUID, purpose: str, attempt: ParserAttemptOutcome, snapshot: Any
) -> str:
    value = {
        "beacon_id": str(beacon_id),
        "purpose": purpose,
        "attempt": attempt.attempt_id,
        "transport": attempt.transport_status.value,
        "parser": attempt.parser_status.value if attempt.parser_status else None,
        "response": attempt.response_reference,
        "profile": (
            attempt.request_envelope.compatibility_profile.profile_id
            if attempt.request_envelope is not None
            else None
        ),
        "evidence": tuple(
            reference.reference_id
            for reference in attempt.evidence_references
        ),
        "snapshot": snapshot,
    }
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


__all__ = [
    "SyntheticScenario",
    "TrustedDispatchBinding",
    "TrustedDispatchAuthorityPort",
    "TrustedDispatchAuthority",
    "DisabledLiveAuthority",
    "RawHttpResponseObservation",
    "HttpxTransport",
    "ParserTransportPort",
    "SyntheticRuntimeResult",
    "ParserBatchRuntimeResult",
    "NormalizedListingSnapshot",
    "ParserPersistenceResult",
    "ParserOutcomeReadback",
    "HttpxAdapterSettings",
    "HttpxLiveAdapter",
    "HTTPXLiveAdapter",
    "SyntheticParserProvider",
    "AvitoParserRuntime",
    "ParserRuntime",
]
