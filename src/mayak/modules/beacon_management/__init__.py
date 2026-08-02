"""Beacon Management module package."""

from mayak.platform.boundaries import BEACON_MANAGEMENT_MODULE_ID

from .contracts import *  # noqa: F401,F403
from .contracts import __all__ as _contracts_all
from .fixtures import *  # noqa: F401,F403
from .fixtures import __all__ as _fixtures_all
from .runtime import (
    AuthorityPort,
    BeaconCommandResult,
    BeaconManagementRuntime,
    BeaconRevisionView,
    BeaconRuntimeError,
    BeaconView,
    ConflictError,
    EntitlementDecision,
    EntitlementPort,
    ResolvedActor,
    SystemAuthorityPort,
)

MODULE_ID = BEACON_MANAGEMENT_MODULE_ID

__all__ = (
    "MODULE_ID",
    *_contracts_all,
    *_fixtures_all,
    "AuthorityPort",
    "BeaconCommandResult",
    "BeaconManagementRuntime",
    "BeaconRevisionView",
    "BeaconRuntimeError",
    "BeaconView",
    "ConflictError",
    "EntitlementDecision",
    "EntitlementPort",
    "ResolvedActor",
    "SystemAuthorityPort",
)
