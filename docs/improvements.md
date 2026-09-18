# Improvements

> **Status: audited 2026-09-18 against `main` @ `dc95c72`.** Migrated from the
> unversioned `~/hobby/IMPROVEMENTS.md`, which covered seven repos at once and
> had drifted; every claim below was re-checked on this date.

This file is the maintenance backlog: defects, debt, test gaps and doc drift.
Candidate new demos live in [`ideas.md`](ideas.md). Design sketches and closed
proposals are the other files in this directory.

## At a glance

1. The two numpy demos still have no tests — M · open
2. No demo's dependencies have ever been checked for currency — S · blocked

## Working on these

- Run a demo: `uv run perceptron_demo.py` (PEP 723 inline dependencies).
- Python tests: `python3 -m unittest discover -s tests` from the repo root, on
  any interpreter meeting the `>=3.13` floor. Stdlib only, nothing to install.
- Prolog: `swipl -g run_tests -t halt mansion_escape/tests.pl` (26 tests).
- Lint and CI: `.github/workflows/ci.yml`; ruff config in `ruff.toml`.
- Public repo. Never commit a work hostname, address, tool name or ticket ID.

## 1. The two numpy demos still have no tests

**M · open**

`genetic_algorithm_demo.py` is covered — 34 tests, see `## Settled`.
`perceptron_demo.py` and `neural_net_demo.py` are not, and the pure functions
worth covering are there: `Perceptron.activation`, `.predict` and
`.weighted_sum` (`perceptron_demo.py:66-80`) and the static `decision_bar`
(`:215`).

The obstacle is numpy. Both scripts declare it as a PEP 723 inline dependency,
so testing them means either installing numpy in CI — a dependency the scripts
resolve for themselves at run time, which is the thing this repo's layout
avoids — or running the tests through `uv run --with numpy --with pytest`, which
reintroduces a resolve step the genetic algorithm tests deliberately do without.
Decide which before writing anything.

_Checked 2026-09-18: `tests/` holds one file, covering the genetic algorithm
demo only. The other two demos declare `numpy>=2.0,<3`._

## 2. No demo's dependencies have ever been checked for currency

**S · blocked on network**

Each demo declares its dependencies inline and nothing pins or audits them. The
2026-09 pass could not reach PyPI, and neither could the 2026-09-18 one, so no
version has been checked and nothing bumped. Run the demos once with a fresh
resolve and see what moves.

_Not verified. `uvx ruff` and `uv sync` both fail here with a tunnel error
reaching `files.pythonhosted.org`._

## Settled

- The genetic algorithm demo had no tests — landed 2026-09-18.
  `tests/test_genetic_algorithm.py`, 34 tests over fitness, gene source,
  population sorting, tournament selection, crossover, mutation and the
  generation cycle, plus target validation and the two display helpers.

  Stdlib `unittest`, no test dependency, no package: `python3 -m unittest
  discover -s tests`. That demo was picked because it is the one declaring
  `dependencies = []`, so the suite needs nothing installed — which is also why
  a third CI job could be added without touching how the scripts resolve.

  _Checked: 34 pass on 3.14.7 and on 3.13.15, in 0.03 s. Verified they bite —
  removing `strict=True` from `Individual.calculate_fitness` fails
  `test_a_length_mismatch_raises_rather_than_scoring_the_prefix`, and the source
  was restored afterwards. `ruff check` and `ruff format --check` pass over the
  new file._
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

There is no `.python-version` here, so a bare `python3` in this directory gets
whatever pyenv's global is — 3.9 on this machine, which cannot even import
`genetic_algorithm_demo.py` (it uses `str | None`). That does not affect `uv
run`, which reads the inline `requires-python`, and it does not affect CI, which
pins 3.13. It only bites someone running `python3` by hand. Adding a
`.python-version` would fix it and would also pin a version the repo otherwise
leaves open; not done, because it is a one-line change with a taste question
attached.

---

**Conventions**

- Size: `S` under an hour · `M` half a day · `L` more, or needs a design
  decision.
- State: `open` · `decision owed` · `blocked on <thing>`.
- `## At a glance` is the only place an item is restated. Renumber it in the same
  edit that renumbers a section.
- Every claim carries a `_Checked:_` line. If you change a claim, change its
  evidence. Say when something was not verified.
