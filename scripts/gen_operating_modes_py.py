"""Generate custom_components/intergas_xtend/operating_modes.py.

Usage:
    python -I -X utf8 scripts/gen_operating_modes_py.py <operating-modes.json>
        <operating_modes.py>

HACS installs only custom_components/<domain>/, so the integration cannot read
docs/ at runtime; the table is written into operating_modes.py as a Python
literal instead. Do not edit the output by hand.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])

HEADER = '''"""Operating mode codes of the Intergas Xtend (stats field 7e51).

Source: docs/operating-modes.json. Regenerate, do not edit by hand:

    python -I -X utf8 scripts/gen_operating_modes_py.py docs/operating-modes.json \\
        custom_components/intergas_xtend/operating_modes.py

The code and name come from the operating mode table in app.js of the Xtend
web interface (provided by the owner, 2026-10-07). The names are the enum
states of the operating mode sensor; their en/nl labels are in strings.json
and translations/. This module has no Home Assistant imports.
"""

from __future__ import annotations

# Source: docs/operating-modes.json. Regenerate, do not edit by hand.
'''

NAME = re.compile(r"[a-z0-9_]+")

entries = json.loads(SRC.read_text(encoding="utf-8"))
codes = [e["code"] for e in entries]
names = [e["name"] for e in entries]
if len(set(codes)) != len(codes) or len(set(names)) != len(names):
    raise SystemExit("codes and names must be unique")
if bad := [n for n in names if not NAME.fullmatch(n)]:
    raise SystemExit(f"names must match [a-z0-9_]+: {bad}")

lines = ["OPERATING_MODES: dict[int, str] = {"]
lines.extend(f"    {e['code']}: {json.dumps(e['name'])}," for e in entries)
lines.append("}")
OUT.write_text(HEADER + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
# ruff format makes the layout exact, so the committed file passes
# ruff format --check.
subprocess.run([sys.executable, "-m", "ruff", "format", str(OUT)], check=True)
print(f"{len(entries)} operating modes -> {OUT}")
