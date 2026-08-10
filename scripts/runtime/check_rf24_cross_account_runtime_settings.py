"""Hosted runtime-settings authority preflight for RF24 acceptance."""
# ruff: noqa
from mayak.runtime.settings import RuntimeConfigurationError, load_runtime_settings


def main() -> int:
    try:
        settings = load_runtime_settings()
    except RuntimeConfigurationError as exc:
        print(f"::error title=runtime-settings-preflight::reason={exc.reason_code} fields={','.join(exc.fields)}")
        return 1
    assert settings.runtime.process_kind.value == "mayak-worker"
    assert settings.runtime.profile.value == "synthetic_acceptance"
    assert settings.session.synthetic_identity_enabled is True
    assert settings.database.application_user == "mayak_application"
    assert settings.database.migration_user == "mayak_migration"
    assert settings.providers.avito_live_enabled is False
    assert settings.providers.telegram_enabled is False
    assert settings.providers.max_enabled is False
    assert settings.providers.yookassa_enabled is False
    assert settings.providers.egress_agent_enabled is False
    assert settings.api.host_port is None
    print("runtime-settings-preflight=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
