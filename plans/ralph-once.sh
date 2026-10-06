#!/usr/bin/env bash
# Ralph once: start one interactive Claude Code session on the next plans/prd.json item.
# Usage: bash plans/ralph-once.sh   (from any directory; the script cds to the repo root)
# Needs the .venv activated so ruff and pytest are on PATH.
# Same instructions as ralph.sh (shared plans/ralph-prompt.txt), but interactive so you can watch and steer.
set -e

cd "$(dirname "$0")/.."
touch progress.txt
prompt=$(cat plans/ralph-prompt.txt)

claude --permission-mode acceptEdits "$prompt"
