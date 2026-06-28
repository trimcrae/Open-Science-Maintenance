# Work types

The four maintenance categories we prioritize, each chosen because it's high-value, low
controversy, and well-suited to an LLM coding agent. Each has a checklist.

## 1. Compatibility & deprecation fixes
Targets: NumPy 2.0 migration, Python 3.12/3.13 support, pandas/SciPy deprecation warnings,
SPEC-0 version bumps.
- [ ] Reproduce the warning/failure (pin the offending dependency version if needed).
- [ ] Locate the changed/removed API and the project's intended replacement.
- [ ] Apply the minimal fix; keep behavior identical on supported versions.
- [ ] Add a regression test (or assert the warning is gone) where practical.
- [ ] Update the CI version matrix / supported-versions metadata if relevant.

## 2. Docs & typing
Targets: docstrings, doctests, README/tutorial fixes, broken links, type annotations/stubs.
- [ ] Fix the content; build the docs locally if the project has a docs build.
- [ ] For typing: add/repair hints and get `mypy`/`pyright` clean **for the touched module**
      (don't try to type the whole codebase in one PR).
- [ ] Run doctests if the project uses them.
- [ ] No behavior change — pure docs/types.

## 3. Bug fixes with reproductions
Targets: open issues that include (or allow) a concrete reproduction.
- [ ] Write a **failing test** that reproduces the bug first.
- [ ] Fix until the new test passes and the baseline suite stays green.
- [ ] Keep the test in the PR.
- [ ] Note the root cause in the PR description.

## 4. Tests / CI / packaging
Targets: coverage gaps, flaky/skipped tests, CI modernization, packaging metadata.
- [ ] For coverage: add tests for an untested but stable code path.
- [ ] For flakiness: identify the nondeterminism (ordering, timing, network) and remove it.
- [ ] For packaging: migrate `setup.py`/`setup.cfg` → `pyproject.toml`, fix classifiers,
      pin/declare correct deps — but only if the project signals it wants this.
- [ ] Confirm CI passes on your fork before requesting review.

## Choosing
Map the scanner's signals to a work type:
- high `compat_issues` → work type 1
- many `good first issue` / `help wanted` → often work type 2 or 3
- low CI health / stale packaging → work type 4
