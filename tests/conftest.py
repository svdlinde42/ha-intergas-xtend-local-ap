"""Shared pytest configuration for the Intergas Xtend tests.

Run the suite on Linux (WSL or CI). Home Assistant core imports Unix-only modules
such as fcntl and does not load on Windows.

The payload fixtures return the inner ``stats`` dict of a captured device response,
which is exactly what ``XtendApi.async_get_stats`` returns. Tests that need the raw
HTTP body read the fixture file directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load custom_components/ in every test."""


def _load_stats(name: str) -> dict[str, int | str]:
    body = (FIXTURES_DIR / name).read_text(encoding="utf-8")
    return json.loads(body)["stats"]


@pytest.fixture
def stats_payload() -> dict[str, int | str]:
    """First capture (2026-10-06): boiler at 7917 W, 6206 and 6115 unavailable."""
    return _load_stats("stats_values.json")


@pytest.fixture
def stats_payload_standby() -> dict[str, int | str]:
    """Second capture: summary page showed Standby, DHW available 100 %."""
    return _load_stats("stats_values_standby.json")


@pytest.fixture
def stats_payload_n095() -> dict[str, int | str]:
    """Third capture: display showed n095, heat pump at 5000 W, DHW setpoint 65 °C."""
    return _load_stats("stats_values_n095.json")


@pytest.fixture
def stats_payload_statistics() -> dict[str, int | str]:
    """Owner's capture of the statistics page request (2026-10-07, 83 fields).

    It holds the energy totals and counters, but not every summary page field
    (for example 47e0 and 7e7a are missing).
    """
    return _load_stats("stats_values_statistics.json")
