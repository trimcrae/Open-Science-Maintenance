"""Detect a repo's stance on AI-generated contributions.

This is the single most important signal for the project's goal: many scientific
projects now restrict or ban AI/agentic contributions (e.g. MDAnalysis bans them
outright, naming "claude code"), while others permit responsible, disclosed use
(e.g. xarray). Submitting AI-assisted PRs to a banning project can get a
contributor restricted, so AI policy gates the composite score.

Classification is a transparent heuristic over the AI policy file and CONTRIBUTING
text; we always return the source URL and an evidence snippet so a human can
verify before acting on it. Categories:

  "banned"      — substantial AI contributions not accepted
  "conditional" — allowed only under conditions (disclosure, deep understanding)
  "allowed"     — responsible/disclosed AI use explicitly permitted
  "none"        — no AI policy found (unknown; verify manually)
"""

from __future__ import annotations

import base64
import re

from .. import config
from ..http import HttpClient, HttpError

API = "https://api.github.com"

# AI terms matched on word boundaries (with optional trailing plural "s") so short
# tokens (e.g. "llm", "ai") match "LLMs"/"AI" but not the insides of unrelated words
# like "fulfillment" or "Hawaii". Longest alternatives first for readable matches.
_AI_TERM_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in sorted(config.AI_TERMS, key=len, reverse=True))
    + r")s?\b",
    re.IGNORECASE,
)


def _get_file(http: HttpClient, owner: str, name: str, path: str) -> str | None:
    try:
        body = http.get_json(
            f"{API}/repos/{owner}/{name}/contents/{path}",
            source="github",
            ttl=config.CACHE_TTL["github"],
        )
    except HttpError:
        return None
    if isinstance(body, dict) and body.get("content"):
        try:
            return base64.b64decode(body["content"]).decode("utf-8", "replace")
        except (ValueError, TypeError):
            return None
    return None


def _ai_windows(low: str, pad: int = 280) -> list[tuple[int, int]]:
    """Character ranges around every AI-term mention, merged where they overlap."""
    spans = [(max(0, m.start() - pad), m.end() + pad) for m in _AI_TERM_RE.finditer(low)]
    spans.sort()
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def _marker_near_ai(text: str, low: str, markers: list[str], windows) -> str | None:
    """Find a marker that occurs *within* an AI-mention window; return a snippet."""
    for m in markers:
        start = 0
        while (idx := low.find(m, start)) >= 0:
            if any(ws <= idx <= we for ws, we in windows):
                snip = text[max(0, idx - 70) : idx + len(m) + 90].strip().replace("\n", " ")
                return " ".join(snip.split())
            start = idx + len(m)
    return None


def classify(text: str) -> tuple[str, str | None]:
    """Return (category, evidence) — markers only count when near an AI mention.

    Proximity matters: a bare "unless" in an unrelated docstring must not be read
    as an AI condition. Priority: explicit allowance > ban > conditional > unclear.
    """
    low = text.lower()
    windows = _ai_windows(low)
    if not windows:
        return "none", None
    for cat, markers in (
        ("allowed", config.AI_ALLOW_MARKERS),
        ("banned", config.AI_BAN_MARKERS),
        ("conditional", config.AI_CONDITIONAL_MARKERS),
    ):
        ev = _marker_near_ai(text, low, markers, windows)
        if ev:
            return cat, ev
    # AI is discussed but stance is unclear -> conditional, flag for manual review.
    ws, we = windows[0]
    return "conditional", " ".join(text[ws:we].strip().replace("\n", " ").split())[:180]


def fetch_ai_policy(http: HttpClient, owner: str, name: str) -> dict:
    """Locate and classify a repo's AI-contribution policy.

    Reads *all* known policy files and concatenates them so a stub that merely
    redirects (e.g. xarray's root AI_POLICY.md -> doc/contribute/ai-policy.md)
    doesn't mask the real policy text. Falls back to CONTRIBUTING.
    """
    found_paths, texts = [], []
    for path in config.AI_POLICY_PATHS:
        text = _get_file(http, owner, name, path)
        if text:
            found_paths.append(path)
            texts.append(text)
    if texts:
        category, ev = classify("\n\n".join(texts))
        # A dedicated policy file always means a real stance exists; never "none".
        if category == "none":
            category = "conditional"
        return {
            "ai_policy": category,
            "ai_policy_url": f"https://github.com/{owner}/{name}/blob/HEAD/{found_paths[0]}",
            "ai_policy_evidence": ev or "AI policy file present; classify manually",
        }
    # Otherwise scan CONTRIBUTING for an AI clause.
    for path in config.CONTRIBUTING_PATHS:
        text = _get_file(http, owner, name, path)
        if text is None:
            continue
        category, ev = classify(text)
        if category != "none":
            return {
                "ai_policy": category,
                "ai_policy_url": f"https://github.com/{owner}/{name}/blob/HEAD/{path}",
                "ai_policy_evidence": ev,
            }
        # CONTRIBUTING exists but says nothing about AI -> stop; policy is "none".
        break
    return {"ai_policy": "none", "ai_policy_url": None, "ai_policy_evidence": None}
