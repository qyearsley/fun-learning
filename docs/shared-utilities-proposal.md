# Proposal: shared utilities for the demo scripts

## Status

Not implemented. This is a sketch to discuss before any extraction work.

## Why this is being considered

Three demos (`perceptron_demo.py`, `neural_net_demo.py`, `genetic_algorithm_demo.py`)
have grown into siblings with nearly identical scaffolding around very different
core algorithms. Specifically:

- `get_validated_input()` is copy-pasted between the GA and NN demos with cosmetic
  message differences.
- The "header / configure / train-with-viz / test / explain" run shape is the same
  in all three.
- ASCII separators (`"=" * 70`, `"-" * 40`), centered titles, and the unicode
  progress-bar rendering (`"█" * filled + "░" * (width - filled)`) are reinvented
  in each file with small style drift.

Each script is independently self-contained today, which is good for a learner
who wants to read one file end-to-end. But maintenance edits (e.g. tweaking
prompt wording, fixing a bug in input validation, adjusting bar style) currently
mean editing the same logic in two or three places.

## Tension to resolve before extracting

These demos are **pedagogical**. A reader benefits from seeing the full
algorithm in one file without chasing imports. A `demo_utils` module that
swallows too much (e.g. the entire training loop) defeats that.

The rule of thumb the proposal recommends:

- **Extract** UI plumbing that is not part of the algorithm being taught
  (input validation, divider rendering, bar rendering, colour codes).
- **Do not extract** anything that constitutes the algorithm itself
  (training loop, evaluation, weight update, evolution step).

## Proposed module: `demo_utils.py`

A single small module at the repo root, importable by all three scripts.
Keep it boring; no classes if a function suffices.

```python
# demo_utils.py — shared cosmetic helpers for the learning demos.
# Algorithm logic lives in the per-demo files; this is just plumbing.

import sys

# ANSI colour codes
GREEN = "\033[32m"
RED   = "\033[31m"
RESET = "\033[0m"

def get_validated_input(prompt, default, min_val, max_val, cast=float):
    """Prompt until the user enters a value in [min_val, max_val], or accepts default."""
    ...

def divider(char="=", width=70):
    return char * width

def centered(title, width=70):
    return title.center(width)

def progress_bar(fraction, width=30, filled_char="█", empty_char="░"):
    filled = int(fraction * width)
    return filled_char * filled + empty_char * (width - filled)
```

That's the entire surface. Roughly five functions plus three colour constants.

## What stays in each demo

- The class that *is* the algorithm (`Perceptron`, `NeuralNetwork`,
  `GeneticAlgorithm`) — untouched.
- The `*_Demo` orchestrator class — keeps its own `print_header`,
  `explain_*`, configure flow, and training loop. The header text and
  pedagogical commentary are part of what each demo teaches; they should
  not be unified.
- Algorithm-specific visualization (the NN ASCII diagram, the GA fitness
  graph, the perceptron decision-boundary bar) — these are part of the
  teaching, not generic UI.

## Estimated impact

- ~40–60 lines of duplication removed.
- One source of truth for input validation and bar rendering.
- Each demo loses a small amount of self-containment: a reader now needs
  to know `demo_utils` exists. README should mention it.

## Risks / things to think about first

- **Self-containment cost.** If the goal of these scripts is "drop one file
  in a gist and it runs", a shared module breaks that. Worth confirming
  the intent before extracting.
- **Single-file scripts use `uv run` script-metadata blocks** (`# /// script`
  ...). A shared `demo_utils.py` is a sibling import, which works locally
  but means the scripts are no longer truly standalone.
- **Drift is currently informative.** The slight wording differences
  between `get_validated_input` variants are accidental rather than
  intentional — but worth scanning for any difference that *is* intentional
  before flattening them.

## Suggested order of work, if approved

1. Add `demo_utils.py` with `get_validated_input` only. Switch GA and NN
   demos to use it. Verify both still run identically.
2. Add `progress_bar` and adopt it in all three demos.
3. Add `divider` / `centered` / colour constants. Adopt selectively;
   leave per-demo title text and explanations alone.
4. Add a one-paragraph note to the README explaining the split.

Each step is independently revertable.
