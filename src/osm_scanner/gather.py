"""Assemble a full ``RawSignals`` for a candidate by calling every source."""

from __future__ import annotations

from . import config
from .http import HttpClient
from .models import Candidate, RawSignals
from .sources import ai_policy, pypistats
from .sources import github_rest as gh


def gather_signals(http: HttpClient, cand: Candidate) -> RawSignals:
    sig = RawSignals()

    # Usage: PyPI downloads.
    sig.monthly_downloads, dl_errors = pypistats.fetch_monthly_downloads(http, cand.pypi)
    sig.errors.extend(dl_errors)

    # Repo metadata (stars/forks/archived/last commit/license/default branch).
    meta = gh.fetch_repo_meta(http, cand.owner, cand.name)
    sig.stars = meta["stars"]
    sig.forks = meta["forks"]
    sig.archived = meta["archived"]
    sig.last_commit_at = meta["last_commit_at"]
    sig.license = meta["license"]
    branch = meta["default_branch"]

    # Maintenance-need signals.
    sig.last_release_at = gh.fetch_last_release(http, cand.owner, cand.name)
    sig.good_first_issues = gh.fetch_label_count(http, cand.owner, cand.name, "good first issue")
    sig.help_wanted_issues = gh.fetch_label_count(http, cand.owner, cand.name, "help wanted")
    sig.compat_issues = gh.fetch_compat_issue_count(http, cand.owner, cand.name)
    counts = gh.fetch_open_counts(http, cand.owner, cand.name)
    sig.open_issues = counts["open_issues"]
    sig.open_prs = counts["open_prs"]
    sig.unanswered_prs = counts["unanswered_prs"]

    # Receptiveness signals.
    profile = gh.fetch_community_profile(http, cand.owner, cand.name)
    sig.has_contributing = profile["has_contributing"]
    sig.has_code_of_conduct = profile["has_code_of_conduct"]
    core = gh.fetch_core_authors(http, cand.owner, cand.name)
    pr_stats = gh.fetch_pr_receptiveness(http, cand.owner, cand.name, core)
    sig.pct_external_merged = pr_stats["pct_external_merged"]
    sig.median_response_days = pr_stats["median_response_days"]
    sig.merge_cadence = pr_stats["merge_cadence"]

    # AI-contribution policy (gates the composite — the project's hard requirement).
    policy = ai_policy.fetch_ai_policy(http, cand.owner, cand.name)
    sig.ai_policy = policy["ai_policy"]
    sig.ai_policy_url = policy["ai_policy_url"]
    sig.ai_policy_evidence = policy["ai_policy_evidence"]

    # Context.
    sig.ci_status = gh.fetch_ci_status(http, cand.owner, cand.name, branch)
    sig.devstats_url = f"{config.DEVSTATS_BASE}/{cand.name}/"

    return sig
