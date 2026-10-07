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
