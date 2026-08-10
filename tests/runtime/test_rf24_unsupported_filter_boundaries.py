# ruff: noqa: E501
from __future__ import annotations

from mayak.modules.filter_catalog.runtime import RuntimeServerAuthority, RuntimeUntrustedDraft


def test_runtime_request_separates_server_authority_from_untrusted_draft() -> None:
    server = RuntimeServerAuthority(
        catalog_version_id="CAT",
        beacon_revision_id="REV",
        provider_surface_reference_id="PROVIDER",
        category_scope_reference_id="CATEGORY",
        geography_scope_reference_id="GEO",
    )
    submitted = RuntimeUntrustedDraft(
        catalog_version_id="CLIENT_TAMPER", beacon_revision_id="CLIENT_REV"
    )
    assert server.catalog_version_id != submitted.catalog_version_id
    assert server.provider_surface_reference_id == "PROVIDER"
