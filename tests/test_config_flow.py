"""Config flow tests. The device is replaced by patching XtendApi.async_get_stats."""

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.intergas_xtend.config_flow import OPTIONS_SCHEMA
from custom_components.intergas_xtend.const import DOMAIN
from custom_components.intergas_xtend.coordinator import scan_interval_from_entry

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


def test_scan_interval_from_entry_prefers_options() -> None:
    data_only = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "10.20.30.1", CONF_SCAN_INTERVAL: 15}
    )
    assert scan_interval_from_entry(data_only) == 15

    with_options = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "10.20.30.1", CONF_SCAN_INTERVAL: 15},
        options={CONF_SCAN_INTERVAL: 30},
    )
    assert scan_interval_from_entry(with_options) == 30

    neither = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "10.20.30.1"})
    assert scan_interval_from_entry(neither) == 10


async def test_options_flow_updates_scan_interval_and_reloads(
    hass: HomeAssistant,
) -> None:
    # Verify step of the options item: saving a new interval reloads the entry
    # and the new interval is the one read from the entry afterwards.
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="10.20.30.1",
        data={CONF_HOST: "10.20.30.1", CONF_SCAN_INTERVAL: 10},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    # The form is prefilled with the current interval.
    schema_field = next(
        key for key in result["data_schema"].schema if key == CONF_SCAN_INTERVAL
    )
    assert schema_field.description == {"suggested_value": 10}

    with patch(
        "custom_components.intergas_xtend.async_setup_entry", return_value=True
    ) as setup_entry:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_SCAN_INTERVAL: 30}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_SCAN_INTERVAL: 30}
    assert entry.data[CONF_SCAN_INTERVAL] == 10
    assert scan_interval_from_entry(entry) == 30
    # The update listener reloaded the entry: setup ran once more.
    assert setup_entry.call_count == 1
    assert entry.state is ConfigEntryState.LOADED


@pytest.mark.parametrize("value", [4, 61, "abc"])
def test_options_schema_rejects_interval_out_of_range(value: int | str) -> None:
    with pytest.raises(vol.Invalid):
        OPTIONS_SCHEMA({CONF_SCAN_INTERVAL: value})


@pytest.mark.parametrize(("value", "expected"), [(5, 5), ("60", 60), (30, 30)])
def test_options_schema_accepts_interval_in_range(
    value: int | str, expected: int
) -> None:
    assert OPTIONS_SCHEMA({CONF_SCAN_INTERVAL: value}) == {CONF_SCAN_INTERVAL: expected}
