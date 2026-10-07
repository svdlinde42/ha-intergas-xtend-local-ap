"""Sensor descriptions: one table, one entry per stats field.

This table lives here and not in const.py because api.py imports const.py and
must stay importable without Home Assistant, while SensorEntityDescription is
a Home Assistant class.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)

from .const import FIRMWARE_FIELD, NOT_AVAILABLE


@dataclass(frozen=True, kw_only=True)
class XtendSensorDescription(SensorEntityDescription):
    """Describe how one stats field becomes a sensor value.

    key is the hex id of the field. factor scales the raw integer (value =
    raw * factor); None keeps the raw value. none_values are raw values that
    mean "no value", so the sensor reports None. text_format is a printf-style
    format applied to the raw value, e.g. "n%03d" for notification codes.
    """

    factor: float | None = None
    none_values: frozenset[int] = frozenset({NOT_AVAILABLE})
    text_format: str | None = None


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


# Source: docs/stats-mapping.md. Do not change factors or units without
# updating that file. One entry per id in STATS_FIELDS, grouped like the
# sections of that document. The per-group entities items in plans/prd.json
# fill in translation keys, factors, units and classes.
SENSORS: tuple[XtendSensorDescription, ...] = (
    # Meldingen (notification, lockout and boiler fault codes)
    XtendSensorDescription(key="7940"),
    XtendSensorDescription(key="7e2c"),
    XtendSensorDescription(key="8439"),
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
    # Systeem: the firmware version is a string, so no numeric sentinel applies.
    XtendSensorDescription(key=FIRMWARE_FIELD, none_values=frozenset()),
    # Bitvelden en ongeduide sleutels
    XtendSensorDescription(key="7e51"),
    XtendSensorDescription(key="7e7a"),
    XtendSensorDescription(key="77c3"),
    XtendSensorDescription(key="77d2"),
    XtendSensorDescription(key="f9f2"),
    XtendSensorDescription(key="6101"),
    XtendSensorDescription(key="6117"),
    XtendSensorDescription(key="7774"),
    XtendSensorDescription(key="77de"),
)
