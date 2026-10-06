#!/usr/bin/env bash
# Ralph loop: run Claude Code repeatedly, one plans/prd.json item per iteration.
# Usage: bash plans/ralph.sh <iterations>   (from any directory; the script cds to the repo root)
# Needs the .venv activated so ruff and pytest are on PATH.
# The prompt lives in plans/ralph-prompt.txt and is shared with ralph-once.sh.
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <iterations>"
  exit 1
fi

cd "$(dirname "$0")/.."
touch progress.txt
prompt=$(cat plans/ralph-prompt.txt)

for ((i=1; i<=$1; i++)); do
  echo "Iteration $i"
  echo "------------------------------"
  result=$(claude --permission-mode acceptEdits -p "$prompt")

  echo "$result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete, exiting."
    exit 0
  fi
done
