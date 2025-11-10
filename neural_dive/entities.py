"""
Entity classes for Neural Dive game.
"""


class Entity:
    """A generic entity in the game (player, NPC, etc.)"""

    def __init__(self, x: int, y: int, char: str, color: str, name: str):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name

    def __repr__(self):
        return f"Entity(name={self.name}, pos=({self.x}, {self.y}))"


class Stairs:
    """Stairs to go up or down floors"""

    def __init__(self, x: int, y: int, direction: str):
        self.x = x
        self.y = y
        self.direction = direction  # "up" or "down"
        self.char = "<" if direction == "up" else ">"
        self.color = "yellow"

    def __repr__(self):
        return f"Stairs(direction={self.direction}, pos=({self.x}, {self.y}))"


class InfoTerminal:
    """Info terminal that displays hints or lore"""

    def __init__(self, x: int, y: int, title: str, content: list[str]):
        self.x = x
        self.y = y
        self.char = "T"
        self.color = "cyan"
        self.title = title
        self.content = content  # List of strings (paragraphs)

    def __repr__(self):
        return f"InfoTerminal(title={self.title}, pos=({self.x}, {self.y}))"


class Gate:
    """A locked gate that requires knowledge to pass"""

    def __init__(self, x: int, y: int, required_knowledge: str):
        self.x = x
        self.y = y
        self.char = "█"  # Block character
        self.color = "magenta"
        self.required_knowledge = required_knowledge  # Knowledge module needed
        self.unlocked = False

    def unlock(self):
        """Unlock the gate"""
        self.unlocked = True

    def __repr__(self):
        status = "unlocked" if self.unlocked else "locked"
        return f"Gate(requires={self.required_knowledge}, {status}, pos=({self.x}, {self.y}))"
