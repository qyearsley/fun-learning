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
- Still one file, still readable in one sitting.

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
