"""codes.py holds the manual's codes exactly as docs/fault-codes.json does."""

import json
from pathlib import Path

import pytest

from custom_components.intergas_xtend.codes import (
    FAULT_CODES,
    NOTIFICATION_CODES,
    NOTIFICATION_RANGES,
    CodeInfo,
    fault_info,
    notification_info,
)

REPO = Path(__file__).resolve().parent.parent
FAULT_CODES_JSON = REPO / "docs" / "fault-codes.json"
CODES_PY = REPO / "custom_components" / "intergas_xtend" / "codes.py"


@pytest.fixture(scope="module")
def manual() -> dict:
    return json.loads(FAULT_CODES_JSON.read_text(encoding="utf-8"))


def test_fault_codes_match_the_manual(manual: dict) -> None:
    expected = {
        entry["code"]: CodeInfo(entry["description"], tuple(entry["cause_solution"]))
        for entry in manual["fault_codes"]
    }
    assert len(expected) == 19
    assert FAULT_CODES == expected
    assert FAULT_CODES["F254"].description == "Bypassmodus actief."


def test_notification_codes_match_the_manual(manual: dict) -> None:
    single = [e for e in manual["notification_codes"] if "range" not in e]
    ranged = [e for e in manual["notification_codes"] if "range" in e]
    expected = {
        entry["code"]: CodeInfo(entry["description"], tuple(entry["cause_solution"]))
        for entry in single
    }
    assert len(expected) == 57
    assert NOTIFICATION_CODES == expected
    assert min(NOTIFICATION_CODES) == "n000"
    assert max(NOTIFICATION_CODES) == "n097"

    assert len(ranged) == 1
    assert NOTIFICATION_RANGES == (
        (
            100,
            165,
            CodeInfo(ranged[0]["description"], tuple(ranged[0]["cause_solution"])),
        ),
    )


def test_notification_info_covers_singles_and_the_fota_range() -> None:
    n095 = notification_info("n095")
    assert n095 is not None
    assert n095.description == "Probleem met driewegklep."
    assert len(n095.cause_solution) == 4

    fota = notification_info("n100")
    assert fota is not None
    assert fota.description == "FOTA gerelateerde melding."
    assert notification_info("n120") is fota
    assert notification_info("n165") is fota
    # Both ends of the range are included; outside it the manual has nothing.
    assert notification_info("n099") is None
    assert notification_info("n166") is None
    assert notification_info("n098") is None


@pytest.mark.parametrize("code", ["", "n", "n95", "n0095", "F100", "nabc", "n10x"])
def test_notification_info_rejects_other_shapes(code: str) -> None:
    assert notification_info(code) is None


def test_fault_info_is_a_plain_lookup() -> None:
    f037 = fault_info("F037")
    assert f037 is not None
    assert f037.description == "Sensorfout retourleiding T04."
    assert fault_info("F002") is None
    assert fault_info("n095") is None


def test_code_info_is_immutable() -> None:
    info = FAULT_CODES["F001"]
    with pytest.raises(AttributeError):
        info.description = "x"  # type: ignore[misc]
    assert isinstance(info.cause_solution, tuple)


def test_codes_py_names_its_source() -> None:
    source = CODES_PY.read_text(encoding="utf-8")
    assert (
        "Source: docs/fault-codes.json, generated from Intergas document 88104401"
        in source
    )
    assert "Regenerate, do not edit by hand." in source
    assert "scripts/gen_codes_py.py" in source
