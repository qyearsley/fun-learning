"""
Enumerations for Neural Dive game.
"""

from enum import Enum


class NPCType(Enum):
    """Different types of NPCs with different behaviors"""

    SPECIALIST = "specialist"  # Standard quiz NPC
    HELPER = "helper"  # Gives hints, restores coherence
    ENEMY = "enemy"  # Hostile, harsher penalties
    QUEST = "quest"  # Gives quests to find other NPCs
