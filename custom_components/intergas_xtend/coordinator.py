"""Coordinator for the Intergas Xtend integration.

One ``XtendCoordinator`` per config entry does the periodic status GET. It is
the only source of HTTP traffic to the device: entities read
``coordinator.data`` and never call the device themselves. Polling also keeps
the access point awake (it switches off after about 15 minutes without
requests), so the coordinator owns the poll interval. Back-off when the
access point is gone is added by the next coordinator items in plans/prd.json.

This module must stay free of imports from __init__.py to avoid an import cycle.
"""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XtendApi, XtendError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type XtendConfigEntry = ConfigEntry[XtendCoordinator]


def scan_interval_from_entry(entry: ConfigEntry) -> int:
    """Return the configured poll interval in seconds.

    The options flow stores a changed interval in entry.options; the value
    chosen when the entry was created stays in entry.data. Options win.
    """
    return int(
        entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
    )


class XtendCoordinator(DataUpdateCoordinator[dict[str, int | str]]):
    """Poll the Xtend status endpoint at the configured interval.

    ``data`` is the raw ``stats`` dict from ``XtendApi.async_get_stats``:
    integer values stay ``int``, string values stay ``str``. Scaling and
    sentinel handling happen in the sensor layer.
    """

    config_entry: XtendConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: XtendConfigEntry, api: XtendApi
    ) -> None:
        """Create the coordinator for one device with the entry's poll interval."""
        self.api = api
        # The interval the user configured; kept separately so the back-off
        # logic can restore it after a successful poll.
        self.scan_interval = scan_interval_from_entry(entry)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {api.host}",
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self) -> dict[str, int | str]:
        """Fetch the status payload; any client error makes the update fail.

        ``UpdateFailed`` marks every entity unavailable instead of leaving stale
        values on screen.
        """
        try:
            return await self.api.async_get_stats()
        except XtendError as err:
            raise UpdateFailed(
                f"Error fetching status from {self.api.host}: {err}"
            ) from err
