"""Render scorecards to ranked Markdown and machine-readable JSON."""

from __future__ import annotations

import json

from .models import Scorecard


def _fmt_int(v) -> str:
    return f"{v:,}" if isinstance(v, int) else "—"


def _release_age(card: Scorecard) -> str:
    raw = card.raw.last_release_at
    return raw[:10] if raw else "none"


def render_markdown(cards: list[Scorecard]) -> str:
    cards = sorted(cards, key=lambda c: c.composite, reverse=True)
    lines: list[str] = []
    lines.append("# Candidate scorecards\n")
    lines.append(
        f"Ranked {len(cards)} candidate(s). Composite = "
        "0.35·Usage + 0.35·MaintenanceNeed + 0.30·Receptiveness.\n"
    )

    # Summary table.
    lines.append(
        "| # | Repo | Composite | Usage | Maint | Recv | Downloads/mo | "
        "GoodFirst | LastRelease | Contributing |"
    )
    lines.append("|--:|------|--:|--:|--:|--:|--:|--:|------|:--:|")
    for i, c in enumerate(cards, 1):
        s = c.subscores
        has = c.raw.has_contributing
        contrib = "?" if has is None else ("✓" if has else "✗")
        lines.append(
            f"| {i} | [{c.candidate.github}](https://github.com/{c.candidate.github}) "
            f"| {c.composite:.1f} | {s.usage:.0f} | {s.maintenance_need:.0f} | "
            f"{s.receptiveness:.0f} | {_fmt_int(c.raw.monthly_downloads)} | "
            f"{_fmt_int(c.raw.good_first_issues)} | {_release_age(c)} | {contrib} |"
        )

    # Per-repo detail.
    lines.append("\n---\n")
    for i, c in enumerate(cards, 1):
        lines.extend(_detail_block(i, c))
    return "\n".join(lines) + "\n"


def _detail_block(rank: int, c: Scorecard) -> list[str]:
    s = c.subscores
    out = [
        f"## {rank}. {c.candidate.github} — {c.composite:.1f}",
        "",
        f"- Domain: {c.candidate.domain or '—'}",
        f"- Sub-scores: Usage {s.usage:.1f}, MaintenanceNeed {s.maintenance_need:.1f}, "
        f"Receptiveness {s.receptiveness:.1f}",
        "",
        "| signal | raw | normalized |",
        "|--------|-----|-----------:|",
    ]
    raw_map = c.raw.to_dict()
    for key in sorted(raw_map):
        if key in ("errors", "devstats_url"):
            continue
        norm = c.normalized.get(_norm_key(key))
        norm_s = f"{norm:.3f}" if norm is not None else ""
        out.append(f"| {key} | {raw_map[key]} | {norm_s} |")
    if c.raw.devstats_url:
        out.append(f"\nEcosystem dashboard (if tracked): {c.raw.devstats_url}")
    if c.flags:
        out.append("\nFlags:")
        out.extend(f"- {f}" for f in c.flags)
    out.append("")
    return out


# Map a raw-signal field name to its normalized-score key where they differ.
_NORM_ALIASES = {
    "last_release_at": "release_age",
    "last_commit_at": "commit_age",
}


def _norm_key(raw_key: str) -> str:
    return _NORM_ALIASES.get(raw_key, raw_key)


def render_json(cards: list[Scorecard]) -> str:
    cards = sorted(cards, key=lambda c: c.composite, reverse=True)
    payload = [c.to_dict() for c in cards]
    return json.dumps(payload, indent=2, sort_keys=True)
