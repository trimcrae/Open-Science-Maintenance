#!/usr/bin/env bash
# Run a target's existing test suite to capture a pre-change baseline.
# Usage: scripts/baseline_tests.sh <name>   (name = the targets/<name> dir)
set -uo pipefail

NAME="${1:?usage: baseline_tests.sh <name>}"
DEST="targets/${NAME}"
LOG="docs/targets/${NAME}-baseline.log"
[[ -d "${DEST}" ]] || { echo "no such target dir: ${DEST}" >&2; exit 2; }

cd "${DEST}"
# shellcheck disable=SC1091
[[ -f .venv/bin/activate ]] && . .venv/bin/activate

echo "running baseline for ${NAME} ..."
{
  echo "# baseline for ${NAME} @ $(git rev-parse --short HEAD 2>/dev/null)"
  echo "# date: $(date -u +%FT%TZ)"
  if [[ -f noxfile.py ]]; then
    nox -s tests 2>&1 || nox 2>&1
  elif [[ -f tox.ini ]]; then
    python -m pytest 2>&1   # run pytest directly; tox envs are slower for a baseline
  else
    python -m pytest 2>&1
  fi
} | tee "../../${LOG}"

echo "baseline log written to ${LOG}"
