"""Coordinator tests. The device is replaced by patching XtendApi.async_get_stats."""

from datetime import timedelta
import logging
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.intergas_xtend.api import XtendConnectionError
from custom_components.intergas_xtend.const import (
    BACKOFF_FACTOR,
    BACKOFF_MAX_SECONDS,
    BACKOFF_START_FAILURES,
    DOMAIN,
    ISSUE_AP_UNREACHABLE,
    STATS_FIELDS,
)
from custom_components.intergas_xtend.coordinator import (
    XtendCoordinator,
    issue_id_for_host,
)

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


def test_backoff_constants() -> None:
    assert BACKOFF_START_FAILURES == 3
    assert BACKOFF_FACTOR == 2
    assert BACKOFF_MAX_SECONDS == 300


async def test_backoff_doubles_from_the_third_failure_up_to_300_s(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # Verify step of the backoff item: with scan_interval 10 the intervals
    # after failures 1..7 are 10, 10, 20, 40, 80, 160, 300; then it stays at 300.
    entry = await setup_entry(hass, stats_payload, scan_interval=10)
    coordinator = entry.runtime_data
    assert coordinator.failures == 0
    assert coordinator.backing_off is False

    expected = [10, 10, 20, 40, 80, 160, 300, 300]
    seen: list[int] = []
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        for failures in range(1, len(expected) + 1):
            await coordinator.async_refresh()
            assert coordinator.failures == failures
            assert coordinator.backing_off is (failures >= 3)
            seen.append(int(coordinator.update_interval.total_seconds()))
    assert seen == expected
    assert coordinator.last_update_success is False
    # The configured interval is not touched by the back-off.
    assert coordinator.scan_interval == 10


async def test_backoff_respects_the_configured_interval(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # 30 s from options: 30, 30, 60, 120, 240, 300.
    entry = await setup_entry(hass, stats_payload, options={CONF_SCAN_INTERVAL: 30})
    coordinator = entry.runtime_data
    seen: list[int] = []
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        for _ in range(6):
            await coordinator.async_refresh()
            seen.append(int(coordinator.update_interval.total_seconds()))
    assert seen == [30, 30, 60, 120, 240, 300]


async def test_one_success_ends_the_backoff(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        for _ in range(5):
            await coordinator.async_refresh()
    assert coordinator.failures == 5
    assert coordinator.update_interval == timedelta(seconds=80)

    with patch(GET_STATS, return_value=stats_payload):
        await coordinator.async_refresh()
    assert coordinator.last_update_success is True
    assert coordinator.failures == 0
    assert coordinator.backing_off is False
    assert coordinator.update_interval == timedelta(seconds=10)

    # A new failure after recovery starts counting from 1 again.
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        await coordinator.async_refresh()
    assert coordinator.failures == 1
    assert coordinator.update_interval == timedelta(seconds=10)


async def test_backoff_logs_one_warning_and_one_info(
    hass: HomeAssistant,
    stats_payload: dict[str, int | str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    coordinator_logger = "custom_components.intergas_xtend.coordinator"
    caplog.set_level(logging.DEBUG, logger=coordinator_logger)
    caplog.clear()

    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        for _ in range(7):
            await coordinator.async_refresh()

    own_records = [r for r in caplog.records if r.name == coordinator_logger]
    warnings = [r for r in own_records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert HOST in warnings[0].getMessage()
    assert "20 s" in warnings[0].getMessage()
    # The base class logs the first failure at ERROR; the other failed polls
    # must not appear above DEBUG.
    errors = [r for r in own_records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert not [r for r in own_records if r.levelno == logging.INFO]

    caplog.clear()
    with patch(GET_STATS, return_value=stats_payload):
        await coordinator.async_refresh()
    own_records = [r for r in caplog.records if r.name == coordinator_logger]
    infos = [r for r in own_records if "answers again" in r.getMessage()]
    assert len(infos) == 1
    assert "10 s" in infos[0].getMessage()
    assert not [r for r in own_records if r.levelno >= logging.WARNING]

    # Two failures without back-off: no warning at all.
    caplog.clear()
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        await coordinator.async_refresh()
        await coordinator.async_refresh()
    with patch(GET_STATS, return_value=stats_payload):
        await coordinator.async_refresh()
    own_records = [r for r in caplog.records if r.name == coordinator_logger]
    assert not [r for r in own_records if r.levelno == logging.WARNING]
    assert not [r for r in own_records if "answers again" in r.getMessage()]


async def test_scheduled_polls_follow_the_backoff_interval(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # The stretched interval must reach the scheduler, not only the attribute.
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    remove_listener = coordinator.async_add_listener(lambda: None)

    with patch(GET_STATS, side_effect=XtendConnectionError("refused")) as get_stats:
        for _ in range(3):
            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
            await hass.async_block_till_done()
        assert get_stats.call_count == 3
        assert coordinator.update_interval == timedelta(seconds=20)

        # 11 s after the 3rd failure nothing is polled yet ...
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
        await hass.async_block_till_done()
        assert get_stats.call_count == 3

        # ... but 21 s after it the 4th poll runs and the interval becomes 40 s.
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=21))
        await hass.async_block_till_done()
        assert get_stats.call_count == 4
        assert coordinator.update_interval == timedelta(seconds=40)

    remove_listener()


def get_issue(hass: HomeAssistant) -> ir.IssueEntry | None:
    return ir.async_get(hass).async_get_issue(DOMAIN, issue_id_for_host(HOST))


async def test_repairs_issue_after_three_failures_gone_after_one_success(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # Verify step of the repairs item: with 3 failed updates the issue exists;
    # after one success it is gone.
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    assert coordinator.issue_id == f"{ISSUE_AP_UNREACHABLE}_{HOST}"
    assert get_issue(hass) is None

    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        await coordinator.async_refresh()
        await coordinator.async_refresh()
        assert get_issue(hass) is None
        await coordinator.async_refresh()
        issue = get_issue(hass)
        assert issue is not None
        assert issue.severity is ir.IssueSeverity.WARNING
        assert issue.is_fixable is False
        assert issue.translation_key == ISSUE_AP_UNREACHABLE
        assert issue.translation_placeholders == {"host": HOST}
        # More failures keep the same issue.
        await coordinator.async_refresh()
        assert get_issue(hass) is issue
        assert len(ir.async_get(hass).issues) == 1

    with patch(GET_STATS, return_value=stats_payload):
        await coordinator.async_refresh()
    assert get_issue(hass) is None
    assert ir.async_get(hass).issues == {}


async def test_success_deletes_an_issue_left_by_a_previous_coordinator(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # A reload during an outage gives a fresh coordinator with 0 failures;
    # its first success must still clear the old issue.
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id_for_host(HOST),
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_AP_UNREACHABLE,
        translation_placeholders={"host": HOST},
    )
    assert get_issue(hass) is not None

    await setup_entry(hass, stats_payload)
    assert get_issue(hass) is None


async def test_removing_the_entry_deletes_the_issue(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    with patch(GET_STATS, side_effect=XtendConnectionError("refused")):
        for _ in range(3):
            await coordinator.async_refresh()
    assert get_issue(hass) is not None

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert get_issue(hass) is None


async def test_unload_entry(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
