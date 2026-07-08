from __future__ import annotations

from importlib import import_module

from mayak.modules import identity_and_access as ia


def test_identity_and_access_package_exports_semantic_primitives() -> None:
    module = import_module("mayak.modules.identity_and_access")

    assert module.MODULE_ID == ia.MODULE_ID
    assert module.Account is ia.Account
    assert module.AccountIdentity is ia.AccountIdentity
    assert module.ContactPoint is ia.ContactPoint
    assert module.CredentialReference is ia.CredentialReference
    assert module.RoleAssignment is ia.RoleAssignment
    assert module.AuthSession is ia.AuthSession
    assert module.AuthChallenge is ia.AuthChallenge
    assert module.IdentityLinkChallenge is ia.IdentityLinkChallenge
    assert module.SYNTHETIC_FIXTURE_IDS == ia.SYNTHETIC_FIXTURE_IDS


def test_identity_and_access_package_imports_are_transport_neutral() -> None:
    contracts = import_module("mayak.modules.identity_and_access.contracts")
    fixtures = import_module("mayak.modules.identity_and_access.fixtures")

    assert contracts.Account.__name__ == "Account"
    assert fixtures.SYNTHETIC_FIXTURE_IDS[0] == "FX-IA-PROVIDER-FIRST-TELEGRAM-001"
