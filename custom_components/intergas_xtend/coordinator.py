"""Coordinator for the Intergas Xtend integration.

One ``XtendCoordinator`` per config entry does the periodic status GET. It is
the only source of HTTP traffic to the device: entities read
``coordinator.data`` and never call the device themselves. Polling also keeps
the access point awake (it switches off after about 15 minutes without
requests), so the coordinator owns the poll interval.

Once the access point is off, polling cannot bring it back: the user must
re-enable it on the device. So after BACKOFF_START_FAILURES consecutive
failures the coordinator doubles its interval per failure up to
BACKOFF_MAX_SECONDS, and one successful poll restores the configured interval.
When the back-off starts the coordinator also raises a repairs issue with the
recovery steps; the next successful poll deletes it. Only scheduled polls
count as failures: a manual poll (the "Poll now" button or the
``homeassistant.update_entity`` service) that fails keeps the current interval.

This module must stay free of imports from __init__.py to avoid an import cycle.
"""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import XtendApi, XtendError
from .const import (
    BACKOFF_FACTOR,
    BACKOFF_MAX_SECONDS,
    BACKOFF_START_FAILURES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ISSUE_AP_UNREACHABLE,
)

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


def issue_id_for_host(host: str) -> str:
    """Return the repairs issue id for one device.

    The host is the entry's unique id, so one issue per config entry.
    """
    return f"{ISSUE_AP_UNREACHABLE}_{host}"


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
        # Consecutive failed scheduled polls; 0 after every successful poll.
        self.failures = 0
        # True while the poll in progress was started by the scheduler, False
        # for a manual poll. Set by _async_refresh, read by _register_failure.
        self._scheduled_poll = False
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {api.host}",
            update_interval=timedelta(seconds=self.scan_interval),
        )

    @property
    def issue_id(self) -> str:
        """Id of the repairs issue raised while the device is unreachable."""
        return issue_id_for_host(self.api.host)

    @property
    def backing_off(self) -> bool:
        """True while the poll interval is stretched because the device is gone."""
        return self.failures >= BACKOFF_START_FAILURES

    async def _async_refresh(
        self,
        log_failures: bool = True,
        raise_on_auth_failed: bool = False,
        scheduled: bool = False,
        raise_on_entry_error: bool = False,
    ) -> None:
        """Remember whether this poll was scheduled before running it.

        The base class is the only place that knows the difference: the
        scheduler calls it with ``scheduled=True``, ``async_refresh`` and
        ``async_request_refresh`` (button, update_entity service) do not.
        """
        self._scheduled_poll = scheduled
        await super()._async_refresh(
            log_failures=log_failures,
            raise_on_auth_failed=raise_on_auth_failed,
            scheduled=scheduled,
            raise_on_entry_error=raise_on_entry_error,
        )

    async def _async_update_data(self) -> dict[str, int | str]:
        """Fetch the status payload; any client error makes the update fail.

        ``UpdateFailed`` marks every entity unavailable instead of leaving stale
        values on screen. The base class reads ``update_interval`` after this
        method returns, so changing it here sets the delay to the next poll.
        """
        try:
            data = await self.api.async_get_stats()
        except XtendError as err:
            self._register_failure()
            raise UpdateFailed(
                f"Error fetching status from {self.api.host}: {err}"
            ) from err
        self._register_success()
        return data

    def _register_failure(self) -> None:
        """Count the failure and stretch the interval from the 3rd one on.

        The base class already logs the first failure at error level and the
        rest at debug level; this method adds one warning when the back-off
        starts and nothing after that.

        A failed manual poll is not counted: the user presses "Poll now" to
        check whether the access point is back, and that check must not
        stretch the interval further.
        """
        if not self._scheduled_poll:
            _LOGGER.debug(
                "Manual poll of %s failed; keeping the interval at %d s",
                self.api.host,
                int(self.update_interval.total_seconds()),
            )
            return
        self.failures += 1
        if not self.backing_off:
            return
        # Equals scan_interval * 2 ** (failures - 2) with the default constants.
        exponent = self.failures - BACKOFF_START_FAILURES + 1
        seconds = min(
            self.scan_interval * BACKOFF_FACTOR**exponent, BACKOFF_MAX_SECONDS
        )
        if self.failures == BACKOFF_START_FAILURES:
            _LOGGER.warning(
                "%s did not answer %d polls in a row; the access point may have "
                "switched off. Polling every %d s instead of %d s, up to %d s",
                self.api.host,
                self.failures,
                seconds,
                self.scan_interval,
                BACKOFF_MAX_SECONDS,
            )
        self.update_interval = timedelta(seconds=seconds)
        # Creating an issue that already exists with the same content is a
        # no-op, so this is safe to repeat on every failure during back-off.
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self.issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_AP_UNREACHABLE,
            translation_placeholders={"host": self.api.host},
        )

    def _register_success(self) -> None:
        """Reset the failure counter and restore the configured interval.

        Manual and scheduled polls count alike here, so one successful press
        of "Poll now" ends the back-off.

        The repairs issue is deleted on every success, not only when this
        coordinator started the back-off: after a reload during an outage a new
        coordinator starts at 0 failures while the old issue still exists.
        """
        if self.backing_off:
            _LOGGER.info(
                "%s answers again after %d failed polls; polling every %d s",
                self.api.host,
                self.failures,
                self.scan_interval,
            )
        self.failures = 0
        self.update_interval = timedelta(seconds=self.scan_interval)
        ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
