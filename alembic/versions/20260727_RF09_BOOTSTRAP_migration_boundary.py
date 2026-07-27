"""RF-09 migration boundary.

Technical ID: RF-09-05-ALEMBIC-BOOTSTRAP-REVISION-AND-MIGRATION-SERIALIZATION-20260727
Implementation owner: Module 14 / RF-09
Domain tables created: 0
This is a roll-forward-only boundary.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "RF09_BOOTSTRAP"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Assert and reassert the accepted mayak privilege boundary."""
    op.execute(
        sa.text(
            """
DO $rf09$
DECLARE
  schema_owner text;
BEGIN
  IF current_user <> 'mayak_migration' THEN
    RAISE EXCEPTION 'RF09_BOOTSTRAP requires mayak_migration';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mayak_migration')
     OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mayak_application') THEN
    RAISE EXCEPTION 'RF09_BOOTSTRAP requires accepted roles';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'mayak') THEN
    RAISE EXCEPTION 'RF09_BOOTSTRAP requires mayak schema';
  END IF;
  SELECT pg_get_userbyid(nspowner) INTO schema_owner
    FROM pg_namespace WHERE nspname = 'mayak';
  IF schema_owner <> 'mayak_migration' THEN
    RAISE EXCEPTION 'RF09_BOOTSTRAP requires accepted schema owner';
  END IF;

  REVOKE ALL ON SCHEMA mayak FROM PUBLIC;
  GRANT USAGE, CREATE ON SCHEMA mayak TO mayak_migration;
  GRANT USAGE ON SCHEMA mayak TO mayak_application;
  REVOKE CREATE ON SCHEMA mayak FROM mayak_application;

  ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak
    REVOKE ALL ON TABLES FROM PUBLIC;
  ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak
    REVOKE ALL ON TABLES FROM mayak_application;
  ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mayak_application;
  ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak
    REVOKE ALL ON SEQUENCES FROM PUBLIC;
  ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak
    REVOKE ALL ON SEQUENCES FROM mayak_application;
  ALTER DEFAULT PRIVILEGES FOR ROLE mayak_migration IN SCHEMA mayak
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO mayak_application;

  REVOKE ALL ON TABLE mayak.alembic_version FROM PUBLIC;
  REVOKE ALL ON TABLE mayak.alembic_version FROM mayak_application;
END
$rf09$;
"""
        )
    )


def downgrade() -> None:
    """This boundary has no supported reverse operation."""
    raise RuntimeError("RF09_BOOTSTRAP is roll-forward only")
