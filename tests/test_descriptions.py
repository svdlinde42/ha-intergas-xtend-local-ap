"""The SENSORS table covers every stats field exactly once."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from custom_components.intergas_xtend.const import (
    FIRMWARE_FIELD,
    NOT_AVAILABLE,
    STATS_FIELDS,
)
from custom_components.intergas_xtend.descriptions import (
    SENSORS,
    XtendSensorDescription,
)

DESCRIPTIONS_PY = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "intergas_xtend"
    / "descriptions.py"
)


def test_sensors_cover_stats_fields_exactly_once() -> None:
    # Verify step of the entities item.
    assert {d.key for d in SENSORS} == set(STATS_FIELDS)
    assert len(SENSORS) == len(STATS_FIELDS) == 32
    assert all(isinstance(d, XtendSensorDescription) for d in SENSORS)


def test_numeric_fields_treat_32767_as_no_value() -> None:
    assert NOT_AVAILABLE == 32767
    for description in SENSORS:
        if description.key == FIRMWARE_FIELD:
            # The firmware version is a string; no numeric sentinel applies.
            assert description.none_values == frozenset()
        else:
            assert NOT_AVAILABLE in description.none_values, description.key


def test_description_defaults_and_immutability() -> None:
    description = XtendSensorDescription(key="0000")
    assert description.factor is None
    assert description.text_format is None
    assert description.none_values == frozenset({NOT_AVAILABLE})
    with pytest.raises(FrozenInstanceError):
        description.factor = 1.0  # type: ignore[misc]
    custom = XtendSensorDescription(
        key="0001", factor=0.01, none_values=frozenset({255}), text_format="n%03d"
    )
    assert (custom.factor, custom.none_values, custom.text_format) == (
        0.01,
        frozenset({255}),
        "n%03d",
    )


def test_sensors_table_names_its_source() -> None:
    source = DESCRIPTIONS_PY.read_text(encoding="utf-8")
    assert "Source: docs/stats-mapping.md" in source
    assert "Do not change factors or units without" in source
