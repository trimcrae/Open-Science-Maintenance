# Open-Science-Maintenance

Tooling for finding where AI-assisted maintenance of widely-used scientific open-source
software can *actually* land — and, crucially, where the projects' own policies allow it.

> **Why the focus on AI policy?** Scientific OSS is rapidly adopting policies on
> AI-generated contributions. Some projects **ban** them outright (e.g. MDAnalysis names
> "claude code"; networkx tells AI assistants not to open PRs), others permit
> **responsible, disclosed** use that still requires a human to understand and own every
> change (e.g. xarray), and many have **no stated policy yet**. No widely-used scientific
> project welcomes *unreviewed, fully-autonomous* AI PRs. So the single most important
> thing to know before contributing is each project's stance — and that's what this
> toolkit surfaces.

It has three parts:

1. **`osm-scan` — a candidate scanner.** Given a list of repos, it scores each one and,
   most importantly, **detects and classifies its AI-contribution policy**
   (banned / conditional / allowed / none), which gates the overall score. It also scores:
   - **Usage** — PyPI monthly downloads, GitHub stars/forks.
   - **MaintenanceNeed** — release/commit staleness, `good first issue` / `help wanted`
     counts, open issues mentioning `numpy 2` / `python 3.13` / deprecations, open PRs
     with no maintainer response.
   - **Receptiveness** — CONTRIBUTING/CoC presence, share of recently-merged PRs from
     non-core authors, median time-to-first-response, and merge cadence.
2. **The ecosystem AI-policy report** ([`docs/AI-POLICY-REPORT.md`](docs/AI-POLICY-REPORT.md))
   — a generated survey of where widely-used scientific projects stand on AI
   contributions, with evidence snippets and policy links. Regenerate with
   `python scripts/ai_policy_report.py`.
3. **A contribution workflow** ([`docs/contribution-workflow.md`](docs/contribution-workflow.md))
   — for the projects whose policies *do* permit responsible AI assistance: a repeatable
   fork → baseline → change → PR process (with a human owner who reviews and discloses),
   geared to four work types: compatibility/deprecation fixes, docs & typing, bug fixes
   with reproductions, and tests/CI/packaging.

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

`Composite = (0.35·Usage + 0.35·MaintenanceNeed + 0.30·Receptiveness) × AIPolicyGate`.
Each raw signal maps to a 0–1 score via documented anchors; sub-scores are weighted
averages; missing signals are dropped and their weight renormalized (and flagged). The
**AI-policy gate** multiplies the composite by `0.0` (banned), `0.7` (conditional), `1.0`
(allowed), or `0.85` (no policy found) — so a repo that bans AI contributions drops to 0
regardless of how attractive it is otherwise. All weights, thresholds, and the AI-policy
keyword heuristics live in [`src/osm_scanner/config.py`](src/osm_scanner/config.py).

The AI-policy classification is heuristic and point-in-time; the scanner always emits the
policy URL and an evidence snippet so you can verify before acting.

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
