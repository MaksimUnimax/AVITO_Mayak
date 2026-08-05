#!/usr/bin/env bash
set -Eeuo pipefail

TECHNICAL_ID="RF23-CROSS-MODULE-API-COMMAND-WIRING-01-CORRECTIVE-05"
OWNER_LABEL="${RF20_POSTGRES_OWNER_LABEL:-${TECHNICAL_ID}}"
IMAGE="${RF23_RUNNER_IMAGE:-mayak-rf23-acceptance-runner:python3.14.6-uv0.11.31}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

redact() { sed -E 's#(postgresql\+?[^:]*://[^:]+:)[^@]+@#\1<redacted>@#g'; }
die() { echo "RF23 acceptance failed: $*" >&2; exit 1; }

host_docker_capability_preflight() {
  test -S /var/run/docker.sock || die "Docker socket unavailable"

  local client_version server_version client_api server_api
  client_version="$(docker version --format '{{.Client.Version}}')" || die "Docker daemon did not answer version request"
  server_version="$(docker version --format '{{.Server.Version}}')" || die "Docker server version unavailable"
  client_api="$(docker version --format '{{.Client.APIVersion}}')" || die "Docker client API version unavailable"
  server_api="$(docker version --format '{{.Server.APIVersion}}')" || die "Docker server API version unavailable"
  test -n "$client_version" || die "Docker client version is empty"
  test -n "$server_version" || die "Docker server version is empty"
  test -n "$client_api" || die "Docker client API version is empty"
  test -n "$server_api" || die "Docker server API version is empty"
  docker info >/dev/null || die "Docker daemon info request failed"
  local buildx_version
  buildx_version="$(docker buildx version | sed -n 's/.*buildx \(v[^ ]*\).*/\1/p')"
  test -n "$buildx_version" || die "Docker buildx version is empty"
  printf 'HOST_DOCKER_CLIENT_VERSION=%s\nHOST_DOCKER_BUILDX_VERSION=%s\nHOST_DOCKER_SERVER_VERSION=%s\nHOST_DOCKER_CLIENT_API_VERSION=%s\nHOST_DOCKER_SERVER_API_VERSION=%s\n' \
    "$client_version" "$buildx_version" "$server_version" "$client_api" "$server_api"
}

acceptance_runner_toolchain_preflight() {
  test -S /var/run/docker.sock || die "Docker socket unavailable inside acceptance runner"
  test "$(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')" = "3.14.6" \
    || die "unexpected acceptance-runner Python version"
  uv --version | grep -Fx 'uv 0.11.31 (x86_64-unknown-linux-musl)' >/dev/null \
    || die "unexpected acceptance-runner uv version"
  local client_version server_version client_api server_api buildx_version
  client_version="$(docker version --format '{{.Client.Version}}')" || die "Docker daemon did not answer version request"
  server_version="$(docker version --format '{{.Server.Version}}')" || die "Docker server version unavailable"
  client_api="$(docker version --format '{{.Client.APIVersion}}')" || die "Docker client API version unavailable"
  server_api="$(docker version --format '{{.Server.APIVersion}}')" || die "Docker server API version unavailable"
  test "$client_version" = "29.2.1" || die "unexpected acceptance-runner Docker client: $client_version"
  buildx_version="$(docker buildx version | sed -n 's/.*buildx \(v[^ ]*\).*/\1/p')"
  test "$buildx_version" = "v0.31.1" || die "unexpected acceptance-runner buildx client: $buildx_version"
  test -n "$server_version" -a -n "$client_api" -a -n "$server_api" \
    || die "acceptance-runner Docker server/API evidence is incomplete"
  docker info >/dev/null || die "acceptance-runner Docker API negotiation failed"
  printf 'RUNNER_DOCKER_CLIENT_VERSION=%s\nRUNNER_DOCKER_BUILDX_VERSION=%s\nRUNNER_OBSERVED_SERVER_VERSION=%s\nRUNNER_OBSERVED_SERVER_API_VERSION=%s\n' \
    "$client_version" "$buildx_version" "$server_version" "$server_api"
}

docker_capability_probe() (
  set -Eeuo pipefail
  local suffix="${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}-$(date +%s%N)"
  local network="rf23-capability-network-$suffix"
  local volume="rf23-capability-volume-$suffix"
  local container="rf23-capability-container-$suffix"
  cleanup() {
    docker rm -f "$container" >/dev/null 2>&1 || true
    docker volume rm "$volume" >/dev/null 2>&1 || true
    docker network rm "$network" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT
  docker network create --label com.avito-mayak.technical-id="$TECHNICAL_ID" --label com.avito-mayak.project-owned=true "$network" >/dev/null
  docker network inspect "$network" >/dev/null
  docker volume create --label com.avito-mayak.technical-id="$TECHNICAL_ID" --label com.avito-mayak.project-owned=true "$volume" >/dev/null
  docker volume inspect "$volume" >/dev/null
  docker create --name "$container" --network "$network" \
    --mount "type=volume,src=$volume,dst=/tmp/rf23-capability" \
    --mount type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
    "$IMAGE" -c 'test -S /var/run/docker.sock && test -d /tmp/rf23-capability' >/dev/null
  docker start -a "$container" >/dev/null
  docker inspect "$container" >/dev/null
)

run_inside() {
  export PYTHONPATH=.
  export MAYAK_RUNTIME_PROFILE=synthetic_acceptance
  export MAYAK_ENVIRONMENT_ID=avito-mayak-rf23-c05
  export MAYAK_DATABASE_HOST=mayak-postgres MAYAK_DATABASE_PORT=5432
  export MAYAK_DATABASE_NAME=mayak
  export MAYAK_DATABASE_APPLICATION_USER=mayak_application
  export MAYAK_DATABASE_MIGRATION_USER=mayak_migration
  export MAYAK_SYNTHETIC_IDENTITY_ENABLED=true MAYAK_IDENTITY_ADMIN_BOOTSTRAP_ENABLED=false
  export MAYAK_AVITO_LIVE_ENABLED=false MAYAK_TELEGRAM_ENABLED=false
  export MAYAK_TELEGRAM_UPDATE_MODE=disabled MAYAK_MAX_ENABLED=false MAYAK_MAX_UPDATE_MODE=disabled
  export MAYAK_YOOKASSA_ENABLED=false MAYAK_EGRESS_AGENT_ENABLED=false
  export MAYAK_API_BIND_HOST=127.0.0.1 MAYAK_API_HOST_PORT=disabled
  export RF20_POSTGRES_OWNER_LABEL="$OWNER_LABEL"
  export MAYAK_RF11_POSTGRES_PASSWORD_FILE=/run/secrets/mayak_database_migration_password
  local migration='postgresql+psycopg://mayak_migration:rf23_migration_synthetic@mayak-postgres:5432/mayak'
  local application='postgresql+psycopg://mayak_application:rf23_application_synthetic@mayak-postgres:5432/mayak'
  export RF10_POSTGRES_DSN="$migration" RF11_POSTGRES_DSN="$migration"
  export MAYAK_RF10_POSTGRES_DSN="$migration" MAYAK_RF11_POSTGRES_DSN="$migration"
  export RF12_ACCEPTANCE_DSN="$migration" RF15_MIGRATION_DSN="$migration" RF15_DSN="$migration"
  export RF17_MIGRATION_DSN="$migration" RF17_APPLICATION_DSN="$application"
  export RF18_MIGRATION_DSN="$migration" RF18_DATABASE_URL="$application"
  export RF19_MIGRATION_DSN="$migration" RF19_DATABASE_URL="$application"
  export RF20_MIGRATION_DSN="$migration" RF20_DATABASE_URL="$application"
  export RF21_MIGRATION_DSN="$migration" RF21_DSN="$application"
  export RF22_MIGRATION_DSN="$migration" RF22_DSN="$application" RF22_DATABASE_URL="$application"
  export RF23_MIGRATION_DSN="$migration" RF23_APPLICATION_DSN="$application" MAYAK_DATABASE_URL="$migration"

  python --version
  uv --version
  test "$(python -c 'import sys; print(sys.version_info[:3])')" = "(3, 14, 6)"
  uv --version | grep -Fx 'uv 0.11.31 (x86_64-unknown-linux-musl)'
  acceptance_runner_toolchain_preflight
  getent hosts mayak-postgres
  git rev-parse HEAD
  git diff --check
  uv sync --frozen --all-groups

  python - <<'PY'
import json, os, subprocess
owner = os.environ["RF20_POSTGRES_OWNER_LABEL"]
network = os.environ["RF23_NETWORK"]
db = os.environ["RF23_DB"]
items = json.loads(subprocess.check_output(["docker", "inspect", db], text=True))[0]
labels = items["Config"]["Labels"]
assert labels.get("com.mayak.owner") == owner
assert labels.get("com.avito-mayak.technical-id") == os.environ["RF23_TECHNICAL_ID"]
assert items["Config"]["Image"].startswith("postgres:18-bookworm")
assert items["HostConfig"].get("PortBindings") in (None, {})
assert items["NetworkSettings"].get("Ports", {}).get("5432/tcp") is None
networks = items["NetworkSettings"]["Networks"]
assert set(networks) == {network}
assert "mayak-postgres" in networks[network]["Aliases"]
assert networks[network]["IPAddress"]
members = json.loads(subprocess.check_output(["docker", "network", "inspect", network], text=True))[0]["Containers"]
postgres_members = []
for cid in members:
    candidate = json.loads(subprocess.check_output(["docker", "inspect", cid], text=True))[0]
    if candidate["Config"]["Image"].startswith("postgres:"):
        postgres_members.append(cid)
assert postgres_members == [db.removeprefix("/")] or len(postgres_members) == 1
print(json.dumps({"endpoint":"mayak-postgres:5432", "owner":owner, "network":network, "host_published":False}))
PY

  if ! uv run python -m mayak.persistence.bootstrap; then
    uv run python - <<'PY'
from mayak.persistence.bootstrap import bootstrap_database
try:
    bootstrap_database()
except Exception as exc:
    cause = exc.__cause__
    detail = f"; cause={type(cause).__name__}: {cause}" if cause is not None else ""
    raise SystemExit(f"bootstrap diagnostic: {type(exc).__name__}: {exc}{detail}") from None
PY
    exit 1
  fi
  uv run alembic upgrade head
  uv run python - <<'PY'
from sqlalchemy import create_engine, text
import os
e=create_engine(os.environ["RF15_MIGRATION_DSN"])
grants=(
"grant select on table mayak.alembic_version to mayak_application",
"grant select on table mayak.filter_catalog_versions, mayak.filter_definitions, mayak.filter_options, mayak.filter_dependencies, mayak.filter_category_applicability, mayak.filter_evidence_references, mayak.filter_capability_profiles to mayak_application",
"grant select, insert, update on table mayak.support_cases to mayak_application",
"grant select, insert on table mayak.support_case_notes, mayak.support_case_events to mayak_application",
"grant select, insert, update on table mayak.platform_idempotency_records to mayak_application",
"grant select, update, references on table mayak.identity_accounts to mayak_application",
"grant select on table mayak.identity_provider_links to mayak_application",
"grant select, insert, update on table mayak.identity_role_assignments to mayak_application",
"grant select, insert, update on table mayak.identity_sessions to mayak_application",
"grant select, insert on table mayak.platform_audit_entries to mayak_application",
"grant select, insert, update on table mayak.beacon_beacons, mayak.beacon_configuration_revisions, mayak.beacon_filter_overrides to mayak_application",
"grant select, insert, references on table mayak.beacon_lifecycle_events to mayak_application",
"grant select, insert on table mayak.entitlement_tariff_definitions to mayak_application",
"grant select, insert, update on table mayak.entitlement_access_grants to mayak_application",
"grant select on table mayak.notification_events, mayak.notification_outbox, mayak.notification_endpoints, mayak.notification_delivery_attempts, mayak.notification_delivery_reconciliations to mayak_application")
with e.begin() as c:
 c.execute(text("revoke all privileges on all tables in schema mayak from mayak_application")); c.execute(text("grant usage on schema mayak to mayak_application"))
 for g in grants: c.execute(text(g))
 c.execute(text("revoke all on all sequences in schema mayak from mayak_application"))
 assert c.execute(text("select current_user")).scalar_one()=="mayak_migration"
 assert c.execute(text("select not rolsuper from pg_roles where rolname='mayak_application'")).scalar_one()
 assert c.execute(text("select not has_schema_privilege('mayak_application','mayak','CREATE')")).scalar_one()
 assert c.execute(text("select version_num from mayak.alembic_version")).scalar_one()
PY
  uv run pytest -q tests/runtime/test_rf20_postgres_acceptance.py tests/runtime/test_rf20_postgres_topology.py tests/runtime/test_rf21_web_ui.py tests/runtime/test_rf23_api_contract.py tests/runtime/test_rf23_acceptance_chain.py tests/runtime/test_rf23_identity_bridge.py
  uv run pytest -q tests/unit/test_runtime_settings.py tests/runtime/test_persistence_transaction.py tests/runtime/test_platform_idempotency_repository_postgres.py tests/runtime/test_identity_runtime_postgres.py tests/runtime/test_rf18_telegram_adapter_postgres.py tests/runtime/test_rf22_filter_catalog_runtime.py
  uv run pytest -q tests/architecture/test_rf23_transport_boundary.py
  uv run ruff check src/mayak/modules/identity_and_access/__init__.py src/mayak/modules/identity_and_access/runtime.py src/mayak/runtime/rf20_acceptance_scenario.py src/mayak/runtime/rf20_composition.py src/mayak/runtime/rf21_composition.py src/mayak/runtime/rf23_composition.py scripts/runtime/run_rf23_postgres_acceptance.py scripts/runtime/check_rf23_artifact_safety.py scripts/runtime/verify_rf23_acceptance.py scripts/runtime/probe_rf23_runtime.py tests/architecture/test_rf23_transport_boundary.py tests/runtime/test_rf23_identity_bridge.py
  uv run mypy src/mayak/modules/identity_and_access src/mayak/runtime/rf20_acceptance_scenario.py src/mayak/runtime/rf20_composition.py src/mayak/runtime/rf21_composition.py src/mayak/runtime/rf23_composition.py scripts/runtime/run_rf23_postgres_acceptance.py scripts/runtime/check_rf23_artifact_safety.py scripts/runtime/verify_rf23_acceptance.py scripts/runtime/probe_rf23_runtime.py tests/architecture/test_rf23_transport_boundary.py tests/runtime/test_rf23_identity_bridge.py
  uv run lint-imports
  uv run pytest -q tests/runtime/test_rf08_safe_compose_bootstrap.py::test_build_input_digest_follows_copy_inputs_and_includes_readme

  git status --short --branch | tee rf23-local-status.log
  if [[ "${RF23_RESUME_AFTER_FULL:-0}" == 1 ]]; then
    test -s rf23-full-pytest.log
  else
    uv run pytest -q 2>&1 | tee rf23-full-pytest.log
  fi
  final_summary="$(grep -E '^[0-9][0-9,]* passed.* in [0-9.]+s' rf23-full-pytest.log | tail -1)"
  [[ -n "$final_summary" ]] || die "pytest terminal summary missing"
  [[ "$final_summary" != *failed* && "$final_summary" != *error* ]] || die "pytest terminal summary is not green"

  # The broad suite may deliberately clear fixture rows.  Seed only the
  # migration-owned synthetic identity immediately before the live probe.
  uv run python - <<'PY'
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timezone
e=create_engine(os.environ["RF15_MIGRATION_DSN"])
account="00000000-0000-0000-0000-000000000023"
now=datetime.now(timezone.utc)
with e.begin() as c:
 c.execute(text("insert into mayak.identity_accounts (id,state,created_at,updated_at) values (:id,'ACTIVE',:now,:now) on conflict (id) do nothing"), {"id":account,"now":now})
 c.execute(text("insert into mayak.identity_provider_links (id,account_id,provider_code,provider_subject,state,created_at,updated_at) values ('00000000-0000-0000-0000-000000000024',:id,'SYNTHETIC_ACCEPTANCE','rf23-probe','VERIFIED',:now,:now) on conflict (provider_code,provider_subject) do nothing"), {"id":account,"now":now})
 row=c.execute(text("select count(*) from mayak.identity_provider_links where provider_code='SYNTHETIC_ACCEPTANCE' and provider_subject='rf23-probe'")).scalar_one()
 assert row == 1, row
PY

  env -u MAYAK_DATABASE_URL -u MAYAK_RF10_POSTGRES_DSN -u MAYAK_RF11_POSTGRES_DSN \
    -u MAYAK_RF11_POSTGRES_PASSWORD_FILE \
    MAYAK_PROCESS_KIND=mayak-api MAYAK_SOURCE_SHA="$(git rev-parse HEAD)" \
    MAYAK_LOCK_IDENTITY="$(sha256sum uv.lock | cut -d' ' -f1)" \
    MAYAK_IMAGE_DIGEST="sha256:$(sha256sum Dockerfile | cut -d' ' -f1)" \
    uv run python -m mayak.runtime.api > rf23-api.log 2>&1 &
  api_pid=$!; trap 'kill "$api_pid" 2>/dev/null || true' EXIT
  for _ in $(seq 1 40); do curl -fsS http://127.0.0.1:8000/health/live >/dev/null && break || sleep 1; done
  uv run python scripts/runtime/probe_rf23_runtime.py rf23-runtime-probes.json --base-url http://127.0.0.1:8000 --repo-root .
  uv run python scripts/runtime/run_rf23_postgres_acceptance.py rf23-evidence.json --repo-root . --pytest-log rf23-full-pytest.log --runtime-probe rf23-runtime-probes.json
  uv run python scripts/runtime/check_rf23_artifact_safety.py rf23-evidence.json rf23-full-pytest.log rf23-runtime-probes.json --manifest rf23-safety-manifest.json --repo-root .
  uv run python scripts/runtime/verify_rf23_acceptance.py rf23-evidence.json --expected-sha "$(git rev-parse HEAD)" --expected-tree "$(git rev-parse HEAD^{tree})" --manifest rf23-safety-manifest.json --pytest-log rf23-full-pytest.log
}

if [[ "${1:-}" == "--inside-runner" ]]; then
  run_inside
  exit 0
fi

command -v docker >/dev/null || die "Docker CLI unavailable"
host_docker_capability_preflight
docker build -f "$ROOT/docker/rf23-acceptance-runner.Dockerfile" -t "$IMAGE" "$ROOT"
export RF23_TECHNICAL_ID="$TECHNICAL_ID"
export RF23_NETWORK="rf23-c05-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}-$(date +%s)"
export RF23_DB="rf23-c05-postgres-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
export RF23_RUNNER="rf23-c05-runner-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
docker_capability_probe
SECRETS="$(mktemp -d /tmp/rf23-c05-secrets.XXXXXX)"; chmod 700 "$SECRETS"
cleanup() {
  docker rm -f "$RF23_RUNNER" "$RF23_DB" >/dev/null 2>&1 || true
  docker network rm "$RF23_NETWORK" >/dev/null 2>&1 || true
  find "$SECRETS" -type f -delete; find "$SECRETS" -depth -type d -empty -delete
}
trap cleanup EXIT
printf '%s\n' rf23_bootstrap_synthetic > "$SECRETS/mayak_postgres_bootstrap_password"; chmod 600 "$SECRETS/mayak_postgres_bootstrap_password"
printf '%s\n' rf23_migration_synthetic > "$SECRETS/mayak_database_migration_password"; chmod 600 "$SECRETS/mayak_database_migration_password"
printf '%s\n' rf23_application_synthetic > "$SECRETS/mayak_database_application_password"; chmod 600 "$SECRETS/mayak_database_application_password"
docker network create --label com.avito-mayak.technical-id="$TECHNICAL_ID" --label com.avito-mayak.project-owned=true "$RF23_NETWORK" >/dev/null
docker run -d --name "$RF23_DB" --network "$RF23_NETWORK" --network-alias mayak-postgres \
  --label com.avito-mayak.technical-id="$TECHNICAL_ID" --label com.avito-mayak.project-owned=true --label com.mayak.owner="$OWNER_LABEL" \
  --mount type=bind,src="$SECRETS/mayak_postgres_bootstrap_password",dst=/run/secrets/postgres_password,readonly \
  -e POSTGRES_DB=mayak -e POSTGRES_USER=mayak -e POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password \
  --health-cmd 'pg_isready -U mayak -d mayak' --health-interval=2s --health-timeout=3s --health-retries=60 \
  postgres:18-bookworm@sha256:1961f96e6029a02c3812d7cb329a3b03a3ac2bb067058dec17b0f5596aca9296 >/dev/null
for _ in $(seq 1 60); do [[ "$(docker inspect -f '{{.State.Health.Status}}' "$RF23_DB")" == healthy ]] && break; sleep 2; done
[[ "$(docker inspect -f '{{.State.Health.Status}}' "$RF23_DB")" == healthy ]] || die "postgres did not become healthy"
docker run --name "$RF23_RUNNER" --network "$RF23_NETWORK" --user "$(id -u):$(id -g)" \
  --add-host host.docker.internal:host-gateway --mount type=bind,src="$ROOT",dst=/workspace \
  --mount type=bind,src="$ROOT",dst="$ROOT",readonly \
  --mount type=bind,src=/opt/avito-mayak,dst=/opt/avito-mayak,readonly \
  --mount type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
  --mount type=bind,src="$SECRETS",dst=/run/secrets,readonly \
  -e RF23_NETWORK -e RF23_DB -e RF23_TECHNICAL_ID -e RF20_POSTGRES_OWNER_LABEL="$OWNER_LABEL" \
  -e RF23_RESUME_AFTER_FULL="${RF23_RESUME_AFTER_FULL:-0}" \
  -e UV_PROJECT_ENVIRONMENT=/opt/rf23-venv "$IMAGE" /workspace/scripts/runtime/run_rf23_acceptance_chain.sh --inside-runner 2>&1 | redact
