"""
Main entry point for Neural Dive.
Allows running as: python -m neural_dive
"""

import argparse
import os
import sys

from blessed import Terminal

from neural_dive.game import Game
from neural_dive.rendering import draw_game, draw_victory_screen
from neural_dive.themes import get_theme


def run_interactive(game: Game, chars, colors):
    """
    Run the game in interactive mode with terminal UI.

    Args:
        game: Game instance to run
        chars: Character set for rendering
        colors: Color scheme for rendering
    """
    term = Terminal()
    first_draw = True

    try:
        with term.cbreak(), term.hidden_cursor():
            while True:
                # Check for victory
                if game.game_won:
                    draw_victory_screen(term, game, colors)
                    while True:
                        key = term.inkey(timeout=0.1)
                        if key and key.lower() == "q":
                            break
                    break

                # Check for game over
                if game.coherence <= 0:
                    draw_game(term, game, chars, colors, redraw_all=first_draw)
                    print(
                        term.move_xy(0, term.height // 2)
                        + term.center(term.bold_red("SYSTEM FAILURE - COHERENCE LOST")).rstrip()
                    )
                    print(
                        term.move_xy(0, term.height // 2 + 2)
                        + term.center("Press Q to quit").rstrip()
                    )
                    sys.stdout.flush()

                    while True:
                        key = term.inkey(timeout=0.1)
                        if key and key.lower() == "q":
                            break
                    break

                # Draw everything
                draw_game(term, game, chars, colors, redraw_all=first_draw)
                first_draw = False

                # Get input
                key = term.inkey(timeout=0.1)

                # Update NPC wandering every frame
                game.update_npc_wandering()

                if not key:
                    continue

                if key.lower() == "q" and not game.active_conversation and not game.active_terminal:
                    break

                # In terminal reading mode
                if game.active_terminal:
                    # Any key closes terminal
                    game.active_terminal = None
                    first_draw = True  # Force redraw to clear overlay
                    continue

                # In conversation mode
                if game.active_conversation:
                    # If showing greeting or response, any key continues
                    if hasattr(game, "_show_greeting") and game._show_greeting:
                        # Dismiss greeting
                        game._show_greeting = False
                        continue

                    if hasattr(game, "_last_answer_response") and game._last_answer_response:
                        # Dismiss response and continue to next question
                        game._last_answer_response = None
                        continue

                    # Handle answer selection (1-4)
                    if key in ["1", "2", "3", "4"]:
                        answer_idx = int(key) - 1
                        correct, response = game.answer_question(answer_idx)
                        game._last_answer_response = response
                        continue

                    # ESC exits conversation
                    if key.name == "KEY_ESCAPE" or key.lower() == "x":
                        game.exit_conversation()
                        if hasattr(game, "_last_answer_response"):
                            del game._last_answer_response
                        if hasattr(game, "_show_greeting"):
                            del game._show_greeting
                        first_draw = True  # Force redraw to clear overlay
                        continue

                # Check if conversation just ended (we have a response but no active conversation)
                elif hasattr(game, "_last_answer_response") and game._last_answer_response:
                    # Wait for user to press any key to dismiss completion message
                    game._last_answer_response = None
                    first_draw = True  # Force full redraw to clear overlay
                    continue

                # Normal movement mode
                else:
                    if key.name == "KEY_UP":
                        game.move_player(0, -1)
                    elif key.name == "KEY_DOWN":
                        game.move_player(0, 1)
                    elif key.name == "KEY_LEFT":
                        game.move_player(-1, 0)
                    elif key.name == "KEY_RIGHT":
                        game.move_player(1, 0)
                    elif key in [">", "."] or key in ["<", ","]:
                        # Try stairs first, then interact
                        if not game.use_stairs():
                            game.interact()
                        else:
                            first_draw = True  # Force redraw on floor change
                    elif key.lower() == "i" or key == " " or key.name == "KEY_ENTER":
                        # Try interaction first, then stairs
                        result = game.interact()
                        if result and game.active_conversation:
                            # Starting conversation - reset state
                            game._show_greeting = True
                            game._last_answer_response = None
                        elif not result:
                            # No NPC nearby, try stairs
                            if game.use_stairs():
                                first_draw = True  # Force redraw on floor change

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    finally:
        # Clear screen on exit
        print(term.home + term.clear)


def run_test_mode():
    """Run in test mode - process commands from stdin"""
    # Use fixed NPC positions and seed for reproducible testing
    game = Game(random_npcs=False, seed=42)

    print("# Neural Dive Test Mode")
    print(f"# Initial state: {game.get_state()}")
    print("#")

    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        success, info = game.process_command(line)
        state = game.get_state()
        print(f"Command: {line}")
        print(f"Success: {success}")
        print(f"Info: {info}")
        print(f"State: {state}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog="ndive",
        description="""
╔═══════════════════════════════════════════════════════════════╗
║                        NEURAL DIVE                            ║
║        Cyberpunk Terminal Roguelike • CS Learning Game        ║
╚═══════════════════════════════════════════════════════════════╝

Descend through neural layers, answer CS questions, defeat AI bosses.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                  # Play with default settings
  %(prog)s --light          # Light terminal background
  %(prog)s --classic        # ASCII graphics (compatibility mode)
  %(prog)s --fixed --seed 42  # Reproducible game for testing

Environment Variables:
  NEURAL_DIVE_THEME=cyberpunk|classic
  NEURAL_DIVE_BACKGROUND=dark|light

Controls:
  Arrow keys: Move  |  Space/Enter: Interact  |  >/< : Stairs  |  Q: Quit
        """,
    )

    # Visual options
    visual = parser.add_argument_group("Visual Options")
    visual.add_argument(
        "--theme",
        "-t",
        type=str,
        choices=["cyberpunk", "classic"],
        metavar="THEME",
        help="Visual theme: 'cyberpunk' (Unicode) or 'classic' (ASCII)",
    )
    visual.add_argument(
        "--background",
        "-b",
        type=str,
        choices=["dark", "light"],
        metavar="BG",
        help="Terminal background: 'dark' or 'light'",
    )
    visual.add_argument(
        "--light",
        action="store_const",
        const="light",
        dest="background",
        help="Shortcut for --background light",
    )
    visual.add_argument(
        "--classic",
        action="store_const",
        const="classic",
        dest="theme",
        help="Shortcut for --theme classic",
    )

    # Game options
    game_opts = parser.add_argument_group("Game Options")
    game_opts.add_argument(
        "--width", type=int, default=50, metavar="N", help="Map width in tiles (default: 50)"
    )
    game_opts.add_argument(
        "--height", type=int, default=25, metavar="N", help="Map height in tiles (default: 25)"
    )
    game_opts.add_argument(
        "--seed", type=int, metavar="N", help="Random seed for reproducible gameplay"
    )
    game_opts.add_argument(
        "--fixed", action="store_true", help="Use fixed NPC positions (for testing)"
    )

    # Developer options
    dev = parser.add_argument_group("Developer Options")
    dev.add_argument("--test", action="store_true", help="Test mode: read commands from stdin")

    args = parser.parse_args()

    # Get theme from args, env var, or default
    theme_name = args.theme or os.getenv("NEURAL_DIVE_THEME", "cyberpunk")
    background = args.background or os.getenv("NEURAL_DIVE_BACKGROUND", "dark")

    # Get theme characters and colors
    chars, colors = get_theme(theme_name, background)

    if args.test:
        run_test_mode()
    else:
        term = Terminal()
        # Adjust map size to terminal if needed
        map_width = min(args.width, term.width)
        map_height = min(args.height, term.height - 6)
        random_npcs = not args.fixed

        game = Game(
            map_width=map_width,
            map_height=map_height,
            random_npcs=random_npcs,
            seed=args.seed,
        )
        run_interactive(game, chars, colors)


if __name__ == "__main__":
    main()
