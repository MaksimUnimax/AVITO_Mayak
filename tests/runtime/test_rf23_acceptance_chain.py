import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "scripts/runtime/check_rf23_artifact_safety.py"
VERIFY = ROOT / "scripts/runtime/verify_rf23_acceptance.py"


def _evidence() -> dict[str, object]:
    return {
        "technical_id": "RF23-CROSS-MODULE-API-COMMAND-WIRING-01-CORRECTIVE-01",
        "candidate_sha": "a" * 40,
        "candidate_tree_identity": "b" * 40,
        "observation_source": "live_http_and_process_local_git",
        "producer_result": "PASS",
        "postgres_major": 18,
        "migration_current_user": "mayak_migration",
        "application_current_user": "mayak_application",
        "migration_revision": "rf23_head",
        "pytest_log_sha256": "",
        "route_inventory": ["/health/live", "/health/ready", "/version", "/acceptance/login"],
        "health": {"status": 200},
        "readiness": {"status": 200},
        "version": {"status": 200},
        "authentication_outcomes": "proven",
        "authorization_outcomes": "proven",
        "idempotency": "proven",
        "idempotency_conflict_outcome": "proven",
        "cross_account_denial": "proven",
        "unauthorized_admin_mutation": "proven",
        "explicit_http_error_mapping": "proven",
        "optional_provider_state": "disabled",
        "filter_catalog_beacon_mutations": 0,
        "provider_calls": 0,
        "direct_transport_dml": 0,
        "foreign_table_mutation": 0,
        "fastapi_background_durable_work": 0,
        "duplicate_domain_effect_count": 0,
        "foreign_resource_impact": 0,
        "api_host_published_bind": "127.0.0.1",
        "postgres_host_published": 0,
        "container_user": "10001:10001",
        "container_root": False,
        "provider_mode": "disabled",
        "runtime_profile": "synthetic_acceptance",
        "db_loss_readiness": "unhealthy",
        "db_recovery_readiness": "healthy",
    }


def _run(
    tmp_path: Path, summary: str = "===== 1 passed, 0 skipped in 0.01s ====="
) -> tuple[Path, Path, Path]:
    evidence = tmp_path / "rf23-evidence.json"
    log = tmp_path / "rf23-full-pytest.log"
    manifest = tmp_path / "rf23-safety-manifest.json"
    evidence.write_text(json.dumps(_evidence()), encoding="utf-8")
    log.write_text(summary, encoding="utf-8")
    evidence_data = json.loads(evidence.read_text(encoding="utf-8"))
    evidence_data["pytest_log_sha256"] = hashlib.sha256(log.read_bytes()).hexdigest()
    evidence.write_text(json.dumps(evidence_data), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCAN), str(evidence), str(log), "--manifest", str(manifest)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return evidence, log, manifest


def _verify(evidence: Path, log: Path, manifest: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFY),
            str(evidence),
            "--expected-sha",
            "a" * 40,
            "--expected-tree",
            "b" * 40,
            "--manifest",
            str(manifest),
            "--pytest-log",
            str(log),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_rf23_verifier_accepts_only_bound_green_log_and_manifest(tmp_path: Path) -> None:
    evidence, log, manifest = _run(tmp_path)
    assert _verify(evidence, log, manifest).returncode == 0


def test_rf23_verifier_rejects_digest_valid_failing_log(tmp_path: Path) -> None:
    evidence, log, manifest = _run(tmp_path)
    log.write_text("===== 1 passed, 1 failed in 0.01s =====", encoding="utf-8")
    rerun = subprocess.run(
        [sys.executable, str(SCAN), str(evidence), str(log), "--manifest", str(manifest)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rerun.returncode == 0
    assert _verify(evidence, log, manifest).returncode != 0


def test_rf23_verifier_rejects_missing_log_and_manifest(tmp_path: Path) -> None:
    evidence, log, manifest = _run(tmp_path)
    log.unlink()
    assert _verify(evidence, log, manifest).returncode != 0
    evidence, log, manifest = _run(tmp_path)
    manifest.unlink()
    assert _verify(evidence, log, manifest).returncode != 0


def test_rf23_verifier_rejects_manifest_tamper_and_artifact_substitution(tmp_path: Path) -> None:
    evidence, log, manifest = _run(tmp_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["payloads"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(data), encoding="utf-8")
    assert _verify(evidence, log, manifest).returncode != 0
    evidence.write_text(json.dumps({"tampered": True}), encoding="utf-8")
    assert _verify(evidence, log, manifest).returncode != 0


def test_rf23_verifier_rejects_complete_material_adversarial_matrix(tmp_path: Path) -> None:
    """Every material producer claim is independently fail-closed."""
    mutations = {
        "wrong candidate SHA": ("candidate_sha", "c" * 40),
        "wrong tree identity": ("candidate_tree_identity", "d" * 40),
        "wrong PostgreSQL major": ("postgres_major", 17),
        "wrong migration role": ("migration_current_user", "postgres"),
        "wrong application role": ("application_current_user", "postgres"),
        "wrong migration revision": ("migration_revision", "stale"),
        "missing required route": ("route_inventory", ["/health/live"]),
        "acceptance login outside profile": ("runtime_profile", "production"),
        "unauthenticated protected route falsely accepted": ("authentication_outcomes", "failed"),
        "authorization falsely accepted": ("authorization_outcomes", "failed"),
        "cross-account denial flipped": ("cross_account_denial", "accepted"),
        "unauthorized Admin mutation flipped": ("unauthorized_admin_mutation", "accepted"),
        "idempotency key not required": ("idempotency", "not_required"),
        "same-key conflict flipped": ("explicit_http_error_mapping", "missing_conflict"),
        "same-key different-fingerprint conflict flipped": (
            "idempotency_conflict_outcome", "accepted"
        ),
        "duplicate domain effect count": ("duplicate_domain_effect_count", 1),
        "healthy readiness falsified": ("readiness", {"status": 500}),
        "DB-loss readiness falsely healthy": ("db_loss_readiness", "healthy"),
        "DB-recovery evidence missing": ("db_recovery_readiness", "not_observed"),
        "optional provider falsely enabled": ("optional_provider_state", "enabled"),
        "provider-call count nonzero": ("provider_calls", 1),
        "direct transport DML nonzero": ("direct_transport_dml", 1),
        "foreign-table mutation nonzero": ("foreign_table_mutation", 1),
        "FastAPI durable background work nonzero": ("fastapi_background_durable_work", 1),
        "Filter Catalog Beacon mutation": ("filter_catalog_beacon_mutations", 1),
        "API public host bind": ("api_host_published_bind", "0.0.0.0"),
        "PostgreSQL host-published": ("postgres_host_published", 1),
        "root application container": ("container_root", True),
        "foreign Docker mutation nonzero": ("foreign_resource_impact", 1),
        "failing pytest summary": ("log", "===== 1 failed in 0.01s ====="),
        "pytest errors summary": ("log", "===== 1 errors in 0.01s ====="),
        "missing pytest log": ("missing_log", None),
        "pytest-log digest mismatch": ("log", "===== 1 passed in 0.02s ====="),
        "missing scanner manifest": ("missing_manifest", None),
        "scanner-manifest digest mismatch": ("manifest_digest", None),
        "scanned-artifact substitution": ("artifact_substitution", None),
        "real sensitive finding inserted": ("sensitive", None),
        "producer artifact digest mismatch": ("producer_digest", None),
    }
    assert len(mutations) >= 35
    for case, (field, value) in mutations.items():
        case_dir = tmp_path / case.replace(" ", "_")
        case_dir.mkdir()
        evidence, log, manifest = _run(case_dir)
        if field == "log":
            log.write_text(value, encoding="utf-8")
            # A changed log is rejected by the old manifest binding.
        elif field == "missing_log":
            log.unlink()
        elif field == "missing_manifest":
            manifest.unlink()
        elif field == "manifest_digest":
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["payloads"][0]["sha256"] = "0" * 64
            manifest.write_text(json.dumps(data), encoding="utf-8")
        elif field == "artifact_substitution":
            evidence.write_text("{}", encoding="utf-8")
        elif field == "sensitive":
            data = json.loads(evidence.read_text(encoding="utf-8"))
            data["password"] = "secret"
            evidence.write_text(json.dumps(data), encoding="utf-8")
            subprocess.run(
                [sys.executable, str(SCAN), str(evidence), str(log), "--manifest", str(manifest)],
                check=False,
            )
        elif field == "producer_digest":
            data = json.loads(evidence.read_text(encoding="utf-8"))
            data["candidate_sha"] = "e" * 40
            evidence.write_text(json.dumps(data), encoding="utf-8")
        else:
            data = json.loads(evidence.read_text(encoding="utf-8"))
            data[field] = value
            evidence.write_text(json.dumps(data), encoding="utf-8")
        assert _verify(evidence, log, manifest).returncode != 0, case
