# Project ideas

## Status

A backlog, not a plan. Nothing here is committed to, and entries are at very
different levels of thought — the first few have been worked through, the rest
are one-paragraph sketches. Ideas can be deleted from this file without
ceremony.

## What fits this repo

Existing demos are single-file, interactive, terminal-based, and teach one
concept each. Three of the four are ML/optimization (perceptron, neural net,
genetic algorithm) and the fourth is a Prolog text adventure.

A good candidate here:

- **Runs in one file** with PEP 723 inline dependencies (or is a single `.pl`).
- **Is interactive** — you press a key and something responds, rather than
  running to completion and printing a result.
- **Teaches by showing intermediate state**, not just the answer. The reason
  these demos work is that you watch the algorithm think.
- **Has a surprise in it.** A tiny rule set producing unexpected structure, or a
  mechanism that turns out to be much simpler than it looked.

Current gap: everything except the Prolog game is gradient-descent-flavoured.
Most ideas below deliberately are not.

## Terminal rendering constraints

Relevant to every visual simulation here, so recorded once.

- One cell is one character. A typical terminal gives roughly **100×30**.
- Half-block `▀` with separate foreground and background colours gives two
  independently coloured pixels per character: **100×60**.
- Braille glyphs (U+2800 block) pack 2×4 subpixels per character, so about
  **200×120** — but only one colour per character. Good for monochrome line art
  (L-systems, boids, attractors), not for colour fields.
- Most modern terminals support 24-bit colour, so smooth ramps are possible.
- Full-screen truecolor repaints cost tens of bytes per cell in escape
  sequences, so diff the frame and only emit changed cells. This is fine locally
  and gets noticeable over SSH. Not benchmarked — treat as a rule of thumb.

Suitability of the simulation ideas, given the above:

| Idea | Fit | Why |
|------|-----|-----|
| Ising model | Excellent | 2 states; near-critical domains are large, so low resolution costs nothing |
| Cyclic CA | Excellent | ~12 states → 12 colours; spirals are screen-scale features |
| Wireworld | Excellent | 4 states; circuits are drawn at cell scale, and a text grid is the native save format |
| Turmites | Excellent | Few states; the interesting event (the "highway") is cell-scale |
| Maze generation | Excellent | Box-drawing walls, one character per wall cell; a 48×14 maze fits, and carving one wall is a cell-scale event |
| Abelian sandpile | Good | Exactly 4 states → 4 colours. The famous fractal wants ~500×500, but avalanches animate well at any size |
| Diffusion-limited aggregation | Good | Binary, and dendrites are one cell thick anyway |
| Boids | Good | Braille dots; flocking reads clearly even coarse |
| Hydraulic erosion | Fair | Needs a height colour ramp; fine channels blur. A cross-section plot alongside recovers most of it |
| Reaction-diffusion | Poor | The appeal is smooth continuous gradients; colour quantization makes Turing patterns muddy |
| Slime mold (Physarum) | Poor | Needs high agent count and fine trail gradients; networks turn to mush below ~300×200 |
| L-systems | Poor in colour, good in braille | Diagonal lines are the terminal's weakest point; braille monochrome plants look genuinely good |

## Worked out

### DCG parser for `mansion_escape`

**Done.** Implemented in `mansion_escape/parser.pl`; kept here for the write-up.

Replace `go(north).` with `go north` — or `unlock the brass door with the rusty
key` — using Prolog's definite clause grammars.

A DCG rule looks like a grammar rule and compiles to an ordinary predicate:

```prolog
command(go(Dir))    --> go_verb, opt_article, direction(Dir).
command(take(Item)) --> [take], noun_phrase(Item).
command(look)       --> [look].

go_verb --> [go].
go_verb --> [walk].
go_verb --> [].              % bare "north" also works

direction(north) --> [north].
direction(north) --> [n].

opt_article --> [the].
opt_article --> [].
```

The teaching content is the desugaring. That first rule becomes:

```prolog
command(go(Dir), S0, S) :- go_verb(S0,S1), opt_article(S1,S2), direction(Dir,S2,S).
```

Each nonterminal takes the remaining words in and hands the leftover out — a
difference list. Once that's visible, `-->` stops being magic: it is threading a
list through a chain of predicates, which is the thing you'd otherwise write by
hand and get wrong.

Two properties are hard to get in other languages. **Ambiguity is free**: with a
brass key and a rusty key in the room, `take the key` leaves a choice point, and
the game can ask "which one?" by collecting solutions with `findall`.
Backtracking becomes the disambiguation mechanism rather than something bolted
on. **Grammar is data**: adding `pull`, `pry`, `shove` as synonyms is three
lines, not a parser rewrite.

Work involved: a REPL that reads a line, lowercases, splits, strips the period,
calls `phrase(command(Cmd), Words)`, then `call(Cmd)` into the existing
predicates. That came to roughly 250 added lines, most of them the explanatory
comments. No command predicate changed, though the loop did expose a
pre-existing bug in `check_win_condition`. Also removes the README's "commands
are Prolog goals, so they need a trailing period" caveat.

### Forth in ~200 lines

A stack language with essentially no syntax: whitespace-separated tokens
evaluated left to right. `3 4 + .` pushes 3, pushes 4, adds, prints 7.

Four parts:

- **Two stacks** — data and return.
- **A dictionary** — name → definition, where a definition is either a host
  function (primitive) or a list of other words (compiled).
- **The outer interpreter** — read a token; execute it if it's in the
  dictionary, else push it as a number, else error.
- **A compile flag** — `:` sets it, and while set, words are *appended to a new
  definition* instead of executed. `;` clears it and installs the definition.

About 15 primitives suffice: `+ - * / dup drop swap over @ ! . = < branch
0branch exit`. Everything else is user code.

The payoff is what comes next. Control flow is not in the language. `IF`,
`ELSE`, `THEN` and loops are *immediate* words — flagged to execute even during
compilation — and what they do when they execute is patch jump offsets into the
definition currently being compiled. In `: abs dup 0 < if negate then ;`, the
`if` runs at compile time, emits a `0branch` with a placeholder, and pushes the
placeholder's address onto the data stack; `then` pops it and backfills. The
compiler's scratch space is the same stack the program uses. Ten lines in,
"syntax" turns out to have been a library all along.

Target session:

```
> 3 4 + .
7  ok
> : square dup * ;
 ok
> 5 square .
25  ok
> see square
: square dup * ;   [ 2 cells ]
```

A key that shows the data stack after every token turns it into a stepper.

### Wireworld

*(Proof of concept 2026-09-25: [`wireworld_demo.py`](../wireworld_demo.py),
about 740 lines. It has a curses editor, a headless `--demo` mode, and a
`--truth-table` mode. The library has a wire, a clock, OR, a diode, AND-NOT
and XOR, and every one is checked by simulation. The diode is the passive
blob-and-gap shape, found by a brute-force search over small shapes. The first
draft claimed no passive diode could exist and used a one-shot primer
instead, which was wrong. The AND-NOT and XOR are timed: their inputs must
arrive on the same tick. Not built: the flip-flop and the 2-bit adder, and
tidier gate shapes. The editor was smoke-tested through a pty only.)*

A four-state cellular automaton that is also a machine you build circuits in.

- empty → empty
- electron head → electron tail
- electron tail → conductor
- conductor → electron head **if exactly 1 or 2 of its 8 neighbours are
  electron heads**, else unchanged

That "1 or 2" clause is the whole trick. It makes a signal travel as a head-tail
pair down a wire instead of flooding outward, and it makes a conductor cell with
three head-neighbours *refuse* to fire — which is where gates come from.

```
  step 34                                    electrons: 3

  wire, electron moving right
      ░░░░░░░░@*░░░░░░░░░░░░░░░

  diode  (passes left-to-right, blocks right-to-left)
                 ░
      ░░░░░░@*░░░ ░░░░░░░░░░░░
                 ░

  clock ring  (fires forever)
      ░░░░░░░░
     ░        ░
     ░        *░░░░░░░░░░░░░
     ░        @
      ░░░░░░░░
```

The interactive part is a grid editor: cursor keys move, space cycles a cell
through the four states, `s` steps, `r` runs, plus a library of prebuilt
components to stamp in. Natural progression: diode → OR → AND → XOR → flip-flop
→ 2-bit adder. People have built full CPUs in it.

### Ising model

A grid of ±1 spins, Metropolis updates, one temperature knob. Slide the
temperature down through the critical point and watch a phase transition
happen live: noise, then huge fluctuating correlated domains right at T_c, then
frozen magnetization. Live magnetization and energy readouts alongside the grid.

The one on this list where the terminal is an asset rather than a compromise,
and the one where an abstract physics concept becomes something you can feel by
holding down a key.

### Cyclic cellular automaton

Each cell holds a colour 0..n and is eaten by its successor colour if any
neighbour has it. From pure noise it goes: static, then crystallizing domains,
then spiral waves that fill the screen indefinitely. Around 40 lines for one of
the best payoff-per-line ratios available.

### Maze generation

*(Proof of concept 2026-09-25: [`maze_demo.py`](../maze_demo.py), about 750
lines. It has DFS, Prim, the growing-tree collapse, Kruskal, Wilson's and
binary tree, plus the BFS gradient, the longest path, the `c` source view and
SVG export. Not built: recursive division, Aldous-Broder, and dead-end
filling. The biggest gap is that Wilson's walk is not animated. Generators
yield only finished carves, so the wandering and the loop erasure, which this
section calls the best animation here, are never drawn.)*

Seven algorithms, one data structure, and the finished maze tells you which
algorithm made it.

A maze is a spanning tree of the grid graph. Every generator below is a
different way to build one. The file states that once at the top, then earns it
six times, in this order:

| Step | What it adds |
|------|--------------|
| DFS backtracker | How a person would draw a maze. Long winding corridors, few dead ends |
| Randomized Prim | Short stubby passages, many dead ends. Same grid, visibly different texture |
| The collapse | The two differ only in which frontier cell you pick next — newest or random. Pick the oldest and a third generator appears. Three functions become one function with a `pick` argument |
| Kruskal | No frontier at all. Shuffle the edges, union-find, about 12 lines with path compression, and you watch the forest merge |
| Wilson's | Loop-erased random walk. Wander at random, and when you cross your own path, erase the loop and carry on. Short, hard to believe, and the best animation here |
| Recursive division | Adds walls instead of carving passages, and is still a spanning tree |
| Solving | One BFS distance field gives the colour gradient. Run it twice for the longest path, by the tree-diameter trick. Dead-end filling solves the maze without searching at all |

Wilson's and Aldous-Broder draw from the same distribution — uniform over all
spanning trees — while looking nothing alike as they run, and both are far
slower than the biased DFS. Correct costs something, and here you can see the
price. Binary tree is four lines, and its output is wrong by eye: a diagonal
grain and two open edges. A correct implementation of a biased algorithm is its
own lesson.

**Rendering is box-drawing characters.** Draw the maze on a (2w+1)×(2h+1) grid
of wall and passage cells, then pick each wall character from a 16-entry table
indexed by a 4-bit mask of which neighbours are also walls. One character per
wall cell, so a 100×30 terminal holds a maze of about 48×14 cells. It is the
same trick as marching squares, and the same shape as the rule tables in the
cellular automata above.

**Two properties carry the reading.** Every generator is a Python generator that
yields after each carve, so no algorithm contains a line of rendering code and
animation comes free. And a `c` key prints the source of the algorithm you just
watched, through `inspect.getsource`, beside its output.

**Export is SVG, not PNG.** A maze is lines on a page, SVG is text, and emitting
it takes about 15 lines with no dependency. Pillow would cost an install and
break the property that every demo here runs from anywhere. The terminal keeps
the process; the SVG keeps the artifact.

Stdlib only — the first demo here with no dependencies at all. It also absorbs
**union-find percolation** below, since Kruskal's needs the same machinery.

### Text adventure: you are a process

*(Finished 2026-09-25: [`process_adventure.py`](../process_adventure.py).
The first cut on 2026-09-24 had three puzzles and four endings. A gameplay
review found the SIGTERM clock had no teeth, most items did nothing, and
dropping an item waited for the GC instead of freeing it. The finished game
adds two real locks and a worker thread, so taking them in the wrong order
deadlocks and forking without the heap lock hangs the child. Drops are now
real refcount frees, and `link` makes a real cycle that waits for
`gc.collect()`. The canary aborts the game if you carry it out of its frame,
and errno holds the real code of your last failure. The game has seven
endings, SIGTERM comes at turn 30 instead of 40, and a revisited room gets a
brief description. It came out at about 1,170 lines, well over the target.
PID 1 is still only mentioned, not met.)*

`adventure`, except you are a process inside a computer and the rooms are
regions of a running program. Python rather than Prolog, for one reason: the
conceit can be literally true.

The game reads its own runtime. `examine self` prints a real refcount from
`sys.getrefcount`. `/proc` shows the real PID. Late on, the item that solves a
puzzle is an actual `weakref`. You spend the first few rooms taking all of it
for a metaphor.

**Draw that line and say where it is.** Read-only introspection is real: `id`,
refcounts, `gc.get_referrers`, the PID, file descriptor numbers. Anything that
would break the game is simulated — no real `os.fork`, no real `exec`. A comment
says which is which, or the trick becomes a lie.

Rooms, each carrying one rule:

| Room | Its rule |
|------|----------|
| The stack | Frames vanish when they return. A timed area |
| The heap | The hub. Allocated blocks and free holes |
| The text segment | Read-only. You change nothing here, but you read the code, and the clues are in it |
| BSS and globals | Anything you leave here outlives everything else |
| The registers | Four slots, clobbered constantly |
| `/proc` | A mirror. It shows you your real self |
| `/dev/null` | A void. Drop something here and it is gone |
| A pipe | Where you meet another process |

NPCs get one rule each. The **garbage collector** wanders and takes anything
unreachable. The **OOM killer** takes whoever carries the most, so greed is
fatal. A **zombie** is already dead and only wants its parent to call `wait`.
**PID 1** is ancient and adopts orphans.

The puzzles come out of real semantics rather than invented ones:

- Make a reference cycle to hide from the refcounter, then find out that the
  cycle detector exists.
- Install a handler and catch SIGTERM before it arrives. SIGKILL cannot be
  caught, and the game lets you try.
- Follow a dangling pointer into a freed block to reach a room with no door.
  Use-after-free as a movement mechanic.
- Take two mutexes in the wrong order and deadlock. A losing ending you can walk
  into.
- Put a value in the environment so a child inherits it.

Target session:

```
> examine self
You are process 48211. Three things are holding a reference to you.
The refcount is real; check it yourself.

> go to the stack
Frame 0x7ffee4a2. Someone is going to return from this soon.

> take pointer
Taken. It points at 0x14f0e2c0, which was freed some time ago.
Nothing stops you from following it.
```

You are short-lived and about to be reaped, and you want to persist. Several
endings: exit cleanly, fork a survivor that outlives you, get written to disk,
or be collected.

The parser is a verb plus an optional noun phrase, with synonyms, in about 60
lines. Not a port of `parser.pl`. The two-word style is what `adventure` had and
it suits this.

**The premise does the work that prose would otherwise do.**
[`mansion-escape-v2.md`](mansion-escape-v2.md) argues that interest per line
comes from rules and not content, and a game written for fun is the obvious way
to break that rule. The defence is that every room, NPC and puzzle above is a
rule with a joke inside it, so the game gets funnier without getting longer.

First cut: eight rooms, ten items, three puzzles, four endings. One file, no
dependencies, 600–800 lines at the comment density the other demos use.

## Sketched: rule sets that grow something

- **Abelian sandpile** — drop grains; any cell with 4+ topples into its
  neighbours, cascading. Dropping a million grains on one square produces a
  startling fractal, and avalanche sizes follow a power law with no tuning. The
  canonical demo of self-organized criticality, in about 30 lines.
- **Diffusion-limited aggregation** — a seed pixel plus random walkers that
  stick on first contact. Coral, lichen, and frost patterns from "wander until
  you bump something". Tune stickiness to turn dense blobs into spindly
  dendrites. Spawn walkers on a shrinking circle to keep it fast.
- **Physarum (slime mold)** — agents deposit a trail and steer toward the
  strongest nearby trail. That is the whole rule, and out of it come transport
  networks that reproduce the Tokyo rail map (Tero et al., 2010). Wants more
  resolution than a terminal has.
- **Hydraulic erosion** — generate a heightmap with noise, then drop water
  droplets that pick up and deposit sediment running downhill. Ridges sharpen,
  valleys and deltas carve themselves.
- **Turmites** — Langton's ant generalized to arbitrary state tables. Most
  tables give noise or dull symmetry, but some spend ~10,000 steps in apparent
  chaos then abruptly build a periodic "highway" off to infinity. Browsing rule
  space for the interesting ones is the game.
- **Reaction-diffusion** — two chemicals, feed and kill rates, Turing patterns.
  Spots become stripes become mitosis as you tune two parameters. Wants pixels.
- **Elementary cellular automata explorer** — all 256 rules, arrow keys to
  browse. Stop on rule 30 (chaos) and rule 110 (Turing complete).
- **Boids** — flocking from three local rules. Tune separation, alignment, and
  cohesion; watch flocks form, split, and rejoin.
- **L-systems** — grow ASCII plants from rewrite rules, edit a rule, watch the
  plant change. Braille rendering for the diagonals.
- **Wave function collapse** — repeatedly collapse the lowest-entropy cell and
  propagate constraints to generate a tile map. You can hand-place a tile and
  watch the ripple. Same core idea as the Prolog demo, but visible.
- **Union-find percolation** — fill a grid randomly, watch clusters merge,
  discover the ~0.593 threshold yourself. Largely absorbed by **maze
  generation** above, which needs union-find for Kruskal's anyway.

## Sketched: machines you build, then run

- **Toy VM + assembler** — write 20 lines of assembly, single-step it with
  registers, stack, and memory on screen. Shares an execution-stepper skeleton
  with Forth and Subleq.
- **Subleq** — a computer with exactly one instruction (subtract and branch if
  less-or-equal), which is Turing complete. Writing "add two numbers" takes real
  thought. The evil twin of the toy VM.
- **Lambda calculus stepper** — no numbers, no booleans, no data, only
  functions. Step through beta reductions watching `2 + 3` compute out of pure
  application, then get numbers from Church numerals and recursion from the Y
  combinator in a language with no recursion.
- **Tiny Lisp with a stepper** — ~200 lines, then step evaluation showing the
  expression being rewritten and the environment chain. How eval and apply
  actually work.
- **Tiny Prolog in Python** — unification plus backtracking in ~150 lines.
  Explains the substrate that `mansion_escape` runs on.
- **Regex → NFA → DFA** — Thompson construction, then subset construction, with
  the state machine drawn at each stage. Explains both why regex engines are
  fast and why backtracking ones sometimes aren't.
- **Turing machine + busy beaver** — tape, head, state table, and a hunt for the
  4- and 5-state champions. BB(5) runs 47,176,870 steps and then halts, which
  gets more unsettling the longer you sit with it.
- **Git from scratch** — hash a file, watch a blob appear; build a tree, a
  commit; check out between them. Content addressing clicks fast when the object
  store is visible.
- **Mark-and-sweep GC** — a heap drawn as cells; drop a reference, watch objects
  become unreachable and get collected. Then swap in a copying collector and
  compare.
- **malloc visualizer** — first-fit versus best-fit on the same allocation
  sequence, fragmentation visible as holes.
- **BPE tokenizer, built live** — feed it a corpus, watch merge rules get
  discovered one at a time, then tokenize your input with the merge history for
  each token. Explains why token counts are weird and why numbers tokenize
  badly.
- **TCP congestion control** — the cwnd sawtooth, live. Drop packets with a
  keypress and watch it back off.

## Sketched: second Prolog piece

- **Prolog metainterpreter** — `solve/1` written in Prolog, in about eight
  lines, able to run Prolog programs. Extend it to print the proof tree and you
  can watch resolution and backtracking on the mansion game. The moment Prolog
  stops being magic.
- **Zebra puzzle with visible search** — the five-houses constraint puzzle,
  instrumented so the search tree shows: which constraint pruned which branch,
  how many nodes died where.

## Sketched: things that are games

- **Assembly puzzle game** — levels give an input stream and a required output;
  you write a handful of instructions and watch registers tick. Fewest
  cycles/instructions as the score. A game whose mechanic is understanding a
  CPU.
- **Guess the hidden rule** — the computer invents a rule about number triples
  and only answers yes or no to your probes. Brutal about confirmation bias:
  most people only test triples they expect to pass. Small to build, and the
  lesson sticks.
- **Connect Four vs MCTS** — you play, it thinks out loud, showing visits and
  win rate per column and the line it expects. Turn rollouts down to 50 and beat
  it; turn them up to 20,000 and lose.
- **Minesweeper solver that narrates** — plays perfectly and explains each
  deduction in words ("the 2 at C4 has exactly two unknowns, so both are
  mines").
- **Wordle entropy solver** — expected information gain per candidate guess, so
  you see why CRANE beats ADIEU.

## Shortlist

Chosen 2026-09-20: **maze generation** first, then **you are a process**. The
maze is the smaller and more contained build. The adventure is the better one to
write. On 2026-09-24 the order was swapped, and the adventure's first cut is
done.

The rest, if picking one:

- **Wireworld** — emergence and a machine at once, and the terminal is the
  correct medium for it rather than a compromise.
- **Ising model** — smallest build with a genuine "oh, *that's* what a phase
  transition is" payoff.
- **DCG parser** — improves something that already exists, and difference lists
  are a real idea. *(Done.)*
- **Forth** — the largest shift in how you think about what a language is.

Natural pairs: Forth and the toy VM and Subleq share an execution-stepper
skeleton; Wireworld, cyclic CA and the maze share a grid renderer.
