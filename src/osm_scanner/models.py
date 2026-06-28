"""Core data structures: candidates, raw signals, and scorecards.

Raw signals deliberately store source-of-truth values (counts, ISO timestamps,
booleans) rather than derived scores. All normalization and age math happens in
``scoring`` against an injected ``now`` so results are deterministic and testable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Candidate:
    """One repo to evaluate."""

    github: str  # "owner/name"
    pypi: str | None = None
    domain: str | None = None
    note: str | None = None

    @property
    def owner(self) -> str:
        return self.github.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.github.split("/", 1)[1]

    def __post_init__(self) -> None:
        if "/" not in self.github:
            raise ValueError(f"github must be 'owner/name', got {self.github!r}")


@dataclass
class RawSignals:
    """Raw, un-scored signals gathered for a single candidate."""

    # --- Usage ---
    monthly_downloads: int | None = None
    stars: int | None = None
    forks: int | None = None

    # --- Maintenance need ---
    archived: bool = False
    last_release_at: str | None = None  # ISO 8601
    last_commit_at: str | None = None  # ISO 8601
    good_first_issues: int | None = None
    help_wanted_issues: int | None = None
    compat_issues: int | None = None  # numpy 2 / py3.12-3.13 / deprecation keyword hits
    open_issues: int | None = None
    open_prs: int | None = None
    unanswered_prs: int | None = None  # open PRs with no maintainer response

    # --- Receptiveness ---
    has_contributing: bool | None = None
    has_code_of_conduct: bool | None = None
    pct_external_merged: float | None = None  # 0..1, recent merged PRs from non-core authors
    median_response_days: float | None = None  # median time-to-first-response on recent PRs
    merge_cadence: float | None = None  # merges per month over the sampled window

    # --- AI-contribution policy (gates the composite; see scoring) ---
    # category: "banned" | "conditional" | "allowed" | "none" (heuristic — verify via url)
    ai_policy: str | None = None
    ai_policy_url: str | None = None
    ai_policy_evidence: str | None = None

    # --- Context (not scored) ---
    ci_status: str | None = None  # "green" | "red" | "none"
    license: str | None = None
    devstats_url: str | None = None

    # Non-fatal problems encountered while gathering (e.g. missing PyPI package).
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SubScores:
    usage: float
    maintenance_need: float
    receptiveness: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Scorecard:
    candidate: Candidate
    raw: RawSignals
    normalized: dict  # signal name -> 0..1 (only present signals)
    subscores: SubScores
    composite: float  # 0..100
    flags: list[str]  # human-readable notes (missing data, guardrails, etc.)
    fetched_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "github": self.candidate.github,
            "pypi": self.candidate.pypi,
            "domain": self.candidate.domain,
            "composite": round(self.composite, 1),
            "subscores": {k: round(v, 1) for k, v in self.subscores.to_dict().items()},
            "normalized": {k: round(v, 3) for k, v in sorted(self.normalized.items())},
            "raw": self.raw.to_dict(),
            "flags": self.flags,
            "fetched_at": self.fetched_at,
        }
