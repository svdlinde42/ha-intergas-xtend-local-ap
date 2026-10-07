"""Coordinator tests. The device is replaced by patching XtendApi.async_get_stats."""

from datetime import timedelta
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.intergas_xtend.api import XtendConnectionError
from custom_components.intergas_xtend.const import DOMAIN, STATS_FIELDS
from custom_components.intergas_xtend.coordinator import XtendCoordinator

# Patch the class method on api.py so every XtendApi instance is covered.
GET_STATS = "custom_components.intergas_xtend.api.XtendApi.async_get_stats"
HOST = "10.20.30.1"


def make_entry(
    scan_interval: int = 10, options: dict[str, int] | None = None
) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=HOST,
        title=f"Intergas Xtend ({HOST})",
        data={CONF_HOST: HOST, CONF_SCAN_INTERVAL: scan_interval},
        options=options or {},
    )


async def setup_entry(
    hass: HomeAssistant,
    stats: dict[str, int | str],
    *,
    scan_interval: int = 10,
    options: dict[str, int] | None = None,
) -> MockConfigEntry:
    """Add and set up an entry whose first poll returns ``stats``."""
    entry = make_entry(scan_interval, options)
    entry.add_to_hass(hass)
    with patch(GET_STATS, return_value=stats):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def test_setup_polls_once_and_stores_the_payload(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # Verify step of the coordinator item: after setup the coordinator has
    # data with 32 keys and last_update_success is True.
    entry = make_entry()
    entry.add_to_hass(hass)
    with patch(GET_STATS, return_value=stats_payload) as get_stats:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert get_stats.call_count == 1
    coordinator = entry.runtime_data
    assert isinstance(coordinator, XtendCoordinator)
    assert coordinator.last_update_success is True
    assert coordinator.data == stats_payload
    assert len(coordinator.data) == 32
    assert set(coordinator.data) == set(STATS_FIELDS)
    assert coordinator.api.host == HOST
    assert coordinator.scan_interval == 10
    assert coordinator.update_interval == timedelta(seconds=10)


async def test_update_interval_comes_from_options_before_data(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(
        hass, stats_payload, scan_interval=10, options={CONF_SCAN_INTERVAL: 30}
    )
    assert entry.runtime_data.scan_interval == 30
    assert entry.runtime_data.update_interval == timedelta(seconds=30)


async def test_scheduled_poll_runs_after_the_interval(
    hass: HomeAssistant,
    stats_payload: dict[str, int | str],
    stats_payload_standby: dict[str, int | str],
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    # A DataUpdateCoordinator only schedules polls while something listens;
    # entities do that once the sensor items land. Stand in for one here.
    remove_listener = coordinator.async_add_listener(lambda: None)

    with patch(GET_STATS, return_value=stats_payload_standby) as get_stats:
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
        await hass.async_block_till_done()
    remove_listener()

    assert get_stats.call_count == 1
    assert coordinator.data == stats_payload_standby
    assert coordinator.last_update_success is True


async def test_failed_first_poll_retries_setup_later(hass: HomeAssistant) -> None:
    # UpdateFailed during the first refresh becomes ConfigEntryNotReady.
    entry = make_entry()
    entry.add_to_hass(hass)
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_client_error_marks_update_failed_and_keeps_old_data(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data

    with patch(GET_STATS, side_effect=XtendConnectionError("timeout")):
        await coordinator.async_refresh()
    assert coordinator.last_update_success is False
    assert coordinator.data == stats_payload

    with patch(GET_STATS, return_value=stats_payload):
        await coordinator.async_refresh()
    assert coordinator.last_update_success is True


async def test_unload_entry(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
