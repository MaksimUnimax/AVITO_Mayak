"""Web Cabinet module package."""

from mayak.modules.web_cabinet.beacon_commands import (
    SubmitBeaconWebCommandCommand,
    WebBeaconCommandKind,
    WebBeaconCommandSubmitOutcome,
    WebBeaconCommandSubmitState,
    WebBeaconPatchField,
)
from mayak.modules.web_cabinet.read_models import (
    RequestWebCabinetViewQuery,
    WebCabinetViewResult,
    WebCabinetViewState,
    WebReadFreshness,
    WebReadModelFamily,
    WebReadModelSourceReference,
    WebSourceState,
    WebViewAudience,
)
from mayak.platform.boundaries import WEB_CABINET_MODULE_ID

MODULE_ID = WEB_CABINET_MODULE_ID

__all__ = [
    "MODULE_ID",
    "RequestWebCabinetViewQuery",
    "WebCabinetViewResult",
    "WebCabinetViewState",
    "WebReadFreshness",
    "WebReadModelFamily",
    "WebReadModelSourceReference",
    "WebSourceState",
    "WebViewAudience",
    "SubmitBeaconWebCommandCommand",
    "WebBeaconCommandKind",
    "WebBeaconCommandSubmitOutcome",
    "WebBeaconCommandSubmitState",
    "WebBeaconPatchField",
]
