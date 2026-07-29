from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from mayak.modules.identity_and_access.contracts import (
    IdentityProvider,
    ProviderIdentityClaim,
)
from mayak.modules.identity_and_access.runtime import (
    FakeProviderIdentityVerifier,
    ProviderVerificationOutcome,
)


def test_provider_claim_is_untrusted_and_bounded() -> None:
    ProviderIdentityClaim(provider=IdentityProvider.TELEGRAM, provider_subject="opaque")
    assert "verified" not in ProviderIdentityClaim.model_fields
    with pytest.raises(ValidationError):
        ProviderIdentityClaim.model_validate(
            {"provider": "SYNTHETIC_ACCEPTANCE", "provider_subject": "x"}
        )
    with pytest.raises(ValidationError):
        ProviderIdentityClaim.model_validate(
            {"provider": "TELEGRAM", "provider_subject": "x", "verified": True}
        )


def test_verifier_is_the_only_source_of_verified_outcome() -> None:
    claim = ProviderIdentityClaim(provider=IdentityProvider.MAX, provider_subject="opaque")
    verifier = FakeProviderIdentityVerifier(
        {
            (IdentityProvider.MAX, "opaque"): ProviderVerificationOutcome(
                "VERIFIED", IdentityProvider.MAX, "opaque", "fake-ref"
            )
        }
    )
    assert verifier.verify(claim).status == "VERIFIED"
    assert verifier.calls == [claim]


def test_raw_secret_and_issued_session_are_not_public_contracts() -> None:
    import mayak.modules.identity_and_access as package
    import mayak.modules.identity_and_access.contracts as contracts

    assert not hasattr(contracts, "SecretSessionToken")
    assert "SecretSessionToken" not in contracts.__all__
    assert "IssuedSession" not in package.__all__
    assert uuid4()  # keep this test independent of persistence setup
