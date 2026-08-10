"""Small Module 14 composition used by the real scheduler and worker.

The composition only adapts owner-owned public runtimes to the ports already
defined by Scan.  It owns no domain tables or durable state.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable, cast
from uuid import UUID, uuid5

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from mayak.contracts.idempotency import IdempotencyFingerprint, IdempotencyKey, IdempotencyScope
from mayak.modules.avito_parser_adapter.runtime import AvitoParserRuntime
from mayak.modules.beacon_management.contracts import BeaconActionCausation, BeaconSystemActorClass
from mayak.modules.beacon_management.runtime import (
    BeaconManagementRuntime,
    ResolvedSystemActor,
)
from mayak.modules.entitlements_and_billing.runtime import (
    AuthorityFacts,
    EntitlementsBillingRuntime,
)
from mayak.modules.identity_and_access import IdentityRuntime
from mayak.modules.notification_delivery import (
    NotificationBeaconLifecycleStatus,
    NotificationChannelClass,
    NotificationChannelEligibilityEvidence,
    NotificationEligibilityContext,
    NotificationEntitlementStatus,
    NotificationRecoveryGraceEvidence,
    NotificationSourceEvent,
    NotificationSourceFamily,
    NotificationSourceProducer,
    create_notification_outbox_item,
    evaluate_notification_eligibility,
    evaluate_notification_source_intake,
    plan_notification_delivery,
)
from mayak.modules.notification_delivery.runtime import (
    EndpointEligibility,
    fanout_event,
    ingest_source,
    register_endpoint,
)
from mayak.modules.scan_orchestration.contracts import (
    AccessTier,
    BeaconSnapshot,
    DecisionStatus,
    EntitlementSnapshot,
    ListingCandidate,
    ParserOutcome,
    ParserOutcomePort,
    ParserStatus,
)
from mayak.modules.scan_orchestration.repository import ScanRepository
from mayak.persistence.config import ApplicationDatabaseSettings, DatabaseEndpoint
from mayak.persistence.engine import create_application_engine
from mayak.persistence.session import create_session_factory
from mayak.runtime.rf21_composition import CustomerIdentityAuthorityAdapter
from mayak.runtime.rf23_composition import CustomerEntitlementPort, CustomerSessionReference
from mayak.runtime.settings import MayakRuntimeSettings


class ScanBeaconAdapter:
    def __init__(self, owner: BeaconManagementRuntime) -> None:
        self.owner = owner
        self.session: Session | None = None

    def current(self, beacon_id: UUID) -> BeaconSnapshot:
        if self.session is None:
            raise RuntimeError("Scan Beacon adapter is not bound to a session")
        view = self.owner.current_for_scan(self.session, beacon_id=beacon_id)
        revision = view.current_revision_no
        if revision is None:
            raise RuntimeError("Beacon has no accepted configuration revision")
        return BeaconSnapshot(
            beacon_id=view.beacon_id,
            account_id=view.account_id,
            revision_no=revision,
            lifecycle_eligible=view.state == "ACTIVE",
        )

    def bind(self, session: Session) -> "ScanBeaconAdapter":
        self.session = session
        return self


class AcceptanceEntitlementAuthority:
    """Synthetic-only Identity bridge for owner entitlement setup commands."""

    def __init__(self, identity: IdentityRuntime) -> None:
        self.identity = identity

    def authority(
        self, session: Session, actor_reference: object, account_id: UUID
    ) -> AuthorityFacts:
        validation = self.identity.validate_session_reference(session, actor_reference)
        if validation.account_id != account_id or validation.metadata is None:
            raise PermissionError("Identity account scope mismatch")
        return AuthorityFacts(
            actor_id=account_id,
            account_id=account_id,
            capabilities=frozenset(
                {"ENTITLEMENTS_TARIFF_ADMIN", "ENTITLEMENTS_TARIFF_ASSIGN_ADMIN"}
            ),
            scope="account_id",
            authorization_reference=f"rf24:{validation.metadata.session_id}",
            audit_reference=f"rf24:{validation.metadata.session_id}",
        )


class ScanEntitlementAdapter:
    def __init__(
        self,
        owner: EntitlementsBillingRuntime,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.owner = owner
        self.clock = clock
        self.session: Session | None = None
        self.at: datetime | None = None

    def current(self, beacon_id: UUID, account_id: UUID | None) -> EntitlementSnapshot:
        if account_id is None or self.session is None:
            return EntitlementSnapshot(
                status=DecisionStatus.DENIED,
                tier=AccessTier.FREE,
                minimum_seconds=10_800,
                step_seconds=10_800,
            )
        projection = self.owner.evaluate_effective(
            self.session, account_id, at=self.at or self.clock()
        )
        allowed = getattr(getattr(projection, "status", None), "value", None) == "ALLOWED"
        code = str(getattr(getattr(projection, "tariff", None), "value", "FREE")).upper()
        tier = AccessTier.BASIC if "BASIC" in code else AccessTier.FREE
        interval = 300 if tier is AccessTier.BASIC else 10_800
        return EntitlementSnapshot(
            status=DecisionStatus.ALLOWED if allowed else DecisionStatus.DENIED,
            tier=tier,
            minimum_seconds=interval,
            step_seconds=interval,
        )

    def bind(self, session: Session, *, at: datetime | None = None) -> "ScanEntitlementAdapter":
        self.session = session
        self.at = at
        return self


class EntitlementsSystemAuthority:
    """Closed internal resolver for the paid-expiry system actor."""

    _REFERENCE = "rf24:system:entitlements-and-billing-expiry"

    def resolve_system(self, session: Session, *, actor_reference: str) -> ResolvedSystemActor:
        if actor_reference != self._REFERENCE:
            raise PermissionError("system authority reference mismatch")
        return ResolvedSystemActor(
            actor_id=UUID("00000000-0000-0000-0000-000000000003"),
            verified=True,
            reference=self._REFERENCE,
            system_actor_class=BeaconSystemActorClass.ENTITLEMENTS_AND_BILLING_SERVICE.value,
        )


class PersistedParserAdapter(ParserOutcomePort):
    """Translate Module 05 immutable parser facts into Scan's contract."""

    def __init__(self, parser: AvitoParserRuntime, session: Session) -> None:
        self.parser, self.session = parser, session

    def resolve(self, outcome_id: UUID, *, run_id: UUID, beacon_id: UUID) -> ParserOutcome:
        row = self.parser.read_outcome(self.session, outcome_id)
        if row is None or row.run_id != run_id or row.beacon_id != beacon_id:
            raise ValueError("parser outcome is outside the current Scan scope")
        status_map = {
            "USABLE_RESPONSE": ParserStatus.CLEAN,
            "EXPLICIT_REJECTION": ParserStatus.EXPLICIT_REJECTION,
            "CAPTCHA_OR_CHALLENGE": ParserStatus.CAPTCHA_OR_CHALLENGE,
            "RATE_OR_ACCESS_RESTRICTED": ParserStatus.RATE_OR_ACCESS_RESTRICTED,
            "PARTIAL": ParserStatus.PARTIAL,
            "RESULT_AMBIGUOUS": ParserStatus.RESULT_AMBIGUOUS,
            "TRANSPORT_UNAVAILABLE": ParserStatus.TRANSPORT_UNAVAILABLE,
        }
        status = status_map.get(row.outcome_code, ParserStatus.RESULT_AMBIGUOUS)
        candidates: list[ListingCandidate] = []
        snapshot = row.listing_snapshot
        if isinstance(snapshot, dict):
            raw_candidates = snapshot.get("candidates", [])
            for item in cast(list[object], raw_candidates):
                if isinstance(item, dict) and isinstance(item.get("listing_candidate_id"), str):
                    fields = item.get("fields", {})
                    if isinstance(fields, dict):
                        candidates.append(
                            ListingCandidate(
                                identity_key=item["listing_candidate_id"],
                                snapshot=fields,
                            )
                        )
        return ParserOutcome(
            outcome_id=outcome_id,
            status=status,
            candidates=tuple(candidates),
            sort_context="NEWEST_FIRST_PROVEN" if status is ParserStatus.CLEAN else None,
            provenance_fingerprint=row.fingerprint,
        )


@dataclass(slots=True)
class RF24RuntimeComposition:
    settings: MayakRuntimeSettings
    engine: Engine
    sessions: sessionmaker[Session]
    beacon: BeaconManagementRuntime
    entitlements: EntitlementsBillingRuntime
    parser: AvitoParserRuntime
    identity: IdentityRuntime
    clock: Callable[[], datetime] = lambda: datetime.now(UTC)

    def scan_repository(self, session: Session) -> ScanRepository:
        return ScanRepository(session)

    def establish_acceptance_access(
        self, session: Session, reference: CustomerSessionReference, account_id: UUID
    ) -> object:
        from datetime import timedelta

        from mayak.modules.entitlements_and_billing.contracts import TariffName

        owner = EntitlementsBillingRuntime(AcceptanceEntitlementAuthority(self.identity))
        now = datetime.now(UTC)
        owner.bootstrap_tariffs(
            session,
            cast(str, reference),
            f"rf24:tariffs:{account_id}",
            effective_at=now,
            target_account_id=account_id,
        )
        return owner.assign_access(
            session,
            cast(str, reference),
            tariff=TariffName.FREE,
            starts_at=now,
            ends_at=now + timedelta(days=1),
            reason="RF24 synthetic acceptance access",
            idempotency_key=f"rf24:free-access:{account_id}",
            target_account_id=account_id,
        )

    def establish_acceptance_basic_access(
        self,
        session: Session,
        reference: CustomerSessionReference,
        account_id: UUID,
        *,
        starts_at: datetime,
        ends_at: datetime,
    ) -> object:
        """Bounded synthetic-only Basic setup through the Entitlements owner."""
        from mayak.modules.entitlements_and_billing.contracts import TariffName

        if ends_at <= starts_at or (ends_at - starts_at).total_seconds() > 86_400:
            raise ValueError("synthetic Basic interval must be positive and bounded")
        owner = EntitlementsBillingRuntime(AcceptanceEntitlementAuthority(self.identity))
        owner.bootstrap_tariffs(
            session,
            cast(str, reference),
            f"rf24:tariffs:{account_id}",
            effective_at=starts_at,
            target_account_id=account_id,
        )
        return owner.assign_access(
            session,
            cast(str, reference),
            tariff=TariffName.BASIC,
            starts_at=starts_at,
            ends_at=ends_at,
            reason="RF24 synthetic Basic expiry acceptance access",
            idempotency_key=f"rf24:basic-access:{account_id}:{ends_at.isoformat()}",
            target_account_id=account_id,
        )

    def scan_beacon(self, session: Session) -> ScanBeaconAdapter:
        return ScanBeaconAdapter(self.beacon).bind(session)

    def scan_entitlement(
        self, session: Session, *, at: datetime | None = None
    ) -> ScanEntitlementAdapter:
        return ScanEntitlementAdapter(self.entitlements, self.clock).bind(session, at=at)

    def reconcile_paid_expiry(self, session: Session, *, at: datetime) -> tuple[UUID, ...]:
        """Reconcile through Entitlements and Beacon owner boundaries only."""
        accounts = self.entitlements.accounts_with_paid_expiry(session, at=at)
        frozen: list[UUID] = []
        for view in self.beacon.active_for_accounts(session, account_ids=accounts):
            decision = self.entitlements.paid_expiry_decision(session, view.account_id, at=at)
            if not decision.actionable or decision.expired_basic_grant_id is None:
                continue
            valid_until = (
                decision.paid_valid_until.isoformat()
                if decision.paid_valid_until is not None
                else "unknown"
            )
            causation = BeaconActionCausation(
                service_actor_class=BeaconSystemActorClass.ENTITLEMENTS_AND_BILLING_SERVICE,
                causation_reference=(
                    f"paid-expiry:{view.account_id}:{view.beacon_id}:"
                    f"{decision.expired_basic_grant_id}:{valid_until}"
                ),
                policy_source_reference="entitlements-and-billing:paid-basic-expiry-freeze:v1",
            )
            try:
                result = self.beacon.freeze_after_expiry(
                    session,
                    system_actor_reference=EntitlementsSystemAuthority._REFERENCE,
                    beacon_id=view.beacon_id,
                    idempotency_key=causation.causation_reference,
                    expected_row_version=view.row_version,
                    causation=causation,
                )
                if result.state == "FROZEN":
                    frozen.append(view.beacon_id)
            except Exception:
                current = self.beacon.current_for_scan(session, beacon_id=view.beacon_id)
                if current.state == "FROZEN":
                    continue
                raise
        return tuple(frozen)

    def parser_port(self, session: Session) -> PersistedParserAdapter:
        return PersistedParserAdapter(self.parser, session)

    def ingest_scan_notification(
        self,
        session: Session,
        *,
        account_id: UUID,
        beacon_id: UUID,
        run_id: UUID,
        listing_keys: tuple[str, ...],
        event_id: UUID,
        now: datetime,
    ) -> tuple[UUID, ...]:
        """Use Notification Delivery's source/intake/fan-out boundaries for Scan effects."""
        if not listing_keys:
            return ()
        fingerprint = hashlib.sha256(f"rf24:scan:{event_id}".encode()).hexdigest()
        source = NotificationSourceEvent(
            source_event_id=str(event_id),
            source_family=NotificationSourceFamily.NEW_LISTINGS_FOUND,
            source_producer=NotificationSourceProducer.SCAN_ORCHESTRATION,
            source_contract="scan.notification.v1",
            source_contract_version="1.0",
            source_fact_id=str(event_id),
            source_committed=True,
            source_commit_reference=str(event_id),
            account_id=str(account_id),
            beacon_id=str(beacon_id),
            scan_run_id=str(run_id),
            listing_count=len(listing_keys),
            safe_listing_reference_ids=listing_keys,
            correlation_id=f"rf24-correlation-{run_id}",
            causation_id=f"rf24-causation-{event_id}",
            idempotency_key=IdempotencyKey(value=f"rf24:scan:{event_id}"),
            idempotency_fingerprint=IdempotencyFingerprint(value=fingerprint),
            idempotency_scope=IdempotencyScope(value="notification.scan-new-listing"),
            source_identity_ambiguous=False,
            contains_raw_provider_payload=False,
            service_access_gate_approved=False,
            evidence_reference_ids=("rf24-scan-commit",),
        )
        intake = evaluate_notification_source_intake(
            decision_id=f"rf24:intake:{event_id}",
            source_event=source,
            evidence_reference_ids=("rf24-intake",),
        )
        event = ingest_source(session, source, now=now)
        if event is None:
            return ()
        endpoint_id = uuid5(UUID("00000000-0000-0000-0000-000000000024"), f"telegram:{account_id}")
        register_endpoint(
            session,
            EndpointEligibility(endpoint_id, account_id, "TELEGRAM", f"rf24-telegram-{account_id}"),
            now=now,
        )
        context = NotificationEligibilityContext(
            account_id=str(account_id),
            beacon_id=str(beacon_id),
            beacon_lifecycle_status=NotificationBeaconLifecycleStatus.ACTIVE,
            beacon_lifecycle_reference_id=str(beacon_id),
            entitlement_status=NotificationEntitlementStatus.ALLOWED,
            entitlement_decision_reference_id=f"rf24-entitlement-{account_id}",
            no_new_status_preference_enabled=False,
            no_new_status_frequency_minutes=None,
            channel_evidence=(
                NotificationChannelEligibilityEvidence(
                    NotificationChannelClass.TELEGRAM,
                    True,
                    f"rf24-telegram-{account_id}",
                    True,
                    True,
                    ("rf24-telegram",),
                ),
                NotificationChannelEligibilityEvidence(
                    NotificationChannelClass.WEB_STATUS_READ_MODEL,
                    True,
                    None,
                    False,
                    False,
                    ("rf24-web",),
                ),
            ),
            recovery_grace_evidence=NotificationRecoveryGraceEvidence(
                False, None, False, False, ("rf24-recovery",)
            ),
            evidence_reference_ids=("rf24-notification-context",),
        )
        eligibility = evaluate_notification_eligibility(
            decision_id=f"rf24:eligibility:{event_id}",
            source_intake_decision=intake,
            context=context,
            evidence_reference_ids=("rf24-eligibility",),
        )
        outbox = create_notification_outbox_item(
            decision_id=f"rf24:outbox:{event_id}",
            outbox_item_id=f"rf24-outbox-{event_id}",
            outbox_contract="notification.outbox.v1",
            outbox_contract_version="1.0",
            eligibility_decision=eligibility,
            idempotency_key=source.idempotency_key,
            idempotency_fingerprint=source.idempotency_fingerprint,
            idempotency_scope=source.idempotency_scope,
            existing_outbox_item=None,
            evidence_reference_ids=("rf24-outbox",),
        )
        plan = plan_notification_delivery(
            decision_id=f"rf24:plan:{event_id}",
            delivery_plan_id=f"rf24-plan-{event_id}",
            outbox_creation_decision=outbox,
            evidence_reference_ids=("rf24-plan",),
        )
        return fanout_event(
            session,
            event.id,
            (endpoint_id,),
            now=now,
            eligibility_decision=eligibility,
            delivery_plan=plan,
        )

    def close(self) -> None:
        self.engine.dispose()


def build_rf24_composition(
    settings: MayakRuntimeSettings,
    *,
    engine: Engine | None = None,
    clock: Callable[[], datetime] | None = None,
) -> RF24RuntimeComposition:
    application = ApplicationDatabaseSettings(
        endpoint=DatabaseEndpoint(
            database=settings.database.name,
            host=settings.database.host,
            port=settings.database.port,
        ),
        user=settings.database.application_user,
        secret_path=settings.runtime.secrets_dir / "mayak_database_application_password",
    )
    app_engine = engine or create_application_engine(settings=application)
    identity = IdentityRuntime(settings)
    acceptance_clock = clock or (lambda: datetime.now(UTC))
    entitlements = EntitlementsBillingRuntime()
    beacon = BeaconManagementRuntime(
        CustomerIdentityAuthorityAdapter(identity),
        CustomerEntitlementPort(entitlements, acceptance_clock),
        system_authority=EntitlementsSystemAuthority(),
    )
    return RF24RuntimeComposition(
        settings=settings,
        engine=app_engine,
        sessions=create_session_factory(app_engine),
        beacon=beacon,
        entitlements=entitlements,
        parser=AvitoParserRuntime(),
        identity=identity,
        clock=acceptance_clock,
    )


__all__ = [
    "PersistedParserAdapter",
    "RF24RuntimeComposition",
    "ScanBeaconAdapter",
    "ScanEntitlementAdapter",
    "build_rf24_composition",
]
