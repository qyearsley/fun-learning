#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
WIREWORLD: A Machine Made of Four Rules
========================================

Wireworld is a cellular automaton, like Conway's Life, but every cell is one
of four states instead of two:

    EMPTY       nothing here, forever
    CONDUCTOR   a wire; inert until an electron reaches it
    HEAD        the front of an electron, moving through a wire
    TAIL        the back of an electron, one step behind the head

The whole simulation is four rules, checked against the 8 surrounding cells
(the Moore neighbourhood) every step:

    empty      -> empty                              (nothing to do)
    head       -> tail                                (the front always falls back)
    tail       -> conductor                            (the back always fades)
    conductor  -> head, if EXACTLY 1 or 2 neighbours are heads; else conductor

That last rule is the whole trick, and it rewards close reading. A lone
electron is a head immediately followed by a tail -- the moment a conductor
cell fires, the cell behind it has already become a head, so on the very next
step *that* cell is the only head next to the conductor two cells further on.
One neighbour, every time. The result is that an electron travels down a wire
as a compact head-tail pair, one cell per step, rather than flooding outward
the way fire or Conway gliders spread. A wire is a wire and not a puddle
*because* firing needs company (0 heads refuses too) but not too much of it.

And "not too much" is where machines come from. A conductor cell wired to
three separate incoming electrons that all arrive on the same tick sees THREE
head-neighbours -- and refuses to fire. A cell built to see 1 or 2 signals
passes them through; built to occasionally see 3, it can be made to block.
Every gate in this file -- the diode, the AND-NOT, the XOR -- is that one
refusal, aimed at a specific junction, by construction and nothing more
exotic. There is no second rule for logic. It is the same rule, wired
differently.

Text format (the native save/load format, and how components are written below)
---------------------------------------------------------------------------
One character per cell, one line per row:

    .   empty
    #   conductor
    @   head
    ~   tail

Rows may be ragged; short rows are padded with `.` on load.

What is in this file
---------------------
- A pure simulation core (`parse_grid`, `step`, `count_head_neighbours`,
  `electron_count`) with no dependency on curses or any UI. It is what the
  tests exercise directly.
- A small library of hand-built, individually verified circuits: a plain
  wire, a self-sustaining clock ring, an OR gate, a diode, an AND-NOT gate,
  and an XOR gate built from two AND-NOTs. Every one of them is checked by
  simulating it, not by eye -- see `tests/test_wireworld.py`.
- A curses editor: arrow keys move the cursor, space cycles a cell through
  the four states, `s` steps once, `r` runs/pauses, `c` stamps the selected
  component, Tab cycles which component is selected, `w`/`o` save/load,
  `q` quits.
- A non-curses fallback (`--demo NAME --steps N`) that prints frames to
  stdout, so the simulation can be watched, piped, or driven from a test
  without a real terminal.
- A `--truth-table NAME` mode that feeds every input combination into a gate
  and reports what came out the other end -- the "it's a machine" payoff.

A note on the gates, since it matters for using them honestly
---------------------------------------------------------------
The diode is passive and reusable: a 2x2 blob beside a one-cell gap in the
wire. Either way in, the blob turns the pulse into a column of three heads.
Going one way, the next cells each touch two of them and fire. Going the
other way, the next cell touches all three and refuses. The shape is not
symmetric, so the behaviour isn't either.

The AND-NOT and XOR gates here are timed rather than passive: an inhibiting
input must arrive on the same tick as the signal it cancels. **Set every
input for one test at tick 0 -- before the first step -- and don't mix
ticks.** Real Wireworld circuits work the same way, which is why clocks come
first: a circuit that fires on the beat keeps its signals in phase.
"""

import argparse
import contextlib
import sys
import time
from dataclasses import dataclass, field

EMPTY = "."
CONDUCTOR = "#"
HEAD = "@"
TAIL = "~"
STATES = (EMPTY, CONDUCTOR, HEAD, TAIL)

Grid = list[list[str]]
Point = tuple[int, int]

# --------------------------------------------------------------------------
# Core simulation. No curses, no I/O beyond load/save -- this is the part
# the tests import and drive directly.
# --------------------------------------------------------------------------


def parse_grid(text: str) -> Grid:
    """Text -> grid. Rows are padded with EMPTY on the right to a rectangle."""
    lines = text.strip("\n").split("\n") if text.strip("\n") else [""]
    width = max(len(line) for line in lines)
    return [list(line.ljust(width, EMPTY)) for line in lines]


def format_grid(grid: Grid) -> str:
    return "\n".join("".join(row) for row in grid)


def make_grid(width: int, height: int) -> Grid:
    return [[EMPTY] * width for _ in range(height)]


def count_head_neighbours(grid: Grid, x: int, y: int) -> int:
    """How many of the 8 surrounding cells are HEAD. Off-grid counts as none."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    total = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == HEAD:
                total += 1
    return total


def step(grid: Grid) -> Grid:
    """Advance the whole grid by one tick. Returns a new grid; does not mutate."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    new_grid = make_grid(width, height)
    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            if cell == EMPTY:
                new_grid[y][x] = EMPTY
            elif cell == HEAD:
                new_grid[y][x] = TAIL
            elif cell == TAIL:
                new_grid[y][x] = CONDUCTOR
            else:  # CONDUCTOR
                heads = count_head_neighbours(grid, x, y)
                new_grid[y][x] = HEAD if heads in (1, 2) else CONDUCTOR
    return new_grid


def electron_count(grid: Grid) -> int:
    """Heads plus tails -- the number of electrons currently in flight."""
    return sum(row.count(HEAD) + row.count(TAIL) for row in grid)


def grid_size(grid: Grid) -> tuple[int, int]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    return width, height


def resize(grid: Grid, width: int, height: int) -> Grid:
    """Return a copy padded or cropped to the given size, top-left anchored."""
    old_w, old_h = grid_size(grid)
    new_grid = make_grid(width, height)
    for y in range(min(old_h, height)):
        for x in range(min(old_w, width)):
            new_grid[y][x] = grid[y][x]
    return new_grid


def place_component(grid: Grid, component: Grid, at: Point) -> Grid:
    """Stamp `component` into a copy of `grid` with its top-left at `at`.

    Cells that would land outside the grid are silently clipped, so stamping
    near an edge never raises.
    """
    ox, oy = at
    width, height = grid_size(grid)
    new_grid = [row[:] for row in grid]
    for y, row in enumerate(component):
        gy = oy + y
        if not (0 <= gy < height):
            continue
        for x, cell in enumerate(row):
            gx = ox + x
            if 0 <= gx < width:
                new_grid[gy][gx] = cell
    return new_grid


def mirror_horizontal(grid: Grid) -> Grid:
    """Flip left-right. Used to get 'the other orientation' of the diode for free:
    a mirror image of a valid Wireworld pattern is itself a valid pattern, since
    the rule only counts neighbours and does not care about handedness."""
    return [list(reversed(row)) for row in grid]


def run(grid: Grid, steps: int) -> list[Grid]:
    """Simulate `steps` ticks. Returns all `steps + 1` frames, including frame 0."""
    frames = [grid]
    for _ in range(steps):
        grid = step(grid)
        frames.append(grid)
    return frames


def load(path: str) -> Grid:
    with open(path, encoding="utf-8") as f:
        return parse_grid(f.read())


def save(grid: Grid, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(format_grid(grid) + "\n")


# --------------------------------------------------------------------------
# The component library.
#
# Every layout below was designed by simulating candidates until one worked,
# not drawn freehand -- see the design notes in docs/ideas.md and the
# derivations that led here. `ports` names the cells worth injecting into or
# watching, in the component's own local (column, row) coordinates; a port is
# always a list of cells because a couple of components duplicate one logical
# input to two physical entry points.
# --------------------------------------------------------------------------


@dataclass
class Component:
    name: str
    text: str
    summary: str
    ports: dict[str, list[Point]] = field(default_factory=dict)

    @property
    def grid(self) -> Grid:
        return parse_grid(self.text)


# A single electron, injected as a lone head, turns into the head-tail pair
# a moving signal always is, and walks to the right one cell per tick.
_WIRE_TEXT = "@#########"

# A self-sustaining generator: a closed loop of conductor with a head-tail
# pair chasing itself around it forever, plus a tap wire so you can watch it
# emit pulses without disturbing the ring. The ring is a chamfered rectangle
# (its corners are cut at 45 degrees) rather than a plain rectangle: a sharp
# 90-degree corner puts two non-adjacent cells of the loop diagonally next to
# each other (a corner cell's diagonal neighbour is the cell two steps
# further round the bend), which is an extra edge the loop doesn't intend and
# makes the electron fork in two directions instead of travelling around
# cleanly. Cutting the corner removes that accidental adjacency. The loop is
# 16 cells around, so it fires once every 16 ticks.
_CLOCK_TEXT = """
..@~##...#
.#....#.#.
#......#..
#......#..
.#....#...
..####....
""".strip("\n")

# Two input wires merge diagonally onto one conductor cell. Either alone
# gives that cell 1 head-neighbour; both at once give it 2 -- both numbers
# the rule fires on, so the merge just passes whichever arrives, no special
# casing needed. This is the entire OR gate.
_OR_TEXT = """
..#....
...#...
....###
...#...
..#....
""".strip("\n")

# The diode: a 2x2 blob beside a one-cell gap. From either side, the blob
# turns the pulse into a vertical line of three heads. Left to right, the
# cells beyond that line each touch only two of the three, so they fire and
# rejoin the wire past the gap. Right to left, the only way on is a single
# wire cell touching all three, and three is too many, so it refuses. Found by
# a brute-force search over 4096 shapes in a 3x4 window, keeping those that
# pass three pulses one way and none the other. This is the smallest one.
_DIODE_TEXT = """
.....##.....
######.#####
.....##.....
""".strip("\n")

# AND-NOT: passes in_a through to out, UNLESS in_b is also driven on the same
# tick, in which case the junction sees in_a's own 1 plus 3 more (in_b fanned
# out through 3 relay cells timed to land on the junction at once) -- 4,
# refused. Fed only in_b, nothing was travelling from in_a in the first
# place, so out is silent regardless. This is the "AND (or AND-NOT)" entry:
# out = in_a AND NOT in_b.
_AND_NOT_TEXT = """
........#.
.......#..
....#.#...
..####....
....#.#...
""".strip("\n")

# XOR, built from two AND-NOT gates back to back and rotated 180 degrees from
# each other: the left one computes (A AND NOT B), the right computes
# (B AND NOT A). in_a drives both gates' "A-shaped" inputs, in_b drives both
# gates' "B-shaped" inputs (each input is duplicated to reach both gates,
# hence two cells per logical port). Exactly one half fires when the inputs
# differ; neither fires when they agree -- which is XOR by definition, with
# no new mechanism beyond the AND-NOT above.
_XOR_TEXT = """
......#.....#.........
.....#.......#........
..#.#.........#.#.....
####...........####...
..#.#.........#.#.....
""".strip("\n")

COMPONENTS: dict[str, Component] = {
    "wire": Component(
        "wire",
        _WIRE_TEXT,
        "A straight wire. Stamp it, set the left cell to a head, and step.",
        ports={"in": [(0, 0)], "out": [(9, 0)]},
    ),
    "clock": Component(
        "clock",
        _CLOCK_TEXT,
        "A generator: fires a pulse out its tap every 16 ticks, unattended.",
        ports={"tap": [(9, 0)]},
    ),
    "or": Component(
        "or",
        _OR_TEXT,
        "OR gate: out fires if in_a or in_b (or both) does.",
        ports={"in_a": [(2, 0)], "in_b": [(2, 4)], "out": [(6, 2)]},
    ),
    "diode": Component(
        "diode",
        _DIODE_TEXT,
        "Diode: passes left to right, every time. Blocks right to left, every time.",
        ports={"in": [(0, 1)], "out": [(11, 1)]},
    ),
    "and_not": Component(
        "and_not",
        _AND_NOT_TEXT,
        "AND-NOT gate: out fires if in_a and not in_b.",
        ports={"in_a": [(8, 0)], "in_b": [(2, 3)], "out": [(6, 4)]},
    ),
    "xor": Component(
        "xor",
        _XOR_TEXT,
        "XOR gate: out fires if exactly one of in_a, in_b does.",
        ports={
            "in_a": [(6, 0), (18, 3)],
            "in_b": [(0, 3), (12, 0)],
            "out": [(4, 4), (14, 4)],
        },
    ),
}

# The diode reflected left-right is a diode facing the other way. Built from
# the same source rather than hand-drawn a second time.
_diode = COMPONENTS["diode"]
_diode_width = grid_size(_diode.grid)[0]


def _mirror_port(pt: Point, width: int) -> Point:
    x, y = pt
    return (width - 1 - x, y)


COMPONENTS["diode_mirrored"] = Component(
    "diode_mirrored",
    format_grid(mirror_horizontal(_diode.grid)),
    "The diode above, reflected: passes right to left, blocks left to right.",
    ports={
        name: [_mirror_port(p, _diode_width) for p in pts] for name, pts in _diode.ports.items()
    },
)

COMPONENT_ORDER = ["wire", "clock", "or", "diode", "diode_mirrored", "and_not", "xor"]


# --------------------------------------------------------------------------
# Truth tables: feed every input combination into a gate and report the
# output, so the "it's a machine, not a picture" part is visible without the
# editor.
# --------------------------------------------------------------------------


def _inject(grid: Grid, cells: list[Point]) -> Grid:
    new_grid = [row[:] for row in grid]
    for x, y in cells:
        new_grid[y][x] = HEAD
    return new_grid


def _port_ever_fires(frames: list[Grid], cells: list[Point]) -> bool:
    return any(frame[y][x] == HEAD for frame in frames for (x, y) in cells)


def pulses_through(grid: Grid, src: list[Point], dst: list[Point], n=3, gap=12) -> int:
    """Send `n` pulses into `src`, `gap` ticks apart, and count how many arrive at `dst`."""
    arrived, was_head = 0, False
    for t in range(n * gap + 2 * gap):
        if t % gap == 0 and t // gap < n:
            grid = _inject(grid, src)
        grid = step(grid)
        is_head = _port_ever_fires([grid], dst)
        arrived += is_head and not was_head
        was_head = is_head
    return arrived


def gate_output(component: Component, active_inputs: set[str], settle: int = 12) -> bool:
    """Run one trial: drive every port in `active_inputs` to HEAD at tick 0,
    settle for `settle` ticks, report whether `out` ever fired."""
    grid = component.grid
    for name in active_inputs:
        grid = _inject(grid, component.ports[name])
    frames = run(grid, settle)
    return _port_ever_fires(frames, component.ports["out"])


def print_truth_table(component: Component, settle: int = 12) -> None:
    inputs = sorted(name for name in component.ports if name.startswith("in_"))
    print(f"{component.name}: {component.summary}\n")
    header = "  ".join(inputs) + "  | out"
    print(header)
    print("-" * len(header))
    for bits in range(2 ** len(inputs)):
        active = {inputs[i] for i in range(len(inputs)) if bits & (1 << i)}
        row_values = ["1" if name in active else "0" for name in inputs]
        out = gate_output(component, active, settle=settle)
        print("   ".join(row_values) + f"   | {'1' if out else '0'}")


def demo_diode() -> None:
    """The diode's asymmetry, spelled out (it has no in_a/in_b truth table)."""
    for name in ("diode", "diode_mirrored"):
        diode = COMPONENTS[name]
        print(f"{diode.name}: {diode.summary}")
        print(format_grid(diode.grid))
        a, b = diode.ports["in"], diode.ports["out"]
        print(f"  3 pulses sent in -> out: {pulses_through(diode.grid, a, b)} arrive")
        print(f"  3 pulses sent out -> in: {pulses_through(diode.grid, b, a)} arrive\n")


# --------------------------------------------------------------------------
# Non-curses fallback: print frames to stdout. Works with no TTY, so it is
# what tests and piped output use, and what `--demo` runs by default.
# --------------------------------------------------------------------------


def _colorize(frame: Grid) -> str:
    if not sys.stdout.isatty():
        return format_grid(frame)
    colors = {HEAD: "\033[97;44m", TAIL: "\033[97;41m", CONDUCTOR: "\033[33m", EMPTY: ""}
    reset = "\033[0m"
    lines = []
    for row in frame:
        chars = [f"{colors[c]}{c}{reset}" if colors[c] else c for c in row]
        lines.append("".join(chars))
    return "\n".join(lines)


def run_headless(grid: Grid, steps: int, delay: float = 0.0) -> None:
    """Print `steps` ticks of `grid` to stdout, one frame at a time."""
    frame = grid
    for tick in range(steps + 1):
        print(f"-- step {tick}, electrons {electron_count(frame)} --")
        print(_colorize(frame))
        print()
        if tick < steps:
            frame = step(frame)
            if delay:
                time.sleep(delay)


# --------------------------------------------------------------------------
# The curses editor. Kept thin and separate from the simulation above: this
# is the only part of the file that touches a terminal, and importing this
# module never calls into curses, so tests can import everything above
# without a TTY.
# --------------------------------------------------------------------------

HELP_LINE = (
    "arrows move | space cycle cell | s step | r run/pause | "
    "c stamp | Tab component | w save | o open | q quit"
)


def _next_state(cell: str) -> str:
    return STATES[(STATES.index(cell) + 1) % len(STATES)]


class Editor:
    """Holds all editor state. `run` is the only method that touches curses
    directly; everything else is plain data manipulation, testable without a
    terminal (though it isn't exercised by the stdlib test suite, per the
    house convention of leaving interactive orchestrators untested)."""

    def __init__(self, grid: Grid | None = None):
        self.grid: Grid = grid if grid is not None else make_grid(60, 24)
        self.cursor: Point = (0, 0)
        self.running = False
        self.steps = 0
        self.component_index = 0
        self.message = ""

    @property
    def component(self) -> Component:
        return COMPONENTS[COMPONENT_ORDER[self.component_index]]

    def move_cursor(self, dx: int, dy: int) -> None:
        width, height = grid_size(self.grid)
        x, y = self.cursor
        self.cursor = (max(0, min(width - 1, x + dx)), max(0, min(height - 1, y + dy)))

    def cycle_cell(self) -> None:
        x, y = self.cursor
        self.grid[y][x] = _next_state(self.grid[y][x])

    def step_once(self) -> None:
        self.grid = step(self.grid)
        self.steps += 1

    def stamp_component(self) -> None:
        self.grid = place_component(self.grid, self.component.grid, self.cursor)

    def cycle_component(self) -> None:
        self.component_index = (self.component_index + 1) % len(COMPONENT_ORDER)

    def save_to(self, path: str) -> None:
        save(self.grid, path)
        self.message = f"saved {path}"

    def load_from(self, path: str) -> None:
        self.grid = load(path)
        self.steps = 0
        self.message = f"loaded {path}"


def _init_colors() -> dict[str, int]:
    import curses

    pairs = {}
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # head
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)  # tail
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # conductor
        pairs = {
            HEAD: curses.color_pair(1),
            TAIL: curses.color_pair(2),
            CONDUCTOR: curses.color_pair(3),
        }
    return pairs


def _draw(stdscr, editor: Editor, color_pairs: dict[str, int]) -> None:
    import curses

    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    for y, row in enumerate(editor.grid):
        if y >= max_y - 2:
            break
        for x, cell in enumerate(row):
            if x >= max_x:
                break
            attr = color_pairs.get(cell, 0)
            with contextlib.suppress(curses.error):
                stdscr.addch(y, x, cell, attr)  # bottom-right cell: terminals refuse it
    status = (
        f"step {editor.steps}  electrons {electron_count(editor.grid)}  "
        f"{'RUNNING' if editor.running else 'paused'}  "
        f"component: {editor.component.name} ({COMPONENT_ORDER.index(editor.component.name) + 1}"
        f"/{len(COMPONENT_ORDER)})  {editor.message}"
    )
    try:
        stdscr.addstr(max_y - 2, 0, status[: max_x - 1])
        stdscr.addstr(max_y - 1, 0, HELP_LINE[: max_x - 1])
        stdscr.move(*reversed(editor.cursor))
    except curses.error:
        pass
    stdscr.refresh()


def _prompt(stdscr, message: str) -> str:
    import curses

    max_y, max_x = stdscr.getmaxyx()
    stdscr.addstr(max_y - 1, 0, (message + " ")[: max_x - 1])
    curses.echo()
    curses.curs_set(1)
    try:
        text = stdscr.getstr(max_y - 1, len(message) + 1, 40).decode("utf-8")
    finally:
        curses.noecho()
        curses.curs_set(0)
    return text


def _editor_loop(stdscr, editor: Editor) -> None:
    import curses

    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.timeout(150 if editor.running else -1)
    color_pairs = _init_colors()

    while True:
        stdscr.timeout(150 if editor.running else -1)
        _draw(stdscr, editor, color_pairs)
        key = stdscr.getch()
        editor.message = ""

        if key in (curses.KEY_UP, ord("k")):
            editor.move_cursor(0, -1)
        elif key in (curses.KEY_DOWN, ord("j")):
            editor.move_cursor(0, 1)
        elif key in (curses.KEY_LEFT, ord("h")):
            editor.move_cursor(-1, 0)
        elif key in (curses.KEY_RIGHT, ord("l")):
            editor.move_cursor(1, 0)
        elif key == ord(" "):
            editor.cycle_cell()
        elif key == ord("s"):
            editor.step_once()
        elif key == ord("r"):
            editor.running = not editor.running
        elif key == ord("c"):
            editor.stamp_component()
        elif key == ord("\t"):
            editor.cycle_component()
        elif key == ord("w"):
            path = _prompt(stdscr, "save to file:")
            if path:
                editor.save_to(path)
        elif key == ord("o"):
            path = _prompt(stdscr, "open file:")
            if path:
                try:
                    editor.load_from(path)
                except OSError as exc:
                    editor.message = f"could not load: {exc}"
        elif key == ord("q"):
            return
        elif key == -1 and editor.running:
            editor.step_once()


def run_editor(grid: Grid | None = None) -> None:
    import curses

    editor = Editor(grid)
    curses.wrapper(_editor_loop, editor)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wireworld: a 4-state cellular automaton you build circuits in."
    )
    parser.add_argument(
        "--demo", choices=COMPONENT_ORDER, help="load a component and run it headlessly"
    )
    parser.add_argument(
        "--steps", type=int, default=20, help="ticks to run with --demo (default: 20)"
    )
    parser.add_argument(
        "--delay", type=float, default=0.15, help="seconds between frames with --demo"
    )
    parser.add_argument(
        "--truth-table",
        choices=["or", "and_not", "xor"],
        help="print every input combination and the resulting output",
    )
    parser.add_argument("--load", help="open a saved grid file in the editor")
    parser.add_argument("--list", action="store_true", help="list library components and exit")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.list:
        for name in COMPONENT_ORDER:
            print(f"{name}: {COMPONENTS[name].summary}")
        return

    if args.truth_table:
        print_truth_table(COMPONENTS[args.truth_table])
        return

    if args.demo:
        if args.demo == "diode":
            demo_diode()
            return
        component = COMPONENTS[args.demo]
        grid = component.grid
        # Give the demo something to watch: drive every input port at tick 0.
        for name, cells in component.ports.items():
            if name.startswith("in"):
                grid = _inject(grid, cells)
        run_headless(grid, args.steps, args.delay)
        return

    grid = load(args.load) if args.load else None
    if not sys.stdout.isatty():
        print("No terminal detected; use --demo NAME or --truth-table NAME instead.")
        return
    run_editor(grid)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
