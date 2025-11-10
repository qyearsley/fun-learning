"""
Unit tests for map generation and entities.
"""

import unittest
from neural_dive.map_generation import create_map
from neural_dive.entities import Entity, Stairs, InfoTerminal, Gate


class TestMapGeneration(unittest.TestCase):
    """Test map generation"""

    def test_create_map_dimensions(self):
        """Test that map has correct dimensions"""
        width, height = 50, 25
        game_map = create_map(width, height, floor=1)

        self.assertEqual(len(game_map), height)
        self.assertEqual(len(game_map[0]), width)

    def test_map_has_walls(self):
        """Test that map has outer walls"""
        game_map = create_map(50, 25, floor=1)

        # Check top and bottom walls
        for x in range(50):
            self.assertEqual(game_map[0][x], "#")
            self.assertEqual(game_map[24][x], "#")

        # Check left and right walls
        for y in range(25):
            self.assertEqual(game_map[y][0], "#")
            self.assertEqual(game_map[y][49], "#")

    def test_map_has_floor_tiles(self):
        """Test that map has floor tiles"""
        game_map = create_map(50, 25, floor=1)

        # Should have at least some floor tiles
        floor_count = sum(
            1 for row in game_map for tile in row if tile == "."
        )
        self.assertGreater(floor_count, 0)

    def test_different_floors_have_different_layouts(self):
        """Test that different floors have different wall layouts"""
        map1 = create_map(50, 25, floor=1)
        map2 = create_map(50, 25, floor=2)
        map3 = create_map(50, 25, floor=3)

        # Count wall tiles in each (excluding outer walls)
        def count_interior_walls(m):
            return sum(
                1
                for y in range(1, 24)
                for x in range(1, 49)
                if m[y][x] == "#"
            )

        walls1 = count_interior_walls(map1)
        walls2 = count_interior_walls(map2)
        walls3 = count_interior_walls(map3)

        # Floor 3 should have more walls (most complex)
        self.assertGreater(walls3, walls1)


class TestEntity(unittest.TestCase):
    """Test Entity class"""

    def test_entity_creation(self):
        """Test creating an entity"""
        entity = Entity(x=10, y=5, char="@", color="cyan", name="Player")

        self.assertEqual(entity.x, 10)
        self.assertEqual(entity.y, 5)
        self.assertEqual(entity.char, "@")
        self.assertEqual(entity.color, "cyan")
        self.assertEqual(entity.name, "Player")

    def test_entity_repr(self):
        """Test entity string representation"""
        entity = Entity(x=10, y=5, char="@", color="cyan", name="Player")
        repr_str = repr(entity)

        self.assertIn("Player", repr_str)
        self.assertIn("10", repr_str)
        self.assertIn("5", repr_str)


class TestStairs(unittest.TestCase):
    """Test Stairs class"""

    def test_stairs_down(self):
        """Test creating down stairs"""
        stairs = Stairs(x=10, y=5, direction="down")

        self.assertEqual(stairs.x, 10)
        self.assertEqual(stairs.y, 5)
        self.assertEqual(stairs.direction, "down")
        self.assertEqual(stairs.char, ">")
        self.assertEqual(stairs.color, "yellow")

    def test_stairs_up(self):
        """Test creating up stairs"""
        stairs = Stairs(x=10, y=5, direction="up")

        self.assertEqual(stairs.direction, "up")
        self.assertEqual(stairs.char, "<")


class TestInfoTerminal(unittest.TestCase):
    """Test InfoTerminal class"""

    def test_terminal_creation(self):
        """Test creating an info terminal"""
        content = ["Line 1", "Line 2", "Line 3"]
        terminal = InfoTerminal(x=10, y=5, title="Test Terminal", content=content)

        self.assertEqual(terminal.x, 10)
        self.assertEqual(terminal.y, 5)
        self.assertEqual(terminal.title, "Test Terminal")
        self.assertEqual(len(terminal.content), 3)
        self.assertEqual(terminal.char, "T")
        self.assertEqual(terminal.color, "cyan")


class TestGate(unittest.TestCase):
    """Test Gate class"""

    def test_gate_creation(self):
        """Test creating a gate"""
        gate = Gate(x=10, y=5, required_knowledge="binary_search")

        self.assertEqual(gate.x, 10)
        self.assertEqual(gate.y, 5)
        self.assertEqual(gate.required_knowledge, "binary_search")
        self.assertFalse(gate.unlocked)
        self.assertEqual(gate.char, "█")
        self.assertEqual(gate.color, "magenta")

    def test_gate_unlock(self):
        """Test unlocking a gate"""
        gate = Gate(x=10, y=5, required_knowledge="binary_search")

        self.assertFalse(gate.unlocked)
        gate.unlock()
        self.assertTrue(gate.unlocked)

    def test_gate_repr(self):
        """Test gate string representation"""
        gate = Gate(x=10, y=5, required_knowledge="binary_search")

        repr_str = repr(gate)
        self.assertIn("binary_search", repr_str)
        self.assertIn("locked", repr_str)

        gate.unlock()
        repr_str = repr(gate)
        self.assertIn("unlocked", repr_str)


if __name__ == "__main__":
    unittest.main()
