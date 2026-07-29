from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.modules.identity_and_access.contracts import (
    AuthSessionState,
    SafeSessionMetadata,
    SecretSessionToken,
    VerifiedProviderIdentity,
)


def test_secret_session_value_is_redacted() -> None:
    secret = SecretSessionToken("synthetic-only-token")
    assert repr(secret) == "SecretSessionToken(<redacted>)"
    assert str(secret) == "<redacted>"
    assert "synthetic-only-token" not in repr(secret)


def test_verified_provider_contract_is_frozen_and_extra_forbid() -> None:
    VerifiedProviderIdentity(
        provider="SYNTHETIC_ACCEPTANCE",
        provider_subject="opaque-subject",
        verified=True,
        verification_reference="acceptance-reference",
    )
    with pytest.raises(ValidationError):
        VerifiedProviderIdentity(
            provider="SYNTHETIC_ACCEPTANCE", provider_subject="opaque-subject",
            verified=True, verification_reference="acceptance-reference", unexpected="value",
        )


def test_session_metadata_is_safe_and_bounded_shape() -> None:
    value = SafeSessionMetadata(
        session_id=uuid4(), account_id=uuid4(), issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC), state=AuthSessionState.ACTIVE,
    )
    assert "token" not in value.model_dump_json().lower()
