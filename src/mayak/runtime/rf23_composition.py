"""RF23 application composition root.

This is the only RF23 module that assembles several owner runtimes.  Routers
receive this typed object and never receive persistence tables or provider
clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

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


__all__ = ["RF23Composition", "build_rf23_composition"]
