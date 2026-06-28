from datetime import datetime, timezone

from osm_scanner.models import Candidate, RawSignals
from osm_scanner.scoring import score_candidate
from osm_scanner.sources.ai_policy import classify

NOW = datetime(2026, 6, 28, tzinfo=timezone.utc)


def test_classify_banned():
    txt = "MDAnalysis does not accept any substantial uses of AI-generated content."
    cat, ev = classify(txt)
    assert cat == "banned" and ev


def test_classify_allowed():
    txt = (
        "This policy applies regardless of whether the code was written by hand, "
        "with AI assistance, or generated entirely by an AI tool."
    )
    assert classify(txt)[0] == "allowed"


def test_classify_conditional_disclosure():
    txt = "Disclose all generative tools (AI, LLMs, agents) that you used."
    assert classify(txt)[0] == "conditional"


def test_classify_none_when_no_ai_terms():
    assert classify("Please run the tests and follow PEP 8.")[0] == "none"


def _raw(policy):
    return RawSignals(
        monthly_downloads=1_000_000, stars=5000, forks=800,
        last_release_at="2025-01-01T00:00:00Z", last_commit_at="2026-06-01T00:00:00Z",
        good_first_issues=10, help_wanted_issues=5, compat_issues=5, unanswered_prs=10,
        has_contributing=True, has_code_of_conduct=True,
        pct_external_merged=0.4, median_response_days=2, merge_cadence=10,
        ai_policy=policy,
    )


def test_banned_policy_zeroes_composite():
    card = score_candidate(Candidate("a/b"), _raw("banned"), now=NOW)
    assert card.composite == 0.0
    assert any("BANS" in f for f in card.flags)


def test_allowed_policy_no_penalty_beats_conditional_and_none():
    allowed = score_candidate(Candidate("a/b"), _raw("allowed"), now=NOW).composite
    cond = score_candidate(Candidate("a/b"), _raw("conditional"), now=NOW).composite
    none = score_candidate(Candidate("a/b"), _raw("none"), now=NOW).composite
    assert allowed > none > cond
