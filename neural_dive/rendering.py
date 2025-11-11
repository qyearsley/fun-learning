"""
Terminal rendering for Neural Dive.
Uses blessed library for terminal control.
"""

import sys
from typing import TYPE_CHECKING

from neural_dive.config import (
    COMPLETION_OVERLAY_MAX_HEIGHT,
    OVERLAY_MAX_HEIGHT,
    OVERLAY_MAX_WIDTH,
    UI_BOTTOM_OFFSET,
)
from neural_dive.conversation import wrap_text
from neural_dive.themes import CharacterSet, ColorScheme

if TYPE_CHECKING:
    from blessed import Terminal

    from neural_dive.game import Game


def draw_game(
    term: "Terminal",
    game: "Game",
    chars: CharacterSet,
    colors: ColorScheme,
    redraw_all: bool = False,
):
    """
    Draw the entire game state.

    Args:
        term: Blessed Terminal instance
        game: Game instance
        chars: Character set for rendering
        colors: Color scheme for rendering
        redraw_all: Whether to redraw everything (first draw or after floor change)
    """
    if redraw_all:
        # Clear screen on first draw or floor change
        print(term.home + term.clear, end="")

        # Draw map
        _draw_map(term, game, chars, colors)
    else:
        # Clear old player position
        _clear_old_player_position(term, game, chars, colors)

        # Clear old NPC positions
        _clear_old_npc_positions(term, game, chars, colors)

    # Draw all entities
    _draw_entities(term, game, chars, colors)

    # Draw UI at bottom
    _draw_ui(term, game, colors)

    # Draw overlays if active
    if game.active_conversation or (
        hasattr(game, "_last_answer_response") and game._last_answer_response
    ):
        draw_conversation_overlay(term, game, colors)

    if game.active_terminal:
        draw_terminal_overlay(term, game, colors)

    sys.stdout.flush()


def _draw_map(term: "Terminal", game: "Game", chars: CharacterSet, colors: ColorScheme):
    """Draw the game map"""
    for y in range(len(game.game_map)):
        for x in range(len(game.game_map[0])):
            char = game.game_map[y][x]
            if char == "#":
                color_func = getattr(term, f"bold_{colors.wall}", term.bold_blue)
                print(term.move_xy(x, y) + color_func(chars.wall), end="")
            elif char == ".":
                color_func = getattr(term, colors.floor, term.cyan)
                print(term.move_xy(x, y) + color_func(chars.floor), end="")


def _clear_old_player_position(
    term: "Terminal", game: "Game", chars: CharacterSet, colors: ColorScheme
):
    """Clear the old player position"""
    if game.old_player_pos:
        old_x, old_y = game.old_player_pos
        char = game.game_map[old_y][old_x]
        if char == ".":
            color_func = getattr(term, colors.floor, term.cyan)
            print(term.move_xy(old_x, old_y) + color_func(chars.floor), end="")


def _clear_old_npc_positions(
    term: "Terminal", game: "Game", chars: CharacterSet, colors: ColorScheme
):
    """Clear old NPC positions"""
    for npc_name, (old_x, old_y) in game.old_npc_positions.items():
        # Check if position is still occupied by any entity
        occupied = False

        # Check if player is there
        if game.player.x == old_x and game.player.y == old_y:
            occupied = True

        # Check if any NPC is there
        if not occupied:
            for npc in game.npcs:
                if npc.x == old_x and npc.y == old_y:
                    occupied = True
                    break

        # Check if any terminal is there
        if not occupied:
            for terminal in game.terminals:
                if terminal.x == old_x and terminal.y == old_y:
                    occupied = True
                    break

        # Check if any stairs are there
        if not occupied:
            for stair in game.stairs:
                if stair.x == old_x and stair.y == old_y:
                    occupied = True
                    break

        # If not occupied, redraw the floor tile
        if not occupied:
            char = game.game_map[old_y][old_x]
            if char == ".":
                color_func = getattr(term, colors.floor, term.cyan)
                print(term.move_xy(old_x, old_y) + color_func(chars.floor), end="")
            elif char == "#":
                color_func = getattr(term, f"bold_{colors.wall}", term.bold_blue)
                print(term.move_xy(old_x, old_y) + color_func(chars.wall), end="")

    # Clear the tracking dictionary after processing
    game.old_npc_positions.clear()


def _draw_entities(term: "Terminal", game: "Game", chars: CharacterSet, colors: ColorScheme):
    """Draw all game entities (NPCs, terminals, gates, stairs, player)"""
    from neural_dive.config import FLOOR_REQUIRED_NPCS

    # Get required NPCs for current floor
    required_npcs = FLOOR_REQUIRED_NPCS.get(game.current_floor, set())

    # Draw NPCs
    for npc in game.npcs:
        # Check if this is a required NPC
        is_required = npc.name in required_npcs

        # Get color based on NPC type
        npc_type = npc.npc_type or "specialist"
        if npc_type == "specialist":
            color_name = colors.npc_specialist
        elif npc_type == "helper":
            color_name = colors.npc_helper
        elif npc_type == "enemy":
            color_name = colors.npc_enemy
        elif npc_type == "quest":
            color_name = colors.npc_quest
        else:
            color_name = colors.npc_specialist

        # Use bold for required NPCs, bright_ prefix if available
        if is_required:
            # Try bright variant first for required NPCs
            bright_color = (
                f"bright_{color_name}" if not color_name.startswith("bright_") else color_name
            )
            npc_color = getattr(
                term, f"bold_{bright_color}", getattr(term, f"bold_{color_name}", term.bold_magenta)
            )
        else:
            # Regular bold for optional NPCs
            npc_color = getattr(term, f"bold_{color_name}", term.bold_magenta)

        print(term.move_xy(npc.x, npc.y) + npc_color(npc.char), end="")

    # Draw terminals
    for terminal in game.terminals:
        terminal_color = getattr(term, f"bold_{colors.terminal}", term.bold_cyan)
        print(term.move_xy(terminal.x, terminal.y) + terminal_color(chars.terminal), end="")

    # Draw stairs
    for stair in game.stairs:
        stair_char = chars.stairs_up if stair.direction == "up" else chars.stairs_down
        stair_color = getattr(term, f"bold_{colors.stairs}", term.bold_yellow)
        print(term.move_xy(stair.x, stair.y) + stair_color(stair_char), end="")

    # Draw player
    player_color = getattr(term, f"bold_{colors.player}", term.bold_green)
    print(
        term.move_xy(game.player.x, game.player.y) + player_color(chars.player),
        end="",
    )


def _draw_ui(term: "Terminal", game: "Game", colors: ColorScheme):
    """Draw the UI panel at the bottom"""
    ui_y = term.height - UI_BOTTOM_OFFSET

    # Separator line
    ui_color = getattr(term, f"bold_{colors.ui_primary}", term.bold)
    print(term.move_xy(0, ui_y) + ui_color("─" * min(term.width, 80)), end="")

    # Status line
    coherence_pct = int((game.coherence / game.max_coherence) * 100)
    knowledge_count = len(game.knowledge_modules)
    status_line = f"Neural Layer {game.current_floor}/{game.max_floors} | Coherence: {coherence_pct}% | Knowledge: {knowledge_count}"
    print(term.move_xy(2, ui_y + 1) + ui_color(status_line), end="")

    # Message line
    print(term.move_xy(2, ui_y + 2) + " " * (term.width - 4), end="")
    msg_color = getattr(term, f"bold_{colors.ui_warning}", term.bold_yellow)
    print(
        term.move_xy(2, ui_y + 2) + msg_color(game.message[: term.width - 4]),
        end="",
    )

    # Instructions
    if game.active_conversation:
        print(
            term.move_xy(0, term.height - 1) + term.normal + "In conversation - see overlay above",
            end="",
        )
    else:
        print(
            term.move_xy(0, term.height - 1)
            + term.normal
            + "Move: Arrows | Interact: Space/Enter | Stairs: >/< | Q: Quit",
            end="",
        )


def draw_conversation_overlay(term: "Terminal", game: "Game", colors: ColorScheme):
    """Draw conversation overlay panel"""
    conv = game.active_conversation

    # If no active conversation, check if we have a completion response to show
    if not conv:
        if hasattr(game, "_last_answer_response") and game._last_answer_response:
            draw_completion_overlay(term, game, colors)
        return

    # Calculate overlay dimensions (centered)
    overlay_width = min(OVERLAY_MAX_WIDTH, term.width - 4)
    overlay_height = min(OVERLAY_MAX_HEIGHT, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end="")

    # Draw border
    _draw_overlay_border(term, start_x, start_y, overlay_width, overlay_height, colors.ui_secondary)

    # NPC name header
    header = f" {conv.npc_name} "
    header_color = getattr(term, f"bold_{colors.ui_accent}", term.bold_magenta)
    print(term.move_xy(start_x + 2, start_y) + header_color(header), end="")

    current_y = start_y + 2

    # If showing greeting
    if hasattr(game, "_show_greeting") and game._show_greeting:
        lines = wrap_text(conv.greeting, overlay_width - 4)
        for line in lines:
            if current_y < start_y + overlay_height - 2:
                print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
                current_y += 1
        current_y += 1

        if current_y < start_y + overlay_height - 2:
            error_color = getattr(term, f"bold_{colors.ui_error}", term.bold_red)
            print(
                term.move_xy(start_x + 2, current_y) + error_color("[Press any key to continue]"),
                end="",
            )
        return

    # Check if we have a pending response to show
    if hasattr(game, "_last_answer_response") and game._last_answer_response:
        _draw_response(
            term, game, start_x, start_y, current_y, overlay_width, overlay_height, colors
        )
        return

    # Show current question
    if conv.current_question_idx < len(conv.questions):
        _draw_question(
            term, conv, start_x, start_y, current_y, overlay_width, overlay_height, colors
        )


def _draw_response(
    term, game, start_x, start_y, current_y, overlay_width, overlay_height, colors: ColorScheme
):
    """Draw response to answer"""
    response_text = game._last_answer_response

    # Check if this is a completion response
    is_completion = "CONVERSATION COMPLETE" in response_text

    if not is_completion:
        # Normal response - draw separator line
        separator = "─" * (overlay_width - 4)
        sep_color = getattr(term, f"bold_{colors.ui_secondary}", term.bold_blue)
        print(term.move_xy(start_x + 2, current_y) + sep_color(separator), end="")
        current_y += 1

        # Show "RESPONSE:" header
        success_color = getattr(term, f"bold_{colors.ui_success}", term.bold_green)
        print(term.move_xy(start_x + 2, current_y) + success_color("RESPONSE:"), end="")
        current_y += 2

    # Show response text
    lines = wrap_text(response_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 3:
            print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
            current_y += 1
    current_y += 1

    if current_y < start_y + overlay_height - 2:
        error_color = getattr(term, f"bold_{colors.ui_error}", term.bold_red)
        print(
            term.move_xy(start_x + 2, current_y) + error_color("[Press any key to continue]"),
            end="",
        )


def _draw_question(
    term, conv, start_x, start_y, current_y, overlay_width, overlay_height, colors: ColorScheme
):
    """Draw current question and answers"""
    question = conv.questions[conv.current_question_idx]

    # Question text
    q_text = f"Q{conv.current_question_idx + 1}/{len(conv.questions)}: {question.question_text}"
    lines = wrap_text(q_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 4:
            print(term.move_xy(start_x + 2, current_y) + term.bold_black(line), end="")
            current_y += 1

    current_y += 1

    # Answer choices
    for i, answer in enumerate(question.answers):
        if current_y < start_y + overlay_height - 2:
            choice_text = f"{i + 1}. {answer.text}"
            lines = wrap_text(choice_text, overlay_width - 4)
            for line in lines:
                if current_y < start_y + overlay_height - 2:
                    print(
                        term.move_xy(start_x + 2, current_y) + term.blue(line),
                        end="",
                    )
                    current_y += 1

    # Instructions at bottom
    error_color = getattr(term, f"bold_{colors.ui_error}", term.bold_red)
    print(
        term.move_xy(start_x + 2, start_y + overlay_height - 2)
        + error_color("Press 1-4 to answer | ESC to exit"),
        end="",
    )


def draw_completion_overlay(term: "Terminal", game: "Game", colors: ColorScheme):
    """Draw completion message overlay when conversation is complete"""
    response_text = game._last_answer_response

    # Calculate overlay dimensions (centered, larger for completion)
    overlay_width = min(OVERLAY_MAX_WIDTH, term.width - 4)
    overlay_height = min(COMPLETION_OVERLAY_MAX_HEIGHT, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end="")

    # Draw border
    _draw_overlay_border(term, start_x, start_y, overlay_width, overlay_height, colors.ui_success)

    current_y = start_y + 2

    # Big completion banner at top - REMOVED per user request
    # (No longer showing "CONVERSATION COMPLETE" banner)

    # Show response text directly
    lines = wrap_text(response_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 3:
            print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
            current_y += 1
    current_y += 1

    # Instructions at bottom
    if current_y < start_y + overlay_height - 2:
        error_color = getattr(term, f"bold_{colors.ui_error}", term.bold_red)
        print(
            term.move_xy(start_x + 2, current_y) + error_color("[Press any key to continue]"),
            end="",
        )


def draw_terminal_overlay(term: "Terminal", game: "Game", colors: ColorScheme):
    """Draw terminal info overlay"""
    terminal = game.active_terminal
    if not terminal:
        return

    # Calculate overlay dimensions (centered)
    overlay_width = min(OVERLAY_MAX_WIDTH, term.width - 4)
    overlay_height = min(20, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end="")

    # Draw border
    _draw_overlay_border(term, start_x, start_y, overlay_width, overlay_height, colors.terminal)

    # Terminal title header
    header = f" {terminal.title} "
    success_color = getattr(term, f"bold_{colors.ui_success}", term.bold_green)
    print(term.move_xy(start_x + 2, start_y) + success_color(header), end="")

    current_y = start_y + 2

    # Show content
    for line in terminal.content:
        wrapped_lines = wrap_text(line, overlay_width - 4)
        for wrapped_line in wrapped_lines:
            if current_y < start_y + overlay_height - 2:
                print(
                    term.move_xy(start_x + 2, current_y) + term.black(wrapped_line),
                    end="",
                )
                current_y += 1

    # Instructions at bottom
    error_color = getattr(term, f"bold_{colors.ui_error}", term.bold_red)
    print(
        term.move_xy(start_x + 2, start_y + overlay_height - 2)
        + error_color("[Press ESC or any key to close]"),
        end="",
    )


def _draw_overlay_border(term, start_x, start_y, width, height, color_name: str):
    """Draw a box border around an overlay"""
    color_func = getattr(term, f"bold_{color_name}", term.bold_blue)

    # Top border
    print(
        term.move_xy(start_x, start_y) + color_func("┏" + "━" * (width - 2) + "┓"),
        end="",
    )

    # Side borders
    for y in range(start_y + 1, start_y + height - 1):
        print(term.move_xy(start_x, y) + color_func("┃"), end="")
        print(term.move_xy(start_x + width - 1, y) + color_func("┃"), end="")

    # Bottom border
    print(
        term.move_xy(start_x, start_y + height - 1) + color_func("┗" + "━" * (width - 2) + "┛"),
        end="",
    )


def draw_victory_screen(term: "Terminal", game: "Game", colors: ColorScheme):
    """Draw victory screen with final statistics"""
    stats = game.get_final_stats()

    # Clear screen
    print(term.home + term.clear, end="")

    # Calculate centered position
    width = min(70, term.width - 4)
    height = min(20, term.height - 4)
    start_x = (term.width - width) // 2
    start_y = (term.height - height) // 2

    # Draw background
    for y in range(start_y, start_y + height):
        print(term.move_xy(start_x, y) + term.black_on_white(" " * width), end="")

    # Draw border
    success_color = getattr(term, f"bold_{colors.ui_success}", term.bold_green)
    _draw_overlay_border(term, start_x, start_y, width, height, colors.ui_success)

    current_y = start_y + 1

    # Title
    title = "★ VICTORY ★"
    print(
        term.move_xy(start_x + (width - len(title)) // 2, current_y) + success_color(title), end=""
    )
    current_y += 1

    subtitle = "Neural Dive Complete"
    print(
        term.move_xy(start_x + (width - len(subtitle)) // 2, current_y) + term.bold_black(subtitle),
        end="",
    )
    current_y += 2

    # Stats
    def format_time(seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    stats_lines = [
        f"Final Score: {stats['score']}",
        "",
        f"Questions Answered: {stats['questions_answered']}",
        f"Correct: {stats['questions_correct']} | Wrong: {stats['questions_wrong']}",
        f"Accuracy: {stats['accuracy']:.1f}%",
        "",
        f"NPCs Defeated: {stats['npcs_completed']}",
        f"Knowledge Modules: {stats['knowledge_modules']}",
        f"Final Coherence: {stats['final_coherence']}/{game.max_coherence}",
        "",
        f"Time Played: {format_time(stats['time_played'])}",
        f"Deepest Layer: {stats['current_floor']}/{game.max_floors}",
    ]

    for line in stats_lines:
        if current_y < start_y + height - 2:
            if line == "":
                current_y += 1
                continue
            # Center align stats
            print(term.move_xy(start_x + 2, current_y) + term.bold_black(line), end="")
            current_y += 1

    # Footer
    print(
        term.move_xy(start_x + 2, start_y + height - 2)
        + getattr(term, f"bold_{colors.ui_primary}", term.bold)("[Press Q to quit]"),
        end="",
    )

    sys.stdout.flush()
