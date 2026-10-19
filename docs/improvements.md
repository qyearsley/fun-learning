# Improvements

> **Status: audited 2026-09-18 against `main` @ `dc95c72`.** Migrated from the
> unversioned `~/hobby/IMPROVEMENTS.md`, which covered seven repos at once and
> had drifted; every claim below was re-checked on this date.
>
> **2026-09-26:** landed the five fixes below (see Settled). These were
> targeted fixes, each checked on its own — this was not a re-audit of the
> rest of the file, and the three demos added since the audit (`maze_demo.py`,
> `process_adventure.py`, `wireworld_demo.py`) still have not been looked at
> beyond their tests passing; see `## Not looked at

- On 2026-10-19 an agent read `maze_demo.py`, `process_adventure.py` and
  `wireworld_demo.py` in full, fuzzed `process_adventure.py` with 3000 seeded
  games, and played `mansion_escape` end to end with piped input. Items 1-3
  are what it found. Nobody has played any of them by hand in a terminal.
- The numpy suite and ruff were not re-run that day: PyPI was unreachable.
- Known gaps in the maze demo are feature ideas, not maintenance debt, and stay
  in [`ideas.md`](ideas.md): Wilson's walk is not animated, and recursive
  division, Aldous-Broder and dead-end filling are not built.

---

`S` under an hour · `M` half a day · `L` more, or needs a decision. State is
`open`, `decision owed`, or `blocked on <thing>`. Every claim carries its
evidence and a date; say so when something was not verified.
