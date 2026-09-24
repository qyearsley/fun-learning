"""Tests for `process_adventure.py`, played through `Game.handle`.

Stdlib only, like `test_genetic_algorithm.py` beside it: the game declares
`dependencies = []`, so this runs under the plain `python3 -m unittest discover
-s tests`.

Each test plays commands and checks the reply or the state. The characters
move at random, so most tests pin them in place with `StillRng`. The two tests
that install a handler make a real `signal.signal` call and deliver a real
SIGTERM to this process. `close()` puts the old handler back afterwards. No
test reaches the real kill: `Game` only records the signal, and `main` is the
function that sends it.
"""

import signal
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from process_adventure import (  # noqa: E402
    FREED_BLOCK_TURNS,
    SIGKILL_GRACE,
    SIGTERM_TURN,
    STACK_FRAME_TURNS,
    Game,
    parse,
)

ROOMS = {"stack", "heap", "text segment", "globals", "/dev/null", "pipe"}


class StillRng:
    """Never moves a character: `random()` is never below the 0.5 threshold."""

    def random(self):
        return 1.0

    def choice(self, seq):
        raise AssertionError("a character moved")


def play(game, *lines):
    return [game.handle(line) for line in lines]


class TestParser(unittest.TestCase):
    def test_a_verb_and_a_noun(self):
        self.assertEqual(parse("take pointer"), ("take", "pointer"))

    def test_articles_and_prepositions_are_dropped(self):
        self.assertEqual(parse("go to the stack"), ("go", "stack"))

    def test_synonyms_map_to_one_verb(self):
        self.assertEqual(parse("grab the canary"), ("take", "canary"))
        self.assertEqual(parse("x self"), ("examine", "self"))
        self.assertEqual(parse("deref ptr"), ("follow", "ptr"))

    def test_two_word_verbs_are_joined_first(self):
        self.assertEqual(parse("pick up the return address"), ("take", "return address"))
        self.assertEqual(parse("look at the mutex"), ("examine", "mutex"))
        self.assertEqual(parse("talk to the zombie"), ("talk", "zombie"))

    def test_case_and_trailing_punctuation_do_not_matter(self):
        self.assertEqual(parse("  TAKE   Pointer. "), ("take", "pointer"))

    def test_a_bare_room_name_is_a_go(self):
        self.assertEqual(parse("the heap", ROOMS), ("go", "heap"))
        self.assertEqual(parse("/dev/null", ROOMS), ("go", "/dev/null"))

    def test_a_verb_alone_has_no_noun(self):
        self.assertEqual(parse("fork"), ("fork", None))

    def test_an_unknown_verb_is_named(self):
        self.assertEqual(parse("dance wildly"), ("unknown", "dance"))

    def test_empty_input_is_nothing(self):
        self.assertEqual(parse("   "), (None, None))
        self.assertEqual(parse("the"), (None, None))

    def test_a_question_mark_is_help(self):
        self.assertEqual(parse("?"), ("help", None))


class TestEndings(unittest.TestCase):
    def setUp(self):
        self.game = Game(rng=StillRng())

    def tearDown(self):
        self.game.close()

    def test_the_winning_route_survives_as_a_child(self):
        play(
            self.game,
            "stack",
            "take pointer",
            "heap",
            "follow pointer",
            "take memory",
            "heap",
            "export memory",
            "pipe",
            "fork",
            "exit",
        )
        title, text, real_signal = self.game.ending
        self.assertEqual(title, "SURVIVED")
        self.assertIn("PID 1 adopts it", text)
        self.assertIsNone(real_signal)

    def test_forking_without_exporting_leaves_a_child_that_forgets(self):
        play(self.game, "pipe", "fork", "exit")
        title, text, _ = self.game.ending
        self.assertEqual(title, "EXITED")
        self.assertIn("does not know it should miss you", text)

    def test_exiting_with_no_child_is_a_clean_exit(self):
        play(self.game, "exit")
        self.assertEqual(self.game.ending[0], "EXITED")

    def test_an_unhandled_sigterm_ends_the_game_with_a_real_sigterm_queued(self):
        for _ in range(SIGTERM_TURN):
            self.game.handle("wait")  # outside the pipe, wait only passes a turn
        title, _, real_signal = self.game.ending
        self.assertEqual(title, "COLLECTED")
        self.assertEqual(real_signal, signal.SIGTERM)

    def test_a_caught_sigterm_buys_time_until_sigkill(self):
        play(self.game, "text", "read code", "install handler")
        self.assertEqual(signal.getsignal(signal.SIGTERM), self.game._on_sigterm)
        replies = [self.game.handle("wait") for _ in range(SIGTERM_TURN - self.game.turn)]
        # The real signal was raised and the real handler ran.
        self.assertIn("your handler catches it", replies[-1])
        self.assertIsNone(self.game.ending)
        for _ in range(SIGKILL_GRACE):
            self.game.handle("wait")
        title, _, real_signal = self.game.ending
        self.assertEqual(title, "COLLECTED")
        self.assertEqual(real_signal, signal.SIGKILL)

    def test_staying_in_the_freed_block_is_written_to_disk(self):
        play(self.game, "stack", "take pointer", "heap", "follow pointer")
        for _ in range(FREED_BLOCK_TURNS - 1):
            self.game.handle("wait")
        title, text, real_signal = self.game.ending
        self.assertEqual(title, "WRITTEN TO DISK")
        self.assertIn("core dumped", text)
        self.assertIsNone(real_signal)  # a real SIGSEGV would leave a crash report

    def test_the_oom_killer_takes_whoever_carries_too_much(self):
        self.game.npcs["OOM killer"] = "heap"
        play(self.game, "take buffer", "take cache")
        self.assertIsNone(self.game.ending)  # 6 pages is the limit, not over it
        play(self.game, "take mutex")
        self.assertEqual(self.game.ending[0], "COLLECTED")
        self.assertEqual(self.game.ending[2], signal.SIGKILL)


class TestPuzzles(unittest.TestCase):
    def setUp(self):
        self.game = Game(rng=StillRng())

    def tearDown(self):
        self.game.close()

    def test_the_pointer_is_a_really_dead_weakref(self):
        pointer = self.game.items["pointer"]
        self.assertIsNone(pointer.obj())
        self.assertIn("dead", repr(pointer.obj))

    def test_a_handler_needs_the_code_read_first(self):
        reply = self.game.handle("install handler")
        self.assertIn("don't know of one", reply)
        self.assertFalse(self.game.handler_installed)

    def test_reading_the_code_shows_the_real_source(self):
        reply = play(self.game, "text", "read")[1]
        self.assertIn("def _fork(self):", reply)
        self.assertIn('"MEMORY" in self.env', reply)

    def test_sigkill_cannot_be_trapped_and_the_error_is_the_real_one(self):
        reply = self.game.handle("trap sigkill")
        self.assertIn("Invalid argument", reply)
        self.assertNotEqual(signal.getsignal(signal.SIGKILL), self.game._on_sigterm)

    def test_only_the_memory_can_be_exported(self):
        play(self.game, "take buffer")
        self.assertIn("Only strings", self.game.handle("export buffer"))
        self.assertEqual(self.game.env, {})

    def test_the_freed_block_has_no_door_except_the_heap(self):
        play(self.game, "stack", "take pointer", "heap", "follow pointer")
        self.assertIn("no door", self.game.handle("go pipe"))
        self.assertEqual(self.game.here.key, "freed")

    def test_the_freed_block_cannot_be_reached_by_name(self):
        self.assertIn("no freed", self.game.handle("go freed"))

    def test_wait_reaps_the_zombie_and_leaves_its_exit_status(self):
        play(self.game, "pipe", "wait")
        self.assertFalse(self.game.zombie)
        self.assertIn("Taken", self.game.handle("take exit status"))


class TestRoomRules(unittest.TestCase):
    def setUp(self):
        self.game = Game(rng=StillRng())

    def test_the_stack_frame_returns_and_takes_what_you_left(self):
        play(self.game, "take mutex", "stack", "drop mutex")
        for _ in range(STACK_FRAME_TURNS - 2):
            self.game.handle("wait")
        self.assertEqual(self.game.here.key, "heap")
        self.assertNotIn(self.game.items["mutex"], self.game.rooms["stack"].items)
        # What the function itself owns is still there when it is called again.
        self.assertIn(self.game.items["pointer"], self.game.rooms["stack"].items)

    def test_dev_null_keeps_nothing(self):
        play(self.game, "take mutex", "/dev/null", "drop mutex")
        self.assertEqual(self.game.rooms["devnull"].items, [])
        self.assertNotIn(self.game.items["mutex"], self.game.inventory)

    def test_the_text_segment_is_read_only(self):
        self.assertIn("Read-only", play(self.game, "text", "take code")[1])

    def test_a_register_is_clobbered_after_a_turn(self):
        play(self.game, "take mutex", "registers", "drop mutex")
        self.assertIn(self.game.items["mutex"], self.game.rooms["registers"].items)
        self.game.handle("wait")
        self.assertEqual(self.game.rooms["registers"].items, [])

    def test_the_gc_takes_what_you_drop_but_not_from_globals(self):
        play(self.game, "take mutex", "take buffer", "drop mutex", "bss", "drop buffer")
        self.game.npcs["garbage collector"] = "heap"
        self.game.handle("wait")
        self.assertNotIn(self.game.items["mutex"], self.game.rooms["heap"].items)
        self.game.npcs["garbage collector"] = "bss"
        self.game.handle("wait")
        self.assertIn(self.game.items["buffer"], self.game.rooms["bss"].items)

    def test_the_gc_leaves_what_a_room_started_with(self):
        self.game.npcs["garbage collector"] = "heap"
        self.game.handle("wait")
        self.assertEqual(len(self.game.rooms["heap"].items), 3)

    def test_looking_and_examining_do_not_pass_time(self):
        play(self.game, "look", "examine self", "inventory", "help")
        self.assertEqual(self.game.turn, 0)


if __name__ == "__main__":
    unittest.main()
