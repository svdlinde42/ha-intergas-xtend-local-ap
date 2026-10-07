"""Scaffold checks: manifest, hacs.json and constants are consistent."""

import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

from custom_components.intergas_xtend.const import (
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ISSUE_AP_UNREACHABLE,
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


def test_operating_modes_json_is_complete() -> None:
    modes = json.loads(
        (ROOT / "docs" / "operating-modes.json").read_text(encoding="utf-8")
    )
    assert len(modes) == 38
    assert all(set(m) == {"code", "name", "en", "nl"} for m in modes)
    codes = [m["code"] for m in modes]
    names = [m["name"] for m in modes]
    assert len(set(codes)) == 38
    assert len(set(names)) == 38
    assert all(isinstance(c, int) and 0 <= c <= 255 for c in codes)
    # Home Assistant enum states allow only [a-z0-9_].
    assert all(re.fullmatch(r"[a-z0-9_]+", n) for n in names)
    assert all(m["en"] and m["nl"] for m in modes)
    by_code = {m["code"]: m["name"] for m in modes}
    assert by_code[126] == "standby"
    assert by_code[206] == "dhw_legionella_prevention"


def test_api_module_does_not_import_home_assistant() -> None:
    # Verify step of the api item: api.py must be usable without Home Assistant.
    source = (INTEGRATION / "api.py").read_text(encoding="utf-8")
    assert "homeassistant" not in source
    # Stronger check: importing api.py in a fresh interpreter with the
    # homeassistant package blocked must succeed. The package __init__.py does
    # import Home Assistant (it is the integration entry point), so register a
    # stub package first and import api as its submodule.
    script = "\n".join(
        [
            "import sys, types",
            "sys.modules['homeassistant'] = None",
            "pkg = types.ModuleType('custom_components.intergas_xtend')",
            f"pkg.__path__ = [{str(INTEGRATION)!r}]",
            "sys.modules[pkg.__name__] = pkg",
            "import custom_components.intergas_xtend.api as api",
            "assert api.XtendApi",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_api_builds_stats_url_from_const() -> None:
    from custom_components.intergas_xtend.api import (
        XtendApi,
        XtendConnectionError,
        XtendError,
        XtendResponseError,
    )

    api = XtendApi(session=None, host="10.20.30.1")  # type: ignore[arg-type]
    assert api.host == "10.20.30.1"
    assert api.stats_url == (
        f"http://10.20.30.1{STATS_PATH}?fields={','.join(EXPECTED_STATS_FIELDS)}"
    )
    assert issubclass(XtendConnectionError, XtendError)
    assert issubclass(XtendResponseError, XtendError)


def test_strings_json_has_config_flow_texts() -> None:
    # Verify step of the config_flow item.
    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    config = strings["config"]
    assert set(config["step"]["user"]["data"]) == {"host", "scan_interval"}
    assert {"cannot_connect", "invalid_response"} <= set(config["error"])
    assert "already_configured" in config["abort"]
    options = strings["options"]
    assert set(options["step"]["init"]["data"]) == {"scan_interval"}


def test_strings_json_has_repairs_issue_texts() -> None:
    # The repairs item: the issue text names the host and the recovery steps.
    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    nl = json.loads(
        (INTEGRATION / "translations" / "nl.json").read_text(encoding="utf-8")
    )
    for texts, button in ((strings, "Poll now"), (nl, "Nu pollen")):
        issue = texts["issues"][ISSUE_AP_UNREACHABLE]
        assert "{host}" in issue["title"]
        assert "{host}" in issue["description"]
        assert "15" in issue["description"]
        assert button in issue["description"]


def test_strings_json_has_poll_now_button_name() -> None:
    # The button item: EN name 'Poll now', NL name 'Nu pollen'.
    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    nl = json.loads(
        (INTEGRATION / "translations" / "nl.json").read_text(encoding="utf-8")
    )
    assert strings["entity"]["button"]["poll_now"]["name"] == "Poll now"
    assert nl["entity"]["button"]["poll_now"]["name"] == "Nu pollen"


def _key_paths(node: object, prefix: str = "") -> set[str]:
    """Return every leaf key path of a nested dict, e.g. 'config.step.user.title'."""
    if not isinstance(node, dict):
        return {prefix}
    paths: set[str] = set()
    for key, value in node.items():
        paths |= _key_paths(value, f"{prefix}.{key}" if prefix else key)
    return paths


def test_translations_match_strings_json() -> None:
    # Verify step of the translations item: en.json is a copy of strings.json,
    # nl.json is valid JSON with the same key structure and no untranslated
    # English leaf left over (except the leaves that are the same in both).
    strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
    en = json.loads(
        (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
    )
    nl = json.loads(
        (INTEGRATION / "translations" / "nl.json").read_text(encoding="utf-8")
    )
    assert en == strings
    assert _key_paths(nl) == _key_paths(strings)
    # Dutch texts differ from English, except labels that are identical in
    # both languages (the host field label, the COP sensor name and two
    # operating mode states).
    same_in_both = {
        "config.step.user.data.host",
        "entity.sensor.cop.name",
        "entity.sensor.operating_mode.state.service",
        "entity.sensor.operating_mode.state.opentherm",
    }
    for path in _key_paths(strings) - same_in_both:
        en_leaf, nl_leaf = strings, nl
        for part in path.split("."):
            en_leaf, nl_leaf = en_leaf[part], nl_leaf[part]
        assert isinstance(nl_leaf, str) and nl_leaf
        assert nl_leaf != en_leaf, path


def test_every_sensor_translation_key_has_a_name_in_all_files() -> None:
    # Verify step of the entity names item: every translation_key in SENSORS has
    # a name in strings.json, en.json and nl.json, and the key sets are identical.
    from custom_components.intergas_xtend.descriptions import SENSORS

    keys = {d.translation_key for d in SENSORS}
    assert len(keys) == len(SENSORS) == 32
    files = {
        "strings": INTEGRATION / "strings.json",
        "en": INTEGRATION / "translations" / "en.json",
        "nl": INTEGRATION / "translations" / "nl.json",
    }
    for label, path in files.items():
        sensors = json.loads(path.read_text(encoding="utf-8"))["entity"]["sensor"]
        assert set(sensors) == keys, label
        for key, value in sensors.items():
            assert isinstance(value["name"], str) and value["name"], (label, key)


def test_sensor_names_follow_the_prd() -> None:
    # Spot checks against the names listed in plans/prd.json.
    en = json.loads(
        (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
    )["entity"]["sensor"]
    nl = json.loads(
        (INTEGRATION / "translations" / "nl.json").read_text(encoding="utf-8")
    )["entity"]["sensor"]
    assert en["room_temperature"]["name"] == "Room temperature"
    assert nl["room_temperature"]["name"] == "Kamertemperatuur"
    assert en["dhw_temperature"]["name"] == "DHW actual"
    assert nl["dhw_temperature"]["name"] == "Tapwater werkelijk"
    assert en["bivalent_service_flags"]["name"] == "Bivalent service flags (raw)"
    assert nl["bivalent_service_flags"]["name"] == "Vlaggen hybride regeling (ruw)"
    assert en["cop"]["name"] == nl["cop"]["name"] == "COP"


def test_operating_mode_name_and_states_in_all_files() -> None:
    # Verify step of the operating mode item: every option of the sensor has a
    # state in all three files, with the label from docs/operating-modes.json.
    from custom_components.intergas_xtend.descriptions import SENSORS

    modes = json.loads(
        (ROOT / "docs" / "operating-modes.json").read_text(encoding="utf-8")
    )
    options = set(next(d for d in SENSORS if d.key == "7e51").options or [])
    files = {
        "strings": (INTEGRATION / "strings.json", "en", "Operating mode"),
        "en": (INTEGRATION / "translations" / "en.json", "en", "Operating mode"),
        "nl": (INTEGRATION / "translations" / "nl.json", "nl", "Bedrijfsmodus"),
    }
    for label, (path, language, name) in files.items():
        sensors = json.loads(path.read_text(encoding="utf-8"))["entity"]["sensor"]
        assert "heat_demand_status" not in sensors, label
        entry = sensors["operating_mode"]
        assert entry["name"] == name, label
        assert set(entry["state"]) == options, label
        assert entry["state"] == {m["name"]: m[language] for m in modes}, label


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


def test_readme_has_the_required_sections_and_lists_every_sensor() -> None:
    from custom_components.intergas_xtend.descriptions import SENSORS

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in (
        "## Installation",
        "## Network",
        "## Access point timeout",
        "## Entities",
        "## Notes",
    ):
        assert heading in readme
    assert "10.20.30.1" in readme
    assert "2025.11.0" in readme
    assert "docs/fault-codes.md" in readme

    names = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))[
        "entity"
    ]["sensor"]
    rows = {
        line.split("|")[1].strip(): line.split("|")[3].strip()
        for line in readme.splitlines()
        if line.startswith("| ") and line.count("|") == 4
    }
    for description in SENSORS:
        name = names[description.translation_key]["name"]
        assert name in rows, name
        enabled = rows[name].startswith("yes")
        assert enabled == description.entity_registry_enabled_default, name
