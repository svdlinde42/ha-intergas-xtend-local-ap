"""Config flow tests. The device is replaced by patching XtendApi.async_get_stats."""

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.intergas_xtend.const import DOMAIN

GET_STATS = "custom_components.intergas_xtend.config_flow.XtendApi.async_get_stats"


async def test_user_flow_with_defaults_creates_entry(
    hass: HomeAssistant, stats_payload: dict[str, int | str]
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(GET_STATS, return_value=stats_payload) as get_stats:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "10.20.30.1", CONF_SCAN_INTERVAL: 10}
        )
        await hass.async_block_till_done()

    assert get_stats.call_count == 1
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Intergas Xtend (10.20.30.1)"
    assert result["data"] == {CONF_HOST: "10.20.30.1", CONF_SCAN_INTERVAL: 10}
    assert result["result"].unique_id == "10.20.30.1"
