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

- Python demos: [uv](https://docs.astral.sh/uv/) (dependencies install
  automatically from each script's inline metadata block; Python 3.9+)
- Prolog demo: [SWI-Prolog](https://www.swi-prolog.org/) (`brew install swi-prolog`)

## Linting

Lint settings live in [`ruff.toml`](ruff.toml) rather than a `pyproject.toml`,
since these are standalone [PEP 723](https://peps.python.org/pep-0723/) scripts
rather than a package.

```bash
uvx ruff check .   # Lint
uvx ruff format .  # Format
```

There are no automated tests — the demos are interactive and print-driven, so
they're checked by running them.

## Docs

- [`docs/shared-utilities-proposal.md`](docs/shared-utilities-proposal.md) — an
  unimplemented sketch for factoring the duplicated UI plumbing out of the three
  Python demos.
- [`docs/project-ideas.md`](docs/project-ideas.md) — a backlog of candidate
  demos, with notes on what suits a terminal.
- [`docs/mansion-escape-v2.md`](docs/mansion-escape-v2.md) — the design sketch
  behind the Prolog game's lever puzzle, planner, and `deduce`.

## License

MIT — see [LICENSE](LICENSE).
