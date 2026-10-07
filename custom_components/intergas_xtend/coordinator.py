"""Coordinator for the Intergas Xtend integration.

Owns the poll interval. The XtendCoordinator class (one DataUpdateCoordinator
doing the periodic status GET, with back-off when the access point is gone) is
added by the coordinator items in plans/prd.json. This module must stay free of
imports from __init__.py to avoid an import cycle.
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL

from .const import DEFAULT_SCAN_INTERVAL


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
