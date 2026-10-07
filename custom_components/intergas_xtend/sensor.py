"""Sensor platform for the Intergas Xtend integration.

One generic ``XtendSensor`` class serves every entry of the SENSORS table in
descriptions.py. The table says how a raw stats value becomes a sensor value
(sentinels, value map, scale factor, text format); this module only applies
those rules.
There are no per-field subclasses: a new field is a new table row, not new code.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import XtendConfigEntry, XtendCoordinator
from .descriptions import SENSORS, XtendSensorDescription


async def async_setup_entry(
    hass: HomeAssistant,
    entry: XtendConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one sensor per SENSORS entry for this device."""
    coordinator = entry.runtime_data
    async_add_entities(XtendSensor(coordinator, description) for description in SENSORS)


class XtendSensor(CoordinatorEntity[XtendCoordinator], SensorEntity):
    """One stats field, converted with the rules of its description.

    Availability follows the coordinator: ``CoordinatorEntity.available`` is
    ``coordinator.last_update_success``, so every sensor goes unavailable when
    a poll fails instead of showing a stale value.
    """

    entity_description: XtendSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: XtendCoordinator, description: XtendSensorDescription
    ) -> None:
        """Create the sensor; the unique id is the host plus the field id."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.api.host}_{description.key}"
        # The per-group items in plans/prd.json give every description its own
        # translation key; until then the field id names the entity.
        self._attr_translation_key = description.translation_key or description.key
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> int | float | str | None:
        """Convert the raw value: sentinel, then value map, text format or factor.

        A raw value that is not a number cannot be mapped, formatted or
        scaled; it becomes None rather than an exception that would stop the
        update of the other sensors. A code missing from the value map is
        None as well.
        """
        description = self.entity_description
        raw = self.coordinator.data.get(description.key)
        if raw is None or raw in description.none_values:
            return None
        if description.value_map is not None:
            if not isinstance(raw, int):
                return None
            return description.value_map.get(raw)
        if description.text_format is not None:
            if not isinstance(raw, int | float):
                return None
            return description.text_format % raw
        if description.factor is not None:
            if not isinstance(raw, int | float):
                return None
            return round(raw * description.factor, 2)
        return raw

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Add the raw code for enum sensors, the manual's text for code sensors.

        A description with a value_map has the attribute code: the raw
        integer, also for a code the map does not know, so an unknown state
        can still be traced; None when the field is missing or not an integer.
        Descriptions with a code_lookup (notification and lockout code) have
        description and cause_solution. The text comes from codes.py and is
        Dutch, quoted from the manual. Without a code, or for a code the
        manual does not list, description is None and cause_solution is
        empty. Either way the attributes keep the same keys at all times.
        """
        description = self.entity_description
        if description.value_map is not None:
            raw = self.coordinator.data.get(description.key)
            return {"code": raw if isinstance(raw, int) else None}
        lookup = description.code_lookup
        if lookup is None:
            return None
        value = self.native_value
        info = lookup(value) if isinstance(value, str) else None
        if info is None:
            return {"description": None, "cause_solution": []}
        return {
            "description": info.description,
            "cause_solution": list(info.cause_solution),
        }
