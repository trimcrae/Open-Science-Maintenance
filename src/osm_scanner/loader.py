"""Load candidate repos from a YAML or JSON file into ``Candidate`` objects."""

from __future__ import annotations

import json

from .models import Candidate


def load_candidates(path: str) -> list[Candidate]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    data = _parse(text, path)
    return _to_candidates(data)


def _parse(text: str, path: str):
    if path.endswith((".yaml", ".yml")):
        import yaml  # local import so JSON-only users don't need PyYAML

        return yaml.safe_load(text)
    return json.loads(text)


def _to_candidates(data) -> list[Candidate]:
    # Accept either a top-level list, or a mapping with a "candidates" key.
    if isinstance(data, dict):
        data = data.get("candidates", [])
    if not isinstance(data, list):
        raise ValueError("candidate file must be a list (or a mapping with 'candidates')")

    out: list[Candidate] = []
    seen: set[str] = set()
    for item in data:
        if isinstance(item, str):
            item = {"github": item}
        if not isinstance(item, dict) or "github" not in item:
            raise ValueError(f"invalid candidate entry: {item!r}")
        cand = Candidate(
            github=item["github"].strip(),
            pypi=item.get("pypi"),
            domain=item.get("domain"),
            note=item.get("note"),
        )
        if cand.github in seen:
            continue
        seen.add(cand.github)
        out.append(cand)
    return out
