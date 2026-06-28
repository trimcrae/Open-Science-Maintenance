#!/usr/bin/env bash
# Clone your fork of a target repo, wire up the upstream remote, and set up a venv
# with an editable install. Usage: scripts/setup_target.sh <owner/name> [your-gh-user]
set -euo pipefail

REPO="${1:?usage: setup_target.sh <owner/name> [your-gh-user]}"
GH_USER="${2:-${GITHUB_USER:-}}"
NAME="${REPO##*/}"
DEST="targets/${NAME}"

if [[ -z "${GH_USER}" ]]; then
  echo "error: pass your GitHub username as arg 2 or set GITHUB_USER (needed for the fork URL)" >&2
  exit 2
fi

mkdir -p targets
if [[ -d "${DEST}/.git" ]]; then
  echo "already cloned at ${DEST}; fetching..."
  git -C "${DEST}" fetch --all --prune
else
  git clone "https://github.com/${GH_USER}/${NAME}.git" "${DEST}"
  git -C "${DEST}" remote add upstream "https://github.com/${REPO}.git" || true
fi
git -C "${DEST}" fetch upstream

cd "${DEST}"
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip

# Editable install with whatever dev/test extras the project offers; fall back gracefully.
if [[ -f pyproject.toml || -f setup.cfg || -f setup.py ]]; then
  pip install -e ".[dev,test,tests,docs]" 2>/dev/null \
    || pip install -e ".[dev]" 2>/dev/null \
    || pip install -e ".[test]" 2>/dev/null \
    || pip install -e . \
    || true
fi
[[ -f requirements-dev.txt ]] && pip install -r requirements-dev.txt || true
[[ -f requirements/test.txt ]] && pip install -r requirements/test.txt || true

echo "--- detected tooling ---"
for f in pyproject.toml setup.cfg tox.ini noxfile.py .pre-commit-config.yaml CONTRIBUTING.md CONTRIBUTING.rst; do
  [[ -e "$f" ]] && echo "  found: $f"
done
echo "ready: ${DEST} (venv at ${DEST}/.venv)"
