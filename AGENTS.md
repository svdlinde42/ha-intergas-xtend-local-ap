# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex, Copilot and others) when working with code in this repository.

## Project

Home Assistant custom integration (distributed via HACS) that monitors and manages an
Intergas Xtend boiler through the Xtend's built-in Wi-Fi access point. Everything below
describes the intended design and must be kept in sync as code lands.

Progress is tracked in `plans/prd.json`: one item per small deliverable with
`passes: false` until verified. Flip `passes` only after the item's own "Verify" step
succeeds. `bash plans/ralph.sh <n>` runs Claude Code in a loop, one item per iteration; each
iteration appends a line to `progress.txt` (repo root) and makes one commit.
`bash plans/ralph-once.sh` does one item in an interactive session. Both read their
instructions from `plans/ralph-prompt.txt`. Items in category `functional` or
`research` need the real device or the owner and are skipped by the loop.

Terminology: this is a HACS **custom integration** (lives in `custom_components/<domain>/`),
not a Home Assistant **add-on** (a Docker container under the Supervisor). HACS does not
distribute add-ons.

## Network topology and the hard constraint

- The Xtend installer Wi-Fi module exposes an access point (AP). The Home Assistant host is
  wired to the LAN and additionally joined to the Xtend AP over Wi-Fi.
- The Xtend is reached by its local IP on that AP (default `10.20.30.1`, configurable) and
  exposes a REST interface: GET for status, writes for installer parameters.
- Status endpoint (captured 2026-10-06, firmware V1.20-):
  `GET http://<host>/api/stats/values?fields=<comma-separated hex ids>`. Response is
  `{"stats": {"<hex-id>": <int | string>}}`. The 32 ids used in phase 1 and their meaning,
  scale factor and unit are in `docs/stats-mapping.md`. That file is the only source for
  field semantics; do not add or change a mapping without updating it.
- Sentinel values: `32767` means "not available" for every numeric field. `255` means
  "no notification" for 7940 and 7e2c. `0` means "no fault" for 8439.
- Fault codes (F, field 7e2c) and notification codes (n, field 7940) with description and
  cause/solution are in `docs/fault-codes.json` (human-readable copy: `docs/fault-codes.md`).
  Field 7940 = n-code is confirmed against the device (7940 = 95 while the display showed
  n095, 2026-10-06). Field 7e2c = F-code follows the mapping document and is not yet
  confirmed by observation.
  Source: Intergas document 88104401, chapter 12.1 and 12.2. The text is Dutch and quoted
  verbatim; it is exposed as sensor attributes and must not be paraphrased or translated.
  Field 8439 is the CV boiler's own OpenTherm code and is not covered.
- **The AP switches itself off after ~15 minutes without requests.** Polling therefore also
  acts as a keep-alive. Once the AP is off, polling cannot bring it back: the user must
  re-enable the AP on the device and possibly reconnect the HA host's Wi-Fi. So when the
  Xtend is unreachable the coordinator backs off (from the 3rd failure, doubling up to
  5 minutes), raises a repairs issue with recovery steps, and offers a "Poll now" button.
  One successful poll, manual or scheduled, resets the backoff to the configured interval.
- Poll interval target: every 5–10 s via a `DataUpdateCoordinator`. Keep this one
  coordinator as the single source of HTTP traffic; do not let entities call the device
  directly.

## Delivery in two phases

1. **Phase 1 – read-only status.** Config flow (host/IP, poll interval), one coordinator
   doing the periodic GET, sensor/binary_sensor entities derived from the status payload.
   Nothing writes to the device.
2. **Phase 2 – installer parameters.** Read parameter list, then expose writable entities
   (`number`/`select`/`switch`) that push values back. Writes change boiler configuration:
   gate them behind explicit entity types, validate ranges from the device's own metadata
   where available, and refresh the coordinator after each write. Do not start Phase 2
   until Phase 1 is stable against a real device.

## Intended layout

```
custom_components/intergas_xtend/
  __init__.py        # async_setup_entry / unload, creates the coordinator
  api.py             # thin aiohttp client for the Xtend REST interface, no HA imports
  coordinator.py     # DataUpdateCoordinator; owns poll interval and AP-timeout handling
  config_flow.py     # host + interval; validate by performing one GET
  const.py
  codes.py           # fault/notification code tables, generated from docs/fault-codes.json
  sensor.py, button.py                 # phase 1 (button = "Poll now")
  number.py, select.py, switch.py      # phase 2
  manifest.json, strings.json, translations/
hacs.json
tests/               # pytest-homeassistant-custom-component
```

`api.py` must be importable and testable without Home Assistant. Keep REST endpoint paths,
payload field names and units in one place (`const.py` or `api.py`) and document their
source (captured from the device, not guessed) in a comment. Unknown fields: expose raw and
mark as diagnostic rather than inventing semantics.

## Commands (planned toolchain)

Standard HA custom-integration tooling; adjust once `pyproject.toml` exists.

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements_dev.txt          # homeassistant, pytest-homeassistant-custom-component, ruff
pytest                                       # all tests
pytest tests/test_api.py -k status           # single test / pattern
ruff check . ; ruff format .
```

Local validation runs in a dev HA instance by symlinking or copying `custom_components/`
into its `config/` directory and restarting. hassfest and HACS validation run as GitHub
Actions on push.

## Conventions

- Async only; use HA's shared `aiohttp` session (`async_get_clientsession`). Never block the
  event loop.
- Use a `DataUpdateCoordinator`; raise `UpdateFailed` on HTTP/timeout errors so entities go
  unavailable instead of holding stale values.
- `unique_id` is the host. The status payload has no serial number or MAC address
  (decided 2026-10-06). The README states that changing the IP creates a new entry.
- Entity naming via `has_entity_name = True` and translation keys in `strings.json`.
  English and Dutch names follow the labels of the Xtend summary page ("Xtend summary" /
  "Xtend overzicht"); the exact names per field are in `plans/prd.json`.
- Commit messages and code comments in English; the README may stay bilingual.
- One commit per finished `plans/prd.json` item. Subject: Conventional Commits with the item's
  category as scope, e.g. `feat(entities): add temperature sensors`. Body: the item's
  description line. No `Co-Authored-By`, `Claude-Session` or other attribution trailers.

## Communication

Say the main thing first: the answer, the decision, or the result. Give the reason after it,
and only when the reason changes what the reader does next. Cut every word that adds nothing.
Say what you assume, what can go wrong, and what you have not checked. Write sentences at
CEFR B2 and words at CEFR B1. One main idea per sentence, never over 25 words. Use the word
you would say in a meeting. Keep every name, number, date, path and participant ID exactly
as it is.

CEFR is the Common European Framework of Reference for Languages, the European scale for
language skill. At B1 a reader knows the everyday words. At B2 a reader can follow an
explanation with several steps. Most of our readers do not have English as a first language.

Everything we keep is English: docs/, README.md, commits, branch names and pull requests. 
Chat follows the language you write in, at the same level. Never translate what you copy in.
