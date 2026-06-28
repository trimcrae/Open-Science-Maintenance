#!/usr/bin/env bash
# Run a target's own linters/formatters/type-checkers + tests, using its config.
# Usage: scripts/run_checks.sh <name>
set -uo pipefail

NAME="${1:?usage: run_checks.sh <name>}"
DEST="targets/${NAME}"
[[ -d "${DEST}" ]] || { echo "no such target dir: ${DEST}" >&2; exit 2; }

cd "${DEST}"
# shellcheck disable=SC1091
[[ -f .venv/bin/activate ]] && . .venv/bin/activate

rc=0
run() { echo "=== $* ==="; "$@"; local r=$?; [[ $r -ne 0 ]] && rc=$r; return 0; }

# Prefer the project's pre-commit config if present (it pins the canonical tools).
if [[ -f .pre-commit-config.yaml ]] && command -v pre-commit >/dev/null 2>&1; then
  run pre-commit run --all-files
else
  command -v ruff   >/dev/null 2>&1 && [[ -f pyproject.toml || -f ruff.toml ]] && run ruff check .
  command -v flake8 >/dev/null 2>&1 && [[ -f .flake8 || -f setup.cfg ]]       && run flake8
  command -v black  >/dev/null 2>&1 && run black --check .
  command -v mypy   >/dev/null 2>&1 && [[ -f mypy.ini || -f pyproject.toml ]] && run mypy . || true
fi

run python -m pytest
echo "checks finished with rc=${rc}"
exit "${rc}"
