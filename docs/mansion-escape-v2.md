# Design sketch: mansion_escape v2

## Status

Implemented. Written before the code, kept as the rationale.

## Problem

The parser accepts more than the game contains. Five rooms, two items, one
puzzle, four moves to win. The demo shows Prolog's syntax well but only makes
one real argument for logic programming — the locked door rule — and makes it
once.

## Principle

Interest per line comes from **rules, not content**. A room description is
three lines and adds nothing to play. `connected(upstairs_hall, north,
master_bedroom) :- inventory(key).` is one line and is the entire puzzle.

So: add rules, keep prose thin, and pick additions where the game getting
better and the demo teaching more are the same work.

## The new puzzle

The way out is the cellar, behind a door held by three levers (brass, iron,
copper), each up or down. Three notes around the mansion each give one
constraint:

| Note in | Constraint |
|---------|------------|
| Library | The brass and iron levers never sit the same way |
| Kitchen | If brass is up, copper is down |
| Bedroom | At least two levers are up |

Exactly one setting satisfies all three: **brass down, iron up, copper up.**

The existing key puzzle survives and becomes load-bearing, since the third note
is in the locked bedroom. The bedroom window is now barred, so reaching it is no
longer the win.

## What each addition teaches

**`deduce` — the centrepiece.** Generate all eight settings, test each against
the constraints you have found, print which one failed:

```
brass=up   iron=up   copper=up    -- fails: brass and iron never sit the same way
brass=up   iron=down copper=up    -- fails: if brass is up, copper is down
brass=down iron=up   copper=up    -- consistent
```

The important part: it reasons from `known_constraint/1`, which is asserted when
you *read* a note. With two notes, three settings survive and it says so. The
solver's power is a function of the player's knowledge, so the game state is
literally a knowledge base. That is the argument for logic programming that the
current file gestures at and never makes.

**`go to cellar` — a path planner.** Depth-first search over `connected/3` with
a visited list, about twelve lines. Because `connected/3` already contains a
*rule*, the planner cannot route through the locked bedroom until the key is in
inventory. Puzzle-awareness for free, because the puzzle was never in the
movement code — it was in the world.

**Darkness — disjunction.** The cellar is dark; `look` shows nothing without the
lamp:

```prolog
can_see :- current_location(Room), \+ dark(Room).
can_see :- inventory(lamp).
```

Two clauses meaning OR, next to a key rule that means AND. Different lesson, not
the same trick twice.

**`examine` / `read`** — needed to deliver the notes, and it fixes a dead end
(`look at book` used to fail). Reuses `noun_phrase//1`, so adjectives come free.

**`use`** — no mechanics, just a contextual answer, because `use key` is a
natural thing to type and hitting "I do not understand" is worse than being told
the key works by being carried.

## Non-goals

- Not restructuring `connected/3` to need explicit unlocking. That rule is the
  file's best teaching moment and the puzzle gains little.
- No new rooms beyond the cellar. Rooms are content; content is not the problem.
- ~~Still one file, still readable in one sitting.~~ Held during the v2 build,
  then abandoned — see the resolution below.

## Budget

Before: 600 lines (273 code, 230 comment, 97 blank). After: just over 1000
(around 515 code, 320 comment, 170 blank).

That overshot the "under 800" target this sketch was written with, and it is
worth being clear about why: the five new commands and the solver are simply
that much code. Two rounds of compression (help text and `use` responses moved
into fact tables, `format/2` in place of `write/1` chains) improved the code but
recovered only six lines. Getting to 800 would have meant cutting a feature or
cutting teaching comments, and neither is a good trade for a round number.

The open question this leaves is the one from before the build: the file no
longer reads in one sitting. If that matters more than having one file, the
answer is to split the minimal tutorial and the larger game into two.

## Resolution: split by concern, not tutorial-and-game

Settled 2026-09-01. The 1010-line file became `mansion_escape/`, four files
that load with `ensure_loaded/1` and declare no modules:

| File | Lines | What is in it |
|------|-------|---------------|
| `world.pl` | 189 | Rooms, connections, darkness, items, notes, the lever mechanism |
| `commands.pl` | 518 | Every player command, plus `deduce` and the path planner |
| `parser.pl` | 175 | The DCG and `read_words/1` |
| `mansion_escape.pl` | 199 | Dynamic declarations, `init_game/0`, the game loop, auto-start |

The sketch above proposed the other split — a minimal tutorial file plus the
full game — which keeps each file readable start to finish but means two
programs to maintain and a tutorial that drifts from the game. Splitting by
concern keeps one program, and the seams were already marked in the source: the
old line 741 said "everything above is the game, everything below turns a typed
line of English into one of those goals."

What it costs is the linear read, which was the point of a literate program.
The mitigation is a reading order in the header of `mansion_escape.pl` and in
the README, and a header on each file saying what argument that file makes.

Not modules. Exports would be one more thing to explain in a program whose
subject is Prolog rather than packaging, and `user` predicates keep every
cross-file call looking exactly like a same-file call.

The code did not change: the only new lines are the three `ensure_loaded`
directives. Everything else moved verbatim, with comments edited where they
pointed at "the bottom of this file".
