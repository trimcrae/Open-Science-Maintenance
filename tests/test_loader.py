import json

import pytest

from osm_scanner.loader import load_candidates


def test_load_yaml_list(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text(
        "candidates:\n  - github: a/b\n    pypi: b\n  - c/d\n",
        encoding="utf-8",
    )
    cands = load_candidates(str(p))
    assert [c.github for c in cands] == ["a/b", "c/d"]
    assert cands[0].pypi == "b"
    assert cands[0].owner == "a" and cands[0].name == "b"


def test_load_json_and_dedupe(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"github": "a/b"}, {"github": "a/b"}, "e/f"]), encoding="utf-8")
    cands = load_candidates(str(p))
    assert [c.github for c in cands] == ["a/b", "e/f"]


def test_invalid_entry(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"pypi": "no-github"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_candidates(str(p))


def test_bad_github_format(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps(["noslash"]), encoding="utf-8")
    with pytest.raises(ValueError):
        load_candidates(str(p))
