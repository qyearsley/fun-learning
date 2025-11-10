"""
Neural Dive - A cyberpunk roguelike with CS conversations.

Renders directly in your terminal. Learn computer science concepts
by conversing with NPCs across multiple neural layers.
"""

__version__ = "1.0.0"
__author__ = "Neural Dive Team"

# Expose key classes for easy imports
from neural_dive.game import Game
from neural_dive.enums import NPCType
from neural_dive.models import Question, Answer, Conversation
from neural_dive.entities import Entity, Stairs, InfoTerminal, Gate

__all__ = [
    "Game",
    "NPCType",
    "Question",
    "Answer",
    "Conversation",
    "Entity",
    "Stairs",
    "InfoTerminal",
    "Gate",
]
