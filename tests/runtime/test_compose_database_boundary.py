import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
COMPOSE = ROOT / "compose.yaml"
DOCKERFILE = ROOT / "Dockerfile"


def _compose() -> str:
    return COMPOSE.read_text(encoding="utf-8")


def _service(name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [a-z0-9-]+:\n"
        r"|^networks:\n|^volumes:\n|^secrets:\n|\Z)",
        _compose(),
    )
    assert match is not None
    return match.group("body")


def _section(name: str) -> str:
    return _service(name)


def test_dockerfile_copies_only_accepted_alembic_assets() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY alembic.ini ./alembic.ini" in text
    assert "COPY alembic ./alembic" in text
    assert text.count("COPY alembic.ini ./alembic.ini") == 1
    assert text.count("COPY alembic ./alembic") == 1
    assert "COPY tests" not in text and "COPY .env" not in text


def test_migration_secret_is_single_file_backed_declaration() -> None:
    text = _compose()
    declaration = (
        "  mayak_database_migration_password_runtime:\n"
        "    file: ${MAYAK_SECRETS_ROOT:-/etc/avito-mayak/secrets}/"
        "mayak_database_migration_password"
    )
    assert text.count("mayak_database_migration_password_runtime:") == 1
    assert declaration in text
    assert "MAYAK_DATABASE_MIGRATION_PASSWORD=" not in text


def test_bootstrap_service_has_exact_boundary() -> None:
    body = _section("mayak-db-bootstrap")
    assert "profiles: [runtime-foundation]" in body
    assert 'command: ["python", "-m", "mayak.persistence.bootstrap"]' in body
    assert 'restart: "no"' in body
    assert "read_only: true" in body and "init: true" in body
    assert "cap_drop: [ALL]" in body
    assert "security_opt: [no-new-privileges:true]" in body
    assert 'tmpfs: ["/tmp:rw,noexec,nosuid,size=64m"]' in body
    assert "networks: [mayak-internal]" in body
    assert re.search(
        r"(?ms)    secrets:\n      - source: mayak_postgres_bootstrap_password_runtime\n"
        r"        target: mayak_postgres_bootstrap_password\n"
        r"      - source: mayak_database_migration_password_runtime\n"
        r"        target: mayak_database_migration_password\n"
        r"      - source: mayak_database_application_password_runtime\n"
        r"        target: mayak_database_application_password\n",
        body,
    )
    assert "mayak_session_signing_key" not in body
    assert "ports:" not in body and "volumes:" not in body


def test_migration_service_has_exact_boundary() -> None:
    body = _section("mayak-migrate")
    assert "profiles: [runtime-foundation]" in body
    assert (
        'command: ["python", "-m", "alembic", "-c", '
        '"/opt/mayak/alembic.ini", "upgrade", "head"]'
    ) in body
    assert 'restart: "no"' in body
    assert "read_only: true" in body and "init: true" in body
    assert "cap_drop: [ALL]" in body
    assert "security_opt: [no-new-privileges:true]" in body
    assert 'tmpfs: ["/tmp:rw,noexec,nosuid,size=64m"]' in body
    assert "networks: [mayak-internal]" in body
    assert "source: mayak_database_migration_password_runtime" in body
    assert "target: mayak_database_migration_password" in body
    assert "mayak_postgres_bootstrap_password" not in body
    assert "mayak_database_application_password" not in body
    assert "mayak_session_signing_key" not in body
    assert "ports:" not in body and "volumes:" not in body


def test_bootstrap_waits_for_postgres_health() -> None:
    body = _section("mayak-db-bootstrap")
    assert re.search(
        r"(?ms)    depends_on:\n      mayak-postgres:\n"
        r"        condition: service_healthy\n",
        body,
    )


def test_migration_waits_for_postgres_and_bootstrap_completion() -> None:
    body = _section("mayak-migrate")
    assert re.search(
        r"(?ms)    depends_on:\n      mayak-postgres:\n"
        r"        condition: service_healthy\n      mayak-db-bootstrap:\n"
        r"        condition: service_completed_successfully\n",
        body,
    )


def test_application_services_have_migration_gate_and_no_elevated_secrets() -> None:
    text = _compose()
    for name, secret in (
        ("mayak-api", "mayak_database_application_password_runtime"),
        ("mayak-worker", "mayak_database_application_password_runtime"),
        ("mayak-scheduler", "mayak_database_application_password_runtime"),
    ):
        body = _section(name)
        assert "mayak-postgres:\n        condition: service_healthy" in body
        assert "mayak-migrate:\n        condition: service_completed_successfully" in body
        assert f"source: {secret}" in body
        assert "mayak_database_migration_password" not in body
        assert "mayak_postgres_bootstrap_password" not in body
        assert "mayak-db-bootstrap" not in body.split("depends_on:", 1)[-1].split("ports:", 1)[0]
        command = re.search(r"    command: (.+)", body)
        assert command is not None
        assert not re.search(
            r"alembic|bootstrap|create table|alter table|create schema",
            command.group(1),
            re.I,
        )
    assert text.count("condition: service_completed_successfully") == 4


def test_project_isolation_and_exposure_boundaries_remain_closed() -> None:
    text = _compose()
    assert text.startswith("name: avito-mayak-acceptance\n")
    assert text.count("profiles: [runtime-foundation]") == 6
    assert "mayak-postgres" in _compose()
    postgres = _section("mayak-postgres")
    assert "ports:" not in postgres
    assert "127.0.0.1:${MAYAK_API_HOST_PORT:-18085}:8000/tcp" in _section("mayak-api")
    assert "internal: true" in text
    assert text.count("mayak-internal:") == 1
    assert text.count("postgres-data:") == 2
    assert "external:" not in text
    assert "docker.sock" not in text
    assert "MAYAK_AVITO_LIVE_ENABLED: \"false\"" in text
    assert "MAYAK_TELEGRAM_ENABLED: \"false\"" in text
    assert "MAYAK_MAX_ENABLED: \"false\"" in text
    assert "MAYAK_YOOKASSA_ENABLED: \"false\"" in text
    assert "MAYAK_EGRESS_AGENT_ENABLED: \"false\"" in text
    assert not re.search(
        r"(?m)^\s+(?:password|secret|token|key)\s*:\s*(?!file:|\$\{)[^\s]+",
        text,
        re.I,
    )
