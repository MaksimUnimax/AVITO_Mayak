from __future__ import annotations

import pytest
from pydantic import ValidationError

from mayak.modules.scan_orchestration.contracts import ListingCandidate


def test_snapshot_accepts_normalized_nested_scalars_at_bound() -> None:
    candidate = ListingCandidate(
        identity_key="listing-1", snapshot={"title": "x", "price": 1, "tags": ["new", "used"]}
    )
    assert candidate.snapshot["price"] == 1


@pytest.mark.parametrize(
    "field", ["raw_body", "headers", "cookies", "token", "seller", "phone", "description", "views"]
)
def test_snapshot_rejects_provider_fields_recursively(field: str) -> None:
    with pytest.raises(ValidationError):
        ListingCandidate(identity_key="listing-1", snapshot={"nested": {field: "blocked"}})


def test_snapshot_rejects_non_json_value() -> None:
    with pytest.raises(ValidationError):
        ListingCandidate(identity_key="listing-1", snapshot={"value": object()})


def test_snapshot_rejects_oversized_utf8_json() -> None:
    with pytest.raises(ValidationError):
        ListingCandidate(identity_key="listing-1", snapshot={"title": "я" * 20000})
