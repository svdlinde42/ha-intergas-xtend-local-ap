"""Binary sensor tests: one bit of a polled bitfield per entity.

The value tests build an XtendBinarySensor around a stub coordinator; the
platform tests set up a real config entry with XtendApi.async_get_stats patched.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
)
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.intergas_xtend.binary_sensor import (
    BINARY_SENSORS,
    XtendBinarySensor,
)
from custom_components.intergas_xtend.const import DOMAIN, STATS_FIELDS

from .test_coordinator import HOST, setup_entry

ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = ROOT / "custom_components" / "intergas_xtend"
ENUMS_JSON = ROOT / "docs" / "xtend-enums.json"

BY_KEY = {d.translation_key: d for d in BINARY_SENSORS}

# translation_key -> (stats field, bit, device class), as listed in plans/prd.json.
EXPECTED = {
    "compressor_running": ("77d2", 5, BinarySensorDeviceClass.RUNNING),
    "ch_pump": ("77d2", 1, BinarySensorDeviceClass.RUNNING),
    "dhw_pump": ("77d2", 0, BinarySensorDeviceClass.RUNNING),
    "silent_mode": ("77c3", 3, None),
    "heat_demand_heat_pump": ("f9f2", 7, BinarySensorDeviceClass.HEAT),
    "heat_demand_boiler": ("f9f2", 8, BinarySensorDeviceClass.HEAT),
    "defrost_active": ("f9f2", 14, None),
}

# Bit names in docs/xtend-enums.json that each entity stands for.
DOC_BIT_NAMES = {
    "compressor_running": "compressorRunning",
    "ch_pump": "chPumpOn",
    "dhw_pump": "dhwPumpOn",
    "silent_mode": "SilentModeActive",
    "heat_demand_heat_pump": "HeatpumpRequested",
    "heat_demand_boiler": "BoilerRequested",
    "defrost_active": "DefrostActive",
}


def make_binary_sensor(
    translation_key: str, data: dict[str, int | str]
) -> XtendBinarySensor:
    """Build a binary sensor around a stub coordinator; no Home Assistant needed."""
    coordinator = SimpleNamespace(
        data=data,
        api=SimpleNamespace(host=HOST),
        device_info={"identifiers": {(DOMAIN, HOST)}},
        last_update_success=True,
    )
    return XtendBinarySensor(coordinator, BY_KEY[translation_key])  # type: ignore[arg-type]


def test_descriptions_match_the_prd() -> None:
    assert len(BINARY_SENSORS) == 7
    assert set(BY_KEY) == set(EXPECTED)
    for key, (field, bit, device_class) in EXPECTED.items():
        description = BY_KEY[key]
        assert (description.key, description.bit) == (field, bit), key
        assert description.device_class == device_class, key
        # The bitfields are already polled; no extra stats field is needed.
        assert description.key in STATS_FIELDS


def test_bits_match_docs_xtend_enums() -> None:
    tables = {
        t["field"]: t["values"]
        for t in json.loads(ENUMS_JSON.read_text(encoding="utf-8"))["tables"]
        if t["kind"] == "bits"
    }
    for key, name in DOC_BIT_NAMES.items():
        description = BY_KEY[key]
        assert tables[description.key][str(description.bit)] == name, key


@pytest.mark.parametrize(
    ("key", "data", "expected"),
    [
        ("dhw_pump", {"77d2": 0b1}, True),
        ("dhw_pump", {"77d2": 0b10}, False),
        ("ch_pump", {"77d2": 0b10}, True),
        ("defrost_active", {"f9f2": 1 << 14}, True),
        ("defrost_active", {"f9f2": (1 << 14) - 1}, False),
        ("silent_mode", {"77c3": 0}, False),
        ("silent_mode", {"77c3": 32767}, None),
        ("silent_mode", {}, None),
        ("silent_mode", {"77c3": "8"}, None),
    ],
)
def test_is_on_reads_one_bit(
    key: str, data: dict[str, int | str], expected: bool | None
) -> None:
    assert make_binary_sensor(key, data).is_on is expected


def test_unique_id_is_host_field_and_bit() -> None:
    sensor = make_binary_sensor("heat_demand_boiler", {})
    assert sensor.unique_id == f"{HOST}_f9f2_bit8"
    assert len({make_binary_sensor(k, {}).unique_id for k in BY_KEY}) == 7


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "stats_payload_n095",
            {
                "compressor_running": True,
                "heat_demand_heat_pump": True,
                "heat_demand_boiler": False,
            },
        ),
        (
            "stats_payload",
            {"heat_demand_boiler": True, "compressor_running": False},
        ),
        (
            "stats_payload_standby",
            {
                "compressor_running": False,
                "silent_mode": False,
                "heat_demand_heat_pump": False,
                "heat_demand_boiler": False,
                "defrost_active": False,
                "ch_pump": True,
            },
        ),
    ],
)
def test_values_from_the_captures(
    request: pytest.FixtureRequest, fixture: str, expected: dict[str, bool]
) -> None:
    # Verify step of the binary sensor item.
    data = request.getfixturevalue(fixture)
    for key, value in expected.items():
        assert make_binary_sensor(key, data).is_on is value, (fixture, key)


async def test_states_under_the_device(
    hass: HomeAssistant, stats_payload_n095: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload_n095)
    registry = er.async_get(hass)
    entries = [
        e
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == BINARY_SENSOR_DOMAIN
    ]
    assert len(entries) == 7
    assert len({e.device_id for e in entries}) == 1

    compressor = hass.states.get("binary_sensor.intergas_xtend_compressor_running")
    assert compressor is not None
    assert compressor.state == STATE_ON
    assert compressor.attributes[ATTR_DEVICE_CLASS] == BinarySensorDeviceClass.RUNNING
    boiler = hass.states.get("binary_sensor.intergas_xtend_heat_demand_boiler")
    assert boiler is not None
    assert boiler.state == STATE_OFF
    silent = hass.states.get("binary_sensor.intergas_xtend_silent_mode")
    assert silent is not None
    assert silent.state == STATE_OFF


async def test_not_available_gives_unknown(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    await setup_entry(hass, {**stats_payload, "77c3": 32767})
    state = hass.states.get("binary_sensor.intergas_xtend_silent_mode")
    assert state is not None
    assert state.state == STATE_UNKNOWN


def test_every_translation_key_has_a_name_in_all_files() -> None:
    keys = {d.translation_key for d in BINARY_SENSORS}
    for name in ("strings.json", "translations/en.json", "translations/nl.json"):
        texts = json.loads((INTEGRATION / name).read_text(encoding="utf-8"))
        binary_sensors = texts["entity"]["binary_sensor"]
        assert set(binary_sensors) == keys, name
        for key, value in binary_sensors.items():
            assert isinstance(value["name"], str) and value["name"], (name, key)


def test_names_follow_the_prd() -> None:
    en = json.loads(
        (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
    )["entity"]["binary_sensor"]
    nl = json.loads(
        (INTEGRATION / "translations" / "nl.json").read_text(encoding="utf-8")
    )["entity"]["binary_sensor"]
    expected = {
        "compressor_running": ("Compressor running", "Compressor actief"),
        "ch_pump": ("CH pump", "Cv-pomp"),
        "dhw_pump": ("DHW pump", "Tapwaterpomp"),
        "silent_mode": ("Silent mode", "Stille modus"),
        "heat_demand_heat_pump": ("Heat demand heat pump", "Warmtevraag warmtepomp"),
        "heat_demand_boiler": ("Heat demand boiler", "Warmtevraag ketel"),
        "defrost_active": ("Defrost active", "Ontdooien actief"),
    }
    for key, (en_name, nl_name) in expected.items():
        assert en[key]["name"] == en_name
        assert nl[key]["name"] == nl_name
