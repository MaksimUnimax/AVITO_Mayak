from __future__ import annotations

import pytest

from scripts.runtime.run_rf24_backup_restore import (
    RECOVERY_STAGE_SEQUENCE,
    execute_recovery_stage_sequence,
)


def test_recovery_stage_sequence_reaches_archive_restore_replay_and_evidence() -> None:
    reached: list[str] = []
    operations = {
        stage: (lambda stage=stage: reached.append(stage))
        for stage in RECOVERY_STAGE_SEQUENCE
    }
    assert execute_recovery_stage_sequence(operations) == list(RECOVERY_STAGE_SEQUENCE)
    assert reached.index("pg_dump") < reached.index("restore")
    assert reached.index("restore") < reached.index("replay") < reached.index("evidence")


def test_recovery_stage_sequence_fails_closed_when_a_stage_is_not_wired() -> None:
    operations = {stage: (lambda: None) for stage in RECOVERY_STAGE_SEQUENCE}
    del operations["clean_target"]
    with pytest.raises(ValueError, match="clean_target"):
        execute_recovery_stage_sequence(operations)
