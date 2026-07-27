"""Deterministic SQLAlchemy registrations for persistence schemas."""

from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.platform import register_platform_tables

__all__ = ["register_identity_tables", "register_platform_tables"]
