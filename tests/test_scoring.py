from datetime import datetime, timezone

from osm_scanner.models import Candidate, RawSignals
from osm_scanner.scoring import _count_norm, _lin_norm, _log_norm, score_candidate

NOW = datetime(2026, 6, 28, tzinfo=timezone.utc)
CAND = Candidate(github="acme/widget", pypi="widget")


def test_norm_helpers():
    assert _log_norm(1000, 1000, 1_000_000) == 0.0
    assert _log_norm(1_000_000, 1000, 1_000_000) == 1.0
    assert abs(_log_norm(31623, 1000, 1_000_000) - 0.5) < 0.01
    assert _lin_norm(30, 30, 365) == 0.0
    assert _lin_norm(365, 30, 365) == 1.0
    # inverted anchors (faster response -> higher score)
    assert _lin_norm(2, 30, 2) == 1.0
    assert _lin_norm(30, 30, 2) == 0.0
    assert abs(_lin_norm(16, 30, 2) - 0.5) < 0.01
    assert _count_norm(0, 0, 15) == 0.0
    assert _count_norm(15, 0, 15) == 1.0


def _full_raw(**over):
    base = dict(
        monthly_downloads=1_000_000,
        stars=5000,
        forks=800,
        last_release_at="2025-01-01T00:00:00Z",  # ~1.5y old -> high need
        last_commit_at="2025-12-01T00:00:00Z",
        good_first_issues=10,
        help_wanted_issues=5,
        compat_issues=5,
        unanswered_prs=10,
        has_contributing=True,
        has_code_of_conduct=True,
        pct_external_merged=0.4,
        median_response_days=2,
        merge_cadence=10,
        ai_policy="allowed",
    )
    base.update(over)
    return RawSignals(**base)


def test_high_everything_scores_near_top():
    card = score_candidate(CAND, _full_raw(), now=NOW)
    assert card.subscores.usage > 95
    assert card.subscores.receptiveness > 95
    assert card.subscores.maintenance_need > 80
    assert card.composite > 85


def test_archived_zeroes_maintenance():
    card = score_candidate(CAND, _full_raw(archived=True), now=NOW)
    assert card.subscores.maintenance_need == 0.0
    assert any("archived" in f for f in card.flags)


def test_missing_signal_renormalizes_weight():
    # Only stars present in usage -> usage == stars normalization (weight renormalized to 1).
    raw = RawSignals(stars=5000)
    card = score_candidate(CAND, raw, now=NOW)
    assert abs(card.subscores.usage - 100.0) < 0.01
    assert any("usage: partial" in f for f in card.flags)


def test_fresh_active_repo_has_low_need():
    raw = _full_raw(
        last_release_at="2026-06-20T00:00:00Z",
        last_commit_at="2026-06-27T00:00:00Z",
        good_first_issues=0,
        help_wanted_issues=0,
        compat_issues=0,
        unanswered_prs=0,
    )
    card = score_candidate(CAND, raw, now=NOW)
    assert card.subscores.maintenance_need < 10


def test_errors_surface_as_flags():
    raw = _full_raw()
    raw.errors.append("pypistats: package not found")
    card = score_candidate(CAND, raw, now=NOW)
    assert any("not found" in f for f in card.flags)
