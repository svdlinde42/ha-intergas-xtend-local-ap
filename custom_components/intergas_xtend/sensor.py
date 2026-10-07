"""Sensor platform for the Intergas Xtend integration.

One generic ``XtendSensor`` class serves every entry of the SENSORS table in
descriptions.py. The table says how a raw stats value becomes a sensor value
(sentinels, scale factor, text format); this module only applies those rules.
There are no per-field subclasses: a new field is a new table row, not new code.
"""

from __future__ import annotations

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
        """Convert the raw value: sentinel -> None, then text format or factor.

        A raw value that is not a number cannot be formatted or scaled; it
        becomes None rather than an exception that would stop the update of
        the other sensors.
        """
        description = self.entity_description
        raw = self.coordinator.data.get(description.key)
        if raw is None or raw in description.none_values:
            return None
        if description.text_format is not None:
            if not isinstance(raw, int | float):
                return None
            return description.text_format % raw
        if description.factor is not None:
            if not isinstance(raw, int | float):
                return None
            return round(raw * description.factor, 2)
        return raw
