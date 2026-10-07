"""Binary sensor platform for the Intergas Xtend integration.

Each binary sensor is one bit of a bitfield stats field that the coordinator
already polls (77d2, 77c3, f9f2). No extra request and no extra field: the
entities read coordinator.data only, like the sensors.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import NOT_AVAILABLE
from .coordinator import XtendConfigEntry, XtendCoordinator


@dataclass(frozen=True, kw_only=True)
class XtendBinarySensorDescription(BinarySensorEntityDescription):
    """One bit of a stats field.

    key is the stats id of the bitfield, bit the bit number (0 = lowest bit).
    The bit is on when (raw >> bit) & 1 is 1.
    """

    bit: int


# Source: bit tables 77d2, 77c3 and f9f2 in docs/xtend-enums.json. The
# statistics page source confirms 77c3 bit 3 (SilentModeActive), f9f2 bit 7
# (HeatpumpRequested) and f9f2 bit 8 (BoilerRequested); the 77d2 bits follow
# the code order in app.js (confidence A). Do not add bits without updating
# that file.
BINARY_SENSORS: tuple[XtendBinarySensorDescription, ...] = (
    XtendBinarySensorDescription(
        key="77d2",
        bit=5,
        translation_key="compressor_running",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    XtendBinarySensorDescription(
        key="77d2",
        bit=1,
        translation_key="ch_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    XtendBinarySensorDescription(
        key="77d2",
        bit=0,
        translation_key="dhw_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    XtendBinarySensorDescription(key="77c3", bit=3, translation_key="silent_mode"),
    XtendBinarySensorDescription(
        key="f9f2",
        bit=7,
        translation_key="heat_demand_heat_pump",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    XtendBinarySensorDescription(
        key="f9f2",
        bit=8,
        translation_key="heat_demand_boiler",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    XtendBinarySensorDescription(key="f9f2", bit=14, translation_key="defrost_active"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: XtendConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one binary sensor per BINARY_SENSORS entry for this device."""
    coordinator = entry.runtime_data
    async_add_entities(
        XtendBinarySensor(coordinator, description) for description in BINARY_SENSORS
    )


class XtendBinarySensor(CoordinatorEntity[XtendCoordinator], BinarySensorEntity):
    """One bit of a stats field.

    Availability follows the coordinator, like XtendSensor.
    """

    entity_description: XtendBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: XtendCoordinator, description: XtendBinarySensorDescription
    ) -> None:
        """Create the binary sensor; the unique id is host, field id and bit.

        Several bits share one field, so the field id alone is not unique.
        """
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.api.host}_{description.key}_bit{description.bit}"
        )
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return the bit, or None when the field is missing or not available.

        32767 is the "not available" sentinel of every numeric field
        (docs/stats-mapping.md); a value that is not an integer cannot hold
        bits and is None as well.
        """
        raw = self.coordinator.data.get(self.entity_description.key)
        if not isinstance(raw, int) or raw == NOT_AVAILABLE:
            return None
        return bool((raw >> self.entity_description.bit) & 1)
