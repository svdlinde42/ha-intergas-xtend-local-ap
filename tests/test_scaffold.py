"""Scaffold checks: manifest, hacs.json and constants are consistent."""

import json
from pathlib import Path

import yaml

from custom_components.intergas_xtend.const import (
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    STATS_FIELDS,
    STATS_PATH,
)

ROOT = Path(__file__).resolve().parent.parent
INTEGRATION = ROOT / "custom_components" / "intergas_xtend"

# Order as listed in plans/prd.json (api item), captured from the device 2026-10-06.
EXPECTED_STATS_FIELDS = (
    "7940,79b3,7921,7e2c,77c3,7e51,77d2,f9f2,7ed3,629c,6280,621d,62ed,503e,5088,"
    "5077,5041,50f2,62d1,620f,6206,8439,47e0,7e7a,7774,77de,6115,61ba,61eb,610b,"
    "6101,6117"
).split(",")


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


def test_stats_fields_are_32_unique_ids_in_order() -> None:
    assert STATS_PATH == "/api/stats/values"
    assert len(STATS_FIELDS) == 32
    assert len(set(STATS_FIELDS)) == 32
    assert list(STATS_FIELDS) == EXPECTED_STATS_FIELDS
    assert all(len(f) == 4 and int(f, 16) >= 0 for f in STATS_FIELDS)


def test_stats_fields_are_documented_in_mapping() -> None:
    mapping = (ROOT / "docs" / "stats-mapping.md").read_text(encoding="utf-8")
    missing = [f for f in STATS_FIELDS if f not in mapping]
    assert missing == []


def test_validate_workflow_has_three_jobs() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    )
    # PyYAML (YAML 1.1) reads the bare key "on" as the boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert "push" in triggers
    assert set(workflow["jobs"]) == {"hassfest", "hacs", "tests"}

    def uses(job: str) -> list[str]:
        return [step.get("uses", "") for step in workflow["jobs"][job]["steps"]]

    hassfest = "home-assistant/actions/hassfest"
    assert any(u.startswith(hassfest) for u in uses("hassfest"))
    assert any(u.startswith("hacs/action") for u in uses("hacs"))
    hacs_step = next(s for s in workflow["jobs"]["hacs"]["steps"] if "with" in s)
    assert hacs_step["with"]["category"] == "integration"
    runs = [step.get("run", "") for step in workflow["jobs"]["tests"]["steps"]]
    assert "ruff check ." in runs
    assert "pytest" in runs
