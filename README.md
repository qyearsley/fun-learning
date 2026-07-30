# fun-learning

Personal experiments for learning programming concepts interactively.
These are toy projects, not production code.

## Projects

| File | What it is | Run with |
|------|------------|----------|
| `perceptron_demo.py` | Interactive perceptron learning logic gates | `./perceptron_demo.py` |
| `neural_net_demo.py` | Neural network learning XOR via backpropagation | `./neural_net_demo.py` |
| `genetic_algorithm_demo.py` | Genetic algorithm evolving toward a target string | `./genetic_algorithm_demo.py` |
| `mansion_escape.pl` | Text adventure game in Prolog | `./mansion_escape.pl` |

All four are interactive and run in the terminal. In the Prolog game, commands
are Prolog goals, so they need a trailing period — e.g. `go(north).`

## Requirements

- Python demos: [uv](https://docs.astral.sh/uv/) (dependencies install
  automatically from each script's inline metadata block; Python 3.9+)
- Prolog demo: [SWI-Prolog](https://www.swi-prolog.org/) (`brew install swi-prolog`)

## Docs

- [`docs/shared-utilities-proposal.md`](docs/shared-utilities-proposal.md) — an
  unimplemented sketch for factoring the duplicated UI plumbing out of the three
  Python demos.

## License

MIT — see [LICENSE](LICENSE).
