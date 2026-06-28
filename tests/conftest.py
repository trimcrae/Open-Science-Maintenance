"""Shared test fixtures: an injectable fake HTTP transport that serves canned
payloads keyed by URL path + query, so the whole suite runs fully offline."""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import pytest


class FakeTransport:
    """Drop-in for ``HttpClient(transport=...)``. Records calls; routes by matcher."""

    def __init__(self):
        self.calls: list[str] = []
        self._routes = []  # (matcher, (status, headers, body_text))

    def add(self, matcher, status=200, body=None, headers=None):
        body_text = "" if body is None else json.dumps(body)
        self._routes.append((matcher, (status, headers or {}, body_text)))
        return self

    def __call__(self, method, url, headers):
        self.calls.append(url)
        parsed = urlparse(url)
        for matcher, resp in self._routes:
            if matcher(parsed):
                return resp
        return (404, {}, json.dumps({"message": "no fake route", "url": url}))

    @property
    def call_count(self) -> int:
        return len(self.calls)


def path_is(path):
    return lambda u: u.path == path


def path_q(path, q_substr):
    def m(u):
        if u.path != path:
            return False
        q = parse_qs(u.query).get("q", [""])[0]
        return q_substr in q

    return m


def make_repo_transport(
    owner="acme",
    name="widget",
    pypi="widget",
    *,
    stars=4000,
    forks=600,
    archived=False,
    pushed_at="2026-06-01T00:00:00Z",
    last_release="2025-01-01T00:00:00Z",
    monthly_downloads=500_000,
    good_first=12,
    help_wanted=8,
    compat=6,
    open_issues=900,
    open_prs=120,
    unanswered_prs=15,
    has_contributing=True,
    has_coc=True,
) -> FakeTransport:
    repo = f"/repos/{owner}/{name}"
    t = FakeTransport()
    # pypistats
    t.add(
        path_is(f"/api/packages/{pypi}/recent"),
        body={"data": {"last_day": 20000, "last_week": 130000, "last_month": monthly_downloads}},
    )
    # repo meta
    t.add(
        path_is(repo),
        body={
            "stargazers_count": stars,
            "forks_count": forks,
            "archived": archived,
            "pushed_at": pushed_at,
            "default_branch": "main",
            "license": {"spdx_id": "BSD-3-Clause"},
        },
    )
    # latest release
    t.add(path_is(f"{repo}/releases/latest"), body={"published_at": last_release})
    # community profile
    t.add(
        path_is(f"{repo}/community/profile"),
        body={
            "files": {
                "contributing": {"url": "x"} if has_contributing else None,
                "code_of_conduct": {"url": "x"} if has_coc else None,
            }
        },
    )
    # contributors (core authors)
    t.add(path_is(f"{repo}/contributors"), body=[{"login": "maint1"}, {"login": "maint2"}])
    # search counts (order matters: register specific before generic)
    t.add(path_q("/search/issues", "label:\"good first issue\""), body={"total_count": good_first})
    t.add(path_q("/search/issues", "label:\"help wanted\""), body={"total_count": help_wanted})
    t.add(path_q("/search/issues", "numpy 2"), body={"total_count": compat})
    t.add(path_q("/search/issues", "comments:0"), body={"total_count": unanswered_prs})
    t.add(path_q("/search/issues", "is:pr is:open"), body={"total_count": open_prs})
    t.add(path_q("/search/issues", "is:issue is:open"), body={"total_count": open_issues})
    # closed PRs sample
    t.add(
        path_is(f"{repo}/pulls"),
        body=[
            {
                "number": 1,
                "user": {"login": "outsider"},
                "created_at": "2026-05-01T00:00:00Z",
                "merged_at": "2026-05-03T00:00:00Z",
            },
            {
                "number": 2,
                "user": {"login": "maint1"},
                "created_at": "2026-04-01T00:00:00Z",
                "merged_at": "2026-04-02T00:00:00Z",
            },
        ],
    )
    # PR comments for response-time
    t.add(
        path_is(f"{repo}/issues/1/comments"),
        body=[{"user": {"login": "maint1"}, "created_at": "2026-05-02T00:00:00Z"}],
    )
    t.add(
        path_is(f"{repo}/issues/2/comments"),
        body=[{"user": {"login": "maint2"}, "created_at": "2026-04-01T12:00:00Z"}],
    )
    # CI check-runs
    t.add(
        path_is(f"{repo}/commits/main/check-runs"),
        body={"check_runs": [{"conclusion": "success"}, {"conclusion": "skipped"}]},
    )
    return t


@pytest.fixture
def repo_transport():
    return make_repo_transport()
