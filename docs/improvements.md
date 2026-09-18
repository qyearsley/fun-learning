# Improvements

> **Status: audited 2026-09-18 against `main` @ `dc95c72`.** Migrated from the
> unversioned `~/hobby/IMPROVEMENTS.md`, which covered seven repos at once and
> had drifted; every claim below was re-checked on this date.

This file is the maintenance backlog: defects, debt, test gaps and doc drift.
Candidate new demos live in [`ideas.md`](ideas.md). Design sketches and closed
proposals are the other files in this directory.

## At a glance

1. The three Python demos have no tests — M · open
2. No demo's dependencies have ever been checked for currency — S · blocked

## Working on these

- Run a demo: `uv run perceptron_demo.py` (PEP 723 inline dependencies).
- Prolog: `swipl -g run_tests -t halt mansion_escape/tests.pl` (26 tests).
- Lint and CI: `.github/workflows/ci.yml`; ruff config in `ruff.toml`.
- Public repo. Never commit a work hostname, address, tool name or ticket ID.

## 1. The three Python demos have no tests

**M · open**

The Prolog half has 26 tests. The Python half has none, and the demos are
print-driven orchestrators that are genuinely awkward to test end to end — but
they are not all orchestrator. `Perceptron.activation`, `.predict` and
`.weighted_sum` (`perceptron_demo.py:66-80`), the static
`decision_bar` (`:215`) and `Individual.calculate_fitness`
(`genetic_algorithm_demo.py:83`) are pure functions over plain values and would
take tests fine.

The obstacle is that PEP 723 inline dependencies mean there is no project to
`uv sync`, so a suite needs its own invocation — `uv run --with pytest --with
numpy pytest` or similar — and CI needs a line for it.

_Checked 2026-09-18: no `tests/` directory and no `test_*.py` anywhere under the
repo; `mansion_escape/tests.pl` has 26 `test(` clauses._

## 2. No demo's dependencies have ever been checked for currency

**S · blocked on network**

Each demo declares its dependencies inline and nothing pins or audits them. The
2026-09 pass could not reach PyPI from the sandbox it ran in, so no version was
checked and nothing was bumped. Run the demos once with a fresh resolve and see
what moves.

_Not verified. Carried forward from the 2026-09-05 review, which recorded the
sandbox as the blocker._

## Settled

- Shared utilities across the three demos — declined, and the reasoning is
  written up in [`no-shared-utilities.md`](no-shared-utilities.md). Do not
  re-propose.
- Typing `abc` at two of the three prompts quit the program — landed 2026-09-05.
- Ctrl-D ended the demos in a traceback, and custom GA targets were unvalidated
  — landed `dc95c72`.
- 26 Prolog tests, up from 0, and CI — landed 2026-09-05.
- Python floor raised from `>=3.9` to `>=3.13` — landed 2026-09-05. The
  dependency-free demo was run end to end on 3.14 to check. All three files
  still declare `>=3.13`.

## Not looked at

`mansion_escape` beyond the fact that its test suite runs. The demos have not
been run interactively since `dc95c72`.

---

**Conventions**

- Size: `S` under an hour · `M` half a day · `L` more, or needs a design
  decision.
- State: `open` · `decision owed` · `blocked on <thing>`.
- `## At a glance` is the only place an item is restated. Renumber it in the same
  edit that renumbers a section.
- Every claim carries a `_Checked:_` line. If you change a claim, change its
  evidence. Say when something was not verified.
