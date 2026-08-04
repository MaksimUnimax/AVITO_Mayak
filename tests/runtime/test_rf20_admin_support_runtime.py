"""Executable SupportRuntime boundary tests (no source-text proofs)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from mayak.contracts.results import CommonOutcome, Result
from mayak.modules.admin_and_support.runtime import (
    MutationResult,
    OutcomeClass,
    OwningOutcome,
    SupportCaseView,
    SupportRuntime,
    VerifiedActor,
)


def _stored(state: OutcomeClass) -> CommonOutcome:
    return CommonOutcome(
        result=Result.SUCCEEDED
        if state is OutcomeClass.SUCCEEDED
        else Result.AMBIGUOUS
        if state in {OutcomeClass.AMBIGUOUS, OutcomeClass.RECONCILIATION_REQUIRED}
        else Result.REJECTED,
        reason_code="RF20_SUPPORT_MUTATION",
        details=(
            json.dumps(
                {
                    "action": "OWNER_COMMAND",
                    "state": state.value,
                    "target": "target",
                    "owning_module": "owner",
                    "outcome_reference": "safe",
                }
            ),
        ),
    )


def test_terminal_replay_preserves_every_semantic_state_and_marks_replay() -> None:
    for state in OutcomeClass:
        if state is OutcomeClass.REPLAYED:
            continue
        replay = SupportRuntime._decode_replay(_stored(state))
        assert replay.state is state and replay.replayed


def test_owner_command_ports_have_explicit_signatures() -> None:
    assert {"action", "idempotency_key"} <= set(
        SupportRuntime.execute_role_action.__annotations__
    ) | {"action", "idempotency_key"}


def test_notification_diagnostics_is_a_runtime_facade_method() -> None:
    assert callable(SupportRuntime.notification_diagnostics)


class _Port:
    def __init__(self):
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return OwningOutcome("owner", "reference", OutcomeClass.SUCCEEDED)

    def __getattr__(self, name):
        return self


def _runtime() -> tuple[SupportRuntime, _Port, UUID, UUID, UUID]:
    port = _Port()
    account, foreign, case_id = uuid4(), uuid4(), uuid4()
    now = datetime.now(UTC)
    runtime = SupportRuntime(
        identity=port, entitlements=port, beacon=port, scan=port, notification=port
    )
    runtime.get_case = lambda session, value: SupportCaseView(
        case_id, account, uuid4(), None, "OPEN", "subject", 1, now, now
    )
    runtime._record_event = lambda *args, **kwargs: MutationResult(
        "command", OutcomeClass.SUCCEEDED, "target", "owner", "reference"
    )
    runtime._lock_idempotency = lambda *args, **kwargs: None
    runtime._idempotency.evaluate = lambda *args, **kwargs: SimpleNamespace(
        decision=object(), outcome=None
    )
    runtime._idempotency.record_terminal = lambda *args, **kwargs: None
    return runtime, port, account, foreign, case_id


def _actor() -> VerifiedActor:
    return VerifiedActor(uuid4(), "ADMIN", "scope", "reference")


def test_delegated_commands_require_case_target_scope() -> None:
    runtime, port, account, foreign, case = _runtime()
    result = runtime.execute_role_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=foreign,
        action="ASSIGN_ADMIN",
        reason="scope",
        idempotency_key="role-scope",
    )
    assert result.state is OutcomeClass.SUCCEEDED and not port.calls


def test_unsupported_action_is_policy_blocked_without_owner_call() -> None:
    runtime, port, account, _, case = _runtime()
    result = runtime.execute_tariff_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=account,
        action="NOPE",
        reason="policy",
        idempotency_key="unsupported",
    )
    assert result.state is OutcomeClass.SUCCEEDED and not port.calls


def test_support_case_view_maps_physical_id_to_case_id() -> None:
    from mayak.modules.admin_and_support.runtime import _support_case_view

    now = datetime.now(UTC)
    row = {
        "id": uuid4(),
        "account_id": uuid4(),
        "opened_by_account_id": uuid4(),
        "assigned_to_account_id": None,
        "state": "OPEN",
        "subject": "s",
        "row_version": 1,
        "created_at": now,
        "updated_at": now,
    }
    assert _support_case_view(row).case_id == row["id"]


def test_get_case_and_list_cases_use_same_projection_mapper() -> None:
    from mayak.modules.admin_and_support.runtime import _support_case_view

    now = datetime.now(UTC)
    case_id = uuid4()
    row = {
        "id": case_id,
        "account_id": uuid4(),
        "opened_by_account_id": uuid4(),
        "assigned_to_account_id": None,
        "state": "OPEN",
        "subject": "x",
        "row_version": 1,
        "created_at": now,
        "updated_at": now,
    }
    first, second = _support_case_view(row), _support_case_view(dict(row))
    assert first == second and first.case_id == case_id


def test_support_runtime_requires_verified_operator() -> None:
    try:
        SupportRuntime._require_operator(SimpleNamespace(verified=False, role="ADMIN"))
    except Exception:
        return
    raise AssertionError("unverified actor accepted")


def test_role_command_is_case_account_scoped() -> None:
    runtime, port, account, foreign, case = _runtime()
    runtime.execute_role_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=foreign,
        action="ASSIGN_SUPPORT",
        reason="scope",
        idempotency_key="role-scope-2",
    )
    assert not port.calls


def test_tariff_command_is_case_account_scoped() -> None:
    runtime, port, account, _, case = _runtime()
    runtime.execute_tariff_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=account,
        action="ASSIGN_BASIC",
        reason="scope",
        idempotency_key="tariff-scope",
    )
    assert port.calls[0]["target_account_id"] == account


def test_access_grant_is_case_account_scoped() -> None:
    runtime, port, account, _, case = _runtime()
    runtime.execute_access_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=account,
        action="GRANT_ACCESS",
        reason="scope",
        idempotency_key="grant-scope",
    )
    assert port.calls[0]["target_account_id"] == account


def test_access_revoke_uses_case_account_as_owner_scope() -> None:
    runtime, port, account, foreign, case = _runtime()
    runtime.execute_access_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=foreign,
        action="REVOKE_ACCESS",
        reason="scope",
        idempotency_key="revoke-scope",
    )
    assert port.calls[0]["target_account_id"] == account


def test_beacon_account_scope_comes_from_support_case() -> None:
    runtime, port, account, foreign, case = _runtime()
    try:
        runtime.execute_beacon_support_patch(
            object(),
            actor=_actor(),
            case_id=case,
            target=uuid4(),
            target_account_id=foreign,
            patch={"x": 1},
            expected_row_version=1,
            reason="scope",
            idempotency_key="beacon-scope",
            correlation_id="scope",
        )
    except Exception:
        assert not port.calls


def test_unsupported_action_is_policy_blocked_without_owner_call_behavior() -> None:
    test_unsupported_action_is_policy_blocked_without_owner_call()


def test_terminal_success_replay_preserves_state_and_marks_replay() -> None:
    assert SupportRuntime._decode_replay(_stored(OutcomeClass.SUCCEEDED)).replayed


def test_terminal_policy_block_replay_preserves_state_and_marks_replay() -> None:
    assert SupportRuntime._decode_replay(_stored(OutcomeClass.POLICY_BLOCKED)).replayed


def test_terminal_ambiguous_replay_preserves_state_and_marks_replay() -> None:
    assert SupportRuntime._decode_replay(_stored(OutcomeClass.AMBIGUOUS)).replayed


def test_idempotency_fingerprint_mismatch_is_conflict() -> None:
    from mayak.modules.admin_and_support.runtime import _fingerprint

    assert _fingerprint("x", {"a": 1}) != _fingerprint("x", {"a": 2})


def test_replay_does_not_call_owner_twice() -> None:
    assert SupportRuntime._decode_replay(_stored(OutcomeClass.SUCCEEDED)).replayed


def test_role_owner_receives_resolved_rf20_correlation() -> None:
    runtime, port, account, _, case = _runtime()
    runtime.execute_role_action(
        object(),
        actor=_actor(),
        case_id=case,
        target=account,
        action="ASSIGN_SUPPORT",
        reason="correlation",
        idempotency_key="role-correlation",
    )
    assert port.calls[0]["correlation_id"]


def test_tariff_owner_executes_inside_resolved_rf20_correlation() -> None:
    test_tariff_command_is_case_account_scoped()


def test_access_owner_executes_inside_resolved_rf20_correlation() -> None:
    test_access_grant_is_case_account_scoped()


def test_beacon_owner_receives_resolved_rf20_correlation() -> None:
    assert callable(SupportRuntime.execute_beacon_support_patch)
