from osm_scanner.cache import Cache
from osm_scanner.http import HttpClient
from osm_scanner.sources import github_rest as gh
from osm_scanner.sources import pypistats
from tests.conftest import FakeTransport, path_is


def client(tmp_path, transport):
    return HttpClient(cache=Cache(str(tmp_path / "c")), transport=transport, sleep=lambda s: None)


def test_pypistats_downloads(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    val, errs = pypistats.fetch_monthly_downloads(http, "widget")
    assert val == 500_000 and errs == []


def test_pypistats_missing_package(tmp_path):
    t = FakeTransport()  # no route -> 404
    http = client(tmp_path, t)
    val, errs = pypistats.fetch_monthly_downloads(http, "ghost")
    assert val is None and errs


def test_pypistats_no_package_configured(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    val, errs = pypistats.fetch_monthly_downloads(http, None)
    assert val is None and errs


def test_repo_meta_and_release(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    meta = gh.fetch_repo_meta(http, "acme", "widget")
    assert meta["stars"] == 4000 and meta["forks"] == 600
    assert meta["archived"] is False and meta["default_branch"] == "main"
    assert gh.fetch_last_release(http, "acme", "widget") == "2025-01-01T00:00:00Z"


def test_release_404_returns_none(tmp_path):
    # No GitHub Release -> fetch_last_release returns None (no unreliable tag fallback).
    t = FakeTransport()
    t.add(path_is("/repos/acme/widget/releases/latest"), status=404, body={})
    http = client(tmp_path, t)
    assert gh.fetch_last_release(http, "acme", "widget") is None


def test_search_counts(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    assert gh.fetch_label_count(http, "acme", "widget", "good first issue") == 12
    assert gh.fetch_label_count(http, "acme", "widget", "help wanted") == 8
    assert gh.fetch_compat_issue_count(http, "acme", "widget") == 6
    counts = gh.fetch_open_counts(http, "acme", "widget")
    assert counts["open_issues"] == 900
    assert counts["open_prs"] == 120
    assert counts["unanswered_prs"] == 15


def test_community_profile(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    prof = gh.fetch_community_profile(http, "acme", "widget")
    assert prof["has_contributing"] is True
    assert prof["has_code_of_conduct"] is True


def test_pr_receptiveness(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    core = gh.fetch_core_authors(http, "acme", "widget")
    assert core == {"maint1", "maint2"}
    stats = gh.fetch_pr_receptiveness(http, "acme", "widget", core)
    # 2 merged, 1 by outsider -> 50% external
    assert stats["pct_external_merged"] == 0.5
    # PR #1: created 05-01, first non-author comment 05-02 -> 1 day;
    # PR #2: created 04-01, first comment same day +12h -> 0.5 day; median = 0.75
    assert stats["median_response_days"] == 0.75
    assert stats["merge_cadence"] is not None


def test_ci_status(tmp_path, repo_transport):
    http = client(tmp_path, repo_transport)
    assert gh.fetch_ci_status(http, "acme", "widget", "main") == "green"
