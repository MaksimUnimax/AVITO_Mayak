# ruff: noqa: E501

from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "rf12_usage_producer", Path(__file__).parents[2] / "scripts/runtime/run_rf12_postgres_acceptance.py"
)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_safe_failure_message = _MODULE._safe_failure_message
_usage_policy_gate = _MODULE._usage_policy_gate


def _observation() -> dict:
    active_from = datetime(2026, 8, 2, 12, tzinfo=UTC).isoformat()
    evaluation_at = (datetime.fromisoformat(active_from) + timedelta(minutes=10)).isoformat()
    return {
        "evaluation_at": evaluation_at,
        "tariff_definitions": {
            "FREE": {"price_minor": 0, "currency": "RUB", "minimum_seconds": 10800, "step_seconds": 10800, "active_from": active_from},
            "BASIC": {"price_minor": 99000, "currency": "RUB", "minimum_seconds": 300, "step_seconds": 300, "active_from": active_from},
        },
        "free": {"minimum": 180, "step": 180, "active_beacon_limit": 1, "interval_180_allowed": True, "interval_179_allowed": False, "interval_181_allowed": False, "active_beacon": {"first": {"state": "RECORDED", "reason_code": "USAGE_RECORDED"}, "second": {"state": "REJECTED", "reason_code": "USAGE_LIMIT_REACHED"}, "usage_rows": [{"consumed": 1, "limit_value": 1}], "persisted_consumed": 1, "persisted_limit": 1}, "grant_interval": {"valid_from": evaluation_at, "valid_until": (datetime.fromisoformat(evaluation_at) + timedelta(days=1)).isoformat()}},
        "basic": {"minimum": 5, "step": 5, "valid_from": active_from, "valid_until": (datetime.fromisoformat(evaluation_at) + timedelta(days=1)).isoformat(), "interval_5_allowed": True, "interval_4_allowed": False, "interval_6_allowed": False, "numeric_beacon_limit_present": False},
        "paid_expiry": {"expired_valid_from": active_from, "expired_valid_until": evaluation_at, "pre_expiry_allowed": True, "effective_allowed": False, "payment_recorded": True, "post_payment_allowed": False},
    }


def test_usage_gate_requires_each_observed_contract_fact() -> None:
    observation = _observation()
    assert _usage_policy_gate(observation)
    for path in (("free", "interval_180_allowed"), ("free", "active_beacon", "persisted_consumed"), ("basic", "interval_5_allowed"), ("paid_expiry", "post_payment_allowed")):
        changed = observation
        target = changed
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = not target[path[-1]]
        assert not _usage_policy_gate(changed)
        observation = _observation()


def test_failure_message_is_bounded_and_redacts_connection_secrets() -> None:
    message = _safe_failure_message(ValueError("tariff authority missing password=secret postgres://user:pw@db/private token=abc"))
    assert len(message) <= 240
    assert "secret" not in message
    assert "postgres://" not in message
    assert "token=abc" not in message
    assert "tariff authority" in message
