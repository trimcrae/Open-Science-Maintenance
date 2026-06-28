"""End-to-end: gather -> score -> render, all offline, plus idempotency."""

import json

from tests.conftest import make_repo_transport

from osm_scanner.cache import Cache
from osm_scanner.gather import gather_signals
from osm_scanner.http import HttpClient
from osm_scanner.models import Candidate
from osm_scanner.scoring import score_candidate

CAND = Candidate(github="acme/widget", pypi="widget", domain="test")


def _http(tmp_path, transport):
    return HttpClient(cache=Cache(str(tmp_path / "c")), transport=transport, sleep=lambda s: None)


def test_gather_full_signals(tmp_path):
    http = _http(tmp_path, make_repo_transport())
    raw = gather_signals(http, CAND)
    assert raw.monthly_downloads == 500_000
    assert raw.stars == 4000
    assert raw.good_first_issues == 12
    assert raw.compat_issues == 6
    assert raw.unanswered_prs == 15
    assert raw.has_contributing is True
    assert raw.pct_external_merged == 0.5
    assert raw.ci_status == "green"
    assert raw.devstats_url.endswith("/widget/")


def test_scan_is_idempotent(tmp_path):
    transport = make_repo_transport()
    http = _http(tmp_path, transport)

    raw1 = gather_signals(http, CAND)
    calls_after_first = transport.call_count
    card1 = score_candidate(CAND, raw1)

    raw2 = gather_signals(http, CAND)
    # Second pass served entirely from cache: no new network calls.
    assert transport.call_count == calls_after_first
    card2 = score_candidate(CAND, raw2)

    # Note: composite uses wall-clock age, so compare the cache-stable JSON minus
    # the time-dependent age fields by checking raw signals are byte-identical.
    assert json.dumps(raw1.to_dict(), sort_keys=True) == json.dumps(raw2.to_dict(), sort_keys=True)
    assert card1.subscores.usage == card2.subscores.usage


def test_archived_repo_flagged(tmp_path):
    http = _http(tmp_path, make_repo_transport(archived=True))
    raw = gather_signals(http, CAND)
    card = score_candidate(CAND, raw)
    assert card.subscores.maintenance_need == 0.0
