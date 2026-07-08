"""Module boundary identifiers for the Mayak bootstrap."""

from typing import Final

PLATFORM_AND_CONTRACTS_MODULE_ID: Final[str] = "01-platform-and-contracts"
IDENTITY_AND_ACCESS_MODULE_ID: Final[str] = "02-identity-and-access"
ENTITLEMENTS_AND_BILLING_MODULE_ID: Final[str] = "03-entitlements-and-billing"
BEACON_MANAGEMENT_MODULE_ID: Final[str] = "04-beacon-management"
AVITO_PARSER_ADAPTER_MODULE_ID: Final[str] = "05-avito-parser-adapter"
SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID: Final[str] = (
    "06-scan-orchestration-and-listing-state"
)
EGRESS_ROUTING_MODULE_ID: Final[str] = "07-egress-routing"
NOTIFICATION_DELIVERY_MODULE_ID: Final[str] = "08-notification-delivery"
TELEGRAM_ADAPTER_MODULE_ID: Final[str] = "09-telegram-adapter"
MAX_ADAPTER_MODULE_ID: Final[str] = "10-max-adapter"
ADMIN_AND_SUPPORT_MODULE_ID: Final[str] = "11-admin-and-support"
WEB_CABINET_MODULE_ID: Final[str] = "12-web-cabinet"
FILTER_CATALOG_AND_BUILDER_MODULE_ID: Final[str] = "13-filter-catalog-and-builder"

MODULE_IDS: Final[tuple[str, ...]] = (
    PLATFORM_AND_CONTRACTS_MODULE_ID,
    IDENTITY_AND_ACCESS_MODULE_ID,
    ENTITLEMENTS_AND_BILLING_MODULE_ID,
    BEACON_MANAGEMENT_MODULE_ID,
    AVITO_PARSER_ADAPTER_MODULE_ID,
    SCAN_ORCHESTRATION_AND_LISTING_STATE_MODULE_ID,
    EGRESS_ROUTING_MODULE_ID,
    NOTIFICATION_DELIVERY_MODULE_ID,
    TELEGRAM_ADAPTER_MODULE_ID,
    MAX_ADAPTER_MODULE_ID,
    ADMIN_AND_SUPPORT_MODULE_ID,
    WEB_CABINET_MODULE_ID,
    FILTER_CATALOG_AND_BUILDER_MODULE_ID,
)
