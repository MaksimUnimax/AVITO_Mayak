"""The single deterministic metadata registry used by Alembic."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from mayak.persistence.schema.beacon import register_beacon_tables
from mayak.persistence.schema.egress import register_egress_tables
from mayak.persistence.schema.entitlements import register_entitlement_tables
from mayak.persistence.schema.filter_catalog import register_filter_catalog_tables
from mayak.persistence.schema.identity import register_identity_tables
from mayak.persistence.schema.max import register_max_tables
from mayak.persistence.schema.notification import register_notification_tables
from mayak.persistence.schema.parser import register_parser_tables
from mayak.persistence.schema.platform import register_platform_tables
from mayak.persistence.schema.scan import register_scan_tables
from mayak.persistence.schema.support import register_support_tables
from mayak.persistence.schema.telegram import register_telegram_tables

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(schema="mayak", naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


register_platform_tables(metadata)
register_identity_tables(metadata)
register_entitlement_tables(metadata)
register_filter_catalog_tables(metadata)
register_beacon_tables(metadata)
register_egress_tables(metadata)
register_scan_tables(metadata)
register_parser_tables(metadata)
register_notification_tables(metadata)
register_telegram_tables(metadata)
register_max_tables(metadata)
register_support_tables(metadata)
