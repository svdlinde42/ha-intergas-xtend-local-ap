"""Sensor tests: one generic class, conversion rules from the description.

The conversion tests build an XtendSensor around a stub coordinator so each
rule (sentinel, text format, factor, raw) is checked on its own. The platform
tests set up a real config entry with XtendApi.async_get_stats patched.
"""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest

from custom_components.intergas_xtend.const import DOMAIN, STATS_FIELDS
from custom_components.intergas_xtend.descriptions import (
    SENSORS,
    XtendSensorDescription,
)
from custom_components.intergas_xtend.sensor import XtendSensor

from .test_coordinator import (
    GET_STATS,
    HOST,
    fail_scheduled_polls,
    scheduled_poll,
    setup_entry,
)

SENSOR_PY = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "intergas_xtend"
    / "sensor.py"
)


def make_sensor(
    description: XtendSensorDescription, data: dict[str, int | str]
) -> XtendSensor:
    """Build a sensor around a stub coordinator; no Home Assistant needed."""
    coordinator = SimpleNamespace(
        data=data,
        api=SimpleNamespace(host=HOST),
        device_info={"identifiers": {(DOMAIN, HOST)}},
        last_update_success=True,
    )
    return XtendSensor(coordinator, description)  # type: ignore[arg-type]


def test_sensor_py_has_only_the_generic_class() -> None:
    # Verify step of the entities item: no per-field subclasses in sensor.py.
    tree = ast.parse(SENSOR_PY.read_text(encoding="utf-8"))
    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    assert classes == ["XtendSensor"]


def test_unique_id_and_translation_key_follow_the_description() -> None:
    sensor = make_sensor(XtendSensorDescription(key="79b3"), {"79b3": 2641})
    assert sensor.unique_id == f"{HOST}_79b3"
    assert sensor.translation_key == "79b3"
    assert sensor.has_entity_name is True
    assert sensor.device_info == {"identifiers": {(DOMAIN, HOST)}}

    named = make_sensor(
        XtendSensorDescription(key="79b3", translation_key="room_temperature"),
        {"79b3": 2641},
    )
    assert named.translation_key == "room_temperature"


@pytest.mark.parametrize(
    ("description", "data", "expected"),
    [
        # Raw value without factor or format stays as it is.
        (XtendSensorDescription(key="77d2"), {"77d2": 17102}, 17102),
        # A string stays a string when no sentinel applies (firmware version).
        (
            XtendSensorDescription(key="47e0", none_values=frozenset()),
            {"47e0": "V1.20-"},
            "V1.20-",
        ),
        # Default sentinel 32767 means no value.
        (XtendSensorDescription(key="6206"), {"6206": 32767}, None),
        # Missing field means no value.
        (XtendSensorDescription(key="6206"), {}, None),
        # Factor scales and rounds to 2 decimals.
        (XtendSensorDescription(key="79b3", factor=0.01), {"79b3": 2641}, 26.41),
        (XtendSensorDescription(key="7921", factor=0.01), {"7921": 2000}, 20.0),
        (XtendSensorDescription(key="5041", factor=0.1), {"5041": 35}, 3.5),
        (XtendSensorDescription(key="503e", factor=1), {"503e": 5000}, 5000),
        # Factor still respects the sentinel.
        (XtendSensorDescription(key="6115", factor=0.01), {"6115": 32767}, None),
        # Text format wins over factor and uses the raw value.
        (
            XtendSensorDescription(
                key="7940", none_values=frozenset({255}), text_format="n%03d"
            ),
            {"7940": 95},
            "n095",
        ),
        (
            XtendSensorDescription(
                key="7e2c", none_values=frozenset({255}), text_format="F%03d"
            ),
            {"7e2c": 37},
            "F037",
        ),
        (
            XtendSensorDescription(
                key="7940", none_values=frozenset({255}), text_format="n%03d"
            ),
            {"7940": 255},
            None,
        ),
        # Own sentinel set: 0 means no fault, 32767 is then a plain value.
        (
            XtendSensorDescription(key="8439", none_values=frozenset({0})),
            {"8439": 0},
            None,
        ),
        (
            XtendSensorDescription(key="8439", none_values=frozenset({0})),
            {"8439": 32767},
            32767,
        ),
        # A non-numeric raw value cannot be scaled or formatted.
        (XtendSensorDescription(key="79b3", factor=0.01), {"79b3": "n/a"}, None),
        (
            XtendSensorDescription(key="7940", text_format="n%03d"),
            {"7940": "n/a"},
            None,
        ),
    ],
)
def test_native_value_conversion(
    description: XtendSensorDescription,
    data: dict[str, int | str],
    expected: int | float | str | None,
) -> None:
    sensor = make_sensor(description, data)
    value = sensor.native_value
    assert value == expected
    assert type(value) is type(expected)


async def test_one_sensor_per_field_under_the_device(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    entity_registry = er.async_get(hass)
    device = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)[0]

    sensors = [
        registry_entry
        for registry_entry in er.async_entries_for_config_entry(
            entity_registry, entry.entry_id
        )
        if registry_entry.domain == SENSOR_DOMAIN
    ]
    assert len(sensors) == 32
    assert {e.unique_id for e in sensors} == {f"{HOST}_{key}" for key in STATS_FIELDS}
    assert all(e.device_id == device.id for e in sensors)
    assert {e.translation_key for e in sensors} == {
        d.translation_key or d.key for d in SENSORS
    }


async def test_states_follow_the_payload(
    hass: HomeAssistant,
    stats_payload: dict[str, int | str],
    stats_payload_standby: dict[str, int | str],
) -> None:
    entry = await setup_entry(hass, stats_payload)
    entity_registry = er.async_get(hass)

    def state_of(key: str) -> str:
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return state.state

    # No factors are set yet, so numeric states are the raw integers.
    assert state_of("79b3") == "2641"
    assert state_of("47e0") == "V1.20-"
    assert state_of("6206") == STATE_UNKNOWN

    with patch(GET_STATS, return_value=stats_payload_standby):
        await scheduled_poll(hass, entry.runtime_data)
    assert state_of("79b3") == "2262"
    assert state_of("6115") == "10000"


async def test_sensors_go_unavailable_on_failure_and_back_on_success(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    entity_id = er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, f"{HOST}_79b3"
    )
    assert entity_id is not None
    assert hass.states.get(entity_id).state == "2641"

    await fail_scheduled_polls(hass, coordinator, 1)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    with patch(GET_STATS, return_value=stats_payload):
        await scheduled_poll(hass, coordinator)
    assert hass.states.get(entity_id).state == "2641"
