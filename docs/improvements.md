# Improvements

> **Status: audited 2026-09-18 against `main` @ `dc95c72`.** Migrated from the
> unversioned `~/hobby/IMPROVEMENTS.md`, which covered seven repos at once and
> had drifted; every claim below was re-checked on this date.

This file is the maintenance backlog: defects, debt, test gaps and doc drift.
Candidate new demos live in [`ideas.md`](ideas.md). Design sketches and closed
proposals are the other files in this directory.

## At a glance

Nothing open. See `## Not looked at` for what has not been checked.

## Working on these

- Run a demo: `uv run perceptron_demo.py` (PEP 723 inline dependencies).
- Python tests: `uv run --no-project --python 3.13 python -m unittest discover
  -s tests` from the repo root. Stdlib only, nothing to install.
- numpy demo tests: `uv run --no-project --python 3.13 --with 'numpy>=2.0,<3'
  python -m unittest discover -s tests/numpy`.
- Prolog: `swipl -g run_tests -t halt mansion_escape/tests.pl` (26 tests).
- Lint and CI: `.github/workflows/ci.yml`; ruff config in `ruff.toml`.
- Public repo. Never commit a work hostname, address, tool name or ticket ID.

## Settled

- The two numpy demos had no tests — landed 2026-09-24. `tests/numpy/`, 17
  tests for each demo. The perceptron tests cover the activation, the weighted
  sum, the learning rule, convergence on the four separable gates over 50
  seeds, and XOR never converging. The neural net tests cover the sigmoid, the
  forward pass, a finite-difference check of every parameter update in
  `backward`, one XOR smoke run, and `progress_bar`.

  The suite is separate so the stdlib one still needs nothing installed.
  `tests/numpy/` has no `__init__.py`, so `discover -s tests` does not recurse
  into it. It runs through `uv run --with`, which resolves numpy the way the
  scripts do, as its own CI job. The version range there copies the two scripts'
  own; keep it in step with them.

  _Checked: 34 pass on 3.13 with numpy 2.5.3. Verified they bite — negating
  `hidden_error` in `backward` fails the gradient check and the XOR run, and
  `>=` to `>` in `Perceptron.activation` fails `test_zero_fires`. Both sources
  were restored afterwards. The stdlib run still reports 34 tests, not 68.
  `ruff check` and `ruff format --check` pass._
- No demo's dependencies had been checked for currency — checked 2026-09-24,
  nothing to bump. PyPI is still unreachable from this machine, but the index
  uv is configured with here does resolve fresh (`uv run --refresh`). numpy
  resolves to 2.5.3, inside the declared `>=2.0,<3`, and all three demos ran end
  to end on it with piped input and no warnings. The new CI job also resolves
  fresh on every push, so a numpy release inside the range that breaks a demo
  now shows up there.

  _Not verified: whether that index lags PyPI. A numpy 3 would need the ceiling
  raised by hand, which is what the ceiling is for._
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
been run by hand since `dc95c72`, only with piped input (2026-09-24).

There is no `.python-version` here, so a bare `python3` in this directory gets
whatever pyenv's global is — 3.9 on this machine, which cannot even import
`genetic_algorithm_demo.py` (it uses `str | None`). That does not affect `uv
run`, which reads the inline `requires-python`, and it does not affect CI, which
pins 3.13. It only bites someone running `python3` by hand. Adding a
`.python-version` would fix it and would also pin a version the repo otherwise
leaves open; not done, because it is a one-line change with a taste question
attached.

---

`S` under an hour · `M` half a day · `L` more, or needs a decision. State is
`open`, `decision owed`, or `blocked on <thing>`. Every claim carries its
evidence and a date; say so when something was not verified.
