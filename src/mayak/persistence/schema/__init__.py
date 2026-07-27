"""Deterministic SQLAlchemy registrations for persistence schemas."""

from mayak.persistence.schema.entitlements import register_entitlement_tables
from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.platform import register_platform_tables

__all__ = [
    "register_platform_tables",
    "register_identity_tables",
    "register_entitlement_tables",
]
