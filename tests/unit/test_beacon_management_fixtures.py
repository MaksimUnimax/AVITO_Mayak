from __future__ import annotations

from mayak.modules.beacon_management import (
    FIXTURE_IDS,
    SYNTHETIC_FIXTURE_BY_ID,
    SYNTHETIC_FIXTURE_CASES,
)
from mayak.modules.beacon_management.contracts import (
    BeaconDecisionStatus,
    BeaconParserOutcomeStatus,
)


def test_fixture_ids_are_unique_and_stable() -> None:
    assert FIXTURE_IDS == tuple(fixture.fixture_id for fixture in SYNTHETIC_FIXTURE_CASES)
    assert len(FIXTURE_IDS) == len(set(FIXTURE_IDS))
    assert SYNTHETIC_FIXTURE_BY_ID[FIXTURE_IDS[0]].fixture_id == FIXTURE_IDS[0]


def test_all_fixtures_are_synthetic_and_have_no_real_avito_url() -> None:
    forbidden_fragments = (
        "avito.ru",
        "www.avito.ru",
        "m.avito.ru",
        "avito.com",
    )

    for fixture in SYNTHETIC_FIXTURE_CASES:
        payload_text = fixture.model_dump_json().lower()
        assert all(fragment not in payload_text for fragment in forbidden_fragments)
        if fixture.source_url is not None:
            assert (
                fixture.source_url.submitted_url
                == "https://example.invalid/search?query=beacon-management&city=synthetic"
            )
        if fixture.beacon is not None:
            assert (
                fixture.beacon.source_url.submitted_url
                == "https://example.invalid/search?query=beacon-management&city=synthetic"
            )
        if fixture.peer_beacon is not None:
            assert (
                fixture.peer_beacon.source_url.submitted_url
                == "https://example.invalid/search?query=beacon-management&city=synthetic"
            )
        if fixture.current_configuration is not None:
            assert (
                fixture.current_configuration.source_url.submitted_url
                == "https://example.invalid/search?query=beacon-management&city=synthetic"
            )


def test_duplicate_same_account_source_url_fixture_has_same_url_and_different_beacon_ids() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-DUPLICATE-SAME-ACCOUNT-001"]

    assert fixture.beacon is not None
    assert fixture.peer_beacon is not None
    assert fixture.beacon.source_url.submitted_url == fixture.peer_beacon.source_url.submitted_url
    assert fixture.beacon.beacon_id != fixture.peer_beacon.beacon_id
    assert fixture.beacon.account_id == fixture.peer_beacon.account_id


def test_duplicate_cross_account_source_url_fixture_has_same_url_and_different_account_ids() -> (
    None
):
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-DUPLICATE-CROSS-ACCOUNT-001"]

    assert fixture.beacon is not None
    assert fixture.peer_beacon is not None
    assert fixture.beacon.source_url.submitted_url == fixture.peer_beacon.source_url.submitted_url
    assert fixture.beacon.account_id != fixture.peer_beacon.account_id


def test_free_country_wide_fixture_is_blocked_and_city_required() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-FREE-COUNTRY-WIDE-BLOCKED-001"]

    assert fixture.activation_decision is not None
    assert fixture.activation_decision.status is BeaconDecisionStatus.BLOCKED
    assert fixture.activation_decision.country_wide_allowed is False
    assert fixture.activation_decision.city_required is True
    assert fixture.activation_decision.requested_city is None


def test_basic_country_wide_fixture_is_allowed() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-BASIC-COUNTRY-WIDE-ALLOWED-001"]

    assert fixture.activation_decision is not None
    assert fixture.activation_decision.status is BeaconDecisionStatus.ALLOWED
    assert fixture.activation_decision.country_wide_allowed is True
    assert fixture.activation_decision.requested_country_wide is True


def test_archived_history_deleted_fixture_does_not_count_toward_active_limit() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-ARCHIVED-EXCLUDED-001"]

    assert fixture.beacon is not None
    assert fixture.history_entry is not None
    assert fixture.beacon.counts_toward_active_limit is False
    assert fixture.history_entry.counts_toward_active_limit is False
    assert fixture.history_entry.outcome.name == "ARCHIVED"


def test_permanently_deleted_fixture_is_not_restorable() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PERMANENTLY-DELETED-001"]

    assert fixture.beacon is not None
    assert fixture.history_entry is not None
    assert fixture.beacon.restorable is False
    assert fixture.history_entry.restorable is False
    assert fixture.beacon.lifecycle_state.name == "PERMANENTLY_DELETED"


def test_patch_based_save_fixture_changes_only_supplied_fields() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PATCH-SAVE-001"]

    assert fixture.mutation_decision is not None
    applied_fields = fixture.mutation_decision.applied_fields
    assert fixture.mutation_decision.patch_fields == ("display_name", "interval_minutes")
    assert applied_fields == ("display_name",)
    assert set(applied_fields).issubset(fixture.mutation_decision.patch_fields)
    assert fixture.mutation_decision.current_configuration_replaced is True


def test_last_write_wins_fixture_represents_later_successful_save_as_authoritative() -> None:
    fixture = SYNTHETIC_FIXTURE_BY_ID["FX-BM-LAST-WRITE-WINS-001"]

    assert fixture.mutation_decision is not None
    assert fixture.mutation_decision.same_field_concurrent_change is True
    assert fixture.mutation_decision.last_write_wins is True
    assert fixture.mutation_decision.status is BeaconDecisionStatus.ALLOWED
    assert fixture.mutation_decision.conflict_fields == ("interval_minutes",)


def test_parser_unsafe_fixtures_remain_not_clean() -> None:
    malformed = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-UNSAFE-001"]
    captcha = SYNTHETIC_FIXTURE_BY_ID["FX-BM-PARSER-CAPTCHA-001"]

    assert malformed.snapshot is not None
    assert captcha.snapshot is not None
    assert malformed.snapshot.parser_outcome_status is BeaconParserOutcomeStatus.MALFORMED
    assert captcha.snapshot.parser_outcome_status is BeaconParserOutcomeStatus.CAPTCHA_AFFECTED
    assert malformed.snapshot.accepted_as_clean is False
    assert captcha.snapshot.accepted_as_clean is False
