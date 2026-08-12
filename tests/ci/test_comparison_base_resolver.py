from __future__ import annotations

import pytest

from scripts.ci.resolve_comparison_base import resolve


SHA = "1" * 40


def test_pull_request_uses_exact_base() -> None:
    assert resolve("pull_request", pull_request_base=SHA, push_before="2" * 40) == SHA


def test_push_requires_before() -> None:
    assert resolve("push", push_before=SHA) == SHA


def test_manual_requires_explicit_input() -> None:
    assert resolve("workflow_dispatch", manual_base=SHA) == SHA


@pytest.mark.parametrize("event", ["pull_request", "push", "workflow_dispatch"])
@pytest.mark.parametrize("value", ["", "0" * 40, "a" * 39, "not-a-sha"])
def test_invalid_base_fails_closed(event: str, value: str) -> None:
    with pytest.raises(ValueError):
        resolve(event, pull_request_base=value, push_before=value, manual_base=value)
