"""
Theme system for Neural Dive.

Defines visual themes with support for light and dark terminal backgrounds.
Uses widely-supported Unicode characters for maximum compatibility.
"""

from dataclasses import dataclass


@dataclass
class ColorScheme:
    """Color scheme for a specific terminal background mode."""

    # Entity colors
    player: str
    npc_specialist: str
    npc_helper: str
    npc_enemy: str
    npc_quest: str

    # Environment colors
    wall: str
    floor: str
    stairs: str
    terminal: str
    gate: str

    # UI colors
    ui_primary: str
    ui_secondary: str
    ui_accent: str
    ui_warning: str
    ui_error: str
    ui_success: str


@dataclass
class CharacterSet:
    """Character glyphs used for rendering."""

    # Entities
    player: str
    npc_default: str  # Fallback if no specific char defined
    stairs_up: str
    stairs_down: str
    terminal: str
    gate_locked: str
    gate_unlocked: str

    # Environment
    wall: str
    floor: str
    wall_alt: str  # For variety/pattern

    # UI
    separator: str


@dataclass
class Theme:
    """Complete theme with characters and color schemes."""

    name: str
    characters: CharacterSet
    dark_colors: ColorScheme
    light_colors: ColorScheme


# ============================================================================
# CHARACTER SETS
# ============================================================================

# Unicode Box Drawing - Cyberpunk style
# Uses widely-supported characters from Unicode blocks:
# - Box Drawing (U+2500-U+257F)
# - Geometric Shapes (U+25A0-U+25FF)
CYBERPUNK_CHARS = CharacterSet(
    # Entities - geometric shapes for visibility
    player="◆",  # U+25C6 Black Diamond
    npc_default="◇",  # U+25C7 White Diamond
    stairs_up="▲",  # U+25B2 Black Up-Pointing Triangle
    stairs_down="▼",  # U+25BC Black Down-Pointing Triangle
    terminal="▣",  # U+25A3 White Square with Horizontal Fill
    gate_locked="█",  # U+2588 Full Block
    gate_unlocked="▒",  # U+2592 Medium Shade
    # Environment - box drawing for walls
    wall="█",  # U+2588 Full Block
    floor="·",  # U+00B7 Middle Dot (very widely supported)
    wall_alt="▓",  # U+2593 Dark Shade (for variety if needed)
    # UI
    separator="─",  # U+2500 Box Drawing Light Horizontal
)

# Classic roguelike style (ASCII-safe fallback)
CLASSIC_CHARS = CharacterSet(
    player="@",
    npc_default="N",
    stairs_up="<",
    stairs_down=">",
    terminal="T",
    gate_locked="#",
    gate_unlocked="+",
    wall="#",
    floor=".",
    wall_alt="#",
    separator="-",
)


# ============================================================================
# COLOR SCHEMES - CYBERPUNK
# ============================================================================

# Dark mode - neon colors on dark background
CYBERPUNK_DARK = ColorScheme(
    # Entities - bright neon colors
    player="bright_green",  # Electric green
    npc_specialist="bright_magenta",  # Neon magenta
    npc_helper="bright_cyan",  # Bright cyan
    npc_enemy="bright_red",  # Danger red
    npc_quest="bright_yellow",  # Important yellow
    # Environment - darker tones for depth
    wall="blue",  # Dark blue walls
    floor="cyan",  # Subtle cyan floor
    stairs="yellow",  # Visible stairs
    terminal="cyan",  # Info terminals
    gate="magenta",  # Locked gates
    # UI - high contrast
    ui_primary="white",
    ui_secondary="cyan",
    ui_accent="bright_magenta",
    ui_warning="yellow",
    ui_error="red",
    ui_success="green",
)

# Light mode - darker colors on light background
CYBERPUNK_LIGHT = ColorScheme(
    # Entities - darker but still vibrant
    player="green",  # Rich green
    npc_specialist="magenta",  # Deep magenta
    npc_helper="blue",  # Deep blue for visibility
    npc_enemy="red",  # Strong red
    npc_quest="blue",  # Dark blue instead of yellow
    # Environment - visible on light
    wall="blue",  # Blue walls
    floor="blue",  # Subtle blue floor
    stairs="magenta",  # Visible stairs
    terminal="blue",  # Info terminals
    gate="magenta",  # Locked gates
    # UI - readable on light
    ui_primary="black",
    ui_secondary="blue",
    ui_accent="magenta",
    ui_warning="red",  # Red instead of yellow for visibility
    ui_error="red",
    ui_success="green",
)


# ============================================================================
# COLOR SCHEMES - CLASSIC
# ============================================================================

CLASSIC_DARK = ColorScheme(
    player="bright_white",
    npc_specialist="bright_magenta",
    npc_helper="bright_green",
    npc_enemy="bright_red",
    npc_quest="bright_yellow",
    wall="blue",  # Darker blue walls, not white
    floor="cyan",  # Subtle cyan floor, not white
    stairs="bright_yellow",
    terminal="bright_cyan",
    gate="magenta",
    ui_primary="white",
    ui_secondary="cyan",
    ui_accent="yellow",
    ui_warning="yellow",
    ui_error="red",
    ui_success="green",
)

CLASSIC_LIGHT = ColorScheme(
    player="black",
    npc_specialist="magenta",
    npc_helper="green",
    npc_enemy="red",
    npc_quest="blue",  # Blue instead of yellow for readability
    wall="black",
    floor="blue",  # Subtle blue instead of black
    stairs="magenta",  # Magenta instead of yellow
    terminal="blue",  # Blue instead of cyan
    gate="magenta",
    ui_primary="black",
    ui_secondary="blue",
    ui_accent="magenta",
    ui_warning="red",  # Red instead of yellow
    ui_error="red",
    ui_success="green",
)


# ============================================================================
# THEME DEFINITIONS
# ============================================================================

THEMES: dict[str, Theme] = {
    "cyberpunk": Theme(
        name="Cyberpunk",
        characters=CYBERPUNK_CHARS,
        dark_colors=CYBERPUNK_DARK,
        light_colors=CYBERPUNK_LIGHT,
    ),
    "classic": Theme(
        name="Classic Roguelike",
        characters=CLASSIC_CHARS,
        dark_colors=CLASSIC_DARK,
        light_colors=CLASSIC_LIGHT,
    ),
}

# Default theme
DEFAULT_THEME = "cyberpunk"
DEFAULT_BACKGROUND = "dark"


def get_theme(
    theme_name: str = DEFAULT_THEME, background: str = DEFAULT_BACKGROUND
) -> tuple[CharacterSet, ColorScheme]:
    """
    Get character set and color scheme for the specified theme and background.

    Args:
        theme_name: Name of the theme ("cyberpunk", "classic")
        background: Background mode ("dark" or "light")

    Returns:
        Tuple of (CharacterSet, ColorScheme)
    """
    theme_name = theme_name.lower()
    background = background.lower()

    if theme_name not in THEMES:
        theme_name = DEFAULT_THEME

    theme = THEMES[theme_name]
    colors = theme.dark_colors if background == "dark" else theme.light_colors

    return theme.characters, colors


def list_themes() -> list[str]:
    """Get list of available theme names."""
    return list(THEMES.keys())
