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
from homeassistant.const import UnitOfTemperature

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
    XtendSensorDescription(key="503e"),
    XtendSensorDescription(key="5088"),
    XtendSensorDescription(key="5077"),
    XtendSensorDescription(key="50f2"),
    XtendSensorDescription(key="5041"),
    # CV-water
    XtendSensorDescription(key="629c"),
    temperature("6280", "ch_return_temperature"),
    temperature("621d", "ch_supply_temperature"),
    temperature("62ed", "ch_setpoint"),
    XtendSensorDescription(key="7ed3"),
    # Tapwater (Xtore)
    temperature("610b", "dhw_temperature"),
    temperature("61eb", "dhw_setpoint"),
    XtendSensorDescription(key="6115"),
    XtendSensorDescription(key="61ba"),
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
