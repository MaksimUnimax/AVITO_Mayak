from __future__ import annotations

from mayak.modules.avito_parser_adapter.contracts import (
    ParserOutcomeStatus,
    TransportOutcomeReference,
    TransportOutcomeStatus,
)
from mayak.modules.avito_parser_adapter.runtime import AvitoParserRuntime


def test_egress_failure_is_explicit_parser_failure_not_empty_success() -> None:
    runtime = AvitoParserRuntime()
    request = runtime.run_synthetic("usable_listing_page").attempt.request_envelope
    assert request is not None
    for status in (
        TransportOutcomeStatus.NOT_SENT,
        TransportOutcomeStatus.TRANSPORT_UNAVAILABLE,
        TransportOutcomeStatus.TRANSPORT_AMBIGUOUS,
    ):
        result = runtime.consume_egress_transport(
            request, TransportOutcomeReference(f"t-{status.value}", status)
        )
        assert (
            result.parser_status is not None
            or result.transport_status is not TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
        )
        assert result.parser_status is not ParserOutcomeStatus.USABLE_RESPONSE


def test_transport_success_alone_does_not_bypass_parser_validation() -> None:
    runtime = AvitoParserRuntime()
    request = runtime.run_synthetic("usable_listing_page").attempt.request_envelope
    assert request is not None
    result = runtime.consume_egress_transport(
        request,
        TransportOutcomeReference(
            "success-transport", TransportOutcomeStatus.RESPONSE_RECEIVED_UNCLASSIFIED
        ),
    )
    assert result.parser_status is None
