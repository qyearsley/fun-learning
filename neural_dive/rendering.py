"""
Terminal rendering for Neural Dive.
Uses blessed library for terminal control.
"""

import sys
from typing import TYPE_CHECKING, Optional
from neural_dive.conversation import wrap_text
from neural_dive.config import (
    OVERLAY_MAX_WIDTH,
    OVERLAY_MAX_HEIGHT,
    COMPLETION_OVERLAY_MAX_HEIGHT,
    UI_BOTTOM_OFFSET,
)

if TYPE_CHECKING:
    from blessed import Terminal
    from neural_dive.game import Game


def draw_game(term: "Terminal", game: "Game", redraw_all: bool = False):
    """
    Draw the entire game state.

    Args:
        term: Blessed Terminal instance
        game: Game instance
        redraw_all: Whether to redraw everything (first draw or after floor change)
    """
    if redraw_all:
        # Clear screen on first draw or floor change
        print(term.home + term.clear, end="")

        # Draw map
        _draw_map(term, game)
    else:
        # Only clear old player position
        _clear_old_player_position(term, game)

    # Draw all entities
    _draw_entities(term, game)

    # Draw UI at bottom
    _draw_ui(term, game)

    # Draw overlays if active
    if game.active_conversation or (
        hasattr(game, "_last_answer_response") and game._last_answer_response
    ):
        draw_conversation_overlay(term, game)

    if game.active_terminal:
        draw_terminal_overlay(term, game)

    sys.stdout.flush()


def _draw_map(term: "Terminal", game: "Game"):
    """Draw the game map"""
    for y in range(len(game.game_map)):
        for x in range(len(game.game_map[0])):
            char = game.game_map[y][x]
            if char == "#":
                print(term.move_xy(x, y) + term.bold_blue(char), end="")
            elif char == ".":
                print(term.move_xy(x, y) + term.cyan(char), end="")


def _clear_old_player_position(term: "Terminal", game: "Game"):
    """Clear the old player position"""
    if game.old_player_pos:
        old_x, old_y = game.old_player_pos
        char = game.game_map[old_y][old_x]
        if char == ".":
            print(term.move_xy(old_x, old_y) + term.cyan(char), end="")


def _draw_entities(term: "Terminal", game: "Game"):
    """Draw all game entities (NPCs, terminals, gates, stairs, player)"""
    # Draw NPCs
    for npc in game.npcs:
        npc_color = getattr(term, f"bold_{npc.color}", term.bold_magenta)
        print(term.move_xy(npc.x, npc.y) + npc_color(npc.char), end="")

    # Draw terminals
    for terminal in game.terminals:
        terminal_color = getattr(term, f"bold_{terminal.color}", term.bold_cyan)
        print(
            term.move_xy(terminal.x, terminal.y) + terminal_color(terminal.char), end=""
        )

    # Draw stairs
    for stair in game.stairs:
        stair_color = getattr(term, f"bold_{stair.color}", term.bold_yellow)
        print(term.move_xy(stair.x, stair.y) + stair_color(stair.char), end="")

    # Draw player
    print(
        term.move_xy(game.player.x, game.player.y) + term.bold_green(game.player.char),
        end="",
    )


def _draw_ui(term: "Terminal", game: "Game"):
    """Draw the UI panel at the bottom"""
    ui_y = term.height - UI_BOTTOM_OFFSET

    # Separator line
    print(term.move_xy(0, ui_y) + term.bold("─" * min(term.width, 80)), end="")

    # Status line
    coherence_pct = int((game.coherence / game.max_coherence) * 100)
    knowledge_count = len(game.knowledge_modules)
    status_line = f"Neural Layer {game.current_floor}/{game.max_floors} | Coherence: {coherence_pct}% | Knowledge: {knowledge_count}"
    print(term.move_xy(2, ui_y + 1) + term.bold(status_line), end="")

    # Message line
    print(term.move_xy(2, ui_y + 2) + " " * (term.width - 4), end="")
    print(
        term.move_xy(2, ui_y + 2) + term.bold_yellow(game.message[: term.width - 4]),
        end="",
    )

    # Instructions
    if game.active_conversation:
        print(
            term.move_xy(0, term.height - 1)
            + term.normal
            + "In conversation - see overlay above",
            end="",
        )
    else:
        print(
            term.move_xy(0, term.height - 1)
            + term.normal
            + "Move: Arrows | Interact: Space/Enter | Stairs: >/< | Q: Quit",
            end="",
        )


def draw_conversation_overlay(term: "Terminal", game: "Game"):
    """Draw conversation overlay panel"""
    conv = game.active_conversation

    # If no active conversation, check if we have a completion response to show
    if not conv:
        if hasattr(game, "_last_answer_response") and game._last_answer_response:
            draw_completion_overlay(term, game)
        return

    # Calculate overlay dimensions (centered)
    overlay_width = min(OVERLAY_MAX_WIDTH, term.width - 4)
    overlay_height = min(OVERLAY_MAX_HEIGHT, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(
            term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
        )

    # Draw border
    _draw_overlay_border(term, start_x, start_y, overlay_width, overlay_height, "blue")

    # NPC name header
    header = f" {conv.npc_name} "
    print(term.move_xy(start_x + 2, start_y) + term.bold_magenta(header), end="")

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
            print(
                term.move_xy(start_x + 2, current_y)
                + term.bold_red("[Press any key to continue]"),
                end="",
            )
        return

    # Check if we have a pending response to show
    if hasattr(game, "_last_answer_response") and game._last_answer_response:
        _draw_response(
            term, game, start_x, start_y, current_y, overlay_width, overlay_height
        )
        return

    # Show current question
    if conv.current_question_idx < len(conv.questions):
        _draw_question(
            term, conv, start_x, start_y, current_y, overlay_width, overlay_height
        )


def _draw_response(
    term, game, start_x, start_y, current_y, overlay_width, overlay_height
):
    """Draw response to answer"""
    response_text = game._last_answer_response

    # Check if this is a completion response
    is_completion = "CONVERSATION COMPLETE" in response_text

    if not is_completion:
        # Normal response - draw separator line
        separator = "─" * (overlay_width - 4)
        print(
            term.move_xy(start_x + 2, current_y) + term.bold_blue(separator), end=""
        )
        current_y += 1

        # Show "RESPONSE:" header
        print(
            term.move_xy(start_x + 2, current_y) + term.bold_green("RESPONSE:"), end=""
        )
        current_y += 2

    # Show response text
    lines = wrap_text(response_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 3:
            print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
            current_y += 1
    current_y += 1

    if current_y < start_y + overlay_height - 2:
        print(
            term.move_xy(start_x + 2, current_y)
            + term.bold_red("[Press any key to continue]"),
            end="",
        )


def _draw_question(term, conv, start_x, start_y, current_y, overlay_width, overlay_height):
    """Draw current question and answers"""
    question = conv.questions[conv.current_question_idx]

    # Question text
    q_text = f"Q{conv.current_question_idx + 1}/{len(conv.questions)}: {question.question_text}"
    lines = wrap_text(q_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 4:
            print(
                term.move_xy(start_x + 2, current_y) + term.bold_black(line), end=""
            )
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
    print(
        term.move_xy(start_x + 2, start_y + overlay_height - 2)
        + term.bold_red("Press 1-4 to answer | ESC to exit"),
        end="",
    )


def draw_completion_overlay(term: "Terminal", game: "Game"):
    """Draw completion message overlay when conversation is complete"""
    response_text = game._last_answer_response

    # Calculate overlay dimensions (centered, larger for completion)
    overlay_width = min(OVERLAY_MAX_WIDTH, term.width - 4)
    overlay_height = min(COMPLETION_OVERLAY_MAX_HEIGHT, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(
            term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
        )

    # Draw border
    _draw_overlay_border(
        term, start_x, start_y, overlay_width, overlay_height, "green"
    )

    current_y = start_y + 2

    # Big completion banner at top
    banner = "*** CONVERSATION COMPLETE ***"
    print(
        term.move_xy(start_x + (overlay_width - len(banner)) // 2, current_y)
        + term.bold_green(banner),
        end="",
    )
    current_y += 2

    # Draw separator
    sep = "=" * (overlay_width - 4)
    print(term.move_xy(start_x + 2, current_y) + term.bold_green(sep), end="")
    current_y += 2

    # Show response text
    lines = wrap_text(response_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 3:
            print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
            current_y += 1
    current_y += 1

    # Instructions at bottom
    if current_y < start_y + overlay_height - 2:
        print(
            term.move_xy(start_x + 2, current_y)
            + term.bold_red("[Press any key to continue]"),
            end="",
        )


def draw_terminal_overlay(term: "Terminal", game: "Game"):
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
        print(
            term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
        )

    # Draw border
    _draw_overlay_border(term, start_x, start_y, overlay_width, overlay_height, "cyan")

    # Terminal title header
    header = f" {terminal.title} "
    print(term.move_xy(start_x + 2, start_y) + term.bold_green(header), end="")

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
    print(
        term.move_xy(start_x + 2, start_y + overlay_height - 2)
        + term.bold_red("[Press ESC or any key to close]"),
        end="",
    )


def _draw_overlay_border(term, start_x, start_y, width, height, color):
    """Draw a box border around an overlay"""
    color_func = getattr(term, f"bold_{color}", term.bold_blue)

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
        term.move_xy(start_x, start_y + height - 1)
        + color_func("┗" + "━" * (width - 2) + "┛"),
        end="",
    )
