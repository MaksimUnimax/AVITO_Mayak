from __future__ import annotations

from pathlib import Path

from scripts.runtime.check_rf24_stale_web_form_ownership import check


def test_stale_web_acceptance_has_no_direct_foreign_dml_or_provider_authority() -> None:
    assert check(Path(__file__).parents[2]) == []
