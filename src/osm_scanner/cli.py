"""Command-line entry point: ``osm-scan scan --candidates ... --out ...``."""

from __future__ import annotations

import argparse
import os
import sys

from . import report
from .cache import Cache
from .gather import gather_signals
from .http import HttpClient
from .loader import load_candidates
from .scoring import score_candidate


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="osm-scan", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="fetch signals, score candidates, write scorecards")
    scan.add_argument("--candidates", required=True, help="path to candidates YAML/JSON")
    scan.add_argument("--out", default="out", help="output directory (default: out)")
    scan.add_argument("--no-cache", action="store_true", help="disable the on-disk cache")
    scan.add_argument("--refresh", action="store_true", help="ignore cached reads (refetch)")
    scan.add_argument("--token", default=None, help="GitHub token (else $GITHUB_TOKEN)")
    return p


def run_scan(args) -> int:
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("warning: no GITHUB_TOKEN set; GitHub signals will be rate-limited/empty",
              file=sys.stderr)

    candidates = load_candidates(args.candidates)
    cache = Cache(os.path.join(args.out, "cache"), enabled=not args.no_cache, refresh=args.refresh)
    http = HttpClient(cache=cache, token=token)

    cards = []
    for cand in candidates:
        print(f"scanning {cand.github} ...", file=sys.stderr)
        try:
            raw = gather_signals(http, cand)
        except Exception as e:  # noqa: BLE001 — one bad repo shouldn't sink the run
            print(f"  error: {e}", file=sys.stderr)
            continue
        cards.append(score_candidate(cand, raw))

    os.makedirs(args.out, exist_ok=True)
    md_path = os.path.join(args.out, "scorecards.md")
    json_path = os.path.join(args.out, "scorecards.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(report.render_markdown(cards))
    with open(json_path, "w", encoding="utf-8") as fh:
        fh.write(report.render_json(cards))

    print(f"wrote {md_path} and {json_path} ({len(cards)} scored)", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        return run_scan(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
