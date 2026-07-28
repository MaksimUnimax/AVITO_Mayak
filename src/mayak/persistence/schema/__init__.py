"""Deterministic SQLAlchemy registrations for persistence schemas."""

from mayak.persistence.schema.beacon import register_beacon_tables
from mayak.persistence.schema.egress import register_egress_tables
from mayak.persistence.schema.entitlements import register_entitlement_tables
from mayak.persistence.schema.filter_catalog import register_filter_catalog_tables
from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.platform import register_platform_tables
from mayak.persistence.schema.scan import register_scan_tables

__all__ = [
    "register_platform_tables",
    "register_identity_tables",
    "register_entitlement_tables",
    "register_filter_catalog_tables",
    "register_beacon_tables",
    "register_egress_tables",
    "register_scan_tables",
]
