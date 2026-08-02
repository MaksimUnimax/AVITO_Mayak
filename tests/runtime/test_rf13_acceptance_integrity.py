from __future__ import annotations

from scripts.runtime.run_rf13_tamper_matrix import REQUIRED_TAMPER_CASES
from scripts.runtime.verify_rf13_acceptance import (
    REQUIRED_ACCEPTANCE_REQUIREMENTS,
    REQUIRED_SECTIONS,
)


def test_every_acceptance_requirement_has_raw_assertion_and_tamper_case() -> None:
    assert REQUIRED_ACCEPTANCE_REQUIREMENTS
    for requirement_id, mapping in REQUIRED_ACCEPTANCE_REQUIREMENTS.items():
        assert mapping["raw"], requirement_id
        assert mapping["tamper"], requirement_id
        assert set(mapping["tamper"]) <= set(REQUIRED_TAMPER_CASES), requirement_id


def test_required_sections_are_substantive_v4_sections() -> None:
    assert "system_authority_mismatch_negative" in REQUIRED_SECTIONS
    assert "security_witness" in REQUIRED_SECTIONS
    assert "diagnostic_gates" not in REQUIRED_SECTIONS


def test_tamper_registry_is_nonempty_and_unique() -> None:
    assert len(REQUIRED_TAMPER_CASES) >= 70
    assert len(REQUIRED_TAMPER_CASES) == len(set(REQUIRED_TAMPER_CASES))
