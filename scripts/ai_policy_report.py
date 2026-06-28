#!/usr/bin/env python3
"""Generate a human-readable AI-contribution-policy report from a scan's JSON.

Usage:
    python scripts/ai_policy_report.py [out/scorecards.json] [docs/AI-POLICY-REPORT.md]

Reads the scorecards produced by ``osm-scan scan`` and emits a Markdown report
grouping projects by their AI-contribution stance (banned / conditional /
allowed / none), with evidence snippets and policy URLs for verification.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys

CATEGORY_ORDER = ["banned", "conditional", "allowed", "none"]
LABELS = {
    "banned": "❌ Banned — AI/agentic contributions not accepted",
    "conditional": "⚠️ Conditional — allowed only with disclosure and/or human understanding",
    "allowed": "✅ Allowed — responsible, disclosed AI use permitted",
    "none": "❔ No stated policy (silent — not permission; norms are tightening)",
}


def main(argv: list[str]) -> int:
    in_path = argv[1] if len(argv) > 1 else "out/scorecards.json"
    out_path = argv[2] if len(argv) > 2 else "docs/AI-POLICY-REPORT.md"
    with open(in_path, encoding="utf-8") as fh:
        cards = json.load(fh)

    by_cat: dict[str, list] = {c: [] for c in CATEGORY_ORDER}
    for card in cards:
        cat = (card.get("raw") or {}).get("ai_policy") or "none"
        by_cat.setdefault(cat, []).append(card)

    today = _dt.date.today().isoformat()
    n = len(cards)
    lines: list[str] = []
    lines.append("# AI-contribution policies across the scientific Python ecosystem\n")
    lines.append(
        f"Survey of **{n}** widely-used scientific/numerical Python projects, generated "
        f"on **{today}** by `osm-scan` (see methodology at the end). The question: *which "
        "projects accept AI-generated / agentic contributions, and under what conditions?*\n"
    )

    # Headline counts.
    lines.append("## Summary\n")
    lines.append("| Stance | Projects |")
    lines.append("|--------|---------:|")
    for cat in CATEGORY_ORDER:
        lines.append(f"| {LABELS[cat]} | {len(by_cat.get(cat, []))} |")
    allowed = len(by_cat.get("allowed", []))
    banned = len(by_cat.get("banned", []))
    lines.append(
        f"\n**Bottom line:** {allowed} of {n} projects explicitly permit AI-generated "
        f"contributions; {banned} ban them outright. **None** were found to welcome "
        "*unreviewed, fully-autonomous* PRs — even the most permissive policies require a "
        "human who understands, reviews, and can explain every change, and who discloses "
        "tool use.\n"
    )

    # Per-category detail.
    for cat in CATEGORY_ORDER:
        group = sorted(by_cat.get(cat, []), key=lambda c: c["github"].lower())
        if not group:
            continue
        lines.append(f"## {LABELS[cat]}\n")
        for c in group:
            raw = c.get("raw") or {}
            url = raw.get("ai_policy_url")
            ev = raw.get("ai_policy_evidence")
            head = f"- **[{c['github']}](https://github.com/{c['github']})**"
            if url:
                head += f" — [policy]({url})"
            lines.append(head)
            if ev:
                lines.append(f'  - evidence: "{ev}"')
        lines.append("")

    # Methodology + caveats.
    lines.append("## Methodology & caveats\n")
    lines.append(
        "- For each repo, `osm-scan` reads any dedicated AI-policy file "
        "(`AI_POLICY.md`, `doc/contribute/ai-policy.md`, …) and the `CONTRIBUTING` file, "
        "then classifies the stance with a transparent keyword heuristic that only counts "
        "ban/allow/condition markers occurring **near an AI mention** (to avoid false "
        "positives).\n"
        "- Classification is heuristic and point-in-time. **Always open the linked policy "
        "and read it before acting.** A `none` result means *no policy was found*, which is "
        "not the same as permission — several projects in this ecosystem added policies "
        "recently and more are expected to.\n"
        "- Evidence snippets are short excerpts for orientation, not the full policy.\n"
    )
    out = "\n".join(lines) + "\n"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {out_path} ({n} projects)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
