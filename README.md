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

All four are interactive and run in the terminal. The Prolog game takes plain
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
rather than a package.

```bash
uvx ruff check .   # Lint
uvx ruff format .  # Format
```

## Tests

```bash
swipl -g run_tests -t halt mansion_escape/tests.pl   # Prolog game, 26 tests
python3 -m unittest discover -s tests                # Python, 34 tests
```

Twenty-six [plunit](https://www.swi-prolog.org/pldoc/package/plunit.html) tests
over the Prolog game's pure predicates: each note's constraint on its own, the
three of them together, `route/4` across the map, and the world's own
consistency. The one that earns the file is `exactly_one_solution` — the game's
whole premise is that reading all three notes narrows eight lever settings to
one, and nothing in `world.pl` says so directly; it falls out of three separate
rules. Loosen any one of them and `deduce` starts offering two answers, with no
error anywhere.

Thirty-four stdlib `unittest` tests over `genetic_algorithm_demo.py` — fitness,
gene source, tournament selection, crossover, mutation, and the generation cycle
that composes them, plus target validation and the display helpers. That demo is
the one declaring `dependencies = []`, so the suite needs nothing installed and
stays as standalone as the scripts it covers. Run it on any interpreter meeting
the `>=3.13` floor; a bare `python3` may be older than that, in which case name
one (`python3.13 -m unittest ...`).

The other two demos are untested: both need numpy, and installing it to test
them would undo the point of the PEP 723 blocks. The interactive orchestrators
are untested everywhere — they are print-driven and are checked by running them.

The lint, the Python tests and the Prolog tests all run on every push and every
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
