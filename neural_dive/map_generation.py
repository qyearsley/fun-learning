"""
Map generation for Neural Dive game.
"""

import random


def create_map(width: int, height: int, floor: int = 1, seed: int = None) -> list[list[str]]:
    """
    Create a map with walls and floor tiles.

    Args:
        width: Map width in tiles
        height: Map height in tiles
        floor: Floor number (1-3), determines wall layout complexity
        seed: Random seed for reproducible maps

    Returns:
        2D list of tile characters
    """
    if seed is not None:
        random.seed(seed)

    tiles = [[" " for _ in range(width)] for _ in range(height)]

    # Draw outer walls
    for x in range(width):
        tiles[0][x] = "#"
        tiles[height - 1][x] = "#"
    for y in range(height):
        tiles[y][0] = "#"
        tiles[y][width - 1] = "#"

    # Draw interior walls based on floor
    _draw_floor_walls(tiles, width, height, floor)

    # Fill empty spaces with floor tiles
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if tiles[y][x] != "#":
                tiles[y][x] = "."

    return tiles


def _draw_floor_walls(tiles: list[list[str]], width: int, height: int, floor: int):
    """Draw interior walls based on floor number"""

    if floor == 1:
        _draw_floor_1_walls(tiles, width, height)
    elif floor == 2:
        _draw_floor_2_walls(tiles, width, height)
    elif floor == 3:
        _draw_floor_3_walls(tiles, width, height)


def _draw_floor_1_walls(tiles: list[list[str]], width: int, height: int):
    """Floor 1: Open learning space with edge-attached walls and scattered pillars"""

    # Vertical wall extending from left edge (creates a small room)
    wall_length = random.randint(8, 12)
    wall_start_y = random.randint(5, 10)
    for y in range(wall_start_y, min(wall_start_y + wall_length, height - 2)):
        tiles[y][12] = "#"

    # Horizontal wall extending from top edge
    wall_length = random.randint(8, 15)
    wall_start_x = random.randint(18, 25)
    for x in range(wall_start_x, min(wall_start_x + wall_length, width - 2)):
        tiles[8][x] = "#"

    # Wall extending from right edge
    wall_length = random.randint(6, 10)
    wall_start_y = random.randint(12, 16)
    for y in range(wall_start_y, min(wall_start_y + wall_length, height - 2)):
        tiles[y][width - 8] = "#"

    # Scattered pillars (small 1-2 tile obstacles)
    num_pillars = random.randint(2, 4)
    for _ in range(num_pillars):
        px = random.randint(width // 3, 2 * width // 3)
        py = random.randint(height // 3, 2 * height // 3)
        if tiles[py][px] == " ":
            tiles[py][px] = "#"
            # Maybe add a second tile
            if random.random() < 0.5 and px + 1 < width - 1:
                tiles[py][px + 1] = "#"


def _draw_floor_2_walls(tiles: list[list[str]], width: int, height: int):
    """Floor 2: Security segmented space with edge-connected corridors"""

    # Vertical wall from top creating a corridor
    wall_length = random.randint(10, 15)
    wall_x = random.randint(width // 3, width // 2)
    for y in range(1, min(wall_length + 1, height - 2)):
        tiles[y][wall_x] = "#"

    # Horizontal wall from left
    wall_length = random.randint(12, 18)
    wall_y = random.randint(height // 3, 2 * height // 3)
    for x in range(1, min(wall_length + 1, width - 2)):
        tiles[wall_y][x] = "#"

    # Vertical wall from bottom
    wall_length = random.randint(8, 12)
    wall_x = random.randint(2 * width // 3, width - 10)
    for y in range(max(height - wall_length - 1, 1), height - 1):
        tiles[y][wall_x] = "#"

    # L-shaped wall in corner (attached to two edges)
    corner_size = random.randint(4, 7)
    corner_x = width - corner_size - 2
    corner_y = random.randint(5, 10)
    # Vertical part
    for y in range(corner_y, min(corner_y + corner_size, height - 2)):
        tiles[y][corner_x] = "#"
    # Horizontal part
    for x in range(corner_x, width - 1):
        tiles[corner_y][x] = "#"

    # Scattered obstacles
    num_obstacles = random.randint(3, 5)
    for _ in range(num_obstacles):
        px = random.randint(15, width - 15)
        py = random.randint(8, height - 8)
        if tiles[py][px] == " ":
            tiles[py][px] = "#"


def _draw_floor_3_walls(tiles: list[list[str]], width: int, height: int):
    """Floor 3: Advanced challenging layout with edge-attached maze sections"""

    # Multiple walls extending from edges to create maze-like feel

    # From left edge
    wall1_length = random.randint(10, 16)
    wall1_y = random.randint(6, 12)
    for x in range(1, min(wall1_length + 1, width - 2)):
        tiles[wall1_y][x] = "#"

    # From right edge
    wall2_length = random.randint(10, 16)
    wall2_y = random.randint(height // 2, height - 8)
    for x in range(max(width - wall2_length - 1, 1), width - 1):
        tiles[wall2_y][x] = "#"

    # From top edge - zigzag pattern
    wall3_x = random.randint(width // 4, width // 3)
    wall3_length = random.randint(8, 12)
    for y in range(1, min(wall3_length + 1, height - 2)):
        tiles[y][wall3_x] = "#"
        # Zigzag
        if y % 3 == 0 and wall3_x + 2 < width - 1:
            tiles[y][wall3_x + 1] = "#"
            tiles[y][wall3_x + 2] = "#"

    # From bottom edge
    wall4_x = random.randint(2 * width // 3, width - 12)
    wall4_length = random.randint(8, 12)
    for y in range(max(height - wall4_length - 1, 1), height - 1):
        tiles[y][wall4_x] = "#"

    # Corner obstacles (attached to two edges)
    # Top-right corner
    corner_size = random.randint(3, 5)
    for i in range(corner_size):
        tiles[1 + i][width - 2] = "#"
        tiles[1][width - 2 - i] = "#"

    # Bottom-left corner
    corner_size = random.randint(3, 5)
    for i in range(corner_size):
        tiles[height - 2 - i][1] = "#"
        tiles[height - 2][1 + i] = "#"

    # Scattered pillars for additional challenge
    num_pillars = random.randint(4, 7)
    for _ in range(num_pillars):
        px = random.randint(width // 4, 3 * width // 4)
        py = random.randint(height // 4, 3 * height // 4)
        if tiles[py][px] == " ":
            tiles[py][px] = "#"
            # Small cluster
            if random.random() < 0.3:
                for dx, dy in [(1, 0), (0, 1), (1, 1)]:
                    if px + dx < width - 1 and py + dy < height - 1:
                        if tiles[py + dy][px + dx] == " " and random.random() < 0.5:
                            tiles[py + dy][px + dx] = "#"
