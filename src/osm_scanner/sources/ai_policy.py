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

from .. import config
from ..http import HttpClient, HttpError

API = "https://api.github.com"


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


def _evidence(text: str, low: str, markers: list[str]) -> str | None:
    for m in markers:
        idx = low.find(m)
        if idx >= 0:
            start = max(0, idx - 60)
            snippet = text[start : idx + len(m) + 80].strip().replace("\n", " ")
            return " ".join(snippet.split())
    return None


def classify(text: str) -> tuple[str, str | None]:
    """Return (category, evidence_snippet) for a policy/contributing text body."""
    low = text.lower()
    if not any(t in low for t in config.AI_TERMS):
        return "none", None
    # Priority: explicit allowance > explicit ban > conditional > unclear.
    ev = _evidence(text, low, config.AI_ALLOW_MARKERS)
    if ev:
        return "allowed", ev
    ev = _evidence(text, low, config.AI_BAN_MARKERS)
    if ev:
        return "banned", ev
    ev = _evidence(text, low, config.AI_CONDITIONAL_MARKERS)
    if ev:
        return "conditional", ev
    # AI is discussed but stance is unclear -> conditional, flag for manual review.
    return "conditional", _evidence(text, low, config.AI_TERMS)


def fetch_ai_policy(http: HttpClient, owner: str, name: str) -> dict:
    """Locate and classify a repo's AI-contribution policy."""
    # A dedicated policy file is the strongest signal; check those first.
    for path in config.AI_POLICY_PATHS:
        text = _get_file(http, owner, name, path)
        if text:
            category, ev = classify(text)
            # A dedicated AI_POLICY file that we couldn't classify is still a real
            # policy -> treat as conditional (verify), not "none".
            if category == "none":
                category = "conditional"
            return {
                "ai_policy": category,
                "ai_policy_url": f"https://github.com/{owner}/{name}/blob/HEAD/{path}",
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
