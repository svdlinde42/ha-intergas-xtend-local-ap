"""Constants for the Intergas Xtend integration."""

from __future__ import annotations

DOMAIN = "intergas_xtend"

# Default IP of the Xtend on its own Wi-Fi access point (see AGENTS.md).
DEFAULT_HOST = "10.20.30.1"

# Poll interval in seconds. Polling also keeps the access point awake,
# which switches itself off after about 15 minutes without requests.
DEFAULT_SCAN_INTERVAL = 10
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 60

# REST status endpoint of the Xtend. Captured from the device on 2026-10-06
# (firmware V1.20-), not guessed. Request:
#   GET http://<host>/api/stats/values?fields=<comma-separated hex ids>
# Response: {"stats": {"<hex id>": <int | str>}}
STATS_PATH = "/api/stats/values"

# The 32 stats ids read in phase 1, in request order. Meaning, scale factor and
# unit of each id are in docs/stats-mapping.md; that file is the only source for
# field semantics. Source: docs/stats-mapping.md and a capture from the device
# on 2026-10-06.
STATS_FIELDS: tuple[str, ...] = (
    "7940",
    "79b3",
    "7921",
    "7e2c",
    "77c3",
    "7e51",
    "77d2",
    "f9f2",
    "7ed3",
    "629c",
    "6280",
    "621d",
    "62ed",
    "503e",
    "5088",
    "5077",
    "5041",
    "50f2",
    "62d1",
    "620f",
    "6206",
    "8439",
    "47e0",
    "7e7a",
    "7774",
    "77de",
    "6115",
    "61ba",
    "61eb",
    "610b",
    "6101",
    "6117",
)
