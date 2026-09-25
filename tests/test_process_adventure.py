"""Tests for `process_adventure.py`, played through `Game.handle`.

Stdlib only, like `test_genetic_algorithm.py` beside it: the game declares
`dependencies = []`, so this runs under the plain `python3 -m unittest discover
-s tests`.

Each test plays commands and checks the reply or the state. The characters
move at random, so most tests pin them in place with `StillRng`. The two tests
that install a handler make a real `signal.signal` call and deliver a real
SIGTERM to this process. `close()` puts the old handler back and releases the
real locks afterwards. No test reaches the real kill: `Game` only records the
signal, and `main` is the function that sends it.

Automatic garbage collection is off during each test, as it is in `main`, so a
reference cycle lives exactly until the game's own collector runs.
"""

import gc
import signal
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import process_adventure  # noqa: E402
from process_adventure import (  # noqa: E402
    ENDINGS,
    FREED_BLOCK_TURNS,
    GC_PERIOD,
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
    """The replies, with line wrapping undone so a phrase can be searched for."""
    return [" ".join(game.handle(line).split()) for line in lines]


class GameTest(unittest.TestCase):
    def setUp(self):
        gc.disable()
        self.game = Game(rng=StillRng())

    def tearDown(self):
        self.game.close()
        gc.enable()


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


# The shortest route to SURVIVED: read the code, take the locks in the order
# it gives, fetch the memory through the dangling pointer, export it, fork.
WINNING_ROUTE = (
    "text",
    "read",
    "bss",
    "take env lock",
    "heap",
    "take heap lock",
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
MEMORY_ROUTE = ("stack", "take pointer", "heap", "follow pointer", "take memory", "heap")


class TestEndings(GameTest):
    def test_the_winning_route_survives_as_a_child(self):
        play(self.game, *WINNING_ROUTE)
        title, text, real_signal = self.game.ending
        self.assertEqual(title, "SURVIVED")
        self.assertIn("PID 1 adopts it", text)
        self.assertNotIn("Nobody will remember", text)
        self.assertIsNone(real_signal)

    def test_the_winning_route_fits_before_sigterm_without_a_handler(self):
        self.assertLess(len(WINNING_ROUTE), SIGTERM_TURN)

    def test_forking_without_the_heap_lock_leaves_a_hung_child(self):
        play(self.game, "pipe", "fork", "exit")
        title, text, _ = self.game.ending
        self.assertEqual(title, "HUNG")
        self.assertIn("will wait forever", text)

    def test_a_safe_fork_without_the_memory_leaves_a_child_that_forgets(self):
        play(self.game, "take heap lock", "pipe", "fork", "exit")
        title, text, _ = self.game.ending
        self.assertEqual(title, "EXITED")
        self.assertIn("does not know it should miss you", text)

    def test_exiting_with_no_child_is_a_clean_exit(self):
        play(self.game, "exit")
        self.assertEqual(self.game.ending[0], "EXITED")
        self.assertIn("Nobody will remember", self.game.ending[1])

    def test_an_unhandled_sigterm_ends_the_game_with_a_real_sigterm_queued(self):
        for _ in range(SIGTERM_TURN):
            self.game.handle("wait")  # outside the pipe, wait only passes a turn
        title, _, real_signal = self.game.ending
        self.assertEqual(title, "COLLECTED")
        self.assertEqual(real_signal, signal.SIGTERM)

    def test_a_caught_sigterm_buys_time_until_sigkill(self):
        play(self.game, "text", "read code", "install handler")
        self.assertEqual(signal.getsignal(signal.SIGTERM), self.game._on_sigterm)
        replies = play(self.game, *["wait"] * (SIGTERM_TURN - self.game.turn))
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
        play(self.game, "take heap lock")
        self.assertEqual(self.game.ending[0], "COLLECTED")
        self.assertEqual(self.game.ending[2], signal.SIGKILL)

    def test_the_locks_in_the_wrong_order_deadlock_and_the_wait_is_real(self):
        self.addCleanup(
            setattr, process_adventure, "DEADLOCK_WAIT", process_adventure.DEADLOCK_WAIT
        )
        process_adventure.DEADLOCK_WAIT = 0.01
        play(self.game, "take heap lock", "bss", "take env lock")
        title, text, real_signal = self.game.ending
        self.assertEqual(title, "DEADLOCKED")
        self.assertIn("returned False", text)  # the real acquire() timed out
        self.assertIn("EDEADLK", text)
        self.assertEqual(real_signal, signal.SIGKILL)

    def test_carrying_the_canary_out_of_the_frame_aborts(self):
        play(self.game, "stack", "take canary", "heap")
        title, text, real_signal = self.game.ending
        self.assertEqual(title, "ABORTED")
        self.assertIn("stack smashing detected", text)
        self.assertIsNone(real_signal)  # a real SIGABRT would leave a crash report

    def test_putting_the_canary_back_is_safe(self):
        play(self.game, "stack", "take canary", "drop canary", "heap", "wait")
        self.assertIsNone(self.game.ending)

    def test_every_ending_title_is_listed(self):
        self.assertEqual(len(ENDINGS), len(set(ENDINGS)))
        for route in (WINNING_ROUTE, ("exit",), ("pipe", "fork", "exit")):
            game = Game(rng=StillRng())
            play(game, *route)
            game.close()
            self.assertIn(game.ending[0], ENDINGS)


class TestPuzzles(GameTest):
    def test_the_pointer_is_a_really_dead_weakref(self):
        pointer = self.game.items["pointer"]
        self.assertIsNone(pointer.obj())
        self.assertIn("dead", repr(pointer.obj))

    def test_a_handler_needs_the_code_read_first(self):
        self.assertIn("don't know of one", play(self.game, "install handler")[0])
        self.assertFalse(self.game.handler_installed)

    def test_reading_the_code_shows_the_real_source(self):
        reply = self.game.handle("text") and self.game.handle("read")
        self.assertIn("def _fork(self):", reply)
        self.assertIn('"MEMORY" in self.env', reply)
        self.assertIn("Lock order is env lock, then heap lock", reply)

    def test_sigkill_cannot_be_trapped_and_the_error_is_the_real_one(self):
        reply = play(self.game, "trap sigkill")[0]
        self.assertIn("Invalid argument", reply)
        self.assertNotEqual(signal.getsignal(signal.SIGKILL), self.game._on_sigterm)
        self.assertIn("EINVAL", play(self.game, "examine errno")[0])

    def test_only_the_memory_can_be_exported(self):
        play(self.game, "take buffer")
        self.assertIn("Only strings", play(self.game, "export buffer")[0])
        self.assertEqual(self.game.env, {})

    def test_exporting_needs_the_env_lock(self):
        play(self.game, *MEMORY_ROUTE)
        self.assertIn("don't hold its lock", play(self.game, "export memory")[0])
        self.assertEqual(self.game.env, {})

    def test_the_worker_holds_the_env_lock_while_you_hold_only_the_heap_lock(self):
        play(self.game, "take heap lock")
        self.assertTrue(self.game.worker_waiting)
        self.assertTrue(self.game.items["env lock"].obj.locked())
        self.assertIn("held by the worker thread", play(self.game, "bss")[0])
        play(self.game, "drop heap lock")
        self.assertFalse(self.game.worker_waiting)
        self.assertFalse(self.game.items["env lock"].obj.locked())

    def test_the_locks_in_the_right_order_are_safe(self):
        play(self.game, "bss", "take env lock", "heap", "take heap lock", "wait")
        self.assertFalse(self.game.worker_waiting)
        self.assertTrue(self.game.holding("env lock") and self.game.holding("heap lock"))

    def test_the_freed_block_has_no_door_except_the_heap(self):
        play(self.game, "stack", "take pointer", "heap", "follow pointer")
        self.assertIn("no door", play(self.game, "go pipe")[0])
        self.assertEqual(self.game.here.key, "freed")

    def test_the_freed_block_cannot_be_reached_by_name(self):
        self.assertIn("no freed", play(self.game, "go freed")[0])

    def test_wait_reaps_the_zombie_and_leaves_its_exit_status(self):
        play(self.game, "pipe", "wait")
        self.assertFalse(self.game.zombie)
        self.assertIn("Taken", play(self.game, "take exit status")[0])

    def test_errno_names_the_last_failure_and_is_visible_anywhere(self):
        self.assertIn("errno. It is 0", play(self.game, "examine errno")[0])
        play(self.game, "wait")  # no children
        reply = play(self.game, "examine errno")[0]
        self.assertIn("ECHILD", reply)
        self.assertIn("No child processes", reply)


class TestRoomRules(GameTest):
    def test_the_stack_frame_returns_and_takes_what_you_left(self):
        play(self.game, "take cache", "stack", "drop cache")
        for _ in range(STACK_FRAME_TURNS - 2):
            self.game.handle("wait")
        self.assertEqual(self.game.here.key, "heap")
        self.assertNotIn(self.game.items["cache"], self.game.rooms["stack"].items)
        # What the function itself owns is still there when it is called again.
        self.assertIn(self.game.items["pointer"], self.game.rooms["stack"].items)

    def test_dev_null_keeps_nothing(self):
        play(self.game, "take cache", "/dev/null", "drop cache")
        self.assertEqual(self.game.rooms["devnull"].items, [])
        self.assertNotIn(self.game.items["cache"], self.game.inventory)

    def test_the_text_segment_is_read_only(self):
        self.assertIn("Read-only", play(self.game, "text", "take code")[1])

    def test_a_register_is_clobbered_after_a_turn(self):
        play(self.game, "take cache", "registers", "drop cache")
        self.assertIn(self.game.items["cache"], self.game.rooms["registers"].items)
        self.game.handle("wait")
        self.assertEqual(self.game.rooms["registers"].items, [])

    def test_dropping_a_thing_really_frees_it_on_the_spot(self):
        cache = self.game.items["cache"]
        reply = play(self.game, "take cache", "drop cache")[1]
        self.assertIn("refcount hits zero", reply)
        self.assertIsNone(cache.ref())  # CPython really freed the object
        self.assertNotIn(cache, self.game.rooms["heap"].items)

    def test_freed_memory_goes_back_to_the_freed_block(self):
        play(self.game, *MEMORY_ROUTE, "drop memory")
        self.assertIn(self.game.items["memory"], self.game.rooms["freed"].items)

    def test_globals_keep_what_you_leave(self):
        play(self.game, "take cache", "bss", "drop cache")
        for _ in range(GC_PERIOD):
            self.game.handle("wait")
        self.assertIn(self.game.items["cache"], self.game.rooms["bss"].items)

    def test_a_cycle_outlives_the_drop_and_dies_on_the_collectors_round(self):
        self.game.turn = 1  # so the collector's round does not fall on the drop
        cache, buffer = self.game.items["cache"], self.game.items["buffer"]
        play(self.game, "take cache", "take buffer", "link cache to buffer")
        play(self.game, "drop cache", "drop buffer")
        self.assertIsNotNone(cache.ref())  # the refcount really is not zero
        self.assertIn("cache (unreachable)", play(self.game, "look")[0])
        reply = play(self.game, *["wait"] * (GC_PERIOD - self.game.turn % GC_PERIOD))[-1]
        self.assertIn("gc.collect() finds", reply)
        self.assertIsNone(cache.ref())
        self.assertIsNone(buffer.ref())
        self.assertNotIn(cache, self.game.rooms["heap"].items)

    def test_the_collector_leaves_a_cycle_you_can_still_reach(self):
        play(self.game, "take cache", "take buffer", "link cache to buffer", "drop cache")
        self.game.collect()
        self.assertIn(self.game.items["cache"], self.game.rooms["heap"].items)
        self.assertIn("Taken", play(self.game, "take cache")[0])

    def test_a_room_is_brief_the_second_time(self):
        first = play(self.game, "stack")[0]
        play(self.game, "heap")
        second = play(self.game, "stack")[0]
        self.assertIn("Locals sit on a shelf", first)
        self.assertNotIn("Locals sit on a shelf", second)
        self.assertIn("Locals sit on a shelf", play(self.game, "look")[0])

    def test_looking_and_examining_do_not_pass_time(self):
        play(self.game, "look", "examine self", "inventory", "help")
        self.assertEqual(self.game.turn, 0)


if __name__ == "__main__":
    unittest.main()
