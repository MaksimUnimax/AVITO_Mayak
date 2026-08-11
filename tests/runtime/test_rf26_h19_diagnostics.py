# ruff: noqa: E501
import json
from pathlib import Path

import pytest

from scripts.runtime.rf26_h19_diagnostics import MAX_FAILURES, parse_junit, write_diagnostic


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "results.xml"
    path.write_text(body, encoding="utf-8")
    return path


def test_successful_junit_parsing_and_identity(tmp_path: Path) -> None:
    report = _write(tmp_path, '<testsuite tests="2" failures="0" errors="0" skipped="1" time="1.25"><testcase classname="a" name="ok"/><testcase classname="a" name="skip"><skipped/></testcase></testsuite>')
    data = parse_junit(report, source_sha="a" * 40, run_id="123", job="rf26", attempt="1")
    assert data["diagnostic_generation_status"] == "ok"
    assert data["total_tests"] == 2 and data["passed"] == 1 and data["skipped"] == 1
    assert data["source_sha"] == "a" * 40 and data["github_run_id"] == "123"


def test_one_and_multiple_failures_are_bounded(tmp_path: Path) -> None:
    body = '<testsuite tests="2" failures="2" time="0.1"><testcase classname="pkg" name="one"><failure message="assertion failed"/></testcase><testcase classname="pkg" name="two"><failure message="different"/></testcase></testsuite>'
    data = parse_junit(_write(tmp_path, body))
    assert data["failed"] == 2
    assert data["failing_tests"] == ["pkg::one", "pkg::two"]
    assert data["exception_categories"] == ["pytest_failure"]

    cases = "".join(f'<testcase classname="pkg" name="case{i}"><failure message="bad"/></testcase>' for i in range(MAX_FAILURES + 5))
    bounded = parse_junit(_write(tmp_path, f'<testsuite tests="{MAX_FAILURES + 5}" failures="{MAX_FAILURES + 5}">{cases}</testsuite>'))
    assert len(bounded["failing_tests"]) == MAX_FAILURES


def test_collection_error_and_malformed_or_missing_input_fail_closed(tmp_path: Path) -> None:
    error = parse_junit(_write(tmp_path, '<testsuite tests="1" errors="1"><testcase classname="collect" name="error"><error message="collection error"/></testcase></testsuite>'))
    assert error["exception_categories"] == ["pytest_collection_or_error"]
    malformed = parse_junit(_write(tmp_path, "not xml"))
    missing = parse_junit(tmp_path / "missing.xml")
    assert malformed["diagnostic_generation_status"] == "fail_closed_input_error"
    assert missing["diagnostic_generation_status"] == "fail_closed_input_error"
    assert malformed["failing_tests"] == missing["failing_tests"] == []


@pytest.mark.parametrize(
    "message",
    [
        "postgresql://user:pw@db:5432/app",
        "https://user:pw@example.test/path",
        "password=synthetic-secret token=synthetic-token",
        "Authorization: Bearer synthetic-bearer",
        "Cookie: session=synthetic-session",
        "-----BEGIN RSA PRIVATE KEY-----",
        "MAYAK_SECRET_TOKEN=synthetic-provider-value",
        "line one\nline two\x00",
    ],
)
def test_adversarial_reasons_are_redacted_and_bounded(tmp_path: Path, message: str) -> None:
    data = parse_junit(_write(tmp_path, f'<testsuite tests="1" failures="1"><testcase classname="pkg" name="safe_test"><failure message={json.dumps(message)!r}/></testcase></testsuite>'))
    serialized = json.dumps(data)
    assert "synthetic-secret" not in serialized
    assert "synthetic-token" not in serialized
    assert "synthetic-bearer" not in serialized
    assert "synthetic-session" not in serialized
    assert "synthetic-provider-value" not in serialized
    assert len(data["redacted_reasons"][0]) <= 160


def test_oversized_message_and_safe_node_id_are_bounded(tmp_path: Path) -> None:
    long_message = "x" * 1000
    data = parse_junit(_write(tmp_path, f'<testsuite tests="1" failures="1"><testcase classname="pkg" name="safe"><failure message="{long_message}"/></testcase></testsuite>'))
    assert data["failing_tests"] == ["pkg::safe"]
    assert len(data["redacted_reasons"][0]) == 160


def test_output_is_json_and_contains_only_safe_generated_fields(tmp_path: Path) -> None:
    report = _write(tmp_path, '<testsuite tests="1" failures="1"><testcase classname="pkg" name="safe"><failure message="boom"/></testcase></testsuite>')
    output = tmp_path / "diagnostic.json"
    write_diagnostic(report, output, source_sha="b" * 40, run_id="456", job="rf26", attempt="1")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["technical_id"] == "RF26-OBSERVABILITY-BACKUP-RECOVERY-01"
    assert data["failing_tests"] == ["pkg::safe"]
    assert set(data) == {
        "schema_version", "technical_id", "source_sha", "github_run_id", "job", "attempt",
        "python_version", "uv_version", "total_tests", "passed", "failed", "skipped",
        "error_count", "duration", "failing_tests", "exception_categories", "redacted_reasons",
        "diagnostic_generation_status",
    }
