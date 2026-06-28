# Open-Science-Maintenance

A toolkit for doing real maintenance on widely-used scientific open-source software.
It has two halves:

1. **`osm-scan` — a candidate scanner.** Given a list of repos, it scores each one
   against three criteria and emits ranked scorecards:
   - **Usage** — PyPI monthly downloads, GitHub stars/forks.
   - **MaintenanceNeed** — release/commit staleness, `good first issue` / `help wanted`
     counts, open issues mentioning `numpy 2` / `python 3.13` / deprecations, and open
     PRs with no maintainer response.
   - **Receptiveness** — CONTRIBUTING/CoC presence, share of recently-merged PRs from
     non-core authors, median time-to-first-response, and merge cadence.
2. **A contribution workflow** ([`docs/contribution-workflow.md`](docs/contribution-workflow.md))
   — a repeatable fork → baseline → change → PR process plus helper scripts, geared to
   four LLM-friendly work types: compatibility/deprecation fixes, docs & typing, bug
   fixes with reproductions, and tests/CI/packaging.

## Quickstart

```bash
python -m pip install -e ".[dev]"
export GITHUB_TOKEN=...            # read-only token; see .env.example
osm-scan scan --candidates candidates/scientific-python.yaml --out out/
# -> out/scorecards.md  and  out/scorecards.json
```

Re-running with a warm cache (`out/cache/`) makes zero network calls and produces
identical output. Use `--refresh` to refetch or `--no-cache` to bypass the cache.

## How scoring works

`Composite = 0.35·Usage + 0.35·MaintenanceNeed + 0.30·Receptiveness`. Each raw signal
maps to a 0–1 score via documented anchors; sub-scores are weighted averages; missing
signals are dropped and their weight renormalized (and flagged). All weights and
thresholds live in [`src/osm_scanner/config.py`](src/osm_scanner/config.py) — tune there.

## Tests

```bash
pytest        # fully offline: all HTTP is served by injected fake transports
ruff check .
```

## Layout

```
src/osm_scanner/   scanner package (sources/, scoring, report, cli)
candidates/        repo lists to scan
docs/              contribution workflow + per-target notes
scripts/           helper scripts for the contribution loop
tests/             offline unit + golden tests
```

Licensed under Apache-2.0.
