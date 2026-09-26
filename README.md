# fun-learning

Personal experiments for learning programming concepts interactively.
These are toy projects, not production code.

## Projects

| Project | What it is | Run with |
|---------|------------|----------|
| `perceptron_demo.py` | Interactive perceptron learning logic gates | `./perceptron_demo.py` |
| `neural_net_demo.py` | Neural network learning XOR via backpropagation | `./neural_net_demo.py` |
| `genetic_algorithm_demo.py` | Genetic algorithm evolving toward a target string | `./genetic_algorithm_demo.py` |
| `mansion_escape/` | Text adventure game in Prolog | `./mansion_escape/mansion_escape.pl` |
| `process_adventure.py` | Text adventure where you are a process, and much of it is real | `./process_adventure.py` |
| `maze_demo.py` | Six maze generators animated, solved, and shown as source (proof of concept) | `./maze_demo.py` |
| `wireworld_demo.py` | Wireworld circuit editor, with a diode and gates checked by simulation (proof of concept) | `./wireworld_demo.py` |

All seven are interactive and run in the terminal. The Prolog game takes plain
English — `go north`, `take the rusty key`, `go to the cellar` — parsed by a
definite clause grammar. Its central puzzle is a lever mechanism constrained by
notes you find; `deduce` makes the game solve it in front of you, reasoning only
from the notes you have actually read.

### `mansion_escape/`

The game is four files, no modules — every predicate lives in `user`, so any
file can call any other without an export list. Read them in this order:

| File | What is in it |
|------|---------------|
| `world.pl` | Rooms, connections, items, the notes, the lever mechanism. Nearly all facts, and where the puzzle is visible |
| `commands.pl` | `look`, `go`, `take`, `examine`, `pull`, `deduce`, `go to` — the bulk of the code |
| `parser.pl` | The DCG that turns `take the rusty key` into `take(key)` |
| `mansion_escape.pl` | Mutable state, initialization, the read-parse-run loop, and the `ensure_loaded` directives that pull in the other three |

## Requirements

- Python demos: [uv](https://docs.astral.sh/uv/) (dependencies and the
  interpreter both install automatically from each script's inline metadata
  block; Python 3.13+)
- Prolog demo: [SWI-Prolog](https://www.swi-prolog.org/) (`brew install swi-prolog`)

## Linting

Lint settings live in [`ruff.toml`](ruff.toml) rather than a `pyproject.toml`,
since these are standalone [PEP 723](https://peps.python.org/pep-0723/) scripts
rather than a package. The version is pinned, so a new ruff release can't
change lint results out from under CI.

```bash
uvx ruff@0.16.9 check .   # Lint
uvx ruff@0.16.9 format .  # Format
```

## Tests

```bash
swipl -g run_tests -t halt mansion_escape/tests.pl   # Prolog game, 36 tests
uv run --no-project --python 3.13 \
    python -m unittest discover -s tests             # Python, 150 tests
uv run --no-project --python 3.13 --with 'numpy>=2.0,<3' \
    python -m unittest discover -s tests/numpy       # numpy demos, 34 tests
```

Thirty-six [plunit](https://www.swi-prolog.org/pldoc/package/plunit.html) tests
over the Prolog game's pure predicates: each note's constraint on its own, the
three of them together, `route/4` across the map, the world's own
consistency, and ten cases of `phrase(command(C), Words)` against the DCG
parser — a disambiguating adjective, a bare direction, `go to`, a lever named
and left unnamed, two synonyms, and a line the grammar has no rule for. The
one that earns the file is `exactly_one_solution` — the game's whole premise
is that reading all three notes narrows eight lever settings to one, and
nothing in `world.pl` says so directly; it falls out of three separate rules.
Loosen any one of them and `deduce` starts offering two answers, with no error
anywhere.

150 stdlib `unittest` tests over the four scripts that declare
`dependencies = []`, so the suite needs nothing installed and stays as
standalone as the scripts it covers. Thirty-four cover `genetic_algorithm_demo.py`
— fitness, gene source, tournament selection, crossover, mutation, and the
generation cycle that composes them, plus target validation and the display
helpers. Forty-six play `process_adventure.py` through its command handler:
the parser, every ending, each room's rule, the real signal handler, the real
locks, and real refcount frees and cycle collection. Twenty-seven check that every
maze generator builds a spanning tree, that the growing tree reproduces the DFS and
Prim generators edge for edge, and the solver and SVG export. Forty-three cover the
Wireworld rules, signal travel, the clock's period, each gate's truth table, and
the diode by simulation. The command runs it through uv on 3.13, because a bare
`python3` may be older than the `>=3.13` floor and fail to import three of the
test modules.

The other two demos need numpy, so their 34 tests are a separate suite in
`tests/numpy/`. That directory has no `__init__.py`, so the stdlib run above
does not pick it up. `uv run --with` resolves numpy the same way the demos do,
and nothing gets installed into an interpreter. The perceptron tests cover the
learning rule and check that the four separable gates converge and XOR does not.
The neural net tests check `backward` against a finite-difference gradient, so a
sign error in backprop fails even though the network would still limp along.

The interactive orchestrators are untested everywhere — they are print-driven
and are checked by running them.

The lint, both Python suites and the Prolog tests all run on every push and every
pull request; see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Docs

- [`docs/no-shared-utilities.md`](docs/no-shared-utilities.md) — why the three
  Python demos duplicate their UI plumbing on purpose, and what would reopen
  the question. Replaces a proposal to extract a `demo_utils.py`, which argued
  itself out of existence: a shared module ends the standalone-ness that the
  PEP 723 block at the top of each script exists to provide.
- [`docs/ideas.md`](docs/ideas.md) — a backlog of candidate
  demos, with notes on what suits a terminal.
- [`docs/improvements.md`](docs/improvements.md) — the maintenance backlog:
  defects, debt and test gaps, and what was turned down.
- [`docs/mansion-escape-v2.md`](docs/mansion-escape-v2.md) — the design sketch
  behind the Prolog game's lever puzzle, planner, and `deduce`.

## License

MIT — see [LICENSE](LICENSE).
