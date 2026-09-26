#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
MAZE GENERATION: A Literate Demonstration
==========================================

A maze, mathematically, is a spanning tree over a grid graph: take every cell
as a node, connect grid-adjacent cells with an edge wherever a passage is
carved between them, and stop once every cell is reachable from every other
one by exactly one route. Different algorithms build that same kind of object
by walking the grid in different orders, and the differences show up as
texture: long corridors, short dead ends, uniform noise, or a visible
diagonal bias.

Six generators, one data structure:
  - DFS backtracker  -- always extend from the newest cell. Long, winding
                         corridors and few dead ends: how a person doodles a
                         maze.
  - Randomized Prim   -- always extend from a random frontier cell instead.
                         Same grid, visibly different texture: short, stubby
                         passages and many dead ends.
  - Growing tree       -- the collapse. The two algorithms above differ only
                         in *which* frontier cell they extend from next, so
                         they become one function with a `pick` argument.
                         `pick="oldest"` is a third texture neither of them
                         has a name for.
  - Kruskal's          -- no frontier at all. Shuffle every possible edge,
                         and use a union-find forest to reject any edge that
                         would close a loop. What survives is a tree.
  - Wilson's           -- loop-erased random walks. Wander at random, and
                         when the walk crosses itself, erase the loop and
                         keep going. Slower than everything above, and
                         (unlike them) draws uniformly from every possible
                         spanning tree of the grid -- being correct costs
                         something, and this is the price.
  - Binary tree        -- four lines, deliberately biased: every cell carves
                         a passage north or east, never south or west. The
                         result is a maze with a visible diagonal grain and
                         two dead-straight open edges. Wrong by eye, and a
                         lesson in what "correct" was buying the others.

Every generator is a Python generator that `yield`s the pair of cells it just
linked, one carve at a time. None of them contain a line of rendering code --
that separation is what lets the same six functions drive the animation, get
printed verbatim by the `c` command (`inspect.getsource`), and get exercised
directly by the test suite with no terminal involved.

Rendering is box-drawing characters on a (2w+1) x (2h+1) character grid:
odd/odd positions are cell floors, and everything else is a wall unless a
passage removed it. Every wall *post* (even/even) picks its glyph -- a
corner, a T-junction, a straight run, or a plus -- from a 16-entry table
indexed by a 4-bit mask of which of its four arms are also walls. It is the
same trick as marching squares, and the same shape as a cellular automaton's
rule table.

Solving is two breadth-first searches. One BFS from any cell gives a distance
field, shown here as a 24-bit colour gradient. Two BFS calls back to back --
from an arbitrary start to find a far cell, then from that far cell to find
the true far end -- gives the longest path in the maze (its diameter)
without ever comparing every pair of cells directly.

Stdlib only, and export is SVG rather than a raster image: a maze is lines on
a page, and SVG is a dozen lines of text, so there is no image library to
install.
"""

import argparse
import inspect
import random
import sys
import time
from collections import deque
from pathlib import Path

type Cell = tuple[int, int]

DEFAULT_WIDTH = 48
DEFAULT_HEIGHT = 14  # a (2*48+1) x (2*14+1) = 97x29 grid, fits a 100x30 terminal

# Animation speed, keyed by the menu choice 1 (slowest) to 5 (fastest).
SPEED_DELAYS = {"1": 0.08, "2": 0.03, "3": 0.012, "4": 0.004, "5": 0.0}

# The pick modes `growing_tree` collapses DFS and Prim into, plus the one
# neither of them is.
PICK_LABELS = {"1": "newest", "2": "random", "3": "oldest"}


# ---------------------------------------------------------------------------
# The data structure: a spanning tree over a grid
# ---------------------------------------------------------------------------


class Maze:
    """A grid of cells and the passages carved between them.

    `Maze` only stores the tree -- a mapping from each cell to the neighbours
    it has been linked to. It knows nothing about how those links were
    chosen or how the result will be drawn; that separation is what lets six
    very different generators, and two very different renderers, all share
    this one class.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.links: dict[Cell, set[Cell]] = {cell: set() for cell in self.cells()}

    def cells(self) -> list[Cell]:
        """Every cell, in row-major order."""
        return [(x, y) for y in range(self.height) for x in range(self.width)]

    def in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    def neighbors(self, cell: Cell) -> list[Cell]:
        """The (up to four) grid-adjacent cells, whether or not a passage
        has been carved to them yet."""
        x, y = cell
        candidates = ((x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y))
        return [c for c in candidates if self.in_bounds(c)]

    def link(self, a: Cell, b: Cell) -> None:
        """Carve a passage between two adjacent cells."""
        self.links[a].add(b)
        self.links[b].add(a)

    def is_linked(self, a: Cell, b: Cell) -> bool:
        return b in self.links[a]

    def edge_count(self) -> int:
        """A perfect maze has exactly `width * height - 1` of these."""
        return sum(len(neighbors) for neighbors in self.links.values()) // 2


class UnionFind:
    """Disjoint-set forest with path compression, for Kruskal's algorithm.

    Each cell starts in its own singleton set. `union` merges two sets and
    reports whether they were different sets to begin with -- which, for
    Kruskal's, is exactly the question "does carving this passage close a
    loop?"
    """

    def __init__(self, items):
        self.parent = {item: item for item in items}

    def find(self, item):
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        # Path compression: point every cell visited on the way straight at
        # the root, so the next find() through here is O(1) rather than
        # O(depth).
        while self.parent[item] != root:
            self.parent[item], item = root, self.parent[item]
        return root

    def union(self, a, b) -> bool:
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return False
        self.parent[root_a] = root_b
        return True


# ---------------------------------------------------------------------------
# The six generators. Every one yields (a, b) after linking a to b.
# ---------------------------------------------------------------------------


def dfs_backtracker(maze: Maze, rng: random.Random):
    """Recursive backtracking, told with an explicit stack.

    Carve to a random unvisited neighbour and keep going. When a cell has no
    unvisited neighbours left, back up to the most recently visited cell
    that still has one. That's exactly what a person doodling a maze does:
    keep drawing forward, and when you're stuck, retreat to your last fork.
    """
    start = (0, 0)
    visited = {start}
    active = [start]
    while active:
        cell = active[-1]  # always work from the newest cell
        unvisited = [n for n in maze.neighbors(cell) if n not in visited]
        if not unvisited:
            active.pop()  # dead end: back up
            continue
        nxt = rng.choice(unvisited)
        visited.add(nxt)
        maze.link(cell, nxt)
        active.append(nxt)
        yield cell, nxt


def randomized_prim(maze: Maze, rng: random.Random):
    """Grow the tree from a random frontier cell each time, not the newest.

    Same shape as `dfs_backtracker` above -- a list of cells still worth
    visiting, extend from one of them, repeat -- but the *choice* of which
    active cell to extend from is uniform at random instead of always "the
    last one added". That one-line difference is why the result looks
    nothing alike: short, stubby passages and many dead ends, instead of
    long corridors.
    """
    start = (0, 0)
    visited = {start}
    active = [start]
    while active:
        i = rng.randrange(len(active))  # any active cell, not just the newest
        cell = active[i]
        unvisited = [n for n in maze.neighbors(cell) if n not in visited]
        if not unvisited:
            del active[i]
            continue
        nxt = rng.choice(unvisited)
        visited.add(nxt)
        maze.link(cell, nxt)
        active.append(nxt)
        yield cell, nxt


def growing_tree(maze: Maze, rng: random.Random, pick: str = "random"):
    """The collapse: `dfs_backtracker` and `randomized_prim` above, unified.

    Both of those functions maintain a list of cells still worth visiting
    and differ only in *which* one they extend from next. Make that choice a
    parameter and the two functions become one: `pick="newest"` reproduces
    `dfs_backtracker`, `pick="random"` reproduces `randomized_prim`, and
    `pick="oldest"` -- extend from the cell that has been waiting longest --
    gives a third texture that neither original algorithm has a name for:
    short and uniform, closer to a breadth-first sprawl than a maze.
    """
    choose_index = {
        "newest": lambda active: len(active) - 1,
        "random": lambda active: rng.randrange(len(active)),
        "oldest": lambda active: 0,
    }[pick]

    start = (0, 0)
    visited = {start}
    active = [start]
    while active:
        i = choose_index(active)
        cell = active[i]
        unvisited = [n for n in maze.neighbors(cell) if n not in visited]
        if not unvisited:
            del active[i]
            continue
        nxt = rng.choice(unvisited)
        visited.add(nxt)
        maze.link(cell, nxt)
        active.append(nxt)
        yield cell, nxt


def kruskal(maze: Maze, rng: random.Random):
    """No frontier, no walk: shuffle every possible edge and keep the ones
    that don't close a loop.

    A union-find forest starts with every cell in its own set. Union two
    cells whenever an edge would join two *different* sets -- that's the
    only test needed, and once every edge has been considered, what
    survived is a spanning tree, built in an order that has nothing to do
    with the grid's geometry.
    """
    edges = []
    for cell in maze.cells():
        for neighbor in maze.neighbors(cell):
            if neighbor > cell:  # count each edge exactly once
                edges.append((cell, neighbor))
    rng.shuffle(edges)

    forest = UnionFind(maze.cells())
    for a, b in edges:
        if forest.union(a, b):
            maze.link(a, b)
            yield a, b


def wilsons(maze: Maze, rng: random.Random):
    """Loop-erased random walks: short, and hard to believe.

    Start with one cell "in the tree". Repeatedly: pick any cell not yet in
    the tree, and take a uniform random walk from it -- stepping to a random
    neighbour each time -- until the walk reaches a cell that already is in
    the tree. If the walk crosses its own earlier path, erase everything
    from that earlier visit onward and keep walking from there. Once the
    walk reaches the tree, carve every step of what remains of it, and add
    those cells to the tree.

    Unlike every generator above, this one draws uniformly from the set of
    all possible spanning trees of the grid -- no bias toward long corridors
    or short dead ends. Correctness costs speed: it is the slowest generator
    here, sometimes dramatically so, especially on the first few walks
    before much of the grid is in the tree to walk into.
    """
    cells = maze.cells()
    in_tree = {rng.choice(cells)}
    remaining = [c for c in cells if c not in in_tree]
    while remaining:
        path = [rng.choice(remaining)]
        while path[-1] not in in_tree:
            step = rng.choice(maze.neighbors(path[-1]))
            if step in path:
                # Loop-erasure: the walk crossed itself, so cut back to the
                # earlier visit and continue from there.
                path = path[: path.index(step) + 1]
            else:
                path.append(step)
        for a, b in zip(path, path[1:], strict=False):
            maze.link(a, b)
            yield a, b
        in_tree.update(path)
        remaining = [c for c in remaining if c not in in_tree]


def binary_tree(maze: Maze, rng: random.Random):
    """Four lines, and deliberately biased.

    For every cell, carve north or east -- whichever are available -- and
    nothing else. It's a spanning tree (every cell but the top row and
    right column gains exactly one link, and those two gain their one link
    from a neighbour), but the bias is visible on sight: a diagonal grain,
    and the top row and right column are one dead-straight open corridor
    each. A correct implementation of a biased algorithm is its own lesson
    in what the other five are paying for.
    """
    for y in range(maze.height):
        for x in range(maze.width):
            options = [n for n in ((x + 1, y), (x, y + 1)) if maze.in_bounds(n)]
            if options:
                nxt = rng.choice(options)
                maze.link((x, y), nxt)
                yield (x, y), nxt


# name, generator function, whether the menu should ask for a `pick` mode
ALGORITHMS = [
    ("DFS backtracker", dfs_backtracker, False),
    ("Randomized Prim", randomized_prim, False),
    ("Growing tree (pick your own frontier rule)", growing_tree, True),
    ("Kruskal's (union-find)", kruskal, False),
    ("Wilson's (loop-erased walk)", wilsons, False),
    ("Binary tree (biased, on purpose)", binary_tree, False),
]


# ---------------------------------------------------------------------------
# Rendering: box-drawing characters, chosen by a marching-squares style mask
# ---------------------------------------------------------------------------

# Indexed by a 4-bit mask of which arms are walls: bit 0 = north, bit 1 =
# south, bit 2 = east, bit 3 = west.
WALL_GLYPHS = {
    0b0000: " ",
    0b0001: "╵",
    0b0010: "╷",
    0b0011: "│",
    0b0100: "╶",
    0b0101: "└",
    0b0110: "┌",
    0b0111: "├",
    0b1000: "╴",
    0b1001: "┘",
    0b1010: "┐",
    0b1011: "┤",
    0b1100: "─",
    0b1101: "┴",
    0b1110: "┬",
    0b1111: "┼",
}


def build_wall_grid(maze: Maze) -> list[list[bool]]:
    """A (2h+1) x (2w+1) grid of booleans, True where a wall stands.

    Grid position (2y+1, 2x+1) is the floor of cell (x, y); everything else
    starts as a wall. Linking two cells clears the wall at the midpoint
    between their two floor positions -- `y + ny + 1, x + nx + 1` lands there
    exactly, since the two floors differ by 2 in one coordinate. This one
    grid is the single source of truth for both the terminal renderer and
    the SVG export below.
    """
    rows, cols = 2 * maze.height + 1, 2 * maze.width + 1
    walls = [[True] * cols for _ in range(rows)]
    for x, y in maze.cells():
        walls[2 * y + 1][2 * x + 1] = False
        for nx, ny in maze.links[(x, y)]:
            walls[y + ny + 1][x + nx + 1] = False
    return walls


def wall_char(walls: list[list[bool]], r: int, c: int) -> str:
    """The glyph for wall post (r, c), from the 16-entry mask table."""
    rows, cols = len(walls), len(walls[0])

    def is_wall(rr, cc):
        # Off the edge of the grid: there is no arm there to draw, which is
        # different from a wall standing in the grid. The border still
        # closes into a rectangle regardless, because the segment positions
        # along row/column 0 and the last row/column are never toggled open
        # (no cell there has a neighbour off the edge to link to).
        return walls[rr][cc] if 0 <= rr < rows and 0 <= cc < cols else False

    mask = (
        (0b0001 if is_wall(r - 1, c) else 0)
        | (0b0010 if is_wall(r + 1, c) else 0)
        | (0b0100 if is_wall(r, c + 1) else 0)
        | (0b1000 if is_wall(r, c - 1) else 0)
    )
    return WALL_GLYPHS[mask]


def gradient_color(t: float) -> str:
    """Blend from cool blue (t=0, near) to warm orange (t=1, far).

    `\\033[38;2;R;G;Bm` sets the terminal foreground colour to an arbitrary
    24-bit RGB triple -- no palette and no 256-colour lookup, just three
    bytes. Almost every terminal built in the last decade understands it.
    """
    near, far = (60, 90, 220), (255, 100, 40)
    r = round(near[0] + (far[0] - near[0]) * t)
    g = round(near[1] + (far[1] - near[1]) * t)
    b = round(near[2] + (far[2] - near[2]) * t)
    return f"\033[38;2;{r};{g};{b}m"


ANSI_RESET = "\033[0m"
ANSI_PATH = "\033[1;97m"  # bright white, for the solved route


def cell_char(
    cell: Cell,
    distances: dict[Cell, int] | None,
    max_distance: int,
    path_cells: set[Cell],
) -> str:
    if distances is None:
        return " "
    if cell in path_cells:
        return f"{ANSI_PATH}●{ANSI_RESET}"
    t = distances[cell] / max_distance if max_distance else 0.0
    return f"{gradient_color(t)}█{ANSI_RESET}"


def render_lines(
    maze: Maze,
    walls: list[list[bool]],
    distances: dict[Cell, int] | None = None,
    max_distance: int = 0,
    path: list[Cell] | None = None,
) -> list[str]:
    """The maze as a list of text rows.

    Posts (both coordinates even) get a glyph from the mask table. Segments
    (exactly one coordinate even) are a plain wall or open space -- with
    only two states, they don't need the table. Cells (both coordinates odd)
    are blank floor, unless a distance field or a solved path was supplied.
    """
    rows, cols = len(walls), len(walls[0])
    path_cells = set(path) if path else set()
    lines = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            if r % 2 == 0 and c % 2 == 0:
                row_chars.append(wall_char(walls, r, c))
            elif r % 2 == 1 and c % 2 == 1:
                cell = ((c - 1) // 2, (r - 1) // 2)
                row_chars.append(cell_char(cell, distances, max_distance, path_cells))
            else:
                segment_glyph = "─" if r % 2 == 0 else "│"
                row_chars.append(segment_glyph if walls[r][c] else " ")
        lines.append("".join(row_chars))
    return lines


# ---------------------------------------------------------------------------
# Solving: one BFS for a distance field, two for the longest path
# ---------------------------------------------------------------------------


def bfs(maze: Maze, start: Cell) -> tuple[dict[Cell, int], dict[Cell, Cell | None]]:
    """Distances and parents from `start`, by breadth-first search."""
    distances = {start: 0}
    parents: dict[Cell, Cell | None] = {start: None}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for neighbor in maze.links[cell]:
            if neighbor not in distances:
                distances[neighbor] = distances[cell] + 1
                parents[neighbor] = cell
                queue.append(neighbor)
    return distances, parents


def longest_path(maze: Maze) -> list[Cell]:
    """The longest shortest-path in the maze: its diameter, as a cell list.

    BFS from any cell finds a cell `a` that is farthest from it. `a` is not
    necessarily an end of the true longest path, but one end of *some*
    longest path is always reachable this way. BFS again, from `a`, finds
    the actual far end `b` -- and walking `b`'s parents back to `a` recovers
    the path between them. Two breadth-first searches, no comparing every
    pair of cells.
    """
    any_cell = maze.cells()[0]
    distances, _ = bfs(maze, any_cell)
    a = max(distances, key=distances.get)
    distances_from_a, parents = bfs(maze, a)
    b = max(distances_from_a, key=distances_from_a.get)

    path = [b]
    while parents[path[-1]] is not None:
        path.append(parents[path[-1]])
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# Export: a maze is lines on a page, and SVG is just text
# ---------------------------------------------------------------------------


def to_svg(maze: Maze, walls: list[list[bool]], cell_px: int = 20) -> str:
    """Render the maze as an SVG document: one `<line>` per wall segment."""
    rows, cols = len(walls), len(walls[0])
    segments = []
    for r in range(rows):
        for c in range(cols):
            if r % 2 == c % 2 or not walls[r][c]:
                continue  # posts and floors aren't segments; open segments aren't walls
            if r % 2 == 0:  # horizontal segment
                x0, y0 = (c - 1) // 2 * cell_px, r // 2 * cell_px
                segments.append((x0, y0, x0 + cell_px, y0))
            else:  # vertical segment
                x0, y0 = c // 2 * cell_px, (r - 1) // 2 * cell_px
                segments.append((x0, y0, x0, y0 + cell_px))

    width, height = maze.width * cell_px, maze.height * cell_px
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    parts.append(f'<rect width="{width}" height="{height}" fill="white"/>')
    for x0, y0, x1, y1 in segments:
        parts.append(
            f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="black" stroke-width="2"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The interactive demo
# ---------------------------------------------------------------------------


def prompt_choice(prompt: str, options: set[str], default: str) -> str:
    """Prompt until the answer is one of `options`, or accept `default` on Enter."""
    while True:
        try:
            answer = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)
        if answer == "":
            return default
        if answer in options:
            return answer
        print(f"  Enter one of: {', '.join(sorted(options))}")


class MazeDemo:
    """Interactive demonstration: pick an algorithm, watch it, then solve it,
    read its source, or export it, before picking another."""

    def __init__(self, width: int, height: int, seed: int | None):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.delay = SPEED_DELAYS["3"]
        self.maze: Maze | None = None
        self.walls: list[list[bool]] | None = None
        self.last_name: str | None = None
        self.last_func = None

    def print_header(self):
        print("\n" + "=" * 70)
        print("  MAZE GENERATION DEMONSTRATION".center(70))
        print("=" * 70)
        print("\nA maze is a spanning tree over a grid: every cell reachable from")
        print("every other cell by exactly one route. Six algorithms below build")
        print("that same kind of object in six different orders, and the order")
        print("shows up as texture -- watch the same grid come out looking nothing")
        print("alike, twice.")

    def choose_speed(self) -> float:
        choice = prompt_choice(
            "\n  Animation speed, 1 (slowest) to 5 (fastest) [Enter for 3]: ",
            set(SPEED_DELAYS),
            "3",
        )
        return SPEED_DELAYS[choice]

    def choose_pick(self) -> str:
        print("  pick=newest is DFS-like, pick=random is Prim-like, pick=oldest is neither.")
        choice = prompt_choice(
            "  Pick 1=newest, 2=random, 3=oldest [Enter for 2]: ", set(PICK_LABELS), "2"
        )
        return PICK_LABELS[choice]

    def choose_algorithm(self):
        print("\nAlgorithms:")
        for i, (name, _, _) in enumerate(ALGORITHMS, 1):
            print(f"  {i}. {name}")
        quit_choice = str(len(ALGORITHMS) + 1)
        print(f"  {quit_choice}. Quit")

        valid = {str(i) for i in range(1, len(ALGORITHMS) + 2)}
        choice = prompt_choice("\nSelect (Enter for 1): ", valid, "1")
        if choice == quit_choice:
            print("\nGoodbye.")
            sys.exit(0)

        name, func, needs_pick = ALGORITHMS[int(choice) - 1]
        kwargs = {}
        if needs_pick:
            pick = self.choose_pick()
            kwargs = {"pick": pick}
            name = f"{name} [pick={pick}]"
        return name, func, kwargs

    def animate(self, name: str, func, kwargs: dict):
        self.maze = Maze(self.width, self.height)
        self.last_name, self.last_func = name, func
        generator = func(self.maze, self.rng, **kwargs)
        interactive = sys.stdout.isatty()

        if interactive:
            print("\033[2J", end="")  # clear once; later frames just repaint
            for _ in generator:
                self.render(name)
                time.sleep(self.delay)
        else:
            for _ in generator:
                pass  # no TTY to animate on: build the maze and move on

        self.walls = build_wall_grid(self.maze)
        self.render(name)

    def render(
        self,
        name: str,
        distances: dict[Cell, int] | None = None,
        max_distance: int = 0,
        path: list[Cell] | None = None,
    ):
        self.walls = build_wall_grid(self.maze)
        lines = render_lines(self.maze, self.walls, distances, max_distance, path)
        if sys.stdout.isatty():
            print("\033[H", end="")
        print(name)
        print("\n".join(lines))

    def solve(self):
        start = (0, 0)
        distances, _ = bfs(self.maze, start)
        max_distance = max(distances.values())
        path = longest_path(self.maze)

        print(f"\n  Distance field from {start} -- 0 is near, {max_distance} is far.")
        self.render(self.last_name, distances, max_distance)
        print(f"\n  Longest path: {len(path)} cells, from {path[0]} to {path[-1]}.")
        self.render(self.last_name, distances, max_distance, path)

    def show_source(self):
        print(f"\n  Source of {self.last_func.__name__}:\n")
        print(inspect.getsource(self.last_func))

    def export(self):
        try:
            filename = input("\n  Filename [Enter for maze.svg]: ").strip() or "maze.svg"
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            sys.exit(0)
        svg = to_svg(self.maze, self.walls)
        Path(filename).write_text(svg)
        print(f"  Wrote {filename} ({len(svg)} bytes).")

    def post_menu(self):
        while True:
            try:
                cmd = input("\n  [s]olve  [c]ode  [e]xport  [n]ext maze  [q]uit > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)
            if cmd in ("s", "solve"):
                self.solve()
            elif cmd in ("c", "code"):
                self.show_source()
            elif cmd in ("e", "export"):
                self.export()
            elif cmd in ("n", "next"):
                return
            elif cmd in ("q", "quit"):
                print("\nGoodbye.")
                sys.exit(0)
            else:
                print("  Enter s, c, e, n, or q")

    def run(self):
        self.print_header()
        self.delay = self.choose_speed()
        while True:
            name, func, kwargs = self.choose_algorithm()
            self.animate(name, func, kwargs)
            self.post_menu()


def main():
    parser = argparse.ArgumentParser(description="Maze generation and solving demo.")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed, for a reproducible maze")
    parser.add_argument(
        "--width", type=int, default=DEFAULT_WIDTH, help=f"cells wide (default {DEFAULT_WIDTH})"
    )
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT, help=f"cells tall (default {DEFAULT_HEIGHT})"
    )
    args = parser.parse_args()

    demo = MazeDemo(args.width, args.height, args.seed)
    try:
        demo.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
    except EOFError:
        print("\nExiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
