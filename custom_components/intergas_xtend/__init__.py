"""The Intergas Xtend integration.

Monitors an Intergas Xtend boiler through the REST interface of its built-in
Wi-Fi access point. Phase 1 is read-only; see AGENTS.md for the design.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intergas Xtend from a config entry."""
    # Reload when the options flow changes the poll interval, so the
    # coordinator is recreated with the new interval.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after its options changed."""
    await hass.config_entries.async_reload(entry.entry_id)
