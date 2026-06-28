"""All tunable knobs in one place: weights, thresholds, label sets, cache TTLs.

The scoring rubric is intentionally transparent — every signal maps to a 0..1
score via the anchors below, sub-scores are weighted averages of those, and the
composite is a weighted sum of sub-scores. Tweak here, not in scoring logic.
"""

from __future__ import annotations

# --- Composite weights (must sum to 1.0) ---
COMPOSITE_WEIGHTS = {
    "usage": 0.35,
    "maintenance_need": 0.35,
    "receptiveness": 0.30,
}

# --- Per-signal weights within each sub-score (each group should sum to 1.0) ---
USAGE_WEIGHTS = {
    "monthly_downloads": 0.55,
    "stars": 0.30,
    "forks": 0.15,
}
MAINTENANCE_WEIGHTS = {
    "release_age": 0.20,
    "commit_age": 0.15,
    "beginner_issues": 0.25,  # good first issue + help wanted
    "compat_issues": 0.25,
    "unanswered_prs": 0.15,
}
RECEPTIVENESS_WEIGHTS = {
    "has_contributing": 0.15,
    "has_code_of_conduct": 0.05,
    "pct_external_merged": 0.30,
    "median_response_days": 0.30,
    "merge_cadence": 0.20,
}

# --- Normalization anchors: (value_at_0.0, value_at_1.0) ---
# Counts use log-scaled interpolation; ages/rates use linear interpolation.
# "higher score" direction is implied by which anchor is larger.
ANCHORS = {
    # Usage (more is better)
    "monthly_downloads": (1_000, 1_000_000),  # log
    "stars": (100, 5_000),  # log
    "forks": (20, 800),  # log
    # Maintenance need (more need -> higher score)
    "release_age_days": (30, 365),  # linear: fresh release -> low need
    "commit_age_days": (7, 180),  # linear
    "beginner_issues": (0, 15),  # log-ish; uses linear-count helper
    "compat_issues": (0, 5),
    "unanswered_prs": (0, 10),
    # Receptiveness (more is better)
    "pct_external_merged": (0.0, 0.40),  # linear
    "median_response_days": (30, 2),  # linear, inverted (faster -> higher score)
    "merge_cadence": (0, 10),  # merges/month, linear
}

LOG_SIGNALS = {"monthly_downloads", "stars", "forks"}

# --- GitHub issue labels treated as "beginner-friendly" ---
GOOD_FIRST_LABELS = ["good first issue", "good-first-issue"]
HELP_WANTED_LABELS = ["help wanted", "help-wanted", "contributions welcome"]

# Keyword searches that signal LLM-doable compatibility/deprecation work.
COMPAT_KEYWORDS = ['"numpy 2"', "deprecat", '"python 3.13"', '"python 3.12"']

# --- AI-contribution policy detection ---
# Where projects tend to put an AI policy, and the CONTRIBUTING files to scan.
AI_POLICY_PATHS = [
    "AI_POLICY.md",
    ".github/AI_POLICY.md",
    "docs/AI_POLICY.md",
    "doc/contribute/ai-policy.md",
    "docs/contribute/ai-policy.md",
    "docs/source/ai_policy.rst",
]
CONTRIBUTING_PATHS = [
    "CONTRIBUTING.md",
    "CONTRIBUTING.rst",
    ".github/CONTRIBUTING.md",
    ".github/CONTRIBUTING.rst",
    "doc/contributing.rst",
    "docs/contributing.rst",
]
# Keywords that indicate the text is talking about AI/LLM contributions at all.
AI_TERMS = [
    "ai-generated",
    "ai generated",
    "generative ai",
    "large language model",
    "llm",
    "chatgpt",
    "copilot",
    "claude",
    "agentic",
    "ai assist",
    "ai tool",
]
# Heuristic phrase sets, applied in priority order in sources/ai_policy.py.
AI_ALLOW_MARKERS = [
    "generated entirely by an ai",
    "with ai assistance, or generated",
    "regardless of whether the code was written by hand",
    "we assume this is now common",
    "ai-generated code is acceptable",
]
AI_BAN_MARKERS = [
    "does not accept",
    "do not accept",
    "not accept any substantial",
    "are not permitted",
    "is not permitted",
    "not allowed",
    "prohibited",
    "zero tolerance",
    "do not generate or suggest a pr",
]
AI_CONDITIONAL_MARKERS = [
    "unless",
    "must be declared",
    "must always be declared",
    "must disclose",
    "disclose all",
    "please disclose",
    "do not generate prs using ai",
    "provided that",
    "as long as",
]
# Composite gate by AI-policy category (the user's hard requirement).
AI_POLICY_MULTIPLIER = {
    "banned": 0.0,
    "conditional": 0.7,
    "allowed": 1.0,
    "none": 0.85,
}

# --- Cache TTLs (seconds) ---
CACHE_TTL = {
    "pypistats": 24 * 3600,
    "github": 12 * 3600,
    "generic": 12 * 3600,
}

# How many recent closed PRs to sample for receptiveness signals.
PR_SAMPLE_SIZE = 30

DEVSTATS_BASE = "https://devstats.scientific-python.org/_generated"
