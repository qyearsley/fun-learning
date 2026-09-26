"""Tests for the pure logic in `maze_demo.py`.

Stdlib `unittest` and nothing else, same convention as
`tests/test_genetic_algorithm.py` -- these scripts are standalone PEP 723
files rather than a package, so `python3 -m unittest discover -s tests` from
the repo root is the whole story, on any interpreter meeting the `>=3.13`
floor the scripts declare.

What is covered: every generator produces a perfect maze (connected, exactly
`cells - 1` passages) across several sizes and seeds; the "collapse" claim,
that `growing_tree(pick="newest")` really does reproduce `dfs_backtracker`
carve-for-carve given the same seed; `UnionFind`; the wall-glyph table; BFS
distances and the longest path on small hand-built structures; and that the
SVG export is well-formed and has the expected number of wall segments. The
`MazeDemo` orchestrator is print- and input()-driven and is not tested here.

Randomness is seeded per test rather than stubbed, exercising the real
`random` calls -- the same approach `test_genetic_algorithm.py` takes.
"""

import random
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from maze_demo import (  # noqa: E402
    WALL_GLYPHS,
    Maze,
    UnionFind,
    bfs,
    binary_tree,
    build_wall_grid,
    dfs_backtracker,
    growing_tree,
    kruskal,
    longest_path,
    randomized_prim,
    to_svg,
    wall_char,
    wilsons,
)

GENERATORS = {
    "dfs_backtracker": lambda m, r: dfs_backtracker(m, r),
    "randomized_prim": lambda m, r: randomized_prim(m, r),
    "growing_tree/newest": lambda m, r: growing_tree(m, r, pick="newest"),
    "growing_tree/random": lambda m, r: growing_tree(m, r, pick="random"),
    "growing_tree/oldest": lambda m, r: growing_tree(m, r, pick="oldest"),
    "kruskal": lambda m, r: kruskal(m, r),
    "wilsons": lambda m, r: wilsons(m, r),
    "binary_tree": lambda m, r: binary_tree(m, r),
}

SIZES = [(1, 1), (2, 1), (1, 2), (3, 3), (5, 4), (8, 6)]
SEEDS = [0, 1, 42]


class TestEveryGeneratorProducesASpanningTree(unittest.TestCase):
    """A perfect maze is connected and has exactly `cells - 1` passages.

    That's the definition of a spanning tree: fewer edges and it can't be
    connected; more edges (for a connected graph) and it has a cycle. Check
    both properties directly rather than assuming one implies the other.
    """

    def test_every_generator_at_every_size_and_seed(self):
        for name, factory in GENERATORS.items():
            for width, height in SIZES:
                for seed in SEEDS:
                    with self.subTest(generator=name, width=width, height=height, seed=seed):
                        maze = Maze(width, height)
                        list(factory(maze, random.Random(seed)))

                        cells = maze.cells()
                        self.assertEqual(maze.edge_count(), len(cells) - 1)

                        distances, _ = bfs(maze, cells[0])
                        self.assertEqual(set(distances), set(cells), "not every cell is reachable")


class TestTheCollapse(unittest.TestCase):
    """`growing_tree` claims to generalize `dfs_backtracker` and
    `randomized_prim`. Prove it: given the same seed, the pick-based
    function must carve exactly the same edges in exactly the same order.
    """

    def test_pick_newest_reproduces_dfs_backtracker(self):
        for seed in (0, 1, 7, 99):
            dfs_maze, growing_maze = Maze(6, 5), Maze(6, 5)
            dfs_edges = list(dfs_backtracker(dfs_maze, random.Random(seed)))
            growing_edges = list(growing_tree(growing_maze, random.Random(seed), pick="newest"))
            self.assertEqual(dfs_edges, growing_edges)
            self.assertEqual(dfs_maze.links, growing_maze.links)

    def test_pick_random_reproduces_randomized_prim(self):
        for seed in (0, 1, 7, 99):
            prim_maze, growing_maze = Maze(6, 5), Maze(6, 5)
            prim_edges = list(randomized_prim(prim_maze, random.Random(seed)))
            growing_edges = list(growing_tree(growing_maze, random.Random(seed), pick="random"))
            self.assertEqual(prim_edges, growing_edges)
            self.assertEqual(prim_maze.links, growing_maze.links)

    def test_pick_oldest_is_still_a_valid_spanning_tree(self):
        # The one texture with no original algorithm to compare against --
        # just confirm it holds the same spanning-tree invariant as the rest.
        maze = Maze(7, 7)
        list(growing_tree(maze, random.Random(3), pick="oldest"))
        self.assertEqual(maze.edge_count(), len(maze.cells()) - 1)


class TestMazeGrid(unittest.TestCase):
    def test_a_fresh_maze_has_no_links(self):
        maze = Maze(3, 3)
        self.assertEqual(maze.edge_count(), 0)
        for cell in maze.cells():
            self.assertEqual(maze.links[cell], set())

    def test_link_is_symmetric(self):
        maze = Maze(3, 3)
        maze.link((0, 0), (1, 0))
        self.assertTrue(maze.is_linked((0, 0), (1, 0)))
        self.assertTrue(maze.is_linked((1, 0), (0, 0)))

    def test_neighbors_excludes_out_of_bounds_cells(self):
        maze = Maze(3, 3)
        self.assertEqual(set(maze.neighbors((0, 0))), {(1, 0), (0, 1)})
        self.assertEqual(set(maze.neighbors((1, 1))), {(0, 1), (2, 1), (1, 0), (1, 2)})

    def test_cells_are_row_major(self):
        maze = Maze(2, 2)
        self.assertEqual(maze.cells(), [(0, 0), (1, 0), (0, 1), (1, 1)])


class TestUnionFind(unittest.TestCase):
    def test_everything_starts_in_its_own_set(self):
        uf = UnionFind(range(5))
        for i in range(5):
            self.assertEqual(uf.find(i), i)

    def test_union_merges_two_different_sets_and_reports_true(self):
        uf = UnionFind(range(5))
        self.assertTrue(uf.union(0, 1))
        self.assertEqual(uf.find(0), uf.find(1))

    def test_union_of_an_already_merged_pair_reports_false(self):
        uf = UnionFind(range(5))
        uf.union(0, 1)
        self.assertFalse(uf.union(0, 1))
        self.assertFalse(uf.union(1, 0))

    def test_transitive_union_puts_everyone_in_one_set(self):
        uf = UnionFind(range(4))
        uf.union(0, 1)
        uf.union(1, 2)
        uf.union(2, 3)
        root = uf.find(0)
        for i in range(4):
            self.assertEqual(uf.find(i), root)

    def test_path_compression_does_not_change_the_answer(self):
        # Build a long chain (0 -> 1 -> 2 -> ... -> 9) so find() has real
        # compression work to do, then check every element still resolves
        # to the same root, twice in a row.
        uf = UnionFind(range(10))
        for i in range(9):
            uf.union(i, i + 1)
        roots_first_pass = [uf.find(i) for i in range(10)]
        roots_second_pass = [uf.find(i) for i in range(10)]
        self.assertEqual(roots_first_pass, roots_second_pass)
        self.assertEqual(len(set(roots_first_pass)), 1)


class TestWallGlyphTable(unittest.TestCase):
    def test_every_mask_from_0_to_15_is_covered(self):
        self.assertEqual(set(WALL_GLYPHS), set(range(16)))

    def test_every_glyph_is_a_single_character(self):
        for glyph in WALL_GLYPHS.values():
            self.assertEqual(len(glyph), 1)

    def test_all_glyphs_are_distinct(self):
        self.assertEqual(len(set(WALL_GLYPHS.values())), 16)

    def test_the_open_and_closed_extremes(self):
        self.assertEqual(WALL_GLYPHS[0b0000], " ")
        self.assertEqual(WALL_GLYPHS[0b1111], "┼")


class TestBorderRendersAsAClosedRectangle(unittest.TestCase):
    """Regression test: `wall_char` used to treat an off-grid neighbour as a
    wall *arm*, which gave every border post a phantom fourth arm pointing
    off the edge -- corners rendered as "┼" and edges as "┴"/"┬"/"├"/"┤"
    instead of proper "┌"/"┐"/"└"/"┘" corners and clean "┬"/"┴"/"├"/"┤" or
    "─"/"│" edges. Off the grid means no arm to draw, not a wall.
    """

    def test_the_four_corners_are_proper_corners_on_an_empty_maze(self):
        # An unlinked maze has every segment standing, so every border post
        # has exactly two real arms: the two that point along the border.
        maze = Maze(4, 3)
        walls = build_wall_grid(maze)
        last_row, last_col = len(walls) - 1, len(walls[0]) - 1
        self.assertEqual(wall_char(walls, 0, 0), "┌")
        self.assertEqual(wall_char(walls, 0, last_col), "┐")
        self.assertEqual(wall_char(walls, last_row, 0), "└")
        self.assertEqual(wall_char(walls, last_row, last_col), "┘")

    def test_a_top_edge_post_has_no_phantom_arm_off_the_grid(self):
        # An interior top-row post has at most three real arms (south,
        # east, west) -- never north, since there is nothing above row 0.
        maze = Maze(4, 3)
        walls = build_wall_grid(maze)
        glyph = wall_char(walls, 0, 2)
        self.assertIn(glyph, {"┬", "─"})


class TestBFS(unittest.TestCase):
    """A hand-built, branching (not just linear) maze, so BFS is exercised
    on something with a real fork in it. Built with an explicit start cell
    so the result doesn't depend on `maze.cells()` ordering or any
    tie-breaking in `max()`.
    """

    def build_forked_maze(self):
        # (0,0) - (1,0) - (2,0)
        #           |
        #         (1,1)
        #           |
        #         (1,2)
        maze = Maze(3, 3)
        maze.link((0, 0), (1, 0))
        maze.link((1, 0), (2, 0))
        maze.link((1, 0), (1, 1))
        maze.link((1, 1), (1, 2))
        return maze

    def test_distances_from_the_fork(self):
        maze = self.build_forked_maze()
        distances, _ = bfs(maze, (1, 0))
        self.assertEqual(distances, {(1, 0): 0, (0, 0): 1, (2, 0): 1, (1, 1): 1, (1, 2): 2})

    def test_distances_from_an_arm_reach_across_the_fork(self):
        maze = self.build_forked_maze()
        distances, _ = bfs(maze, (0, 0))
        self.assertEqual(distances, {(0, 0): 0, (1, 0): 1, (2, 0): 2, (1, 1): 2, (1, 2): 3})

    def test_parents_trace_a_path_back_to_the_start(self):
        maze = self.build_forked_maze()
        _, parents = bfs(maze, (1, 0))
        self.assertEqual(parents[(1, 2)], (1, 1))
        self.assertEqual(parents[(1, 1)], (1, 0))
        self.assertIsNone(parents[(1, 0)])


class TestLongestPath(unittest.TestCase):
    def test_a_straight_line_has_the_whole_line_as_its_longest_path(self):
        # No branching and no ties, so the double-BFS trick has exactly one
        # right answer to find.
        maze = Maze(5, 1)
        for x in range(4):
            maze.link((x, 0), (x + 1, 0))

        path = longest_path(maze)
        self.assertEqual(len(path), 5)
        self.assertEqual({path[0], path[-1]}, {(0, 0), (4, 0)})
        # The path is a contiguous walk, not just the right endpoints.
        for a, b in zip(path, path[1:], strict=False):
            self.assertTrue(maze.is_linked(a, b))

    def test_a_single_cell_maze_has_a_trivial_longest_path(self):
        maze = Maze(1, 1)
        self.assertEqual(longest_path(maze), [(0, 0)])


class TestSVGExport(unittest.TestCase):
    """A maze always has exactly `(width + 1) * (height + 1)` wall segments,
    regardless of which spanning tree it is. Total segment positions in the
    (2h+1) x (2w+1) grid are `2wh + w + h`; a perfect maze opens exactly
    `wh - 1` of them (one per passage); what's left standing is
    `wh + w + h + 1 == (w + 1) * (h + 1)`. That identity is what makes this
    test possible without caring which generator built the maze.
    """

    def build_svg(self, width, height, seed):
        maze = Maze(width, height)
        list(dfs_backtracker(maze, random.Random(seed)))
        walls = build_wall_grid(maze)
        return maze, to_svg(maze, walls)

    def test_the_svg_is_well_formed_xml(self):
        _, svg = self.build_svg(4, 3, seed=1)
        root = ET.fromstring(svg)  # raises ParseError if malformed
        self.assertTrue(root.tag.endswith("svg"))

    def test_the_line_count_matches_the_wall_segment_invariant(self):
        for width, height in [(1, 1), (2, 2), (4, 3), (6, 5)]:
            with self.subTest(width=width, height=height):
                maze, svg = self.build_svg(width, height, seed=2)
                root = ET.fromstring(svg)
                lines = [el for el in root.iter() if el.tag.endswith("line")]
                self.assertEqual(len(lines), (width + 1) * (height + 1))

    def test_the_outer_border_is_present(self):
        # Every segment along the very top row (y1 == y2 == 0) should span
        # the full width, one cell_px-wide piece at a time -- i.e. there are
        # exactly `width` of them, forming an unbroken top edge.
        maze, svg = self.build_svg(5, 4, seed=3)
        root = ET.fromstring(svg)
        top_edge = [
            el
            for el in root.iter()
            if el.tag.endswith("line") and el.get("y1") == "0" and el.get("y2") == "0"
        ]
        self.assertEqual(len(top_edge), maze.width)


if __name__ == "__main__":
    unittest.main()
