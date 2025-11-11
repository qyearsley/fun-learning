"""
Configuration constants for Neural Dive game.
Centralizes magic numbers for easy tuning.
"""

# Game dimensions
DEFAULT_MAP_WIDTH = 50
DEFAULT_MAP_HEIGHT = 25
MAX_FLOORS = 3

# Player stats
STARTING_COHERENCE = 80
MAX_COHERENCE = 100

# Conversation rewards and penalties
CORRECT_ANSWER_COHERENCE_GAIN = 8
WRONG_ANSWER_COHERENCE_PENALTY = 30
ENEMY_WRONG_ANSWER_PENALTY = 45
HELPER_COHERENCE_RESTORE = 15
QUEST_COMPLETION_COHERENCE_BONUS = 50

# Player starting position
PLAYER_START_X = 5
PLAYER_START_Y = 5

# Stairs positions (used when descending/ascending)
STAIRS_DOWN_DEFAULT_X = 45
STAIRS_DOWN_DEFAULT_Y = 20
STAIRS_UP_DEFAULT_X = 10
STAIRS_UP_DEFAULT_Y = 5

# NPC placement
NPC_MIN_DISTANCE_FROM_PLAYER = 5
NPC_PLACEMENT_ATTEMPTS = 100

# Terminal placement
TERMINAL_PLACEMENT_ATTEMPTS = 50
TERMINAL_X_OFFSET = 3
TERMINAL_Y_OFFSET = 3
TERMINAL_X_BONUS = 5
TERMINAL_Y_BONUS = 5

# Gate placement
GATE_PLACEMENT_ATTEMPTS = 20
GATE_X_OFFSET = 3
GATE_Y_OFFSET = 3

# Rendering
OVERLAY_MAX_WIDTH = 80  # Increased from 60 for better readability
OVERLAY_MAX_HEIGHT = 30  # Increased from 25
COMPLETION_OVERLAY_MAX_HEIGHT = 35  # Increased from 30
UI_BOTTOM_OFFSET = 4

# Floor completion requirements
FLOOR_REQUIRED_NPCS = {
    1: {"ALGO_SPIRIT", "HEAP_MASTER", "PATTERN_ARCHITECT"},
    2: {"WEB_ARCHITECT", "CRYPTO_GUARDIAN", "SYSTEM_CORE", "SCALE_MASTER"},
    3: set(),  # No requirements for final floor - boss rush with optional NPCs
}

# Quest system
QUEST_TARGET_NPCS = {
    "ALGO_SPIRIT",
    "NET_DAEMON",
    "COMPILER_SAGE",
    "DB_GUARDIAN",
}

# NPC Wandering System
# NPCs alternate between idle and wander states for natural movement
NPC_WANDER_ENABLED = True  # Set to False to disable all NPC movement
NPC_IDLE_TICKS_MIN = 5  # Minimum ticks to stay idle
NPC_IDLE_TICKS_MAX = 10  # Maximum ticks to stay idle
NPC_WANDER_TICKS_MIN = 3  # Minimum ticks to wander
NPC_WANDER_TICKS_MAX = 7  # Maximum ticks to wander
NPC_WANDER_RADIUS = 8  # Maximum distance from spawn point before returning home

# NPC movement speeds by type (ticks between moves, lower = faster)
NPC_MOVEMENT_SPEEDS = {
    "specialist": 5,  # Slow, focused scholars
    "helper": 3,  # Moderate speed, approachable helpers
    "enemy": 3,  # Moderate speed, threatening
    "quest": 999,  # Effectively stationary (important quest givers)
}

# Theme and visual settings
DEFAULT_THEME = "cyberpunk"  # Available: "cyberpunk", "classic"
DEFAULT_BACKGROUND = "dark"  # "dark" or "light" terminal background
