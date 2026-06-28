# Contribution workflow

A repeatable process for turning a scanner pick into a merged maintenance PR. It is
deliberately fork-based (no direct pushes to upstream) so it works through the GitHub
MCP tools and never needs write access to a target repo.

## 0. Prerequisites
- A `GITHUB_TOKEN` with permission to fork and push to your own forks and open PRs.
- The scanner output (`out/scorecards.md`) to choose from.

## 1. Select a target and a scoped issue
1. From `out/scorecards.md`, prefer a repo with **high Receptiveness** and a non-trivial
   **MaintenanceNeed**.
2. Open its issue tracker; pick an issue that is:
   - clearly scoped and reproducible (or a docs/typing/compat task with an obvious fix),
   - mapped to one of the four work types in [`work-types.md`](work-types.md),
   - **unclaimed** (no open PR, no "I'll take this" within the last few weeks).
3. Scaffold a tracking note: `python scripts/new_target.py <owner/name>` → fill in
   `docs/targets/<name>.md` (issue URL, work type, plan).

## 2. Fork and clone
- Fork via the GitHub MCP `fork_repository` tool.
- `scripts/setup_target.sh <owner/name>` clones your fork into `targets/<name>/`, adds the
  `upstream` remote, creates a venv, and does an editable install with dev/test extras.

## 3. Establish a baseline
- `scripts/baseline_tests.sh <name>` runs the project's existing test suite **before any
  change** and tees the result to `docs/targets/<name>-baseline.log`. A regression is only
  meaningful against a known-green baseline. If the baseline is already red, note which
  tests fail so you don't get blamed for them.

## 4. Make the change
- Branch off the default branch using the project's naming convention (check recent merged
  PRs / CONTRIBUTING).
- Keep the diff **minimal and single-purpose**. One issue, one PR.
- For bug fixes: write the failing test first, then fix until it passes (see work-types).

## 5. Verify
- `scripts/run_checks.sh <name>` runs the project's own linters/formatters/type-checkers
  and the test suite (it reads their config — pre-commit, ruff/flake8/black, mypy, tox/nox
  — it does not reinvent them).
- Confirm: baseline-passing tests still pass, and new behavior is covered by a test.

## 6. Open the PR
- Follow the target's `CONTRIBUTING` exactly: commit-message style, **changelog / news
  fragment** (many scientific projects require one — e.g. `towncrier`), DCO sign-off or
  CLA, and the PR template.
- Push the branch to your fork; open the PR upstream via MCP `create_pull_request`.
- Cross-link the issue ("Closes #1234") and summarize what/why + how you verified.
- Record the PR URL in `docs/targets/<name>.md`.

## 7. Iterate on review
- Read review feedback via `pull_request_read`; reply via `add_issue_comment` /
  `add_reply_to_pull_request_comment`. Push fixups to the same branch.
- Where a reviewer's request is ambiguous or implies a large refactor, ask before
  committing to it.

## Etiquette
- One in-flight PR per repo until you've built some trust; don't flood maintainers.
- Don't "claim" issues you're not about to work on.
- Respect scope: a deprecation fix PR should not also reformat the file.
