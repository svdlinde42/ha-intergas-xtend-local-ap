"""Button platform for the Intergas Xtend integration.

One button, "Poll now", asks the coordinator for an immediate poll. It is the
recovery step named in the repairs issue: once the user has re-enabled the
access point, one successful press ends the back-off without a restart.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import XtendConfigEntry, XtendCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: XtendConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the "Poll now" button for this device."""
    async_add_entities([XtendPollNowButton(entry.runtime_data)])


class XtendPollNowButton(CoordinatorEntity[XtendCoordinator], ButtonEntity):
    """Ask the coordinator for one poll right now."""

    _attr_has_entity_name = True
    _attr_translation_key = "poll_now"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: XtendCoordinator) -> None:
        """Create the button; the unique id follows the host like every entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.api.host}_poll_now"
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        """Always available.

        A CoordinatorEntity goes unavailable when the last poll failed. That is
        exactly when this button is needed, so it stays available.
        """
        return True

    async def async_press(self) -> None:
        """Poll once. On success the coordinator ends the back-off itself."""
        await self.coordinator.async_request_refresh()
