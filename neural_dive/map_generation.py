"""
Map generation for Neural Dive game.
"""


def create_map(width: int, height: int, floor: int = 1) -> list[list[str]]:
    """
    Create a map with walls and floor tiles.

    Args:
        width: Map width in tiles
        height: Map height in tiles
        floor: Floor number (1-3), determines wall layout complexity

    Returns:
        2D list of tile characters
    """
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
    """Floor 1: Learning space with rooms and corridors"""
    # Horizontal wall across middle-top
    for x in range(20, 35):
        if x < width:
            tiles[10][x] = "#"

    # Vertical wall creating a room on the left
    for y in range(5, 15):
        if y < height:
            tiles[y][15] = "#"

    # Some pillars/obstacles
    if height > 18 and width > 30:
        tiles[18][30] = "#"
        tiles[18][31] = "#"
        tiles[17][30] = "#"

    # Small horizontal segment on right side
    for x in range(40, 46):
        if x < width:
            tiles[15][x] = "#"


def _draw_floor_2_walls(tiles: list[list[str]], width: int, height: int):
    """Floor 2: Security segmented space with corridors"""
    # Vertical wall
    for y in range(8, 18):
        if y < height:
            tiles[y][25] = "#"

    # Additional vertical wall creating corridors
    for y in range(5, 12):
        if y < height:
            tiles[y][35] = "#"

    # Horizontal walls to create more complexity
    for x in range(15, 25):
        if x < width:
            tiles[15][x] = "#"

    for x in range(30, 40):
        if x < width:
            tiles[20][x] = "#"

    # Small room in corner
    for x in range(10, 15):
        if x < width:
            tiles[8][x] = "#"

    for y in range(8, 12):
        if y < height:
            tiles[y][10] = "#"


def _draw_floor_3_walls(tiles: list[list[str]], width: int, height: int):
    """Floor 3: Advanced maze-like challenging layout"""
    # Horizontal walls
    for x in range(15, 40):
        if x < width:
            tiles[12][x] = "#"

    for x in range(25, 35):
        if x < width:
            tiles[8][x] = "#"

    # Vertical walls
    for y in range(5, 12):
        if y < height:
            tiles[y][35] = "#"

    for y in range(15, 22):
        if y < height:
            tiles[y][20] = "#"

    for y in range(8, 15):
        if y < height:
            tiles[y][10] = "#"

    # Additional maze sections
    for x in range(8, 18):
        if x < width:
            tiles[18][x] = "#"

    # Corner obstacles
    for x in range(42, 47):
        if x < width:
            tiles[10][x] = "#"
            tiles[17][x] = "#"
