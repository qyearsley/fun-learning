"""
Main entry point for Neural Dive.
Allows running as: python -m neural_dive
"""

import sys
import argparse
from blessed import Terminal
from neural_dive.game import Game
from neural_dive.rendering import draw_game


def run_interactive(game: Game):
    """
    Run the game in interactive mode with terminal UI.

    Args:
        game: Game instance to run
    """
    term = Terminal()
    first_draw = True

    try:
        with term.cbreak(), term.hidden_cursor():
            while True:
                # Check for game over
                if game.coherence <= 0:
                    draw_game(term, game, redraw_all=first_draw)
                    print(
                        term.move_xy(0, term.height // 2)
                        + term.center(
                            term.bold_red("SYSTEM FAILURE - COHERENCE LOST")
                        ).rstrip()
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
                draw_game(term, game, redraw_all=first_draw)
                first_draw = False

                # Get input
                key = term.inkey(timeout=0.1)

                if not key:
                    continue

                if (
                    key.lower() == "q"
                    and not game.active_conversation
                    and not game.active_terminal
                ):
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

                    if (
                        hasattr(game, "_last_answer_response")
                        and game._last_answer_response
                    ):
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
                elif (
                    hasattr(game, "_last_answer_response")
                    and game._last_answer_response
                ):
                    # Show final message, then clear everything
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
                    elif key in [">", "."]:
                        # Try stairs first, then interact
                        if not game.use_stairs():
                            game.interact()
                        else:
                            first_draw = True  # Force redraw on floor change
                    elif key in ["<", ","]:
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
        description="Neural Dive - Cyberpunk roguelike with CS conversations"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (reads commands from stdin)",
    )
    parser.add_argument("--seed", type=int, help="Random seed for NPC placement")
    parser.add_argument(
        "--fixed", action="store_true", help="Use fixed NPC positions instead of random"
    )
    parser.add_argument(
        "--width", type=int, default=50, help="Map width (default: 50)"
    )
    parser.add_argument(
        "--height", type=int, default=25, help="Map height (default: 25)"
    )
    args = parser.parse_args()

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
        run_interactive(game)


if __name__ == "__main__":
    main()
