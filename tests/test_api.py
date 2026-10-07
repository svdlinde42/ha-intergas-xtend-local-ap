"""Unit tests for custom_components/intergas_xtend/api.py.

The parser tests below call ``XtendApi._parse_stats`` directly. HTTP round-trip
tests against a mocked server are a separate prd item and will be added here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.intergas_xtend.api import XtendApi, XtendResponseError
from custom_components.intergas_xtend.const import STATS_FIELDS

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_parse_fixture_returns_stats_unchanged() -> None:
    # Verify step of the parser item: 32 keys, firmware string stays a string.
    body = (FIXTURES / "stats_values.json").read_text(encoding="utf-8")
    stats = XtendApi._parse_stats(body)
    assert isinstance(stats, dict)
    assert len(stats) == 32
    assert set(stats) == set(STATS_FIELDS)
    assert stats["47e0"] == "V1.20-"
    assert stats == json.loads(body)["stats"]


def test_parse_keeps_ints_and_sentinels_raw() -> None:
    # No scaling and no sentinel handling in api.py; that is the sensor layer.
    body = (FIXTURES / "stats_values.json").read_text(encoding="utf-8")
    stats = XtendApi._parse_stats(body)
    assert stats["79b3"] == 2641
    assert isinstance(stats["79b3"], int)
    assert stats["6206"] == 32767
    assert stats["7940"] == 255
    assert stats["8439"] == 0


@pytest.mark.parametrize(
    "body",
    [
        "not json",
        "",
        '{"stats": {',
    ],
)
def test_parse_invalid_json_raises_response_error(body: str) -> None:
    with pytest.raises(XtendResponseError):
        XtendApi._parse_stats(body)


@pytest.mark.parametrize(
    "body",
    [
        '{"other": {}}',
        "{}",
        '{"stats": null}',
        '{"stats": []}',
        '{"stats": "V1.20-"}',
        "[]",
        '"stats"',
        "42",
    ],
)
def test_parse_wrong_shape_raises_response_error(body: str) -> None:
    with pytest.raises(XtendResponseError):
        XtendApi._parse_stats(body)
