#!/usr/bin/env python3
"""Scaffold docs/targets/<name>.md from the TEMPLATE for a chosen repo.

Usage: python scripts/new_target.py <owner/name>
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "docs" / "targets" / "TEMPLATE.md"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or "/" not in argv[1]:
        print("usage: new_target.py <owner/name>", file=sys.stderr)
        return 2
    repo = argv[1]
    name = repo.split("/", 1)[1]
    dest = ROOT / "docs" / "targets" / f"{name}.md"
    if dest.exists():
        print(f"already exists: {dest}", file=sys.stderr)
        return 1
    text = TEMPLATE.read_text(encoding="utf-8").replace("<owner/name>", repo).replace(
        "<name>", name
    )
    dest.write_text(text, encoding="utf-8")
    print(f"created {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
