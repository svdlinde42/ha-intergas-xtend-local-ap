"""The Intergas Xtend integration.

Monitors an Intergas Xtend boiler through the REST interface of its built-in
Wi-Fi access point. Phase 1 is read-only; see AGENTS.md for the design.
"""

from __future__ import annotations

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import XtendApi
from .const import DOMAIN
from .coordinator import XtendConfigEntry, XtendCoordinator, issue_id_for_host

# Phase 1 is read-only: sensors, binary sensors (status bits) plus the
# "Poll now" button, which only polls.
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: XtendConfigEntry) -> bool:
    """Set up Intergas Xtend from a config entry.

    One coordinator per entry does all HTTP traffic. The first refresh runs
    before the platforms load; when the device does not answer it raises
    ConfigEntryNotReady so Home Assistant retries the setup later.
    """
    api = XtendApi(async_get_clientsession(hass), entry.data[CONF_HOST])
    coordinator = XtendCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Reload when the options flow changes the poll interval, so the
    # coordinator is recreated with the new interval.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: XtendConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: XtendConfigEntry) -> None:
    """Delete the repairs issue when the user removes the entry.

    The coordinator only deletes it after a successful poll; an entry removed
    during an outage would otherwise leave the issue behind.
    """
    ir.async_delete_issue(hass, DOMAIN, issue_id_for_host(entry.data[CONF_HOST]))


async def _async_update_listener(hass: HomeAssistant, entry: XtendConfigEntry) -> None:
    """Reload the entry after its options changed."""
    await hass.config_entries.async_reload(entry.entry_id)
