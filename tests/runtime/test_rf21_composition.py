from __future__ import annotations

from uuid import UUID

from mayak.modules.web_cabinet.runtime import VerifiedWebCustomer
from mayak.runtime.rf21_composition import (
    BeaconWebAdapter,
    EntitlementWebAdapter,
    IdentityWebAdapter,
    NotificationWebAdapter,
)

ACCOUNT = UUID("11111111-1111-1111-1111-111111111111")
SESSION = UUID("22222222-2222-2222-2222-222222222222")


class _Validation:
    account_id = ACCOUNT
    metadata = type("Meta", (), {"session_id": SESSION})()


class _Identity:
    def validate_session(self, session: object, reference: object) -> _Validation:
        assert reference == "opaque"
        return _Validation()


def test_identity_adapter_derives_account_only_from_owner_session() -> None:
    adapter = IdentityWebAdapter(_Identity())
    customer = adapter.resolve_session(object(), "opaque")
    assert customer is not None
    assert customer.account_id == ACCOUNT
    assert customer.authority_reference.startswith("identity-session:")


class _Beacon:
    def list(self, session: object, *, actor_reference: str) -> tuple[str, ...]:
        assert actor_reference.startswith("identity-session:")
        return ("owned-beacon",)

    def get(self, *args: object, **kwargs: object) -> object:
        return "owned-detail"

    def history(self, *args: object, **kwargs: object) -> tuple[str, ...]:
        return ("archive-event",)


def test_beacon_adapter_delegates_reads_to_owner() -> None:
    adapter = BeaconWebAdapter(_Beacon())
    customer = VerifiedWebCustomer(ACCOUNT, SESSION, "identity-session:verified")
    assert adapter.read(object(), customer) == ("owned-beacon",)


class _Entitlements:
    def evaluate_effective(self, session: object, account_id: UUID, *, at: object) -> str:
        assert account_id == ACCOUNT
        return "BASIC"


def test_entitlement_adapter_delegates_effective_access_to_owner() -> None:
    customer = VerifiedWebCustomer(ACCOUNT, SESSION, "identity-session:verified")
    assert EntitlementWebAdapter(_Entitlements()).read(object(), customer) == "BASIC"


def test_notification_adapter_keeps_account_scope() -> None:
    seen: list[UUID] = []

    def read(
        session: object, *, account_id: UUID, actor_account_id: UUID, limit: int
    ) -> tuple[str, ...]:
        seen.extend((account_id, actor_account_id))
        return ("history",)

    customer = VerifiedWebCustomer(ACCOUNT, SESSION, "identity-session:verified")
    assert NotificationWebAdapter(read).read(object(), customer) == ("history",)
    assert seen == [ACCOUNT, ACCOUNT]
