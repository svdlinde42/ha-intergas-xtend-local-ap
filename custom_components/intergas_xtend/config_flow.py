"""Config flow for the Intergas Xtend integration.

One step: the user enters the host (IP on the Xtend access point) and the poll
interval. The flow validates the host by doing one status GET. The host is the
unique id because the status payload carries no serial number or MAC address
(decided 2026-10-06); changing the IP therefore creates a new entry.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import XtendApi, XtendConnectionError, XtendResponseError
from .const import (
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SCHEMA = vol.All(
    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): (
            SCAN_INTERVAL_SCHEMA
        ),
    }
)


class XtendConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the user step of the Intergas Xtend config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for host and poll interval, then validate with one status GET."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            api = XtendApi(async_get_clientsession(self.hass), host)
            try:
                await api.async_get_stats()
            except XtendConnectionError:
                errors["base"] = "cannot_connect"
            except XtendResponseError:
                errors["base"] = "invalid_response"
            else:
                return self.async_create_entry(
                    title=f"Intergas Xtend ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )
