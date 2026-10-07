"""Sensor descriptions: one table, one entry per stats field.

This table lives here and not in const.py because api.py imports const.py and
must stay importable without Home Assistant, while SensorEntityDescription is
a Home Assistant class.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription

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
    XtendSensorDescription(key="6280"),
    XtendSensorDescription(key="621d"),
    XtendSensorDescription(key="62ed"),
    XtendSensorDescription(key="7ed3"),
    # Tapwater (Xtore)
    XtendSensorDescription(key="610b"),
    XtendSensorDescription(key="61eb"),
    XtendSensorDescription(key="6115"),
    XtendSensorDescription(key="61ba"),
    XtendSensorDescription(key="620f"),
    XtendSensorDescription(key="6206"),
    # Ruimte en buiten
    XtendSensorDescription(key="79b3"),
    XtendSensorDescription(key="7921"),
    XtendSensorDescription(key="62d1"),
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
