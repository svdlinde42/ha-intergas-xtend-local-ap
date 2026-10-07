"""Sensor tests: one generic class, conversion rules from the description.

The conversion tests build an XtendSensor around a stub coordinator so each
rule (sentinel, text format, factor, raw) is checked on its own. The platform
tests set up a real config entry with XtendApi.async_get_stats patched.
"""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    EntityCategory,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest

from custom_components.intergas_xtend.codes import fault_info, notification_info
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


# Enum support item: a test description with a value map.
ENUM_DESCRIPTION = XtendSensorDescription(
    key="7e51",
    device_class=SensorDeviceClass.ENUM,
    options=["a"],
    value_map={1: "a"},
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (1, "a"),
        # A code that is not in the map: no name is invented.
        (2, None),
        # The sentinel is checked before the map.
        (32767, None),
        # A raw value that is not an integer cannot be mapped.
        ("1", None),
        (1.0, None),
    ],
)
def test_value_map_gives_the_state_name(
    raw: int | float | str, expected: str | None
) -> None:
    # Verify step of the enum support item.
    assert make_sensor(ENUM_DESCRIPTION, {"7e51": raw}).native_value == expected


def test_value_map_respects_none_values() -> None:
    description = XtendSensorDescription(
        key="7e51", none_values=frozenset({1}), value_map={1: "a", 2: "b"}
    )
    assert make_sensor(description, {"7e51": 1}).native_value is None
    assert make_sensor(description, {"7e51": 2}).native_value == "b"


async def test_unknown_enum_code_does_not_stop_other_sensors(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    room = next(d for d in SENSORS if d.key == "79b3")
    payload = {**stats_payload, "7e51": 999}
    with patch(
        "custom_components.intergas_xtend.sensor.SENSORS", (ENUM_DESCRIPTION, room)
    ):
        entry = await setup_entry(hass, payload)
    entity_registry = er.async_get(hass)

    def state_of(key: str) -> str:
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        return hass.states.get(entity_id).state

    assert state_of("7e51") == STATE_UNKNOWN
    assert state_of("79b3") == "26.41"

    with patch(GET_STATS, return_value={**payload, "7e51": 1, "79b3": 2262}):
        await scheduled_poll(hass, entry.runtime_data)
    assert state_of("7e51") == "a"
    assert state_of("79b3") == "22.62"

    with patch(GET_STATS, return_value={**payload, "7e51": 3, "79b3": 2000}):
        await scheduled_poll(hass, entry.runtime_data)
    assert state_of("7e51") == STATE_UNKNOWN
    assert state_of("79b3") == "20.0"


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

    # Temperatures and the DHW percentage carry factor 0.01.
    assert state_of("79b3") == "26.41"
    assert state_of("47e0") == "V1.20-"
    assert state_of("6206") == STATE_UNKNOWN
    assert state_of("6115") == STATE_UNKNOWN

    with patch(GET_STATS, return_value=stats_payload_standby):
        await scheduled_poll(hass, entry.runtime_data)
    assert state_of("79b3") == "22.62"
    assert state_of("6115") == "100.0"


async def test_sensors_go_unavailable_on_failure_and_back_on_success(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    entity_id = er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, f"{HOST}_79b3"
    )
    assert entity_id is not None
    assert hass.states.get(entity_id).state == "26.41"

    await fail_scheduled_polls(hass, coordinator, 1)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    with patch(GET_STATS, return_value=stats_payload):
        await scheduled_poll(hass, coordinator)
    assert hass.states.get(entity_id).state == "26.41"


# Temperature sensors (entities item): key -> translation_key.
TEMPERATURE_SENSORS = {
    "79b3": "room_temperature",
    "7921": "room_target_temperature",
    "62d1": "outside_temperature",
    "6280": "ch_return_temperature",
    "621d": "ch_supply_temperature",
    "62ed": "ch_setpoint",
    "620f": "aux1_temperature",
    "6206": "aux2_temperature",
    "610b": "dhw_temperature",
    "61eb": "dhw_setpoint",
}


def test_temperature_descriptions() -> None:
    by_key = {d.key: d for d in SENSORS}
    for key, translation_key in TEMPERATURE_SENSORS.items():
        description = by_key[key]
        assert description.translation_key == translation_key, key
        assert description.factor == 0.01, key
        assert description.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        assert description.device_class == SensorDeviceClass.TEMPERATURE, key
        assert description.state_class == SensorStateClass.MEASUREMENT, key
        assert description.none_values == frozenset({32767}), key


@pytest.mark.parametrize(
    ("key", "expected"),
    [("79b3", 26.41), ("7921", 20.0), ("62d1", 20.1), ("6206", None)],
)
def test_temperature_values_from_first_capture(
    stats_payload: dict[str, int | str], key: str, expected: float | None
) -> None:
    # Verify step of the temperature item, first capture.
    by_key = {d.key: d for d in SENSORS}
    assert make_sensor(by_key[key], stats_payload).native_value == expected


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("79b3", 22.62),
        ("62d1", 16.17),
        ("6280", 21.75),
        ("621d", 32.55),
        ("62ed", 20.0),
        ("610b", 23.15),
        ("61eb", 50.0),
    ],
)
def test_temperature_values_match_the_standby_summary_page(
    stats_payload_standby: dict[str, int | str], key: str, expected: float
) -> None:
    # Verify step of the temperature item: values as shown on the summary
    # screenshot of the standby capture.
    by_key = {d.key: d for d in SENSORS}
    assert make_sensor(by_key[key], stats_payload_standby).native_value == expected


async def test_temperature_state_has_unit_and_classes(
    hass: HomeAssistant, stats_payload_standby: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_standby)
    entity_id = er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, f"{HOST}_62d1"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "16.17"
    assert state.attributes["unit_of_measurement"] == "°C"
    assert state.attributes["device_class"] == "temperature"
    assert state.attributes["state_class"] == "measurement"


# Power and COP sensors (entities item): key -> translation_key.
POWER_SENSORS = {
    "503e": "heat_pump_power",
    "5088": "boiler_power",
    "5077": "total_thermal_power",
    "50f2": "retrieved_power",
}


def test_power_descriptions() -> None:
    by_key = {d.key: d for d in SENSORS}
    for key, translation_key in POWER_SENSORS.items():
        description = by_key[key]
        assert description.translation_key == translation_key, key
        assert description.factor == 1, key
        assert description.native_unit_of_measurement == UnitOfPower.WATT, key
        assert description.device_class == SensorDeviceClass.POWER, key
        assert description.state_class == SensorStateClass.MEASUREMENT, key
        assert description.none_values == frozenset({32767}), key


def test_cop_description() -> None:
    description = {d.key: d for d in SENSORS}["5041"]
    assert description.translation_key == "cop"
    assert description.factor == 0.1
    assert description.native_unit_of_measurement is None
    assert description.device_class is None
    assert description.state_class == SensorStateClass.MEASUREMENT
    assert description.icon == "mdi:heat-pump"
    assert description.none_values == frozenset({32767})


@pytest.mark.parametrize(
    ("fixture_name", "key", "expected"),
    [
        # Verify step, first capture.
        ("stats_payload", "5088", 7917),
        ("stats_payload", "50f2", 7),
        ("stats_payload", "5041", 0.0),
        # Verify step, n095 capture (heat pump at 5000 W, COP 3.5).
        ("stats_payload_n095", "503e", 5000),
        ("stats_payload_n095", "5077", 5000),
        ("stats_payload_n095", "50f2", 1419),
        ("stats_payload_n095", "5041", 3.5),
        # Verify step, standby capture against the summary screenshot.
        ("stats_payload_standby", "503e", 0),
        ("stats_payload_standby", "5088", 0),
        ("stats_payload_standby", "5077", 0),
        ("stats_payload_standby", "50f2", 7),
        ("stats_payload_standby", "5041", 0.0),
    ],
)
def test_power_and_cop_values_from_the_captures(
    request: pytest.FixtureRequest, fixture_name: str, key: str, expected: float
) -> None:
    payload: dict[str, int | str] = request.getfixturevalue(fixture_name)
    value = make_sensor({d.key: d for d in SENSORS}[key], payload).native_value
    assert value == expected
    # Power stays an integer number of W; COP is a float.
    assert type(value) is type(expected)


async def test_power_and_cop_states_have_unit_and_classes(
    hass: HomeAssistant, stats_payload_n095: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_n095)
    entity_registry = er.async_get(hass)

    def state_of(key: str):
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return state

    power = state_of("503e")
    assert power.state == "5000"
    assert power.attributes["unit_of_measurement"] == "W"
    assert power.attributes["device_class"] == "power"
    assert power.attributes["state_class"] == "measurement"

    cop = state_of("5041")
    assert cop.state == "3.5"
    assert "unit_of_measurement" not in cop.attributes
    assert "device_class" not in cop.attributes
    assert cop.attributes["state_class"] == "measurement"
    assert cop.attributes["icon"] == "mdi:heat-pump"


# Flow and pressure sensors (entities item).
def test_flow_and_pressure_descriptions() -> None:
    by_key = {d.key: d for d in SENSORS}

    flow = by_key["629c"]
    assert flow.translation_key == "ch_flow"
    assert flow.factor == 0.01
    assert flow.native_unit_of_measurement == UnitOfVolumeFlowRate.LITERS_PER_MINUTE
    assert flow.device_class == SensorDeviceClass.VOLUME_FLOW_RATE
    assert flow.state_class == SensorStateClass.MEASUREMENT
    assert flow.none_values == frozenset({32767})

    pressure = by_key["7ed3"]
    assert pressure.translation_key == "ch_pressure"
    assert pressure.factor == 0.01
    assert pressure.native_unit_of_measurement == UnitOfPressure.BAR
    assert pressure.device_class == SensorDeviceClass.PRESSURE
    assert pressure.state_class == SensorStateClass.MEASUREMENT
    assert pressure.none_values == frozenset({32767})


@pytest.mark.parametrize(
    ("fixture_name", "key", "expected"),
    [
        # Verify step, first capture.
        ("stats_payload", "629c", 14.91),
        ("stats_payload", "7ed3", 2.01),
        # Verify step, standby capture against the summary screenshot.
        ("stats_payload_standby", "629c", 15.03),
        ("stats_payload_standby", "7ed3", 1.85),
    ],
)
def test_flow_and_pressure_values_from_the_captures(
    request: pytest.FixtureRequest, fixture_name: str, key: str, expected: float
) -> None:
    payload: dict[str, int | str] = request.getfixturevalue(fixture_name)
    value = make_sensor({d.key: d for d in SENSORS}[key], payload).native_value
    assert value == expected
    assert type(value) is float


async def test_flow_and_pressure_states_have_unit_and_classes(
    hass: HomeAssistant, stats_payload_standby: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_standby)
    entity_registry = er.async_get(hass)

    def state_of(key: str):
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return state

    flow = state_of("629c")
    assert flow.state == "15.03"
    assert flow.attributes["unit_of_measurement"] == "L/min"
    assert flow.attributes["device_class"] == "volume_flow_rate"
    assert flow.attributes["state_class"] == "measurement"

    pressure = state_of("7ed3")
    assert pressure.state == "1.85"
    assert pressure.attributes["unit_of_measurement"] == "bar"
    assert pressure.attributes["device_class"] == "pressure"
    assert pressure.attributes["state_class"] == "measurement"


# Domestic hot water (Xtore) sensors (entities item).
def test_dhw_descriptions() -> None:
    by_key = {d.key: d for d in SENSORS}

    available = by_key["6115"]
    assert available.translation_key == "dhw_available"
    assert available.factor == 0.01
    assert available.native_unit_of_measurement == PERCENTAGE
    assert available.device_class is None
    assert available.state_class == SensorStateClass.MEASUREMENT
    assert available.entity_category is None
    assert available.none_values == frozenset({32767})

    volume = by_key["61ba"]
    assert volume.translation_key == "dhw_volume"
    assert volume.factor == 1
    assert volume.native_unit_of_measurement == UnitOfVolume.LITERS
    assert volume.device_class == SensorDeviceClass.VOLUME_STORAGE
    assert volume.state_class is None
    assert volume.entity_category == EntityCategory.DIAGNOSTIC
    assert volume.none_values == frozenset({32767})


@pytest.mark.parametrize(
    ("fixture_name", "key", "expected"),
    [
        # Verify step, first capture: 6115 is 32767 (not available).
        ("stats_payload", "6115", None),
        ("stats_payload", "61ba", 80),
        # Verify step, standby capture against the summary screenshot (DHW 100 %).
        ("stats_payload_standby", "6115", 100.0),
        ("stats_payload_standby", "61ba", 80),
    ],
)
def test_dhw_values_from_the_captures(
    request: pytest.FixtureRequest,
    fixture_name: str,
    key: str,
    expected: float | None,
) -> None:
    payload: dict[str, int | str] = request.getfixturevalue(fixture_name)
    value = make_sensor({d.key: d for d in SENSORS}[key], payload).native_value
    assert value == expected
    # The percentage is a float; the volume stays an integer number of liters.
    assert type(value) is type(expected)


async def test_dhw_states_have_unit_and_category(
    hass: HomeAssistant, stats_payload_standby: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_standby)
    entity_registry = er.async_get(hass)

    def entry_and_state(key: str):
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return entity_registry.async_get(entity_id), state

    available_entry, available = entry_and_state("6115")
    assert available.state == "100.0"
    assert available.attributes["unit_of_measurement"] == "%"
    assert "device_class" not in available.attributes
    assert available.attributes["state_class"] == "measurement"
    assert available_entry.entity_category is None

    volume_entry, volume = entry_and_state("61ba")
    assert volume.state == "80"
    assert volume.attributes["unit_of_measurement"] == "L"
    assert volume.attributes["device_class"] == "volume_storage"
    assert "state_class" not in volume.attributes
    assert volume_entry.entity_category == EntityCategory.DIAGNOSTIC


# Notification, lockout and fault code sensors (entities item).
def test_code_descriptions() -> None:
    by_key = {d.key: d for d in SENSORS}

    notification = by_key["7940"]
    assert notification.translation_key == "notification_code"
    assert notification.none_values == frozenset({255})
    assert notification.text_format == "n%03d"
    assert notification.factor is None
    assert notification.code_lookup is notification_info
    assert notification.entity_category == EntityCategory.DIAGNOSTIC

    lockout = by_key["7e2c"]
    assert lockout.translation_key == "lockout_code"
    assert lockout.none_values == frozenset({255})
    assert lockout.text_format == "F%03d"
    assert lockout.factor is None
    assert lockout.code_lookup is fault_info
    assert lockout.entity_category == EntityCategory.DIAGNOSTIC

    fault = by_key["8439"]
    assert fault.translation_key == "boiler_fault_code"
    assert fault.none_values == frozenset({0})
    assert fault.text_format is None
    assert fault.factor is None
    # The boiler's own OpenTherm code is not in the Xtend manual.
    assert fault.code_lookup is None
    assert fault.entity_category == EntityCategory.DIAGNOSTIC

    # Only the two code sensors with a lookup carry attributes.
    assert [d.key for d in SENSORS if d.code_lookup is not None] == ["7940", "7e2c"]

    # Code sensors are text or plain numbers: no unit, device class or
    # state class.
    for description in (notification, lockout, fault):
        assert description.native_unit_of_measurement is None, description.key
        assert description.device_class is None, description.key
        assert description.state_class is None, description.key


def test_code_values_from_first_capture(stats_payload: dict[str, int | str]) -> None:
    # Verify step: all three codes are "no code" in the first capture; a
    # lockout 37 reads F037.
    by_key = {d.key: d for d in SENSORS}
    for key in ("7940", "7e2c", "8439"):
        assert make_sensor(by_key[key], stats_payload).native_value is None, key

    with_lockout = {**stats_payload, "7e2c": 37}
    assert make_sensor(by_key["7e2c"], with_lockout).native_value == "F037"


@pytest.mark.parametrize(
    ("key", "expected"),
    [("7940", "n095"), ("7e2c", None), ("8439", None)],
)
def test_code_values_from_the_n095_capture(
    stats_payload_n095: dict[str, int | str], key: str, expected: str | None
) -> None:
    # Verify step: real capture while the display showed n095 (owner,
    # 2026-10-06).
    by_key = {d.key: d for d in SENSORS}
    assert make_sensor(by_key[key], stats_payload_n095).native_value == expected


def test_boiler_fault_code_keeps_the_raw_number() -> None:
    # 8439 is the CV boiler's own OpenTherm code: 0 means no fault, any other
    # value is shown as the number itself; 32767 is not a sentinel here.
    description = {d.key: d for d in SENSORS}["8439"]
    assert make_sensor(description, {"8439": 12}).native_value == 12
    assert make_sensor(description, {"8439": 32767}).native_value == 32767


async def test_code_states_are_diagnostic_text(
    hass: HomeAssistant, stats_payload_n095: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_n095)
    entity_registry = er.async_get(hass)

    def entry_and_state(key: str):
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return entity_registry.async_get(entity_id), state

    notification_entry, notification = entry_and_state("7940")
    assert notification.state == "n095"
    assert "unit_of_measurement" not in notification.attributes
    assert "device_class" not in notification.attributes
    assert "state_class" not in notification.attributes
    assert notification_entry.entity_category == EntityCategory.DIAGNOSTIC

    lockout_entry, lockout = entry_and_state("7e2c")
    assert lockout.state == STATE_UNKNOWN
    assert lockout_entry.entity_category == EntityCategory.DIAGNOSTIC

    fault_entry, fault = entry_and_state("8439")
    assert fault.state == STATE_UNKNOWN
    assert fault_entry.entity_category == EntityCategory.DIAGNOSTIC


# Code attributes from the manual (entities item: codes.py).
NO_CODE_ATTRIBUTES = {"description": None, "cause_solution": []}


def test_code_attributes_from_the_captures(
    stats_payload: dict[str, int | str], stats_payload_n095: dict[str, int | str]
) -> None:
    by_key = {d.key: d for d in SENSORS}

    # No code: the attributes keep their keys but hold nothing.
    for key in ("7940", "7e2c"):
        sensor = make_sensor(by_key[key], stats_payload)
        assert sensor.native_value is None
        assert sensor.extra_state_attributes == NO_CODE_ATTRIBUTES, key

    # Verify step: the real n095 capture.
    sensor = make_sensor(by_key["7940"], stats_payload_n095)
    assert sensor.native_value == "n095"
    attributes = sensor.extra_state_attributes
    assert attributes is not None
    assert attributes["description"] == "Probleem met driewegklep."
    assert attributes["cause_solution"] == [
        "Controleer de bedrading.",
        "Controleer de motor van de driewegklep.",
        "Controleer de behuizing van de driewegklep.",
        "Controleer parameter P047, P068 en P069.",
    ]
    assert len(attributes["cause_solution"]) == 4
    assert isinstance(attributes["cause_solution"], list)


@pytest.mark.parametrize(
    ("key", "raw", "state", "description"),
    [
        # Verify step: n120 falls in the n100-n165 FOTA range.
        ("7940", 120, "n120", "FOTA gerelateerde melding."),
        # Verify step: F254 is the last fault code in the manual.
        ("7e2c", 254, "F254", "Bypassmodus actief."),
        ("7e2c", 37, "F037", "Sensorfout retourleiding T04."),
        # Codes the manual does not list keep the state but have no text.
        ("7940", 99, "n099", None),
        ("7e2c", 2, "F002", None),
    ],
)
def test_code_attributes_follow_the_formatted_value(
    stats_payload: dict[str, int | str],
    key: str,
    raw: int,
    state: str,
    description: str | None,
) -> None:
    sensor = make_sensor({d.key: d for d in SENSORS}[key], {**stats_payload, key: raw})
    assert sensor.native_value == state
    attributes = sensor.extra_state_attributes
    assert attributes is not None
    assert attributes["description"] == description
    if description is None:
        assert attributes["cause_solution"] == []
    else:
        assert len(attributes["cause_solution"]) >= 1


def test_only_code_sensors_have_attributes(stats_payload: dict[str, int | str]) -> None:
    for description in SENSORS:
        sensor = make_sensor(description, stats_payload)
        if description.key in ("7940", "7e2c"):
            assert sensor.extra_state_attributes is not None, description.key
        else:
            assert sensor.extra_state_attributes is None, description.key


async def test_code_attributes_reach_the_state_machine(
    hass: HomeAssistant,
    stats_payload_n095: dict[str, int | str],
    stats_payload: dict[str, int | str],
) -> None:
    entry = await setup_entry(hass, stats_payload_n095)
    entity_registry = er.async_get(hass)

    def state_of(key: str):
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return state

    notification = state_of("7940")
    assert notification.state == "n095"
    assert notification.attributes["description"] == "Probleem met driewegklep."
    assert len(notification.attributes["cause_solution"]) == 4

    lockout = state_of("7e2c")
    assert lockout.state == STATE_UNKNOWN
    assert lockout.attributes["description"] is None
    assert lockout.attributes["cause_solution"] == []

    assert "description" not in state_of("8439").attributes
    assert "description" not in state_of("79b3").attributes

    # The attributes follow the value on the next poll.
    with patch(GET_STATS, return_value={**stats_payload, "7e2c": 254}):
        await scheduled_poll(hass, entry.runtime_data)
    assert state_of("7940").state == STATE_UNKNOWN
    assert state_of("7940").attributes["description"] is None
    lockout = state_of("7e2c")
    assert lockout.state == "F254"
    assert lockout.attributes["description"] == "Bypassmodus actief."
    assert len(lockout.attributes["cause_solution"]) == 2


# Firmware version sensor (entities item).
def test_firmware_description() -> None:
    description = {d.key: d for d in SENSORS}["47e0"]
    assert description.translation_key == "firmware_version"
    assert description.factor is None
    assert description.text_format is None
    assert description.code_lookup is None
    # The value is a string, so no numeric sentinel applies.
    assert description.none_values == frozenset()
    assert description.entity_category == EntityCategory.DIAGNOSTIC
    assert description.icon == "mdi:chip"
    assert description.native_unit_of_measurement is None
    assert description.device_class is None
    assert description.state_class is None


@pytest.mark.parametrize(
    "fixture_name", ["stats_payload", "stats_payload_standby", "stats_payload_n095"]
)
def test_firmware_value_is_the_string_unchanged(
    request: pytest.FixtureRequest, fixture_name: str
) -> None:
    # Verify step: every capture reports firmware V1.20-.
    payload: dict[str, int | str] = request.getfixturevalue(fixture_name)
    value = make_sensor({d.key: d for d in SENSORS}["47e0"], payload).native_value
    assert value == "V1.20-"
    assert type(value) is str


def test_firmware_value_is_none_only_when_missing(
    stats_payload: dict[str, int | str],
) -> None:
    description = {d.key: d for d in SENSORS}["47e0"]
    without = {k: v for k, v in stats_payload.items() if k != "47e0"}
    assert make_sensor(description, without).native_value is None
    # 32767 is not a sentinel for this field: an unexpected number is shown
    # as it is rather than hidden.
    assert make_sensor(description, {**stats_payload, "47e0": 32767}).native_value == (
        32767
    )


async def test_firmware_state_is_diagnostic_text(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload)
    entity_registry = er.async_get(hass)
    entity_id = entity_registry.async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, f"{HOST}_47e0"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "V1.20-"
    assert state.attributes["icon"] == "mdi:chip"
    assert "unit_of_measurement" not in state.attributes
    assert "device_class" not in state.attributes
    assert "state_class" not in state.attributes
    registry_entry = entity_registry.async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.entity_category == EntityCategory.DIAGNOSTIC
    assert registry_entry.translation_key == "firmware_version"


# Raw bitfield and unknown fields (entities item): key -> translation_key.
RAW_SENSORS = {
    "7e51": "heat_demand_status",
    "7e7a": "burner_status",
    "77c3": "status_flags",
    "77d2": "system_io",
    "f9f2": "bivalent_service_flags",
    "6101": "raw_6101",
    "6117": "raw_6117",
    "7774": "raw_7774",
    "77de": "raw_77de",
}


def test_raw_descriptions() -> None:
    by_key = {d.key: d for d in SENSORS}
    for key, translation_key in RAW_SENSORS.items():
        description = by_key[key]
        assert description.translation_key == translation_key, key
        assert description.factor is None, key
        assert description.text_format is None, key
        assert description.code_lookup is None, key
        assert description.none_values == frozenset(), key
        assert description.entity_category == EntityCategory.DIAGNOSTIC, key
        assert description.entity_registry_enabled_default is False, key
        assert description.native_unit_of_measurement is None, key
        assert description.device_class is None, key
        assert description.state_class is None, key

    # Every other sensor is enabled by default.
    for description in SENSORS:
        if description.key not in RAW_SENSORS:
            assert description.entity_registry_enabled_default is True, description.key


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        # Verify step: the raw number is shown, 255 is not a sentinel here.
        ("77d2", 17102),
        ("7774", 255),
        ("77de", 255),
        ("7e51", 206),
        ("7e7a", 64),
        ("77c3", 208),
        ("f9f2", 265),
        ("6101", 396),
        ("6117", 3),
    ],
)
def test_raw_values_from_first_capture(
    stats_payload: dict[str, int | str], key: str, expected: int
) -> None:
    value = make_sensor({d.key: d for d in SENSORS}[key], stats_payload).native_value
    assert value == expected
    assert type(value) is int


def test_raw_values_keep_32767(stats_payload: dict[str, int | str]) -> None:
    # 32767 means "not available" elsewhere; a raw field shows it as it is.
    description = {d.key: d for d in SENSORS}["77d2"]
    assert make_sensor(description, {**stats_payload, "77d2": 32767}).native_value == (
        32767
    )


async def test_raw_sensors_are_disabled_diagnostics(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    entity_registry = er.async_get(hass)

    for key, translation_key in RAW_SENSORS.items():
        entity_id = entity_registry.async_get_entity_id(
            SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
        )
        assert entity_id is not None, key
        registry_entry = entity_registry.async_get(entity_id)
        assert registry_entry is not None
        assert registry_entry.entity_category == EntityCategory.DIAGNOSTIC, key
        assert registry_entry.translation_key == translation_key, key
        assert registry_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION, key
        # A disabled entity is registered but has no state.
        assert hass.states.get(entity_id) is None, key

    # Enabling one in the registry brings it up with the raw value after a reload.
    entity_id = entity_registry.async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, f"{HOST}_77d2"
    )
    assert entity_id is not None
    entity_registry.async_update_entity(entity_id, disabled_by=None)
    with patch(GET_STATS, return_value=stats_payload):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "17102"
    assert "unit_of_measurement" not in state.attributes
    assert "device_class" not in state.attributes
    assert "state_class" not in state.attributes


def state_by_unique_id(hass: HomeAssistant, key: str):
    entity_id = er.async_get(hass).async_get_entity_id(
        SENSOR_DOMAIN, DOMAIN, f"{HOST}_{key}"
    )
    assert entity_id is not None, key
    state = hass.states.get(entity_id)
    assert state is not None, key
    return state


async def test_room_temperature_entity_id_state_and_unit(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload)
    state = hass.states.get("sensor.intergas_xtend_room_temperature")
    assert state is not None
    assert state.state == "26.41"
    assert state.attributes["unit_of_measurement"] == "°C"


async def test_standby_states_match_the_summary_page(
    hass: HomeAssistant, stats_payload_standby: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_standby)
    expected = {
        "79b3": "22.62",  # room temperature
        "62d1": "16.17",  # outside temperature
        "7ed3": "1.85",  # CH water pressure
        "629c": "15.03",  # CH water flow
        "50f2": "7",  # retrieved power
        "6115": "100.0",  # DHW available
    }
    for key, value in expected.items():
        assert state_by_unique_id(hass, key).state == value, key


async def test_unavailable_value_and_empty_notification_are_unknown(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload)
    assert state_by_unique_id(hass, "6206").state == STATE_UNKNOWN
    notification = state_by_unique_id(hass, "7940")
    assert notification.state == STATE_UNKNOWN
    assert notification.attributes["description"] is None
    assert notification.attributes["cause_solution"] == []


async def test_n095_state_and_attributes(
    hass: HomeAssistant, stats_payload_n095: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload_n095)
    notification = state_by_unique_id(hass, "7940")
    assert notification.state == "n095"
    assert notification.attributes["description"] == "Probleem met driewegklep."
    assert len(notification.attributes["cause_solution"]) == 4


async def test_32_sensors_and_1_button_are_registered(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    domains = [
        e.domain
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    ]
    assert domains.count(SENSOR_DOMAIN) == 32
    assert domains.count("button") == 1
    assert len(domains) == 33
