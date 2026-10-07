"""Thin aiohttp client for the Intergas Xtend REST interface.

This module must stay importable without Home Assistant, so it imports nothing
from it. The caller passes in the aiohttp session (Home Assistant's shared
session in production, a test session in the unit tests).

Endpoint and field ids come from ``const.py``; they were captured from the
device on 2026-10-06 (firmware V1.20-), not guessed.
"""

from __future__ import annotations

import json

import aiohttp

from .const import STATS_FIELDS, STATS_PATH

# Total request timeout in seconds. The Xtend answers in well under a second on
# its own access point; 5 s leaves room for a busy Wi-Fi link without delaying
# the 5-10 s poll cycle much when the access point has gone away.
REQUEST_TIMEOUT = 5


class XtendError(Exception):
    """Base error for the Xtend client."""


class XtendConnectionError(XtendError):
    """The device could not be reached (network error or timeout)."""


class XtendResponseError(XtendError):
    """The device answered, but not with a usable status payload."""


class XtendApi:
    """Read the status payload from an Intergas Xtend over its REST interface."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        """Store the shared aiohttp session and the device host (IP or name)."""
        self._session = session
        self._host = host

    @property
    def host(self) -> str:
        """Return the host this client talks to."""
        return self._host

    @property
    def stats_url(self) -> str:
        """Return the full status URL including the fields query string."""
        return f"http://{self._host}{STATS_PATH}?fields={','.join(STATS_FIELDS)}"

    async def async_get_stats(self) -> dict[str, int | str]:
        """Fetch the status values for all ``STATS_FIELDS``.

        Returns the inner ``stats`` dict unchanged: integer values stay ``int``,
        string values (47e0, firmware version) stay ``str``. Scaling and
        sentinel handling belong to the sensor layer, not here.

        Raises ``XtendConnectionError`` on network errors and timeouts and
        ``XtendResponseError`` when the HTTP status is not 200.
        """
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        try:
            async with self._session.get(self.stats_url, timeout=timeout) as resp:
                if resp.status != 200:
                    raise XtendResponseError(
                        f"Unexpected HTTP status {resp.status} from {self._host}"
                    )
                body = await resp.text()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise XtendConnectionError(
                f"Cannot connect to Xtend at {self._host}: {err}"
            ) from err
        return self._parse_stats(body)

    @staticmethod
    def _parse_stats(body: str) -> dict[str, int | str]:
        """Parse the response body into the ``stats`` dict.

        Response shape (captured 2026-10-06): ``{"stats": {"<hex id>": <int | str>}}``.
        Anything else raises ``XtendResponseError``: a body that is not JSON, a
        top-level value that is not an object, or a missing or non-object
        ``stats`` key. The inner dict is returned unchanged; no scaling, no
        sentinel handling.
        """
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as err:
            raise XtendResponseError(f"Response is not valid JSON: {err}") from err
        if not isinstance(payload, dict):
            raise XtendResponseError(
                f"Expected a JSON object, got {type(payload).__name__}"
            )
        stats = payload.get("stats")
        if not isinstance(stats, dict):
            raise XtendResponseError("Response has no 'stats' object")
        return stats
