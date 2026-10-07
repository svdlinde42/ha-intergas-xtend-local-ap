"""Checks on the captured device responses in tests/fixtures.

Each file is one verbatim capture of GET /api/stats/values (2026-10-06, firmware
V1.20-). The values asserted here are the ones that tell the captures apart; they
are also used by the sensor tests later on.
"""

from __future__ import annotations

import json

from custom_components.intergas_xtend.const import STATS_FIELDS

from .conftest import FIXTURES_DIR


def test_fixture_files_are_single_line_json_with_32_fields() -> None:
    for name in (
        "stats_values.json",
        "stats_values_standby.json",
        "stats_values_n095.json",
    ):
        body = (FIXTURES_DIR / name).read_text(encoding="utf-8")
        assert body.count("\n") <= 1, name
        payload = json.loads(body)
        assert set(payload) == {"stats"}, name
        assert set(payload["stats"]) == set(STATS_FIELDS), name


def test_stats_payload_is_first_capture(stats_payload: dict[str, int | str]) -> None:
    assert len(stats_payload) == 32
    assert stats_payload["7940"] == 255
    assert stats_payload["5088"] == 7917
    assert stats_payload["6115"] == 32767
    assert stats_payload["47e0"] == "V1.20-"


def test_stats_payload_standby_is_second_capture(
    stats_payload_standby: dict[str, int | str],
) -> None:
    assert len(stats_payload_standby) == 32
    assert stats_payload_standby["77c3"] == 0
    assert stats_payload_standby["5077"] == 0
    assert stats_payload_standby["6115"] == 10000
    assert stats_payload_standby["61eb"] == 5000


def test_stats_payload_n095_is_third_capture(
    stats_payload_n095: dict[str, int | str],
) -> None:
    assert len(stats_payload_n095) == 32
    assert stats_payload_n095["7940"] == 95
    assert stats_payload_n095["503e"] == 5000
    assert stats_payload_n095["5041"] == 35
    assert stats_payload_n095["61eb"] == 6500
