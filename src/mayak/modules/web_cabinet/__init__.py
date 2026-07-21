"""Web Cabinet module package."""

# ruff: noqa: I001

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
from mayak.modules.web_cabinet.auth_context import (
    RequestWebPresentationContextQuery,
    WebIdentityAuthorityReference,
    WebPresentationActorState,
    WebPresentationContextResult,
    WebPresentationContextState,
    WebSessionReferenceState,
)
from mayak.modules.web_cabinet.entitlement_projections import (
    RequestWebEntitlementProjectionQuery,
    WebEntitlementAccessState,
    WebEntitlementCapabilityProjection,
    WebEntitlementProjectionResult,
    WebEntitlementProjectionState,
    WebTariffOptionProjection,
    WebTariffOptionState,
)
from mayak.modules.web_cabinet.notification_history import (
    RequestWebNotificationHistoryQuery,
    WebNotificationDeliveryHistoryEntry,
    WebNotificationDeliveryState,
    WebNotificationHistoryResult,
    WebNotificationHistoryResultState,
    WebNotificationListingReferenceProjection,
)
from mayak.modules.web_cabinet.status_display import (
    RequestWebStatusDisplayQuery,
    WebStatusDisplayFamily,
    WebStatusDisplayItem,
    WebStatusDisplayResult,
    WebStatusDisplayResultState,
    WebStatusEvidenceClass,
    WebStatusEvidenceReference,
    WebStatusSourceFamily,
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
    "RequestWebPresentationContextQuery",
    "WebIdentityAuthorityReference",
    "WebPresentationActorState",
    "WebPresentationContextResult",
    "WebPresentationContextState",
    "WebSessionReferenceState",
    "RequestWebEntitlementProjectionQuery",
    "WebEntitlementAccessState",
    "WebEntitlementCapabilityProjection",
    "WebEntitlementProjectionResult",
    "WebEntitlementProjectionState",
    "WebTariffOptionProjection",
    "WebTariffOptionState",
    "RequestWebNotificationHistoryQuery",
    "WebNotificationDeliveryHistoryEntry",
    "WebNotificationDeliveryState",
    "WebNotificationHistoryResult",
    "WebNotificationHistoryResultState",
    "WebNotificationListingReferenceProjection",
    "RequestWebStatusDisplayQuery",
    "WebStatusDisplayFamily",
    "WebStatusDisplayItem",
    "WebStatusDisplayResult",
    "WebStatusDisplayResultState",
    "WebStatusEvidenceClass",
    "WebStatusEvidenceReference",
    "WebStatusSourceFamily",
]
