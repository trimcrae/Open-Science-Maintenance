"""Transparent weighted scoring: raw signals -> normalized 0..1 -> sub-scores -> composite.

Design choices that keep this auditable and testable:
  * Every normalization anchor lives in ``config`` (not here).
  * Age math takes an injected ``now`` so tests are deterministic.
  * A signal that is ``None`` is dropped and its weight is renormalized over the
    signals that *are* present, with a flag recorded so partial scores are visible.
  * Guardrail: an archived repo gets MaintenanceNeed = 0 (you can't contribute to it).
"""

from __future__ import annotations

import math
from datetime import datetime

from . import config
from .models import RawSignals, Scorecard, SubScores
from .sources.github_rest import now_utc, parse_dt


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _log_norm(value: float, lo: float, hi: float) -> float:
    """Log-scaled 0..1 between anchors (value<=lo -> 0, value>=hi -> 1)."""
    if value <= 0:
        return 0.0
    return _clamp((math.log10(value) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)))


def _lin_norm(value: float, at0: float, at1: float) -> float:
    """Linear 0..1: ``at0`` maps to 0, ``at1`` maps to 1 (handles inverted anchors)."""
    if at1 == at0:
        return 0.0
    return _clamp((value - at0) / (at1 - at0))


def _count_norm(value: float, lo: float, hi: float) -> float:
    return _lin_norm(value, lo, hi)


def _age_days(iso: str | None, now: datetime) -> float | None:
    dt = parse_dt(iso)
    if dt is None:
        return None
    return (now - dt).total_seconds() / 86400


def _weighted(parts: dict[str, float], weights: dict[str, float]) -> tuple[float | None, bool]:
    """Weighted average over present parts; renormalize weights. Returns (score, had_missing)."""
    present = {k: v for k, v in parts.items() if v is not None}
    total_w = sum(weights[k] for k in present)
    if total_w == 0:
        return None, True
    score = sum(present[k] * weights[k] for k in present) / total_w
    return score, len(present) < len(weights)


def score_candidate(candidate, raw: RawSignals, now: datetime | None = None) -> Scorecard:
    now = now or now_utc()
    a = config.ANCHORS
    norm: dict[str, float] = {}
    flags: list[str] = []

    # --- Usage ---
    if raw.monthly_downloads is not None:
        norm["monthly_downloads"] = _log_norm(raw.monthly_downloads, *a["monthly_downloads"])
    if raw.stars is not None:
        norm["stars"] = _log_norm(raw.stars, *a["stars"])
    if raw.forks is not None:
        norm["forks"] = _log_norm(raw.forks, *a["forks"])
    usage, usage_missing = _weighted(
        {k: norm.get(k) for k in config.USAGE_WEIGHTS}, config.USAGE_WEIGHTS
    )

    # --- Maintenance need ---
    rel_age = _age_days(raw.last_release_at, now)
    com_age = _age_days(raw.last_commit_at, now)
    if rel_age is not None:
        norm["release_age"] = _lin_norm(rel_age, *a["release_age_days"])
    if com_age is not None:
        norm["commit_age"] = _lin_norm(com_age, *a["commit_age_days"])
    beginner = _sum_opt(raw.good_first_issues, raw.help_wanted_issues)
    if beginner is not None:
        norm["beginner_issues"] = _count_norm(beginner, *a["beginner_issues"])
    if raw.compat_issues is not None:
        norm["compat_issues"] = _count_norm(raw.compat_issues, *a["compat_issues"])
    if raw.unanswered_prs is not None:
        norm["unanswered_prs"] = _count_norm(raw.unanswered_prs, *a["unanswered_prs"])
    maint, maint_missing = _weighted(
        {
            "release_age": norm.get("release_age"),
            "commit_age": norm.get("commit_age"),
            "beginner_issues": norm.get("beginner_issues"),
            "compat_issues": norm.get("compat_issues"),
            "unanswered_prs": norm.get("unanswered_prs"),
        },
        config.MAINTENANCE_WEIGHTS,
    )
    if raw.archived:
        maint = 0.0
        flags.append("archived: maintenance need forced to 0 (cannot contribute)")

    # --- Receptiveness ---
    if raw.has_contributing is not None:
        norm["has_contributing"] = 1.0 if raw.has_contributing else 0.0
    if raw.has_code_of_conduct is not None:
        norm["has_code_of_conduct"] = 1.0 if raw.has_code_of_conduct else 0.0
    if raw.pct_external_merged is not None:
        norm["pct_external_merged"] = _lin_norm(raw.pct_external_merged, *a["pct_external_merged"])
    if raw.median_response_days is not None:
        norm["median_response_days"] = _lin_norm(
            raw.median_response_days, *a["median_response_days"]
        )
    if raw.merge_cadence is not None:
        norm["merge_cadence"] = _lin_norm(raw.merge_cadence, *a["merge_cadence"])
    recv, recv_missing = _weighted(
        {k: norm.get(k) for k in config.RECEPTIVENESS_WEIGHTS}, config.RECEPTIVENESS_WEIGHTS
    )

    for label, missing in (
        ("usage", usage_missing),
        ("maintenance", maint_missing),
        ("receptiveness", recv_missing),
    ):
        if missing:
            flags.append(f"{label}: partial (some signals missing)")

    subs = SubScores(
        usage=(usage or 0.0) * 100,
        maintenance_need=(maint or 0.0) * 100,
        receptiveness=(recv or 0.0) * 100,
    )
    cw = config.COMPOSITE_WEIGHTS
    composite = (
        subs.usage * cw["usage"]
        + subs.maintenance_need * cw["maintenance_need"]
        + subs.receptiveness * cw["receptiveness"]
    )

    # AI-policy gate: the decisive criterion for this project. A repo that bans
    # AI/agentic contributions is unusable no matter how attractive otherwise.
    policy = raw.ai_policy or "none"
    mult = config.AI_POLICY_MULTIPLIER.get(policy, 0.85)
    composite *= mult
    if policy == "banned":
        flags.append("AI policy: BANS AI-generated contributions — do not submit")
    elif policy == "conditional":
        flags.append("AI policy: conditional (disclosure/human-understanding required) — verify")
    elif policy == "allowed":
        flags.append("AI policy: permits responsible/disclosed AI use")
    else:
        flags.append("AI policy: none found (unknown; norms tightening — verify manually)")

    if raw.errors:
        flags.extend(raw.errors)

    return Scorecard(
        candidate=candidate,
        raw=raw,
        normalized=norm,
        subscores=subs,
        composite=composite,
        flags=flags,
    )


def _sum_opt(*vals) -> int | None:
    present = [v for v in vals if v is not None]
    return sum(present) if present else None
