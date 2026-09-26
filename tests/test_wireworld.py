"""Tests for the pure simulation core and component library in
`wireworld_demo.py`. Stdlib `unittest` only, same convention as
`test_genetic_algorithm.py` -- see that file's module docstring for why.

Wireworld itself is fully deterministic (no `random` calls anywhere in the
core), so nothing here is seeded; the same grid always produces the same
next grid.

What is covered: the four state-transition rules in isolation, the "exactly
1 or 2" firing rule across all five possible head-neighbour counts, that a
signal travels one cell per tick and the head-tail pair never separates,
text load/save round-tripping, and every library component -- the wire, the
clock's period, the OR/AND-NOT/XOR truth tables by simulation, and the
diode passing every pulse one way and none the other. The curses editor is not
tested, per this repo's convention for interactive orchestrators; importing
the module and driving the pure functions never touches curses.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wireworld_demo import (  # noqa: E402
    COMPONENTS,
    CONDUCTOR,
    EMPTY,
    HEAD,
    TAIL,
    Component,
    _inject,
    count_head_neighbours,
    electron_count,
    format_grid,
    gate_output,
    grid_size,
    load,
    make_grid,
    mirror_horizontal,
    parse_grid,
    place_component,
    pulses_through,
    resize,
    run,
    save,
    step,
)


def single_cell_grid(state: str, neighbours: set[tuple[int, int]] = frozenset()) -> list[list[str]]:
    """A 3x3 grid with the centre cell set to `state` and HEAD placed at each
    (dx, dy) offset in `neighbours` (offsets in -1..1, excluding (0, 0))."""
    grid = make_grid(3, 3)
    grid[1][1] = state
    for dx, dy in neighbours:
        grid[1 + dy][1 + dx] = HEAD
    return grid


class TestStateTransitions(unittest.TestCase):
    """Each of the four rules, in isolation, with no neighbours at all
    (except conductor, which needs them to say anything interesting)."""

    def test_empty_stays_empty(self):
        grid = single_cell_grid(EMPTY)
        self.assertEqual(step(grid)[1][1], EMPTY)

    def test_head_becomes_tail(self):
        grid = single_cell_grid(HEAD)
        self.assertEqual(step(grid)[1][1], TAIL)

    def test_head_becomes_tail_regardless_of_neighbours(self):
        # The head->tail rule has no neighbour condition at all.
        grid = single_cell_grid(HEAD, neighbours={(1, 0), (-1, 0), (0, 1)})
        self.assertEqual(step(grid)[1][1], TAIL)

    def test_tail_becomes_conductor(self):
        grid = single_cell_grid(TAIL)
        self.assertEqual(step(grid)[1][1], CONDUCTOR)

    def test_tail_becomes_conductor_regardless_of_neighbours(self):
        grid = single_cell_grid(TAIL, neighbours={(1, 1), (-1, -1)})
        self.assertEqual(step(grid)[1][1], CONDUCTOR)


class TestConductorFiringRule(unittest.TestCase):
    """The "exactly 1 or 2" rule -- the one the whole module's docstring
    argues is the entire mechanism. Checked for every count from 0 to 3,
    since the interesting behaviour is the boundary on both sides: 0 and 3
    both refuse, only 1 and 2 fire."""

    def test_zero_head_neighbours_does_not_fire(self):
        grid = single_cell_grid(CONDUCTOR, neighbours=set())
        self.assertEqual(step(grid)[1][1], CONDUCTOR)

    def test_one_head_neighbour_fires(self):
        grid = single_cell_grid(CONDUCTOR, neighbours={(1, 0)})
        self.assertEqual(step(grid)[1][1], HEAD)

    def test_two_head_neighbours_fires(self):
        grid = single_cell_grid(CONDUCTOR, neighbours={(1, 0), (-1, 0)})
        self.assertEqual(step(grid)[1][1], HEAD)

    def test_three_head_neighbours_refuses(self):
        # This is the refusal every gate in the library is built on.
        grid = single_cell_grid(CONDUCTOR, neighbours={(1, 0), (-1, 0), (0, 1)})
        self.assertEqual(step(grid)[1][1], CONDUCTOR)

    def test_all_eight_head_neighbours_refuses(self):
        offsets = {(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)}
        grid = single_cell_grid(CONDUCTOR, neighbours=offsets)
        self.assertEqual(step(grid)[1][1], CONDUCTOR)


class TestNeighbourCounting(unittest.TestCase):
    def test_counts_only_heads_not_tails_or_conductor(self):
        grid = make_grid(3, 3)
        grid[0][0] = HEAD
        grid[0][1] = TAIL
        grid[0][2] = CONDUCTOR
        self.assertEqual(count_head_neighbours(grid, 1, 1), 1)

    def test_off_grid_neighbours_are_not_counted(self):
        # A cell in the corner has only 3 real neighbours; the other 5
        # offsets fall off the grid and must not raise or count as heads.
        grid = make_grid(2, 2)
        grid[0][1] = HEAD
        grid[1][0] = HEAD
        self.assertEqual(count_head_neighbours(grid, 0, 0), 2)

    def test_a_cell_is_not_its_own_neighbour(self):
        grid = make_grid(3, 3)
        grid[1][1] = HEAD
        self.assertEqual(count_head_neighbours(grid, 1, 1), 0)


class TestSignalTravel(unittest.TestCase):
    """A single electron on a plain wire: does it move one cell per tick,
    and does the head-tail pair stay exactly two cells long?"""

    def setUp(self):
        self.grid = parse_grid("@" + "#" * 9)

    def test_the_head_advances_one_cell_per_tick(self):
        grid = self.grid
        for tick in range(5):
            head_positions = [x for x, cell in enumerate(grid[0]) if cell == HEAD]
            self.assertEqual(head_positions, [tick])
            grid = step(grid)

    def test_the_tail_is_always_exactly_one_cell_behind_the_head(self):
        grid = step(self.grid)  # first step: head at 0 is gone, pair has formed
        for _tick in range(1, 6):
            row = grid[0]
            head_positions = [x for x, cell in enumerate(row) if cell == HEAD]
            tail_positions = [x for x, cell in enumerate(row) if cell == TAIL]
            self.assertEqual(len(head_positions), 1, row)
            self.assertEqual(len(tail_positions), 1, row)
            self.assertEqual(tail_positions[0], head_positions[0] - 1, row)
            grid = step(grid)

    def test_electron_count_is_two_while_travelling(self):
        grid = step(self.grid)
        for _ in range(6):
            self.assertEqual(electron_count(grid), 2)
            grid = step(grid)

    def test_the_pulse_dissipates_off_the_end_of_the_wire(self):
        grid = self.grid
        for _ in range(15):  # long enough to run off a 10-cell wire
            grid = step(grid)
        self.assertEqual(electron_count(grid), 0)
        self.assertTrue(all(cell == CONDUCTOR for cell in grid[0]))


class TestLoadAndSave(unittest.TestCase):
    def test_parse_then_format_round_trips(self):
        text = "@#~.\n.##."
        self.assertEqual(format_grid(parse_grid(text)), text)

    def test_short_rows_are_padded_with_empty(self):
        grid = parse_grid("##\n#")
        self.assertEqual(grid[1], ["#", EMPTY])

    def test_save_then_load_round_trips_through_a_file(self):
        grid = parse_grid("@#~.\n.##.")
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "circuit.txt")
            save(grid, path)
            self.assertEqual(load(path), grid)

    def test_saved_files_end_with_a_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "circuit.txt")
            save(parse_grid("@#"), path)
            self.assertTrue(Path(path).read_text().endswith("\n"))


class TestGridHelpers(unittest.TestCase):
    def test_make_grid_is_all_empty(self):
        grid = make_grid(4, 3)
        self.assertEqual(grid_size(grid), (4, 3))
        self.assertTrue(all(cell == EMPTY for row in grid for cell in row))

    def test_resize_larger_pads_with_empty(self):
        grid = parse_grid("##\n##")
        bigger = resize(grid, 4, 4)
        self.assertEqual(grid_size(bigger), (4, 4))
        self.assertEqual(bigger[0][:2], ["#", "#"])
        self.assertEqual(bigger[0][2:], [EMPTY, EMPTY])
        self.assertEqual(bigger[3], [EMPTY] * 4)

    def test_resize_smaller_crops(self):
        grid = parse_grid("####\n####\n####\n####")
        smaller = resize(grid, 2, 2)
        self.assertEqual(smaller, [["#", "#"], ["#", "#"]])

    def test_place_component_stamps_at_the_given_offset(self):
        base = make_grid(5, 5)
        component = parse_grid("@#")
        result = place_component(base, component, (2, 1))
        self.assertEqual(result[1][2], HEAD)
        self.assertEqual(result[1][3], CONDUCTOR)
        self.assertEqual(result[0][2], EMPTY)  # untouched elsewhere

    def test_place_component_clips_instead_of_raising(self):
        base = make_grid(3, 3)
        component = parse_grid("####")  # wider than the grid once offset
        result = place_component(base, component, (1, 0))
        self.assertEqual(grid_size(result), (3, 3))  # did not raise or resize
        self.assertEqual(result[0], [EMPTY, "#", "#"])

    def test_mirror_horizontal_reverses_each_row(self):
        grid = parse_grid("@#.\n.#~")
        mirrored = mirror_horizontal(grid)
        self.assertEqual(format_grid(mirrored), ".#@\n~#.")

    def test_mirroring_twice_is_the_identity(self):
        grid = parse_grid("@#.~\n.#~@")
        self.assertEqual(mirror_horizontal(mirror_horizontal(grid)), grid)


class TestClockGenerator(unittest.TestCase):
    """The clock ring is a closed loop with one electron chasing itself
    around it. Verified: it never runs down, and it repeats exactly."""

    def setUp(self):
        self.grid = COMPONENTS["clock"].grid

    def test_the_grid_repeats_with_a_period_of_16_ticks(self):
        frames = run(self.grid, 32)
        for tick in range(16):
            self.assertEqual(frames[tick], frames[tick + 16], f"tick {tick}")

    def test_the_ring_never_runs_down(self):
        # One head-tail pair circulates forever. It briefly becomes two while
        # the tap is firing (the tap carries its own short-lived pair off the
        # ring), so the bound is a range rather than an exact count -- but it
        # never reaches zero, and it never runs away either.
        frames = run(self.grid, 32)
        for frame in frames:
            self.assertTrue(2 <= electron_count(frame) <= 4)

    def test_the_tap_fires_once_per_period_not_zero_or_twice(self):
        tap = COMPONENTS["clock"].ports["tap"][0]
        x, y = tap
        frames = run(self.grid, 32)
        fired_ticks = [t for t, frame in enumerate(frames) if frame[y][x] == HEAD]
        # Exactly two occurrences per 16-tick period (16 and 32 excluded as
        # the window edges): the tap sees a HEAD for one tick each lap.
        self.assertEqual(len(fired_ticks), 2, fired_ticks)
        self.assertEqual(fired_ticks[1] - fired_ticks[0], 16)


class TestWire(unittest.TestCase):
    def test_the_library_wire_carries_a_signal_end_to_end(self):
        component = COMPONENTS["wire"]
        grid = component.grid
        in_x, in_y = component.ports["in"][0]
        out_x, out_y = component.ports["out"][0]
        grid[in_y][in_x] = HEAD
        frames = run(grid, 12)
        self.assertTrue(any(frame[out_y][out_x] == HEAD for frame in frames))


class TestGateTruthTables(unittest.TestCase):
    """Each gate's full truth table, produced by actually simulating the
    component rather than asserting on its shape. `gate_output` drives the
    named input ports to HEAD at tick 0 (as the module docstring's "set
    every input at tick 0" contract requires) and reports whether `out`
    ever fires within the settle window."""

    def test_or_gate_truth_table(self):
        gate = COMPONENTS["or"]
        expected = {
            frozenset(): False,
            frozenset({"in_a"}): True,
            frozenset({"in_b"}): True,
            frozenset({"in_a", "in_b"}): True,
        }
        for inputs, want in expected.items():
            with self.subTest(inputs=sorted(inputs)):
                self.assertEqual(gate_output(gate, set(inputs)), want)

    def test_and_not_gate_truth_table(self):
        gate = COMPONENTS["and_not"]
        expected = {
            frozenset(): False,
            frozenset({"in_a"}): True,
            frozenset({"in_b"}): False,
            frozenset({"in_a", "in_b"}): False,  # the inhibited case
        }
        for inputs, want in expected.items():
            with self.subTest(inputs=sorted(inputs)):
                self.assertEqual(gate_output(gate, set(inputs)), want)

    def test_xor_gate_truth_table(self):
        gate = COMPONENTS["xor"]
        expected = {
            frozenset(): False,
            frozenset({"in_a"}): True,
            frozenset({"in_b"}): True,
            frozenset({"in_a", "in_b"}): False,
        }
        for inputs, want in expected.items():
            with self.subTest(inputs=sorted(inputs)):
                self.assertEqual(gate_output(gate, set(inputs)), want)


class TestDiode(unittest.TestCase):
    """The diode passes every pulse one way and none the other, with no
    primer and no timing. Both orientations, since `diode_mirrored` is made
    by reflection rather than drawn a second time."""

    def test_every_forward_pulse_passes(self):
        d = COMPONENTS["diode"]
        self.assertEqual(pulses_through(d.grid, d.ports["in"], d.ports["out"], n=5), 5)

    def test_no_reverse_pulse_passes(self):
        d = COMPONENTS["diode"]
        self.assertEqual(pulses_through(d.grid, d.ports["out"], d.ports["in"], n=5), 0)

    def test_it_still_works_after_blocking(self):
        d = COMPONENTS["diode"]
        grid = run(_inject(d.grid, d.ports["out"]), 20)[-1]
        self.assertEqual(pulses_through(grid, d.ports["in"], d.ports["out"]), 3)

    def test_the_same_wire_without_the_blob_passes_both_ways(self):
        wire = parse_grid("#" * 12)
        self.assertEqual(pulses_through(wire, [(11, 0)], [(0, 0)]), 3)

    def test_mirrored_diode_passes_the_other_way(self):
        d = COMPONENTS["diode_mirrored"]
        self.assertEqual(pulses_through(d.grid, d.ports["in"], d.ports["out"]), 3)
        self.assertEqual(pulses_through(d.grid, d.ports["out"], d.ports["in"]), 0)


class TestComponentRegistry(unittest.TestCase):
    def test_every_component_parses_to_a_rectangular_grid(self):
        for name, component in COMPONENTS.items():
            with self.subTest(name=name):
                grid = component.grid
                width, _ = grid_size(grid)
                self.assertTrue(all(len(row) == width for row in grid))

    def test_every_port_cell_is_inside_the_component(self):
        for name, component in COMPONENTS.items():
            width, height = grid_size(component.grid)
            for port_name, cells in component.ports.items():
                for x, y in cells:
                    with self.subTest(component=name, port=port_name):
                        self.assertTrue(0 <= x < width)
                        self.assertTrue(0 <= y < height)

    def test_component_is_a_plain_dataclass_not_accidentally_shared(self):
        # Two different components should not somehow alias the same grid.
        self.assertIsNot(COMPONENTS["or"].grid, COMPONENTS["and_not"].grid)
        self.assertIsInstance(COMPONENTS["wire"], Component)


if __name__ == "__main__":
    unittest.main()
