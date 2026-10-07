"""Coordinator tests. The device is replaced by patching XtendApi.async_get_stats.

Only scheduled polls count towards the back-off, so a failing poll is simulated
by moving time past the next scheduled poll (``scheduled_poll``), not by calling
``coordinator.async_refresh()``. The latter is a manual poll, like the button.
"""

from datetime import timedelta
import logging
from unittest.mock import patch

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_ICON,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    STATE_UNAVAILABLE,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
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
REFUSED = XtendConnectionError("refused")


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


async def scheduled_poll(hass: HomeAssistant, coordinator: XtendCoordinator) -> None:
    """Move time past the next scheduled poll and let it run.

    The coordinator only schedules polls while an entity listens; the "Poll
    now" button is such a listener from setup on. Each call fires exactly one
    poll: the timer the poll creates for the one after it lies in the future
    again, relative to the real clock.
    """
    seconds = coordinator.update_interval.total_seconds() + 1
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done(wait_background_tasks=True)


async def fail_scheduled_polls(
    hass: HomeAssistant, coordinator: XtendCoordinator, count: int
) -> None:
    """Let ``count`` scheduled polls fail with a connection error."""
    with patch(GET_STATS, side_effect=REFUSED):
        for _ in range(count):
            await scheduled_poll(hass, coordinator)


def poll_now_entity_id(hass: HomeAssistant) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        BUTTON_DOMAIN, DOMAIN, f"{HOST}_poll_now"
    )
    assert entity_id is not None
    return entity_id


async def press_poll_now(hass: HomeAssistant) -> None:
    """Press the button the way the frontend does: through the button.press service."""
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: poll_now_entity_id(hass)},
        blocking=True,
    )
    await hass.async_block_till_done(wait_background_tasks=True)


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
    # The capture predates the statistics fields: 32 of the polled ids.
    assert len(coordinator.data) == 32
    assert set(coordinator.data) < set(STATS_FIELDS)
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

    with patch(GET_STATS, return_value=stats_payload_standby) as get_stats:
        # 8 s after setup nothing is polled yet. The coordinator aligns the
        # next poll to a whole second, so it may be due anywhere between 9 s
        # and 10 s after the first refresh; checking at 9 s was flaky.
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=8))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert get_stats.call_count == 0
        # ... 11 s after it the scheduled poll has run.
        await scheduled_poll(hass, coordinator)

    assert get_stats.call_count == 1
    assert coordinator.data == stats_payload_standby
    assert coordinator.last_update_success is True


async def test_failed_first_poll_retries_setup_later(hass: HomeAssistant) -> None:
    # UpdateFailed during the first refresh becomes ConfigEntryNotReady.
    entry = make_entry()
    entry.add_to_hass(hass)
    with patch(GET_STATS, side_effect=REFUSED):
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
    with patch(GET_STATS, side_effect=REFUSED) as get_stats:
        for failures in range(1, len(expected) + 1):
            await scheduled_poll(hass, coordinator)
            assert get_stats.call_count == failures
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
    with patch(GET_STATS, side_effect=REFUSED):
        for _ in range(6):
            await scheduled_poll(hass, coordinator)
            seen.append(int(coordinator.update_interval.total_seconds()))
    assert seen == [30, 30, 60, 120, 240, 300]


async def test_one_success_ends_the_backoff(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    await fail_scheduled_polls(hass, coordinator, 5)
    assert coordinator.failures == 5
    assert coordinator.update_interval == timedelta(seconds=80)

    with patch(GET_STATS, return_value=stats_payload):
        await scheduled_poll(hass, coordinator)
    assert coordinator.last_update_success is True
    assert coordinator.failures == 0
    assert coordinator.backing_off is False
    assert coordinator.update_interval == timedelta(seconds=10)

    # A new failure after recovery starts counting from 1 again.
    await fail_scheduled_polls(hass, coordinator, 1)
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

    await fail_scheduled_polls(hass, coordinator, 7)

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
        await scheduled_poll(hass, coordinator)
    own_records = [r for r in caplog.records if r.name == coordinator_logger]
    infos = [r for r in own_records if "answers again" in r.getMessage()]
    assert len(infos) == 1
    assert "10 s" in infos[0].getMessage()
    assert not [r for r in own_records if r.levelno >= logging.WARNING]

    # Two failures without back-off: no warning at all.
    caplog.clear()
    await fail_scheduled_polls(hass, coordinator, 2)
    with patch(GET_STATS, return_value=stats_payload):
        await scheduled_poll(hass, coordinator)
    own_records = [r for r in caplog.records if r.name == coordinator_logger]
    assert not [r for r in own_records if r.levelno == logging.WARNING]
    assert not [r for r in own_records if "answers again" in r.getMessage()]


async def test_scheduled_polls_follow_the_backoff_interval(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # The stretched interval must reach the scheduler, not only the attribute.
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data

    with patch(GET_STATS, side_effect=REFUSED) as get_stats:
        for _ in range(3):
            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
            await hass.async_block_till_done(wait_background_tasks=True)
        assert get_stats.call_count == 3
        assert coordinator.update_interval == timedelta(seconds=20)

        # 11 s after the 3rd failure nothing is polled yet ...
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert get_stats.call_count == 3

        # ... but 21 s after it the 4th poll runs and the interval becomes 40 s.
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=21))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert get_stats.call_count == 4
        assert coordinator.update_interval == timedelta(seconds=40)


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

    await fail_scheduled_polls(hass, coordinator, 2)
    assert get_issue(hass) is None
    await fail_scheduled_polls(hass, coordinator, 1)
    issue = get_issue(hass)
    assert issue is not None
    assert issue.severity is ir.IssueSeverity.WARNING
    assert issue.is_fixable is False
    assert issue.translation_key == ISSUE_AP_UNREACHABLE
    assert issue.translation_placeholders == {"host": HOST}
    # More failures keep the same issue.
    await fail_scheduled_polls(hass, coordinator, 1)
    assert get_issue(hass) is issue
    assert len(ir.async_get(hass).issues) == 1

    with patch(GET_STATS, return_value=stats_payload):
        await scheduled_poll(hass, coordinator)
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
    await fail_scheduled_polls(hass, entry.runtime_data, 3)
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


async def test_one_device_with_firmware_and_link(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # Verify step of the device info item: the device registry shows one
    # device with sw_version V1.20- for the fixture.
    entry = await setup_entry(hass, stats_payload)
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert len(devices) == 1
    device = devices[0]
    assert device.identifiers == {(DOMAIN, HOST)}
    assert device.name == "Intergas Xtend"
    assert device.manufacturer == "Intergas"
    assert device.sw_version == "V1.20-"
    assert device.configuration_url == f"http://{HOST}"

    # Every entity of the entry hangs under that device, which also gives the
    # button its entity id (device name + entity name).
    entity_id = poll_now_entity_id(hass)
    assert entity_id == "button.intergas_xtend_poll_now"
    registry_entry = er.async_get(hass).async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.device_id == device.id


@pytest.mark.parametrize("firmware", [32767, None])
async def test_device_without_firmware_string_has_no_sw_version(
    hass: HomeAssistant, stats_payload: dict[str, int | str], firmware: int | None
) -> None:
    # sw_version is only set when 47e0 holds a string.
    stats = dict(stats_payload)
    if firmware is None:
        del stats["47e0"]
    else:
        stats["47e0"] = firmware
    entry = await setup_entry(hass, stats)
    device = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)[0]
    assert device.sw_version is None
    assert entry.runtime_data.device_info["sw_version"] is None


async def test_poll_now_button_is_registered_as_diagnostic(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload)
    entity_id = poll_now_entity_id(hass)
    registry_entry = er.async_get(hass).async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.entity_category is EntityCategory.DIAGNOSTIC
    assert registry_entry.translation_key == "poll_now"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.attributes[ATTR_ICON] == "mdi:refresh"
    # Device name plus the English entity name from translations/en.json.
    assert state.attributes["friendly_name"] == "Intergas Xtend Poll now"


async def test_poll_now_button_stays_available_while_the_device_is_gone(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    await fail_scheduled_polls(hass, coordinator, 3)
    assert coordinator.last_update_success is False

    state = hass.states.get(poll_now_entity_id(hass))
    assert state is not None
    assert state.state != STATE_UNAVAILABLE


async def test_poll_now_button_has_the_documented_entity_id(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    await setup_entry(hass, stats_payload)
    assert poll_now_entity_id(hass) == "button.intergas_xtend_poll_now"


async def test_sensor_is_unavailable_after_a_failed_poll_and_recovers(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    sensor_id = "sensor.intergas_xtend_room_temperature"
    state = hass.states.get(sensor_id)
    assert state is not None
    assert state.state == "26.41"

    await fail_scheduled_polls(hass, coordinator, 1)
    state = hass.states.get(sensor_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    with patch(GET_STATS, return_value=stats_payload):
        await scheduled_poll(hass, coordinator)
    state = hass.states.get(sensor_id)
    assert state is not None
    assert state.state == "26.41"


async def test_successful_press_ends_the_backoff_and_closes_the_issue(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    # Verify step of the button item: after 5 failures and interval 80 s, a
    # successful press makes update_interval 10 s again and the issue disappears.
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    await fail_scheduled_polls(hass, coordinator, 5)
    assert coordinator.failures == 5
    assert coordinator.update_interval == timedelta(seconds=80)
    assert get_issue(hass) is not None

    with patch(GET_STATS, return_value=stats_payload) as get_stats:
        await press_poll_now(hass)
    assert get_stats.call_count == 1
    assert coordinator.last_update_success is True
    assert coordinator.failures == 0
    assert coordinator.backing_off is False
    assert coordinator.update_interval == timedelta(seconds=10)
    assert get_issue(hass) is None


@pytest.mark.parametrize(
    ("failures_before", "interval_before"), [(0, 10), (2, 10), (5, 80), (7, 300)]
)
async def test_failed_press_keeps_the_current_interval(
    hass: HomeAssistant,
    stats_payload: dict[str, int | str],
    caplog: pytest.LogCaptureFixture,
    failures_before: int,
    interval_before: int,
) -> None:
    # A failed manual poll does not count and does not stretch the interval.
    entry = await setup_entry(hass, stats_payload)
    coordinator = entry.runtime_data
    await fail_scheduled_polls(hass, coordinator, failures_before)
    assert coordinator.failures == failures_before
    assert coordinator.update_interval == timedelta(seconds=interval_before)
    issue_before = get_issue(hass)
    caplog.clear()

    with patch(GET_STATS, side_effect=REFUSED) as get_stats:
        await press_poll_now(hass)
    assert get_stats.call_count == 1
    assert coordinator.last_update_success is False
    assert coordinator.failures == failures_before
    assert coordinator.update_interval == timedelta(seconds=interval_before)
    assert get_issue(hass) is issue_before
    own_records = [
        r
        for r in caplog.records
        if r.name == "custom_components.intergas_xtend.coordinator"
    ]
    assert not [r for r in own_records if r.levelno == logging.WARNING]

    # The next scheduled failure continues the sequence where it was.
    await fail_scheduled_polls(hass, coordinator, 1)
    assert coordinator.failures == failures_before + 1
