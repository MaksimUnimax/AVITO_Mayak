from __future__ import annotations

from dataclasses import replace

import httpx

from mayak.modules.avito_parser_adapter import (
    AvitoParserRuntime,
    CompatibilityProfileAuthorityClass,
    HttpxLiveAdapter,
    NormalizedListingSnapshot,
    ParserOutcomeStatus,
    ParserSourceReference,
    ProviderResponseEvidenceClass,
    SourceReferenceKind,
    SyntheticParserProvider,
    SyntheticScenario,
    TransportOutcomeStatus,
    TrustedDispatchAuthority,
    TrustedDispatchBinding,
)


def test_synthetic_provider_is_deterministic_and_fail_closed() -> None:
    provider = SyntheticParserProvider()
    first = provider.execute(SyntheticScenario.USABLE_LISTING_PAGE, request_id="same")
    second = provider.execute(SyntheticScenario.USABLE_LISTING_PAGE, request_id="same")
    assert first == second
    assert first.page is not None
    assert first.page.normalized_listing_candidates[0].listing_candidate_id == "listing::1"

    expected = {
        "clean_empty": ParserOutcomeStatus.USABLE_RESPONSE,
        "empty_without_proof": ParserOutcomeStatus.RESULT_AMBIGUOUS,
        "captcha": ParserOutcomeStatus.CAPTCHA_OR_CHALLENGE,
        "rate_restricted": ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED,
        "malformed": ParserOutcomeStatus.MALFORMED_RESPONSE,
        "incomplete": ParserOutcomeStatus.INCOMPLETE_RESPONSE,
        "partial": ParserOutcomeStatus.PARTIAL,
        "unsupported": ParserOutcomeStatus.UNSUPPORTED_STRUCTURE,
        "ambiguous": ParserOutcomeStatus.RESULT_AMBIGUOUS,
    }
    for scenario, status in expected.items():
        assert provider.execute(scenario).attempt.parser_status is status


def test_synthetic_configuration_preserves_repeated_values() -> None:
    result = SyntheticParserProvider().execute("usable_configuration")
    assert result.configuration is not None
    candidate = result.configuration.parameter_candidates[0]
    assert candidate.repeated_values == ("synthetic", "synthetic")
    assert candidate.multivalue_normalization is not None
    assert candidate.multivalue_normalization.normalized_values == candidate.repeated_values


def test_live_adapter_is_disabled_without_server_proof() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"items": [], "empty_proof": True})

    result = SyntheticParserProvider().execute("usable_listing_page")
    profile = result.attempt.request_envelope.compatibility_profile
    adapter = HttpxLiveAdapter(transport=httpx.MockTransport(handler))
    classification = adapter.fetch(
        ParserSourceReference("test-source", SourceReferenceKind.SAFE_REFERENCE, "beacon-source", "https://synthetic.invalid"),
        profile=profile,
    )
    assert classification.transport_status is TransportOutcomeStatus.NOT_SENT
    assert classification.explanation is not None
    assert classification.explanation.summary == "PROVIDER_DISABLED_CONTINUE"
    assert not calls


def test_authorized_fake_httpx_never_invents_live_schema_semantics() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"items": [], "empty_proof": True})

    profile = (
        SyntheticParserProvider()
        .execute("clean_empty")
        .attempt.request_envelope.compatibility_profile
    )
    profile = replace(
        profile, authority_class=CompatibilityProfileAuthorityClass.PROOF_GATED
    )

    source = ParserSourceReference(
        "test-source", SourceReferenceKind.SAFE_REFERENCE, "beacon-source", "https://caller.invalid"
    )
    authority = TrustedDispatchAuthority((TrustedDispatchBinding(
        source.source_reference_id, source.beacon_source_reference, profile.profile_id,
        profile.profile_version, "test-authority", "test-proof", "https://synthetic.invalid/search",
        ("EMPTY_WITH_PROOF",),
    ),))

    adapter = HttpxLiveAdapter(
        enabled=True, transport=httpx.MockTransport(handler), authority=authority
    )
    classification = adapter.fetch(
        source,
        profile=profile,
    )
    assert classification.parser_status is ParserOutcomeStatus.UNSUPPORTED_STRUCTURE
    assert (
        classification.provider_response_evidence_class
        is ProviderResponseEvidenceClass.UNSUPPORTED_STRUCTURE
    )
    assert len(calls) == 1 and calls[0].method == "GET"


def test_live_generic_success_shapes_are_all_non_usable() -> None:
    profile = replace(
        SyntheticParserProvider().execute("clean_empty").attempt.request_envelope.compatibility_profile,
        authority_class=CompatibilityProfileAuthorityClass.PROOF_GATED,
    )
    source = ParserSourceReference(
        "test-source", SourceReferenceKind.SAFE_REFERENCE, "beacon-source", "https://caller.invalid"
    )
    binding = TrustedDispatchBinding(
        "test-source", "beacon-source", profile.profile_id, profile.profile_version,
        "test-authority", "test-proof", "https://synthetic.invalid/search", ("EMPTY_WITH_PROOF",),
    )
    bodies = (
        b"{}", b'{"items":[]}', b'{"items":[{"id":"x"}]}',
        b'{"items":[],"empty_proof":true}', b'{"challenge":true}',
        b'{"other":"value"}', b'[{"id":"x"}]',
    )
    for body in bodies:
        adapter = HttpxLiveAdapter(
            enabled=True,
            transport=httpx.MockTransport(
                lambda request, body=body: httpx.Response(200, content=body)
            ),
            authority=TrustedDispatchAuthority((binding,)),
        )
        result = adapter.fetch(source, profile=profile)
        assert result.parser_status not in {ParserOutcomeStatus.USABLE_RESPONSE}
        assert (
            result.provider_response_evidence_class
            is not ProviderResponseEvidenceClass.EMPTY_WITH_PROOF
        )


def test_httpx_restriction_and_malformed_are_not_empty_success() -> None:
    profile = (
        SyntheticParserProvider()
        .execute("usable_listing_page")
        .attempt.request_envelope.compatibility_profile
    )
    for status_code, body, expected in (
        (429, b"blocked", ParserOutcomeStatus.RATE_OR_ACCESS_RESTRICTED),
        (200, b"not-json", ParserOutcomeStatus.MALFORMED_RESPONSE),
    ):
        profile = replace(
            profile, authority_class=CompatibilityProfileAuthorityClass.PROOF_GATED
        )

        adapter = HttpxLiveAdapter(
            enabled=True,
            transport=httpx.MockTransport(
                lambda request, status_code=status_code, body=body: httpx.Response(
                    status_code, content=body
                )
            ),
            authority=TrustedDispatchAuthority((TrustedDispatchBinding(
                "test-source", "beacon-source", profile.profile_id, profile.profile_version,
                "test-authority", "test-proof", "https://synthetic.invalid", ("EMPTY_WITH_PROOF",),
            ),)),
        )
        result = adapter.fetch(
            ParserSourceReference(
                "test-source",
                SourceReferenceKind.SAFE_REFERENCE,
                "beacon-source",
                "https://synthetic.invalid",
            ),
            profile=profile,
        )
        assert result.parser_status is expected


def test_runtime_does_not_make_scan_or_newness_decisions() -> None:
    page = AvitoParserRuntime().run_synthetic("usable_listing_page").page
    assert page is not None
    assert not hasattr(page, "baseline")
    assert not hasattr(page, "newness")


def test_unknown_synthetic_scenario_is_rejected() -> None:
    import pytest

    with pytest.raises(ValueError, match="unsupported synthetic scenario"):
        SyntheticParserProvider().execute("future-scenario")


def test_source_analysis_is_fail_closed_for_absent_and_unclassified_transport() -> None:
    runtime = AvitoParserRuntime()
    attempt = runtime.run_synthetic("usable_listing_page").attempt
    assert (
        runtime.analyze_source(attempt.request_envelope, None).status
        is TransportOutcomeStatus.NOT_SENT
    )
    assert (
        runtime.analyze_source(attempt.request_envelope, attempt.transport_outcome).status
        is ParserOutcomeStatus.RESULT_AMBIGUOUS
    )


def test_synthetic_profile_cannot_authorize_live_even_with_enabled_adapter() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"items": [{"id": "x"}]})

    result = SyntheticParserProvider().execute("usable_listing_page")
    classification = HttpxLiveAdapter(
        enabled=True, transport=httpx.MockTransport(handler), authority=object()
    ).fetch(
        ParserSourceReference(
            "test-source", SourceReferenceKind.SAFE_REFERENCE, "beacon-source", "https://synthetic.invalid"
        ),
        profile=result.attempt.request_envelope.compatibility_profile,
    )
    assert classification.explanation is not None
    assert classification.explanation.summary == "SYNTHETIC_PROFILE_CANNOT_AUTHORIZE_LIVE"
    assert calls == []


def test_batch_preserves_order_counts_and_duplicate_observations() -> None:
    result = AvitoParserRuntime().run_batch(
        ("usable_listing_page", "rate_restricted", "usable_listing_page")
    )
    assert [item.scenario for item in result.outcomes] == [
        "usable_listing_page",
        "rate_restricted",
        "usable_listing_page",
    ]
    assert (result.succeeded_count, result.failed_count, result.ambiguous_count) == (2, 1, 0)
    assert result.duplicate_observations == ("listing::1",)


def test_normalized_snapshot_rejects_provider_shaped_fields() -> None:
    import pytest

    with pytest.raises(ValueError, match="unapproved"):
        NormalizedListingSnapshot(candidates=({"body": "raw html"},))
