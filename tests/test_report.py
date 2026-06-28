import json
from datetime import datetime, timezone

from osm_scanner.models import Candidate, RawSignals
from osm_scanner.report import render_json, render_markdown
from osm_scanner.scoring import score_candidate

NOW = datetime(2026, 6, 28, tzinfo=timezone.utc)


def _card(github, downloads, stars):
    raw = RawSignals(
        monthly_downloads=downloads,
        stars=stars,
        forks=stars // 5,
        last_release_at="2025-01-01T00:00:00Z",
        last_commit_at="2026-06-01T00:00:00Z",
        good_first_issues=10,
        help_wanted_issues=2,
        compat_issues=3,
        unanswered_prs=5,
        has_contributing=True,
        has_code_of_conduct=True,
        pct_external_merged=0.3,
        median_response_days=5,
        merge_cadence=8,
    )
    return score_candidate(Candidate(github=github, pypi=github.split("/")[1]), raw, now=NOW)


def test_markdown_ranks_by_composite():
    low = _card("a/low", 1000, 100)
    high = _card("a/high", 1_000_000, 5000)
    md = render_markdown([low, high])
    assert "# Candidate scorecards" in md
    # higher composite should appear first in the ranked table
    assert md.index("a/high") < md.index("a/low")
    assert "| 1 |" in md and "Composite" in md


def test_json_sorted_and_stable():
    cards = [_card("a/low", 1000, 100), _card("a/high", 1_000_000, 5000)]
    out = json.loads(render_json(cards))
    assert out[0]["github"] == "a/high"  # ranked first
    # stable: re-rendering yields identical bytes
    assert render_json(cards) == render_json(cards)
    assert "raw" in out[0] and "subscores" in out[0] and "normalized" in out[0]
