"""Scaffold checks: manifest, hacs.json and constants are consistent."""

import json
from pathlib import Path

from custom_components.intergas_xtend.const import (
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = ROOT / "custom_components" / "intergas_xtend"


def test_manifest_is_valid_and_matches_domain() -> None:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == DOMAIN
    assert manifest["name"] == "Intergas Xtend"
    assert manifest["version"] == "0.1.0"
    assert manifest["iot_class"] == "local_polling"
    assert manifest["config_flow"] is True
    assert manifest["requirements"] == []
    for key in ("codeowners", "documentation", "issue_tracker"):
        assert manifest[key]


def test_hacs_json_is_valid() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    assert hacs["name"] == "Intergas Xtend"
    assert hacs["homeassistant"]


def test_scan_interval_constants() -> None:
    assert DEFAULT_HOST == "10.20.30.1"
    assert MIN_SCAN_INTERVAL <= DEFAULT_SCAN_INTERVAL <= MAX_SCAN_INTERVAL
    assert (MIN_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, MAX_SCAN_INTERVAL) == (5, 10, 60)
