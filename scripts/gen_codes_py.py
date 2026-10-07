"""Generate custom_components/intergas_xtend/codes.py from docs/fault-codes.json.

Usage: python -I -X utf8 scripts/gen_codes_py.py <fault-codes.json> <codes.py>

docs/fault-codes.json is itself generated from the manual by scripts/gen_codes.py.
HACS installs only custom_components/<domain>/, so the integration cannot read
docs/ at runtime; the tables are written into codes.py as Python literals instead.
The Dutch text is copied verbatim; do not edit the output by hand.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

HEADER = '''"""Fault (F) and notification (n) code tables of the Intergas Xtend.

Source: docs/fault-codes.json, generated from Intergas document 88104401
chapter 12.1 and 12.2. Regenerate, do not edit by hand:

    python -I -X utf8 scripts/gen_codes_py.py docs/fault-codes.json \\
        custom_components/intergas_xtend/codes.py

The Dutch text is quoted verbatim from the manual and shown as sensor
attributes; it must not be paraphrased or translated. Fault codes belong to
stats field 7e2c (lockout code), notification codes to field 7940. Field 8439
holds the CV boiler's own OpenTherm code and is not covered here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeInfo:
    """The manual's description of one code and its cause/solution items."""

    description: str
    cause_solution: tuple[str, ...]


# Source: docs/fault-codes.json, generated from Intergas document 88104401
# chapter 12.1 and 12.2. Regenerate, do not edit by hand.
'''

FOOTER = '''

def fault_info(code: str) -> CodeInfo | None:
    """Return the manual's entry for a lockout code such as "F037", or None."""
    return FAULT_CODES.get(code)


def notification_info(code: str) -> CodeInfo | None:
    """Return the manual's entry for a notification code such as "n095", or None.

    Codes that are not listed one by one are looked up in NOTIFICATION_RANGES,
    e.g. n100 up to and including n165 share one FOTA entry.
    """
    if (info := NOTIFICATION_CODES.get(code)) is not None:
        return info
    if len(code) == 4 and code[0] == "n" and code[1:].isdigit():
        number = int(code[1:])
        for first, last, info in NOTIFICATION_RANGES:
            if first <= number <= last:
                return info
    return None
'''


def literal(text: str) -> str:
    """Render a string as a double-quoted Python literal (JSON escapes are valid)."""
    return json.dumps(text, ensure_ascii=False)


def code_info(entry: dict, indent: str) -> str:
    """Render one CodeInfo(...) call, one item per line."""
    inner = indent + "    "
    lines = [
        "CodeInfo(",
        f"{inner}description={literal(entry['description'])},",
        f"{inner}cause_solution=(",
    ]
    lines.extend(f"{inner}    {literal(item)}," for item in entry["cause_solution"])
    lines.append(f"{inner}),")
    lines.append(f"{indent})")
    return "\n".join(lines)


def table(name: str, entries: list[dict]) -> str:
    """Render a dict[str, CodeInfo] literal keyed by code."""
    lines = [f"{name}: dict[str, CodeInfo] = {{"]
    for entry in entries:
        lines.append(f"    {literal(entry['code'])}: {code_info(entry, '    ')},")
    lines.append("}")
    return "\n".join(lines)


def ranges(name: str, entries: list[dict]) -> str:
    """Render the (first, last, CodeInfo) tuples of range entries."""
    lines = [
        "# Notification codes that share one entry: (first, last, info), both",
        "# ends included.",
        f"{name}: tuple[tuple[int, int, CodeInfo], ...] = (",
    ]
    for entry in entries:
        first, last = entry["range"]
        lines.append(f"    (\n        {first},\n        {last},")
        lines.append(f"        {code_info(entry, '        ')},\n    ),")
    lines.append(")")
    return "\n".join(lines)


data = json.loads(SRC.read_text(encoding="utf-8"))
faults = data["fault_codes"]
notes = [e for e in data["notification_codes"] if "range" not in e]
note_ranges = [e for e in data["notification_codes"] if "range" in e]
if any("range" in e for e in faults):
    raise SystemExit("fault code ranges are not supported")

body = "\n\n".join(
    [
        table("FAULT_CODES", faults),
        table("NOTIFICATION_CODES", notes),
        ranges("NOTIFICATION_RANGES", note_ranges),
    ]
)
OUT.write_text(HEADER + body + FOOTER, encoding="utf-8", newline="\n")
# The layout above is close to ruff's style; ruff format makes it exact (for
# example single-item tuples), so the committed file passes ruff format --check.
subprocess.run([sys.executable, "-m", "ruff", "format", str(OUT)], check=True)
print(
    f"{len(faults)} fault codes, {len(notes)} notification codes,",
    f"{len(note_ranges)} notification ranges -> {OUT}",
)
