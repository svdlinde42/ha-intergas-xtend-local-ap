"""Sensor descriptions: one table, one entry per stats field.

This table lives here and not in const.py because api.py imports const.py and
must stay importable without Home Assistant, while SensorEntityDescription is
a Home Assistant class.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)

from .codes import CodeInfo, fault_info, notification_info
from .const import FIRMWARE_FIELD, NO_CODE, NO_FAULT, NOT_AVAILABLE
from .operating_modes import OPERATING_MODES


@dataclass(frozen=True, kw_only=True)
class XtendSensorDescription(SensorEntityDescription):
    """Describe how one stats field becomes a sensor value.

    key is the hex id of the field. factor scales the raw integer (value =
    raw * factor); None keeps the raw value. none_values are raw values that
    mean "no value", so the sensor reports None. text_format is a printf-style
    format applied to the raw value, e.g. "n%03d" for notification codes.
    code_lookup maps the formatted value (e.g. "n095") to the manual's entry
    in codes.py; the sensor shows it as the attributes description and
    cause_solution. None means the sensor has no such attributes.
    value_map turns a raw integer code into an enum state name (for a sensor
    with device_class ENUM). It applies after none_values; a code that is not
    in the map gives None, so an unknown code shows as unknown and no name is
    invented.
    value_fn computes the value from the whole stats payload, for a derived
    sensor with no stats field of its own (DERIVED_SENSORS); key is then a
    name, not a hex id, and the other conversion fields are not used.
    """

    factor: float | None = None
    none_values: frozenset[int] = frozenset({NOT_AVAILABLE})
    text_format: str | None = None
    code_lookup: Callable[[str], CodeInfo | None] | None = None
    value_map: Mapping[int, str] | None = None
    value_fn: Callable[[Mapping[str, int | str]], float | None] | None = None


def temperature(key: str, translation_key: str) -> XtendSensorDescription:
    """Describe a temperature field: raw value in 0.01 °C (docs/stats-mapping.md)."""
    return XtendSensorDescription(
        key=key,
        translation_key=translation_key,
        factor=0.01,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    )


def power(key: str, translation_key: str) -> XtendSensorDescription:
    """Describe a power field: raw value in W.

    docs/stats-mapping.md lists factor 0,001 and kW; the Xtend summary page
    shows the same quantity in W, so the raw value is used as it is.
    """
    return XtendSensorDescription(
        key=key,
        translation_key=translation_key,
        factor=1,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    )


def energy(key: str, translation_key: str) -> XtendSensorDescription:
    """Describe an energy total: whole kWh since commissioning.

    Source: docs/stats-mapping.md, section "Energie totaal". The value only
    goes up, so the sensor can be used in the Home Assistant Energy dashboard.
    """
    return XtendSensorDescription(
        key=key,
        translation_key=translation_key,
        factor=1,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )


def hours(key: str, translation_key: str) -> XtendSensorDescription:
    """Describe an hour counter of the statistics page (docs/stats-mapping.md)."""
    return XtendSensorDescription(
        key=key,
        translation_key=translation_key,
        factor=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    )


def count(key: str, translation_key: str) -> XtendSensorDescription:
    """Describe a start or cycle counter of the statistics page: no unit."""
    return XtendSensorDescription(
        key=key,
        translation_key=translation_key,
        factor=1,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    )


def raw(key: str, translation_key: str) -> XtendSensorDescription:
    """Describe a bitfield or unknown field: the raw number, nothing more.

    The meaning of these fields is not known (docs/stats-mapping.md, section
    "Bitvelden en ongeduide sleutels"), so no factor, unit or sentinel is
    applied: 255 and 32767 are shown as they are, because hiding them would
    hide the data needed to work out what the field means. They are
    diagnostic and disabled by default; the research item in plans/prd.json
    uses them to map the derived states of the summary page.
    """
    return XtendSensorDescription(
        key=key,
        translation_key=translation_key,
        none_values=frozenset(),
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )


# DHW state of field 6117 (code -> enum state). Source: table 6117 in
# docs/xtend-enums.json (app.js, confirmed by the owner 2026-10-07); the names
# are lowercased because Home Assistant enum states allow only [a-z0-9_].
DHW_STATES: dict[int, str] = {
    0: "dhw_idle",
    1: "dhw_start",
    3: "dhw_active",
    7: "dhw_suspended",
    8: "dhw_reclaim",
    9: "dhw_postrun",
}


# Source: docs/stats-mapping.md. Do not change factors or units without
# updating that file. One entry per id in STATS_FIELDS, grouped like the
# sections of that document. The per-group entities items in plans/prd.json
# fill in translation keys, factors, units and classes.
SENSORS: tuple[XtendSensorDescription, ...] = (
    # Meldingen (notification, lockout and boiler fault codes). 255 means no
    # notification or lockout; the codes are shown as the display shows them
    # (n095, F037). codes.py (from docs/fault-codes.json) holds their meaning,
    # exposed as attributes through code_lookup.
    XtendSensorDescription(
        key="7940",
        translation_key="notification_code",
        none_values=frozenset({NO_CODE}),
        text_format="n%03d",
        code_lookup=notification_info,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    XtendSensorDescription(
        key="7e2c",
        translation_key="lockout_code",
        none_values=frozenset({NO_CODE}),
        text_format="F%03d",
        code_lookup=fault_info,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # 8439 is the CV boiler's own OpenTherm fault code: 0 means no fault and
    # the raw number is shown, because the Xtend manual does not cover it, so
    # there is no code_lookup and no attributes.
    XtendSensorDescription(
        key="8439",
        translation_key="boiler_fault_code",
        none_values=frozenset({NO_FAULT}),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Vermogen en COP
    power("503e", "heat_pump_power"),
    power("5088", "boiler_power"),
    power("5077", "total_thermal_power"),
    power("50f2", "retrieved_power"),
    # COP is a ratio: raw value in 0.1, no unit and no device class.
    XtendSensorDescription(
        key="5041",
        translation_key="cop",
        factor=0.1,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heat-pump",
    ),
    # CV-water: flow in 0.01 l/min and pressure in 0.01 bar (docs/stats-mapping.md).
    XtendSensorDescription(
        key="629c",
        translation_key="ch_flow",
        factor=0.01,
        native_unit_of_measurement=UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    temperature("6280", "ch_return_temperature"),
    temperature("621d", "ch_supply_temperature"),
    temperature("62ed", "ch_setpoint"),
    XtendSensorDescription(
        key="7ed3",
        translation_key="ch_pressure",
        factor=0.01,
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Tapwater (Xtore)
    temperature("610b", "dhw_temperature"),
    temperature("61eb", "dhw_setpoint"),
    # Available hot water in 0.01 % (10000 = 100 %); 32767 while unknown.
    XtendSensorDescription(
        key="6115",
        translation_key="dhw_available",
        factor=0.01,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Xtore tank size in liters: a fixed property, so diagnostic and no
    # state class.
    XtendSensorDescription(
        key="61ba",
        translation_key="dhw_volume",
        factor=1,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    temperature("620f", "aux1_temperature"),
    temperature("6206", "aux2_temperature"),
    # Ruimte en buiten
    temperature("79b3", "room_temperature"),
    temperature("7921", "room_target_temperature"),
    temperature("62d1", "outside_temperature"),
    # Systeem: the firmware version is a string ("V1.20-"), shown unchanged;
    # no factor and no numeric sentinel apply.
    XtendSensorDescription(
        key=FIRMWARE_FIELD,
        translation_key="firmware_version",
        none_values=frozenset(),
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:chip",
    ),
    # Operating mode: an enum of 38 codes (docs/operating-modes.json, via
    # operating_modes.py). An unknown code or 32767 shows as unknown.
    XtendSensorDescription(
        key="7e51",
        translation_key="operating_mode",
        device_class=SensorDeviceClass.ENUM,
        options=sorted(OPERATING_MODES.values()),
        value_map=OPERATING_MODES,
    ),
    # DHW state: an enum of 6 codes (DHW_STATES). An unknown code or 32767
    # shows as unknown.
    XtendSensorDescription(
        key="6117",
        translation_key="dhw_state",
        device_class=SensorDeviceClass.ENUM,
        options=sorted(DHW_STATES.values()),
        value_map=DHW_STATES,
    ),
    # Bitvelden en ongeduide sleutels: raw diagnostics, disabled by default.
    raw("7e7a", "burner_status"),
    raw("77c3", "status_flags"),
    raw("77d2", "system_io"),
    raw("f9f2", "bivalent_service_flags"),
    # 6101 is a volume in 0.01 L (app.js); what it measures is not known, so
    # it stays a disabled diagnostic. 32767 means "not available", as for
    # every other scaled field.
    XtendSensorDescription(
        key="6101",
        translation_key="raw_6101",
        factor=0.01,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    raw("7774", "raw_7774"),
    raw("77de", "raw_77de"),
    # Energie totaal (statistics page, column Total): whole kWh.
    energy("63b3", "ch_heat_pump_energy_used"),
    energy("63f0", "ch_heat_pump_energy_generated"),
    energy("63df", "ch_boiler_energy_generated"),
    energy("6358", "dhw_heat_pump_energy_used"),
    energy("6339", "dhw_heat_pump_energy_generated"),
    energy("4a76", "dhw_boiler_energy_generated"),
    # Tellers (statistics page): hours and counts, diagnostic.
    count("6a8e", "compressor_starts_ch"),
    count("6a8d", "compressor_starts_dhw"),
    hours("6ac5", "compressor_runtime_ch"),
    hours("6a6c", "compressor_runtime_dhw"),
    hours("71a7", "uptime"),
    count("7160", "power_cycles"),
    count("6a53", "defrost_cycles"),
    hours("4e13", "water_pump_hours"),
    hours("4eeb", "crank_heater_hours"),
    hours("4e3a", "base_pan_heater_hours"),
    count("4a22", "water_pump_starts"),
    count("4a3c", "crank_heater_starts"),
    count("4aeb", "base_pan_heater_starts"),
    count("8e00", "boiler_starts"),
    hours("8ef9", "boiler_runtime_ch"),
    hours("8e37", "boiler_runtime_dhw"),
    count("8e18", "boiler_flame_loss"),
)


def cop_total(
    generated_key: str, used_key: str
) -> Callable[[Mapping[str, int | str]], float | None]:
    """Return a value_fn for COP total = generated / used, rounded to 1 decimal.

    Source: docs/stats-mapping.md, section "Energie totaal": the statistics
    page computes this itself; there is no stats field for it. A missing,
    non-integer or 32767 total gives None, and so does used = 0.
    """

    def value(data: Mapping[str, int | str]) -> float | None:
        generated = data.get(generated_key)
        used = data.get(used_key)
        if not isinstance(generated, int) or not isinstance(used, int):
            return None
        if NOT_AVAILABLE in (generated, used) or used == 0:
            return None
        return round(generated / used, 1)

    return value


def derived_cop(key: str, generated_key: str, used_key: str) -> XtendSensorDescription:
    """Describe a COP total: a ratio, so no unit and no device class."""
    return XtendSensorDescription(
        key=key,
        translation_key=key,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heat-pump",
        value_fn=cop_total(generated_key, used_key),
    )


# Sensors computed from other stats fields. They have no field of their own,
# so they are kept out of SENSORS, which has one entry per STATS_FIELDS id.
DERIVED_SENSORS: tuple[XtendSensorDescription, ...] = (
    derived_cop("cop_total_ch", "63f0", "63b3"),
    derived_cop("cop_total_dhw", "6339", "6358"),
)
