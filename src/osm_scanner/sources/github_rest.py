"""Maintenance + receptiveness signals from the GitHub REST API.

Each public function fetches one slice and tolerates missing data (returns None
plus an error note) rather than aborting the whole candidate. The orchestration
that assembles a full ``RawSignals`` lives in ``osm_scanner.gather``.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone

from .. import config
from ..http import HttpClient, HttpError

API = "https://api.github.com"


def _iso(dt: str | None) -> str | None:
    return dt or None


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _gh(http: HttpClient, path: str, params: dict | None = None):
    return http.get_json(
        f"{API}{path}", params=params, source="github", ttl=config.CACHE_TTL["github"]
    )


# --- Repo metadata -------------------------------------------------------------

def fetch_repo_meta(http: HttpClient, owner: str, name: str) -> dict:
    body = _gh(http, f"/repos/{owner}/{name}")
    lic = body.get("license") or {}
    return {
        "stars": body.get("stargazers_count"),
        "forks": body.get("forks_count"),
        "archived": bool(body.get("archived", False)),
        "last_commit_at": _iso(body.get("pushed_at")),
        "default_branch": body.get("default_branch", "main"),
        "license": lic.get("spdx_id") if isinstance(lic, dict) else None,
    }


def fetch_last_release(http: HttpClient, owner: str, name: str) -> str | None:
    try:
        body = _gh(http, f"/repos/{owner}/{name}/releases/latest")
        return _iso(body.get("published_at"))
    except HttpError as e:
        if e.status == 404:
            return None  # no published releases
        raise


# --- Issue / PR counts via the Search API --------------------------------------

def _search_count(http: HttpClient, query: str) -> int | None:
    try:
        body = http.get_json(
            f"{API}/search/issues",
            params={"q": query, "per_page": "1"},
            source="github",
            ttl=config.CACHE_TTL["github"],
        )
    except HttpError:
        return None
    return body.get("total_count")


def fetch_label_count(http: HttpClient, owner: str, name: str, label: str) -> int | None:
    return _search_count(http, f'repo:{owner}/{name} is:issue is:open label:"{label}"')


def fetch_compat_issue_count(http: HttpClient, owner: str, name: str) -> int | None:
    keywords = " OR ".join(config.COMPAT_KEYWORDS)
    return _search_count(http, f"repo:{owner}/{name} is:issue is:open ({keywords})")


def fetch_open_counts(http: HttpClient, owner: str, name: str) -> dict:
    return {
        "open_issues": _search_count(http, f"repo:{owner}/{name} is:issue is:open"),
        "open_prs": _search_count(http, f"repo:{owner}/{name} is:pr is:open"),
        "unanswered_prs": _search_count(
            http, f"repo:{owner}/{name} is:pr is:open comments:0"
        ),
    }


# --- Contribution-friendliness -------------------------------------------------

def fetch_community_profile(http: HttpClient, owner: str, name: str) -> dict:
    try:
        body = _gh(http, f"/repos/{owner}/{name}/community/profile")
    except HttpError:
        return {"has_contributing": None, "has_code_of_conduct": None}
    files = body.get("files") or {}
    return {
        "has_contributing": files.get("contributing") is not None,
        "has_code_of_conduct": files.get("code_of_conduct") is not None,
    }


def fetch_core_authors(http: HttpClient, owner: str, name: str) -> set[str]:
    try:
        body = _gh(http, f"/repos/{owner}/{name}/contributors", params={"per_page": "10"})
    except HttpError:
        return set()
    if not isinstance(body, list):
        return set()
    return {c.get("login") for c in body if c.get("login")}


def fetch_pr_receptiveness(http: HttpClient, owner: str, name: str, core: set[str]) -> dict:
    """Compute %-external-merged, median first-response days, and merge cadence."""
    out = {"pct_external_merged": None, "median_response_days": None, "merge_cadence": None}
    try:
        prs = http.get_json(
            f"{API}/repos/{owner}/{name}/pulls",
            params={
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": str(config.PR_SAMPLE_SIZE),
            },
            source="github",
            ttl=config.CACHE_TTL["github"],
        )
    except HttpError:
        return out
    if not isinstance(prs, list) or not prs:
        return out

    merged = [p for p in prs if p.get("merged_at")]
    if merged:
        external = [p for p in merged if (p.get("user") or {}).get("login") not in core]
        out["pct_external_merged"] = len(external) / len(merged)
        out["merge_cadence"] = _merge_cadence(merged)

    out["median_response_days"] = _median_response_days(http, owner, name, prs[:10])
    return out


def _merge_cadence(merged: list[dict]) -> float | None:
    dates = sorted(d for p in merged if (d := parse_dt(p.get("merged_at"))))
    if len(dates) < 2:
        return None
    span_days = (dates[-1] - dates[0]).total_seconds() / 86400
    if span_days <= 0:
        return None
    return len(dates) / (span_days / 30.0)


def _median_response_days(http, owner, name, prs) -> float | None:
    deltas = []
    for pr in prs:
        created = parse_dt(pr.get("created_at"))
        author = (pr.get("user") or {}).get("login")
        number = pr.get("number")
        if not created or number is None:
            continue
        first = _first_response_at(http, owner, name, number, author)
        if first:
            deltas.append((first - created).total_seconds() / 86400)
    if not deltas:
        return None
    return statistics.median(deltas)


def _first_response_at(http, owner, name, number, author) -> datetime | None:
    try:
        comments = http.get_json(
            f"{API}/repos/{owner}/{name}/issues/{number}/comments",
            params={"per_page": "20"},
            source="github",
            ttl=config.CACHE_TTL["github"],
        )
    except HttpError:
        return None
    if not isinstance(comments, list):
        return None
    times = [
        dt
        for c in comments
        if (c.get("user") or {}).get("login") != author and (dt := parse_dt(c.get("created_at")))
    ]
    return min(times) if times else None


def fetch_ci_status(http: HttpClient, owner: str, name: str, branch: str) -> str | None:
    try:
        body = _gh(http, f"/repos/{owner}/{name}/commits/{branch}/check-runs")
    except HttpError:
        return None
    runs = body.get("check_runs") or []
    if not runs:
        return "none"
    conclusions = {r.get("conclusion") for r in runs}
    if conclusions & {"failure", "timed_out", "cancelled"}:
        return "red"
    if conclusions <= {"success", "skipped", "neutral", None}:
        return "green"
    return "none"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
