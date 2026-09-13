# The three Python demos duplicate their UI plumbing, on purpose

**Decided 2026-09-05. Closed.** This replaces a proposal to extract a
`demo_utils.py`; that document is deleted, and this records why.

## What is duplicated

- `get_validated_input`, defined identically in `neural_net_demo.py` and
  `genetic_algorithm_demo.py`. Sixteen lines, one word apart: one says "Please
  enter a value between…" and the other says "Enter a value between…".
  `perceptron_demo.py` does not have it and validates inline instead, because
  its prompt picks from a list rather than range-checking a number.
- A filled progress bar. It was four copies -- one in
  `genetic_algorithm_demo.py` and three in `neural_net_demo.py` -- and is now
  two, because the three in one file were collapsed into a `progress_bar`
  function there. See "What was done instead".
- The `if __name__ == "__main__":` block, three times, identical apart from the
  class name.

The deleted proposal also listed two helpers, `divider` and `centered`. Neither
has ever existed: they were functions it proposed *writing*, and it conceded in
its own impact section that they would "remove no lines". They are named here
only so nobody goes looking for them.

## Why it stays

**A shared module ends the thing these files are.** Each one begins with a
[PEP 723](https://peps.python.org/pep-0723/) metadata block and a
`#!/usr/bin/env -S uv run` shebang, so it installs its own dependencies and
runs from anywhere — you can drop one in a gist and it works. A sibling import
takes that away, and it is the property that makes a teaching demo worth having.

**The payoff was small even before that.** The original proposal costed itself
at "~20–25 lines of duplication removed, nearly all of it the second copy of
`get_validated_input`", and noted in the same paragraph that two of its four
proposed helpers would "remove no lines — they replace one expression with
another".

**A reader benefits from one file.** The point of these scripts is to be read
top to bottom. Chasing an import to find out what a prompt does is a cost paid
by every reader to save a cost paid once by the author.

## What was done instead

- **Deduplicated within a file, where it costs nothing.** The three inline
  progress bars in `neural_net_demo.py` are one `progress_bar` function now.
  That was three copies in one file, which no argument about standalone-ness
  defends.
- **Fixed the thing the duplication was hiding.** Two of the three demos
  validated inline with `except (ValueError, KeyboardInterrupt)`, so typing
  `abc` at the prompt quit the program. The extracted helper the other two share
  keeps the two exceptions apart and always did. That is the real cost of
  copy-and-paste here — not the line count, but that a fix lands in one copy.

## What would reopen this

A fourth demo, or a helper that grows past a few lines. At that point the trade
changes: the duplication stops being three short functions and starts being a
maintenance surface, and a `demo_utils.py` beside the scripts — with the
standalone property consciously given up — becomes the better answer.

## On the Ctrl-C messages

Not a defect, and not being flattened. There are three things a Ctrl-C can mean
here, and the wording distinguishes them:

| Where | What it prints | What happens next |
| --- | --- | --- |
| At a prompt | `Exiting...` | The program exits |
| During a run | `Training interrupted.` / `Evolution interrupted.` | The run stops, the demo carries on to its results |
| At the top level | `Interrupted.` | The program exits |

The middle row is the one worth keeping distinct: interrupting a training run is
not the same as leaving.

## On Ctrl-D

Ctrl-D at a prompt raises `EOFError`, not `KeyboardInterrupt`. Until it was
fixed, every prompt let it escape to the top and the demo ended in a traceback.
This is the same shape as the `abc` defect above: the handler named one
exception when two reach it.

Ctrl-D has only one meaning here — there is no more input, so the program
cannot continue:

| Where | What it prints | What happens next |
| --- | --- | --- |
| At a validating prompt | `Exiting...` | The program exits |
| At a `Press Enter` prompt | `Exiting...` | The program exits, from the top-level handler |

The `Press Enter` prompts validate nothing, so they have no handler of their
own. The `except EOFError` in each `__main__` block catches those.
