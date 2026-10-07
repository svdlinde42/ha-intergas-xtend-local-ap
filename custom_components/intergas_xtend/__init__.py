"""The Intergas Xtend integration.

Monitors an Intergas Xtend boiler through the REST interface of its built-in
Wi-Fi access point. Phase 1 is read-only; see AGENTS.md for the design.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intergas Xtend from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True
