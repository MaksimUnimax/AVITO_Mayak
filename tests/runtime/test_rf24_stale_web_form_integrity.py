from __future__ import annotations

import copy

import pytest

from scripts.runtime.verify_rf24_stale_web_form import verify
from tests.runtime.test_rf24_stale_web_form_core import _evidence


@pytest.mark.parametrize(
    "mutation",
    [
        lambda d: d["phases"].pop(),
        lambda d: d["phases"].__setitem__(1, {"phase": "S0"}),
        lambda d: d["identity"].__setitem__("source_sha", "b" * 40),
        lambda d: d["summary"].__setitem__("stale_revision_delta", 1),
        lambda d: d["summary"].__setitem__("credential_exposure", True),
    ],
)
def test_adversarial_mutation_is_rejected(mutation) -> None:
    data = copy.deepcopy(_evidence())
    mutation(data)
    with pytest.raises(AssertionError):
        verify(data, "a" * 40)
