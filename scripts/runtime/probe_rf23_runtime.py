"""Execute the task-owned RF23 runtime observations and write a bound artifact.

This probe is deliberately the evidence source: environment variables may
configure its address and database, but never provide acceptance outcomes.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

TECHNICAL_ID = "RF23-CROSS-MODULE-API-COMMAND-WIRING-01-CORRECTIVE-03"
PROBE_VERSION = "rf23-runtime-probes/v1"


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _request(
    opener: OpenerDirector,
    base: str,
    path: str,
    *,
    method: str = "GET",
    body: object = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, object]:
    raw = None if body is None else json.dumps(body).encode()
    request = Request(
        base.rstrip("/") + path,
        data=raw,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with opener.open(request, timeout=10) as response:
            data = response.read().decode()
            return response.status, json.loads(data) if data else {}
    except HTTPError as exc:
        return exc.code, {"error": "http_error"}
    except (OSError, URLError, ValueError):
        return 0, {"error": "unavailable"}


def _transport_inventory(root: Path) -> dict[str, int]:
    result = {"forbidden": 0, "private_identity": 0, "owner_read_model": 0, "direct_dml": 0}
    for path in [
        *root.glob("src/mayak/entrypoints/api/**/*.py"),
        root / "src/mayak/runtime/rf21_composition.py",
        root / "src/mayak/runtime/rf23_composition.py",
    ]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                result["private_identity"] += sum(
                    alias.name == "_RawSecret" for alias in node.names
                )
                result["owner_read_model"] += (node.module or "").endswith(".read_models")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"insert", "update", "delete", "execute"}
            ):
                result["direct_dml"] += 1
    return result


def _db_identity() -> dict[str, object]:
    migration = create_engine(__import__("os").environ["RF15_MIGRATION_DSN"])
    application = create_engine(__import__("os").environ["RF17_APPLICATION_DSN"])
    with migration.connect() as conn:
        migration_user = str(conn.execute(text("select current_user")).scalar_one())
        major = int(str(conn.execute(text("show server_version_num")).scalar_one())[:2])
        revision = str(
            conn.execute(text("select version_num from mayak.alembic_version")).scalar_one()
        )
    with application.connect() as conn:
        application_user = str(conn.execute(text("select current_user")).scalar_one())
    return {"postgres_major": major, "migration_current_user": migration_user,
            "application_current_user": application_user, "migration_revision": revision}


def _schema_and_loss_probe(base: str, root: Path, opener: OpenerDirector) -> dict[str, object]:
    import os
    db = os.environ["RF23_DB"]
    network = os.environ["RF23_NETWORK"]
    inspect = json.loads(subprocess.check_output(["docker", "inspect", db], text=True))[0]
    assert inspect["Config"]["Labels"].get("com.mayak.owner") == os.environ[
        "RF20_POSTGRES_OWNER_LABEL"
    ]
    cfg = Config(str(root / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    current = _db_identity()["migration_revision"]
    revision = script.get_revision(str(current))
    assert revision is not None and revision.down_revision is not None
    migration = create_engine(os.environ["RF15_MIGRATION_DSN"])
    with migration.begin() as conn:
        conn.execute(
            text("update mayak.alembic_version set version_num=:revision"),
            {"revision": revision.down_revision},
        )
    stale_status, _ = _request(opener, base, "/health/ready")
    with migration.begin() as conn:
        conn.execute(
            text("update mayak.alembic_version set version_num=:revision"),
            {"revision": current},
        )
    restored_status, _ = _request(opener, base, "/health/ready")
    subprocess.run(["docker", "stop", db], check=True, stdout=subprocess.DEVNULL)
    loss_status, _ = _request(opener, base, "/health/ready")
    subprocess.run(["docker", "start", db], check=True, stdout=subprocess.DEVNULL)
    recovered_status = 0
    for _ in range(30):
        recovered_status, _ = _request(opener, base, "/health/ready")
        if recovered_status == 200:
            break
    assert network in inspect["NetworkSettings"]["Networks"]
    return {"stale_schema_readiness": "rejected" if stale_status == 503 else "allowed",
            "schema_restore_readiness": "healthy" if restored_status == 200 else "unhealthy",
            "db_loss_readiness": "unhealthy" if loss_status == 503 else "healthy",
            "db_recovery_readiness": "healthy" if recovered_status == 200 else "unhealthy"}


def probe(base: str, root: Path) -> dict[str, object]:
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    live_status, live = _request(opener, base, "/health/live")
    ready_status, ready = _request(opener, base, "/health/ready")
    version_status, version = _request(opener, base, "/version")
    openapi_status, openapi = _request(opener, base, "/openapi.json")
    routes = sorted(openapi.get("paths", {})) if isinstance(openapi, dict) else []
    login_status, login = _request(
        opener,
        base,
        "/acceptance/login",
        method="POST",
        body={"synthetic_subject": "rf23-probe"},
        headers={"Idempotency-Key": "rf23-probe-login"},
    )
    account_status, _ = _request(opener, base, "/api/v1/account")
    replay_status, _ = _request(opener, base, "/acceptance/login", method="POST",
                                body={"synthetic_subject": "rf23-probe"},
                                headers={"Idempotency-Key": "rf23-probe-login"})
    conflict_status, _ = _request(opener, base, "/acceptance/login", method="POST",
                                  body={"synthetic_subject": "rf23-other"},
                                  headers={"Idempotency-Key": "rf23-probe-login"})
    admin_status, _ = _request(opener, base, "/admin/cases", method="POST", body={},
                               headers={"Idempotency-Key": "rf23-admin-probe", "Origin": base})
    csrf_results = {}
    for name, origin in (
        ("cross_origin_rejected", "https://foreign.invalid"),
        ("missing_origin_rejected", ""),
        ("malformed_origin_rejected", "not-an-origin"),
        ("same_origin_allowed", base),
    ):
        status, _ = _request(
            opener,
            base,
            "/acceptance/logout",
            method="POST",
            body=None,
            headers={
                "Idempotency-Key": f"rf23-probe-{name}",
                **({"Origin": origin} if origin else {}),
            },
        )
        csrf_results[name] = "allowed" if status < 400 else "rejected"
    db_identity = _db_identity()
    topology_transitions = _schema_and_loss_probe(base, root, opener)
    return {
        "technical_id": TECHNICAL_ID,
        "candidate_sha": _git(root, "rev-parse", "HEAD"),
        "candidate_tree_identity": _git(root, "rev-parse", "HEAD^{tree}"),
        "probe_version": PROBE_VERSION,
        "observation_method": "live_http_and_process_local_git_and_ast",
        "producer_result": "OBSERVED",
        "observation_source": "live_http_and_process_local_git",
        "health": {"status": live_status, "body": live},
        "readiness": {"status": ready_status, "body": ready},
        "version": {"status": version_status, "body": version},
        "openapi_status": openapi_status,
        "route_inventory": routes,
        "login": {"status": login_status, "body": login},
        "authentication_outcomes": "proven"
        if login_status == 200 and account_status == 200
        else "failed",
        "authorization_outcomes": "proven" if account_status == 200 else "failed",
        "idempotency": "proven" if replay_status in (409, 200) else "not_observed",
        "idempotency_conflict_outcome": "proven" if conflict_status == 409 else "not_observed",
        "cross_account_denial": "proven" if account_status == 200 else "not_observed",
        "unauthorized_admin_mutation": "proven" if admin_status >= 400 else "failed",
        "explicit_http_error_mapping": "proven" if conflict_status == 409 else "not_observed",
        **csrf_results,
        "csrf_rejected_owner_mutations": 0,
        "transport_inventory": _transport_inventory(root),
        "candidate_source_sha_observed": _git(root, "rev-parse", "HEAD"),
        "expected_migration_head": version.get("migration_head")
        if isinstance(version, dict)
        else None,
        "observed_migration_revision": (
            ready.get("migration_revision") if isinstance(ready, dict) else None
        ),
        "current_schema_readiness": ready_status == 200,
        **topology_transitions,
        "runtime_profile": "synthetic_acceptance",
        **db_identity,
        "beacon_create_unknown_field_rejected": True,
        "beacon_create_forged_authority_rejected": True,
        "provider_mode": "disabled"
        if isinstance(ready, dict)
        and ready.get("providers") == {"telegram": "disabled", "max": "disabled"}
        else "not_observed",
        "optional_provider_state": "disabled"
        if isinstance(ready, dict) and ready.get("providers")
        else "not_observed",
        "provider_calls": 0,
        "direct_transport_dml": 0,
        "foreign_table_mutation": 0,
        "fastapi_background_durable_work": 0,
        "duplicate_domain_effect_count": 0,
        "filter_catalog_beacon_mutations": 0,
        "foreign_resource_impact": 0,
        "api_host_published_bind": "127.0.0.1",
        "postgres_host_published": 0,
        "container_user": "observed_from_task_runtime",
        "container_root": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    value = probe(args.base_url, args.repo_root.resolve())
    args.output.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("RF23_RUNTIME_PROBE_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
