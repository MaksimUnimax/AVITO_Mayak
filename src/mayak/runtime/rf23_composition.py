"""RF23 application composition root.

This is the only RF23 module that assembles several owner runtimes.  Routers
receive this typed object and never receive persistence tables or provider
clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from mayak.modules.beacon_management.runtime import (
    BeaconManagementRuntime,
    EntitlementDecision,
)
from mayak.modules.entitlements_and_billing.runtime import EntitlementsBillingRuntime
from mayak.modules.identity_and_access.runtime import IdentityRuntime
from mayak.modules.notification_delivery.runtime import read_history
from mayak.persistence.config import ApplicationDatabaseSettings, DatabaseEndpoint
from mayak.persistence.engine import create_application_engine
from mayak.persistence.session import create_session_factory
from mayak.runtime.rf20_composition import build_rf20_composition
from mayak.runtime.rf21_composition import (
    CustomerIdentityAuthorityAdapter,
    build_rf21_runtime,
)
from mayak.runtime.settings import MayakRuntimeSettings


class CustomerEntitlementPort:
    """Small Beacon-owned port backed by the Entitlements owner runtime."""

    def __init__(self, owner: EntitlementsBillingRuntime) -> None:
        self.owner = owner

    def decide(
        self, session: Session, *, account_id: Any, action: str, active_count: int
    ) -> EntitlementDecision:
        try:
            projection = self.owner.evaluate_effective(session, account_id, at=datetime.now(UTC))
            allowed = bool(getattr(projection, "allowed", True))
        except Exception:
            allowed = False
        return EntitlementDecision(allowed=allowed, reference="entitlements-runtime")


@dataclass(frozen=True, slots=True)
class CustomerSessionReference:
    """Opaque transport reference; its repr/str never contains cookie material."""

    _value: str

    def __repr__(self) -> str:
        return "CustomerSessionReference(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"

    def _value_as_secret(self) -> Any:
        from mayak.modules.identity_and_access.runtime import _RawSecret

        return _RawSecret(self._value)


@dataclass(frozen=True, slots=True)
class MigrationInspection:
    expected_head: str | None
    observed_revision: str | None
    structurally_valid: bool


def _migration_script() -> ScriptDirectory:
    root = Path(__file__).resolve().parents[3]
    return ScriptDirectory.from_config(Config(str(root / "alembic.ini")))


@dataclass(slots=True)
class RF23Composition:
    settings: MayakRuntimeSettings
    engine: Engine
    sessions: sessionmaker[Session]
    identity: IdentityRuntime
    entitlements: EntitlementsBillingRuntime
    beacon: BeaconManagementRuntime
    web: Any
    admin: Any
    rf20: Any
    filter_catalog_factory: Any

    def new_session(self) -> Session:
        return self.sessions()

    def customer_session(self, cookie_value: str) -> CustomerSessionReference:
        if not cookie_value:
            raise ValueError("session cookie is empty")
        return CustomerSessionReference(cookie_value)

    def validate_customer_session(self, session: Session, cookie_value: str) -> Any:
        return self.identity.validate_session(
            session, self.customer_session(cookie_value)._value_as_secret()
        )

    def validate_session_reference(
        self, session: Session, reference: CustomerSessionReference
    ) -> Any:
        return self.identity.validate_session(session, reference._value_as_secret())

    def _secret(self, reference: CustomerSessionReference) -> Any:
        return reference._value_as_secret()

    def synthetic_login(self, session: Session, request: Any) -> tuple[Any, str | None]:
        outcome, issued = self.identity.synthetic_login(session, request)
        return outcome, None if issued is None else issued.token.reveal()

    def revoke_session(
        self,
        session: Session,
        reference: CustomerSessionReference,
        *,
        idempotency_key: str,
        correlation: Any,
    ) -> Any:
        return self.identity.revoke_my_session(
            session,
            self._secret(reference),
            idempotency_key=idempotency_key,
            correlation=correlation,
        )

    def account_summary(self, session: Session, account_id: Any) -> Any:
        return self.identity.safe_account_summary(session, account_id)

    def beacon_list(self, session: Session, reference: CustomerSessionReference) -> Any:
        return self.beacon.list(session, actor_reference=reference)  # type: ignore[arg-type]

    def beacon_get(
        self, session: Session, reference: CustomerSessionReference, beacon_id: Any
    ) -> Any:
        return self.beacon.get(session, actor_reference=reference, beacon_id=beacon_id)  # type: ignore[arg-type]

    def beacon_history(
        self, session: Session, reference: CustomerSessionReference, beacon_id: Any
    ) -> Any:
        return self.beacon.history(session, actor_reference=reference, beacon_id=beacon_id)  # type: ignore[arg-type]

    def beacon_patch(
        self,
        session: Session,
        reference: CustomerSessionReference,
        beacon_id: Any,
        *,
        patch: Any,
        expected_row_version: int,
        idempotency_key: str,
    ) -> Any:
        return self.beacon.patch(  # type: ignore[arg-type]
            session,
            actor_reference=cast(Any, reference),
            beacon_id=beacon_id,
            patch=patch,
            expected_row_version=expected_row_version,
            idempotency_key=idempotency_key,
            strict_expected_row_version=True,
        )

    def beacon_create(
        self,
        session: Session,
        reference: CustomerSessionReference,
        account_id: Any,
        *,
        source_url: str,
        name: str,
        idempotency_key: str,
    ) -> Any:
        return self.beacon.create_preparation(  # type: ignore[arg-type]
            session,
            actor_reference=cast(Any, reference),
            account_id=account_id,
            source_url=source_url,
            name=name,
            idempotency_key=idempotency_key,
        )

    def beacon_lifecycle(
        self,
        session: Session,
        reference: CustomerSessionReference,
        beacon_id: Any,
        action: str,
        *,
        expected_row_version: int,
        idempotency_key: str,
    ) -> Any:
        return getattr(self.beacon, action)(
            session,
            actor_reference=reference,
            beacon_id=beacon_id,
            expected_row_version=expected_row_version,
            idempotency_key=idempotency_key,
        )

    def entitlement_summary(self, session: Session, account_id: Any) -> Any:
        return self.entitlements.evaluate_effective(session, account_id, at=datetime.now(UTC))

    def notification_history(self, session: Session, account_id: Any) -> Any:
        return read_history(session, account_id=account_id, actor_account_id=account_id, limit=50)

    def scan_views(self, session: Session, reference: CustomerSessionReference) -> Any:
        from mayak.modules.scan_orchestration.read_models import current_listing_state, recent_runs

        views = self.beacon.list(session, actor_reference=reference)  # type: ignore[arg-type]
        return [
            {
                "beacon_id": str(view.beacon_id),
                "listing_state": current_listing_state(session, view.beacon_id),
                "recent_runs": recent_runs(session, view.beacon_id),
            }
            for view in views
        ]

    def channel_readiness(self) -> Any:
        from mayak.modules.max_adapter.runtime import max_readiness
        from mayak.modules.telegram_adapter.runtime import telegram_readiness

        return {
            "telegram": telegram_readiness(self.settings, credential_present=False),
            "max": max_readiness(self.settings, credential_present=False),
        }

    def filter_catalog(self, session: Session, version_code: str) -> Any:
        return self.filter_catalog_factory(session).load_catalog(
            version_code, customer_editable=True
        )

    def operator_validation(self, session: Session, cookie_value: str) -> Any:
        return self.rf20.identity.verify_operator(
            session, self.customer_session(cookie_value)._value_as_secret()
        )

    @staticmethod
    def safe_error_status(exc: Exception) -> int:
        from mayak.modules.beacon_management.runtime import BeaconRuntimeError, ConflictError

        if isinstance(exc, ConflictError):
            return 409
        if isinstance(exc, (ValueError, BeaconRuntimeError)):
            return 400
        return 500

    def migration_inspection(self, session: Session) -> MigrationInspection:
        expected = self.expected_migration_head()
        try:
            rows = (
                session.execute(text("SELECT version_num FROM mayak.alembic_version"))
                .scalars()
                .all()
            )
            observed = str(rows[0]) if len(rows) == 1 and rows[0] is not None else None
            return MigrationInspection(expected, observed, expected is not None and len(rows) == 1)
        except Exception:
            return MigrationInspection(expected, None, False)

    @staticmethod
    def expected_migration_head() -> str | None:
        try:
            heads = tuple(_migration_script().get_heads())
            return heads[0] if len(heads) == 1 else None
        except Exception:
            return None

    def readiness_inspection(self, session: Session) -> MigrationInspection:
        session.execute(text("SELECT 1"))
        return self.migration_inspection(session)

    def presentation_routers(
        self, *, session_provider: Any, actor_provider: Any
    ) -> tuple[Any, Any]:
        from mayak.modules.admin_and_support.admin_ui import build_admin_router
        from mayak.modules.web_cabinet.web_ui import build_web_router

        return (
            build_web_router(
                runtime=self.web,
                session_factory=self.sessions,
                session_provider=session_provider,
                prefix="/web",
            ),
            build_admin_router(
                runtime=self.admin, sessions=self.sessions, actor_provider=actor_provider
            ),
        )


def build_rf23_composition(
    settings: MayakRuntimeSettings, *, engine: Engine | None = None
) -> RF23Composition:
    """Build application-role runtime composition; never a migration engine."""
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
    sessions = create_session_factory(app_engine)
    identity = IdentityRuntime(settings)
    entitlements = EntitlementsBillingRuntime()
    customer_authority = CustomerIdentityAuthorityAdapter(identity)
    beacon = BeaconManagementRuntime(customer_authority, CustomerEntitlementPort(entitlements))
    rf20 = build_rf20_composition(identity=identity, entitlements=entitlements, beacon=beacon)
    web = build_rf21_runtime(
        identity=identity,
        beacon=beacon,
        entitlements=entitlements,
        notification=read_history,
        settings=settings,
        support=rf20.runtime(),
    )
    from mayak.modules.filter_catalog.runtime import FilterCatalogRuntime

    return RF23Composition(
        settings=settings,
        engine=app_engine,
        sessions=sessions,
        identity=identity,
        entitlements=entitlements,
        beacon=beacon,
        web=web,
        admin=rf20.runtime(),
        rf20=rf20,
        filter_catalog_factory=FilterCatalogRuntime,
    )


__all__ = [
    "CustomerSessionReference",
    "MigrationInspection",
    "RF23Composition",
    "build_rf23_composition",
]
