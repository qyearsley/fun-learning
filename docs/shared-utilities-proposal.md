# Proposal: shared utilities for the demo scripts

## Status

Not implemented. This is a sketch to discuss before any extraction work.

## Why this is being considered

Three demos (`perceptron_demo.py`, `neural_net_demo.py`, `genetic_algorithm_demo.py`)
have grown into siblings with nearly identical scaffolding around very different
core algorithms. Specifically:

- `get_validated_input()` is copy-pasted between the GA and NN demos. The two
  copies are 16 lines each and differ only in an out-of-range hint ("Enter a
  value between…" vs "Please enter a value between…") and the `KeyboardInterrupt`
  message.
- The "header / configure / train-with-viz / test / explain" run shape is the same
  in all three.
- ASCII separators (`"=" * 70`, `"-" * 40`) and centered titles are re-typed
  inline throughout all three files.
- The unicode progress-bar rendering (`"█" * filled + "░" * (width - filled)`)
  appears four times: once in the GA demo's `fitness_bar` and three times inline
  in the NN demo.
- All three `if __name__ == "__main__"` blocks are byte-identical apart from the
  class name: construct the demo, call `run()`, catch `KeyboardInterrupt`, print
  `"\n\nInterrupted."`, `sys.exit(0)`.

Each script is independently self-contained today, which is good for a learner
who wants to read one file end-to-end. But maintenance edits (e.g. tweaking
prompt wording, fixing a bug in input validation, adjusting bar style) currently
mean editing the same logic in two or three files.

## Tension to resolve before extracting

These demos are **pedagogical**. A reader benefits from seeing the full
algorithm in one file without chasing imports. A `demo_utils` module that
swallows too much (e.g. the entire training loop) defeats that.

The rule of thumb the proposal recommends:

- **Extract** UI plumbing that is not part of the algorithm being taught
  (input validation, divider rendering, bar rendering, colour codes).
- **Do not extract** anything that constitutes the algorithm itself
  (training loop, evaluation, weight update, evolution step).

Note that the colour codes are not duplication today — only the GA demo defines
them (`ANSI_GREEN`, `ANSI_RED`, `ANSI_RESET`). Hoisting them is about making a
consistent palette available to the other two, not about removing copies.

## Proposed module: `demo_utils.py`

A single small module at the repo root, importable by all three scripts.
Keep it boring; no classes if a function suffices.

```python
# demo_utils.py — shared cosmetic helpers for the learning demos.
# Algorithm logic lives in the per-demo files; this is just plumbing.

import sys

# ANSI colour codes (names match the GA demo's existing constants,
# so adopting them there is a pure import swap)
ANSI_GREEN = "\033[32m"
ANSI_RED   = "\033[31m"
ANSI_RESET = "\033[0m"

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

That's the entire surface: four functions plus three colour constants.

## What stays in each demo

- The class that *is* the algorithm (`Perceptron`, `NeuralNetwork`,
  `GeneticAlgorithm`) — untouched.
- The demo orchestrator classes (`PerceptronDemo`, `NeuralNetDemo`,
  `GeneticAlgorithmDemo`) — each keeps its own `print_header`, `explain_*`,
  setup prompts, and training loop. The header text and pedagogical commentary
  are part of what each demo teaches; they should not be unified.
- Algorithm-specific visualization (`NetworkVisualizer.draw_network`, the GA
  fitness graph, `PerceptronDemo.decision_bar`) — these are part of the
  teaching, not generic UI. In particular `decision_bar` is not a progress bar:
  it renders a marker on a centered axis (`─`, `│`, `●`) to show which side of
  the decision boundary the weighted sum falls on.
- The `if __name__ == "__main__"` block. It is triplicated, but it is also the
  entry point a reader looks for first, and a shared `main(DemoClass)` helper
  would hide it. Not worth extracting — just keep the three copies in sync.

## Estimated impact

- ~20–25 lines of duplication removed, nearly all of it the second copy of
  `get_validated_input` plus the three inline bar expressions in the NN demo.
  `divider` and `centered` remove no lines — they replace one expression with
  another — so their value is consistency, not brevity.
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
- **Reconcile the interrupt messages before flattening them.** The two
  `get_validated_input` copies differ in their `KeyboardInterrupt` output: the NN
  demo prints `"👋 Interrupted. Goodbye!"`, the GA demo prints `"Exiting..."`.
  Neither matches the `"\n\nInterrupted."` that all three top-level `__main__`
  blocks print for the same signal. Pick one wording for the shared helper and
  make the `__main__` blocks agree, rather than inheriting whichever copy gets
  moved first.

## Suggested order of work, if approved

1. Add `demo_utils.py` with `get_validated_input` only. Switch GA and NN
   demos to use it. Verify both still run identically.
2. Add `progress_bar` and adopt it in the GA and NN demos (the perceptron
   demo has no progress bar to replace).
3. Add `divider` / `centered` / colour constants. Adopt selectively;
   leave per-demo title text and explanations alone.
4. Add a one-paragraph note to the README explaining the split.

Each step is independently revertable.
