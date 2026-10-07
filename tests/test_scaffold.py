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
