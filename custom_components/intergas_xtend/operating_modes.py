"""Operating mode codes of the Intergas Xtend (stats field 7e51).

Source: docs/operating-modes.json. Regenerate, do not edit by hand:

    python -I -X utf8 scripts/gen_operating_modes_py.py docs/operating-modes.json \
        custom_components/intergas_xtend/operating_modes.py

The code and name come from the operating mode table in app.js of the Xtend
web interface (provided by the owner, 2026-10-07). The names are the enum
states of the operating mode sensor; their en/nl labels are in strings.json
and translations/. This module has no Home Assistant imports.
"""

from __future__ import annotations

# Source: docs/operating-modes.json. Regenerate, do not edit by hand.
OPERATING_MODES: dict[int, str] = {
    85: "sensortest",
    86: "commissioning",
    87: "crankheating",
    88: "commissioning_waiting",
    170: "service",
    171: "heatpump_selftest",
    204: "dhw",
    51: "dhw_int",
    240: "boiler_int",
    15: "boiler_ext",
    153: "postrun_boiler",
    102: "ch",
    103: "ch_wait",
    104: "defrosting",
    105: "defrosting_wait",
    106: "defrosting_wait_flow",
    107: "ch_blocked_by_sgready",
    108: "ch_wait_dhw_active",
    109: "ch_concrete_drying",
    0: "opentherm",
    255: "heatup",
    24: "frost",
    230: "starting_ch",
    231: "postrun_ch",
    126: "standby",
    127: "switched_off",
    37: "ch_rf",
    205: "dhw_hreco",
    206: "dhw_legionella_prevention",
    207: "dhw_wait",
    117: "starting_cooling",
    118: "cooling",
    119: "cooling_wait",
    120: "cooling_blocked_by_sgready",
    121: "cooling_waiting_for_flow",
    122: "cooling_condense_protection",
    123: "cooling_floor_thermostat_off",
    189: "postrun_cooling",
}
