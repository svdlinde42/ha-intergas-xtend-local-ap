"""Sensor platform for the Intergas Xtend integration.

The coordinator item forwards setup to this platform. The sensor entities
(one generic XtendSensor per SENSORS entry in descriptions.py) are added by the
entities items in plans/prd.json; until then this platform adds nothing.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import XtendConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: XtendConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform; no entities are defined yet."""
