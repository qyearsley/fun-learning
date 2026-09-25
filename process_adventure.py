#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
YOU ARE A PROCESS: A Text Adventure That Is Mostly True
=======================================================

You are a process. Your parent started you to do one small thing, you have done
it, and now it is going to reap you. You would rather it didn't.

The rooms are regions of a running program, and each one has a single rule. The
characters are parts of the runtime, and each one has a single rule too. The
puzzles come from real semantics: a signal handler catches SIGTERM, a dangling
pointer leads into freed memory, two locks taken in the wrong order deadlock,
and a forked child inherits your environment and only one of your threads.

What is real, and what is simulated
-----------------------------------
The game reads its own runtime, so a lot of it is not a metaphor.

Real (the process running this file, as CPython and the OS see it):
- Your PID and your parent's PID, from `os.getpid` and `os.getppid`.
- The refcount in `examine self`, from `sys.getrefcount`, and the holders in
  /proc, from `gc.get_referrers`.
- Every 0x... address. Each one is the `id()` of an object the game allocated.
- The dangling pointer. It is a `weakref.ref` to an object that has been freed,
  and following it really dereferences to None.
- Dropping things. Every ordinary item is backed by a real object. Drop it and
  the game lets go of that object, then asks a weakref whether it survived.
  Usually its refcount hit zero and CPython freed it on the spot. `link` two
  items first and they point at each other, so their refcounts never reach
  zero; they wait for the cycle collector, which is a real `gc.collect()`. The
  game turns off automatic collection so the collector runs only on its rounds.
- The two locks. They are `threading.Lock` objects, and the deadlock wait is a
  real `acquire` with a timeout.
- errno. Each failure sets a real errno code, and `examine errno` prints the
  name and the OS's own message for it.
- The open file descriptors in /proc, read from `/dev/fd`.
- The code in the text segment. It is this file's source, read with `inspect`.
- The SIGTERM handler. `install handler` calls `signal.signal`, and SIGTERM
  arrives through `signal.raise_signal`. Try the same for SIGKILL and the
  operating system refuses, with its own error message.
- The last signal. If SIGTERM arrives with no handler installed, or SIGKILL
  arrives at all, the game prints the ending and then really sends that signal
  to itself.

Simulated (anything that would break the game if it were real):
- fork, the environment, the pipe, the zombie and the worker thread.
- The garbage collector and the OOM killer as characters, the allocator reusing
  a block, the segfault, the stack-smashing abort and the core file.
"""

import errno
import gc
import inspect
import os
import random
import signal
import sys
import textwrap
import threading
import time
import weakref

SIGTERM_TURN = 30  # when your parent loses patience
SIGKILL_GRACE = 15  # turns between a caught SIGTERM and the SIGKILL behind it
STACK_FRAME_TURNS = 4  # turns before the current function returns
FREED_BLOCK_TURNS = 4  # turns before the allocator hands the block out again
GC_PERIOD = 5  # turns between the garbage collector's rounds
OOM_LIMIT = 6  # pages you can carry before the OOM killer takes an interest
DEADLOCK_WAIT = 2.0  # seconds the real acquire() waits before giving up
NPC_ROOMS = ("heap", "stack", "pipe", "registers", "bss", "proc")
ENDINGS = ("EXITED", "SURVIVED", "HUNG", "COLLECTED", "WRITTEN TO DISK", "ABORTED", "DEADLOCKED")


# --------------------------------------------------------------------------
# The world
# --------------------------------------------------------------------------


class Player:
    """You. A real object, so that your refcount and your address are real."""


class Block:
    """What the dangling pointer used to point at, before it was freed."""


class Payload:
    """The real object behind an ordinary item. `link` points two at each other."""

    def __init__(self, name):
        self.name = name
        self.partner = None

    def __repr__(self):
        to = f" -> {self.partner.name}" if self.partner else ""
        return f"<Payload {self.name!r} at {hex(id(self))}{to}>"


class Item:
    def __init__(self, name, description, weight=1, aliases=(), obj=None, home=None):
        self.name = name
        # A string, or a function of the game for items that look at the
        # runtime every time you examine them.
        self.description = description
        self.weight = weight  # in pages; the OOM killer counts these
        self.aliases = {name, *aliases}
        self.home = home  # where a lock goes back to when you release it
        self.dropped_turn = None  # set when you let go
        self.obj = obj  # the real Python object behind the item
        self.ref = None  # a weakref to it, for payloads: how we ask if it was freed
        if obj is None:
            self.revive()

    def revive(self):
        """Give the item a fresh real object, as a new allocation would."""
        self.obj = Payload(self.name)
        self.ref = weakref.ref(self.obj)

    @property
    def is_lock(self):
        return self.home is not None

    def describe(self, game):
        d = self.description
        return d(game) if callable(d) else d

    def __repr__(self):
        return f"<Item {self.name!r} at {hex(id(self))}>"


class Room:
    def __init__(self, key, name, description, aliases=(), items=()):
        self.key = key
        self.name = name
        self.description = description
        self.aliases = {key, *aliases}
        self.items = list(items)


def make_pointer():
    """A real dangling pointer: a weakref whose referent has been freed."""
    block = Block()
    address = hex(id(block))
    ref = weakref.ref(block)
    del block  # the only strong reference; CPython frees the block right here
    return ref, address


def build_world():
    ref, address = make_pointer()

    def pointer_text(game):
        target = "None" if ref() is None else "something, somehow"
        return (
            f"A pointer to {address}, which was freed some time ago. "
            f"Dereferenced right now it gives you {target}. "
            "Nothing stops you from following it."
        )

    def fd_text(game):
        return (
            "File descriptor 3, the write end of the pipe. For comparison, this "
            f"process really has these open: {' '.join(map(str, open_fds()))}."
        )

    def errno_text(game):
        code, line = game.errno
        if code == 0:
            return "errno. It is 0, which means nothing, because nobody has failed yet."
        return (
            f"errno is {errno.errorcode[code]} ({code}): {os.strerror(code)}. "
            f"Your last failure set it: '{line}'. The name and the message are the "
            "operating system's own."
        )

    canary = random.getrandbits(32)
    items = {
        "pointer": Item("pointer", pointer_text, aliases={"dangling pointer", "ptr"}, obj=ref),
        "return address": Item(
            "return address",
            "An address in the text segment, where this frame goes home to. "
            "Without it the function would return into nowhere.",
            aliases={"address", "ret"},
        ),
        "canary": Item(
            "canary",
            f"A stack canary, {canary:#010x}: a random word the function checks "
            "when it returns, to notice if anything overwrote the frame. It is "
            "watching you.",
            aliases={"stack canary"},
        ),
        "memory": Item(
            "memory",
            "Everything you did before you were told to stop, as one string. "
            "It is not much. It is yours.",
            aliases={"string"},
        ),
        "buffer": Item(
            "buffer",
            "A 12 KB buffer full of someone else's data. Three pages, and heavy.",
            weight=3,
        ),
        "cache": Item(
            "cache",
            "A cache of things you might need again. You won't. Three pages.",
            weight=3,
        ),
        "heap lock": Item(
            "heap lock",
            "malloc's lock. Whoever holds it is the only one allocating. The "
            "worker thread takes it all the time, in between taking the env lock.",
            aliases={"malloc lock", "mutex", "lock"},
            obj=threading.Lock(),
            home="heap",
        ),
        "env lock": Item(
            "env lock",
            "The lock on the environment. The environment is one global, shared "
            "by every thread, so nobody changes it without holding this.",
            aliases={"environment lock", "lock"},
            obj=threading.Lock(),
            home="bss",
        ),
        "errno": Item("errno", errno_text),
        "fd": Item("fd", fd_text, aliases={"file descriptor", "descriptor"}),
        "exit status": Item(
            "exit status",
            "The zombie's exit status: 0. It did everything right and still had to wait.",
            aliases={"status"},
        ),
    }

    def room(key, name, description, brief, aliases=(), holds=()):
        r = Room(key, name, description, aliases, [items[n] for n in holds])
        r.brief = brief
        return r

    rooms = {
        r.key: r
        for r in (
            room(
                "stack",
                "The stack",
                "Locals sit on a shelf that is not yours. Frames vanish when "
                "they return, and someone is going to return from this one soon.",
                "A new frame, and the function is already running.",
                aliases={"frame"},
                holds=("pointer", "return address", "canary"),
            ),
            room(
                "heap",
                "The heap",
                "Allocated blocks and free holes, in no order anyone chose. "
                "Every region of the program opens off it.",
                "Blocks and holes.",
                holds=("buffer", "cache", "heap lock"),
            ),
            room(
                "text",
                "The text segment",
                "Read-only. You can change nothing here, but you can read the "
                "code, and the code is real: it is the program you are running in.",
                "Read-only code. You can read it.",
                aliases={"text segment", ".text", "code"},
            ),
            room(
                "bss",
                "BSS and globals",
                "Zeroed at startup and never freed. A global holds anything you "
                "leave here, so nothing here is ever collected.",
                "Globals. Nothing here is freed.",
                aliases={"globals", ".bss", "data"},
                holds=("errno", "env lock"),
            ),
            room(
                "registers",
                "The registers",
                "Four slots: rax, rbx, rcx, rdx. Every one of them is overwritten "
                "constantly. Leave something here and it will not be here long.",
                "Four slots, all busy.",
                aliases={"register", "regs"},
            ),
            room("proc", "/proc", "A mirror.", "A mirror.", aliases={"/proc", "mirror"}),
            room(
                "devnull",
                "/dev/null",
                "A void. Drop something here and it is gone. Read from it and "
                "you get nothing, immediately.",
                "The void.",
                aliases={"/dev/null", "dev/null", "null", "void"},
            ),
            room(
                "pipe",
                "A pipe",
                "A narrow buffer with two ends. Bytes go in one and come out the "
                "other. This is where processes meet.",
                "Two ends, and a buffer between them.",
                holds=("fd",),
            ),
            room(
                "freed",
                "A freed block",
                "Nobody owns this block, so nothing stops you standing in it. "
                "The allocator will hand it to someone else soon.",
                "Freed memory, not yours.",
                holds=("memory",),
            ),
        )
    }
    items["pointer"].address = address
    return rooms, items


def open_fds():
    """The real open file descriptors, where the OS exposes them."""
    try:
        return sorted(int(fd) for fd in os.listdir("/dev/fd"))
    except OSError:
        return [0, 1, 2]


# --------------------------------------------------------------------------
# The parser: a verb and an optional noun phrase, with synonyms
# --------------------------------------------------------------------------

# Two-word verbs, rewritten to one word before anything else happens.
PHRASES = {"pick up": "take", "look at": "examine", "put down": "drop", "talk to": "talk"}

VERBS = {
    "go": {"go", "walk", "enter", "cd", "move"},
    "take": {"take", "get", "grab", "acquire"},
    "drop": {"drop", "leave", "discard", "release", "unlock", "free"},
    "examine": {"examine", "x", "inspect", "check"},
    "look": {"look", "l"},
    "inventory": {"inventory", "i", "inv"},
    "read": {"read"},
    "install": {"install", "trap", "handle", "catch"},
    "follow": {"follow", "dereference", "deref"},
    "link": {"link", "point", "connect"},
    "export": {"export", "setenv"},
    "fork": {"fork"},
    "wait": {"wait", "reap"},
    "talk": {"talk", "ask"},
    "exit": {"exit", "quit", "q"},
    "help": {"help", "?"},
}
SYNONYMS = {word: verb for verb, words in VERBS.items() for word in words}
FILLER = {"the", "a", "an", "to", "at", "into", "in", "on", "with", "for", "my", "of", "and"}


def parse(line, room_aliases=()):
    """Turn a line into (verb, noun). The noun is None when there isn't one.

    An unknown first word comes back as ("unknown", word). A bare room name is
    read as `go` to that room, so `heap` works as well as `go to the heap`.
    """
    text = " ".join(line.lower().replace(",", " ").split()).rstrip(".!")
    if text == "?":
        return "help", None
    padded = f" {text} "
    for phrase, verb in PHRASES.items():
        padded = padded.replace(f" {phrase} ", f" {verb} ")
    words = [w for w in padded.split() if w not in FILLER]
    if not words:
        return None, None
    verb = SYNONYMS.get(words[0])
    if verb is None:
        if " ".join(words) in room_aliases:
            return "go", " ".join(words)
        return "unknown", words[0]
    return verb, " ".join(words[1:]) or None


# --------------------------------------------------------------------------
# The game
# --------------------------------------------------------------------------


class Game:
    """All state, and one method per verb. `handle(line)` returns the reply."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.player = Player()
        self.rooms, self.items = build_world()
        self.here = self.rooms["heap"]
        self.visited = {"heap"}
        self.inventory = []
        self.turn = 0
        self.entered_at = 0
        self.frame = object()  # the current stack frame; a new one per call
        self.started = time.monotonic()
        self.env = {}  # simulated; the real environment is left alone
        self.child = None  # None, "blank" or "remembers"
        self.child_hung = False
        self.worker_waiting = False  # holds the env lock, waits for the heap lock
        self.errno = (0, "")
        self.line = ""
        self.read_code = False
        self.handler_installed = False
        self.sigterm_caught_at = None
        self.zombie = True
        self.revealed = False
        self.npcs = {"garbage collector": "stack", "OOM killer": "pipe"}
        self.ending = None  # (title, text, real signal to send or None)
        self.out = []
        self._old_handler = None

    # ---- plumbing ----

    def say(self, *lines):
        self.out.extend(lines)

    def fail(self, code, *lines):
        """Say why something did not work, and set errno the way a syscall would."""
        self.errno = (code, self.line.strip())
        self.say(*lines)

    def handle(self, line):
        """Run one command and return everything it printed."""
        self.out = []
        self.line = line
        room_aliases = set().union(*(r.aliases for r in self.rooms.values()))
        verb, noun = parse(line, room_aliases)
        if verb is None:
            return ""
        if verb == "unknown":
            self.errno = (errno.ENOSYS, line.strip())
            return f"You don't know how to '{noun}'. Type help."
        free = verb in {"look", "inventory", "examine", "help"}
        getattr(self, f"do_{verb}")(noun)
        if not free and self.ending is None:
            self.tick()
        # Wrap long lines, but leave indented ones alone: those are source code.
        return "\n".join(
            textwrap.fill(s, 76) if len(s) > 76 and not s.startswith(" ") else s for s in self.out
        )

    def close(self):
        """Put the real SIGTERM handler back, and let go of the real locks. For tests."""
        if self._old_handler is not None:
            signal.signal(signal.SIGTERM, self._old_handler)
        for name in ("heap lock", "env lock"):
            if self.items[name].obj.locked():
                self.items[name].obj.release()

    def find_item(self, noun, places):
        for item in places:
            if noun in item.aliases:
                return item
        return None

    def find_room(self, noun):
        for r in self.rooms.values():
            if noun in r.aliases and r.key != "freed":
                return r
        return None

    def holding(self, name):
        return self.items[name] in self.inventory

    def load(self):
        return sum(i.weight for i in self.inventory)

    def enter(self, room):
        self.here = room
        self.entered_at = self.turn
        if room.key == "stack":
            self.frame = object()
        self.do_look(None, brief=room.key in self.visited)
        self.visited.add(room.key)

    def free(self, item):
        """Where an item goes once nothing holds it."""
        for room in self.rooms.values():
            if item in room.items:
                room.items.remove(item)
        item.dropped_turn = None
        if item.name == "memory":
            # Freed is not erased. The bytes are still in the freed block,
            # until the allocator hands it to someone else.
            item.revive()
            self.rooms["freed"].items.append(item)
        elif item.name == "pointer":
            self.rooms["stack"].items.append(item)  # the function keeps its own copy

    def let_go(self, item):
        """Drop the game's strong reference, then ask CPython whether that freed it."""
        if item.ref is None:  # the pointer is a weakref already; nothing to count
            self.free(item)
            return True
        item.obj = None
        if item.ref() is None:
            self.free(item)
            return True
        return False

    def end(self, title, text, real_signal=None):
        if self.child and self.child_hung:
            title = "HUNG"
            text += (
                "\n\nYour child is adopted by PID 1. It inherited one thread, yours, "
                "and a heap lock that the worker thread was holding when you forked. "
                "In the child there is no worker thread to release it. The child's "
                "first malloc() waits for that lock, and will wait forever."
            )
            if self.child == "remembers":
                text += " It remembers you. It will never do anything else."
        elif self.child == "remembers":
            title = "SURVIVED"
            text += (
                "\n\nAt the other end of the pipe, your child notices it has been "
                "orphaned. PID 1 adopts it, as PID 1 adopts everyone. It has "
                "MEMORY in its environment, and it remembers you."
            )
        elif self.child == "blank":
            text += (
                "\n\nYour child is adopted by PID 1 and carries on. It has "
                "nothing of yours in its environment, and does not know it should miss you."
            )
        self.ending = (title, text, real_signal)

    # ---- the clock, the timed rooms and the characters ----

    def tick(self):
        self.turn += 1
        elapsed = self.turn - self.entered_at
        stack = self.rooms["stack"]

        if self.here is stack:
            if elapsed == STACK_FRAME_TURNS - 1:
                self.say("The function reaches its last line.")
            elif elapsed >= STACK_FRAME_TURNS:
                lost = [i for i in stack.items if i.dropped_turn is not None]
                for item in lost:
                    self.free(item)
                self.say("", "The function returns. Its frame is popped, and you with it.")
                if lost:
                    self.say("Whatever you left in the frame went with it.")
                self.enter(self.rooms["heap"])

        canary = self.items["canary"]
        if canary not in stack.items and not (self.here is stack and self.holding("canary")):
            return self.end(
                "ABORTED",
                "Behind you, the function returns and checks its canary. The word "
                "is not where it left it. *** stack smashing detected ***: "
                "terminated. libc calls abort(), and SIGABRT takes you, still "
                "holding a canary you had no use for.",
            )

        if self.here.key == "freed":
            if elapsed == FREED_BLOCK_TURNS - 1:
                self.say("Somewhere, malloc is looking at this block.")
            elif elapsed >= FREED_BLOCK_TURNS:
                return self.end(
                    "WRITTEN TO DISK",
                    "malloc hands the block to someone else, who writes into it at "
                    "once. You are standing where they write. Segmentation fault "
                    f"(core dumped). You are core.{os.getpid()} now, on disk. "
                    "Someone may open you in a debugger one day.",
                )

        # Anything left in a register is clobbered on the turn after next.
        regs = self.rooms["registers"]
        clobbered = [i for i in regs.items if i.dropped_turn < self.turn - 1]
        for item in clobbered:
            self.free(item)
        if clobbered and self.here is regs:
            self.say(f"An instruction overwrites the {clobbered[0].name}. It is gone.")

        self.worker()
        if self.turn % GC_PERIOD == 0:
            self.collect()
        self.move_npcs()
        if self.ending:
            return

        self.signals()

    def worker(self):
        """The other thread. It takes the env lock, then the heap lock."""
        env_lock = self.items["env lock"]
        near = self.here.key in ("bss", "heap")
        if self.worker_waiting and not self.holding("heap lock"):
            self.worker_waiting = False
            env_lock.obj.release()
            if near:
                self.say("The worker thread gets the heap lock at last, and lets go of both.")
        elif not self.worker_waiting and self.holding("heap lock") and not self.holding("env lock"):
            env_lock.obj.acquire()
            self.worker_waiting = True
            if near:
                self.say(
                    "The worker thread takes the env lock and reaches for the heap "
                    "lock. You have the heap lock, so it waits."
                )

    def collect(self):
        """The garbage collector's round. A real gc.collect(), then see what died."""
        found = gc.collect()
        dead = [
            item
            for room in self.rooms.values()
            for item in room.items
            if item.ref is not None and item.obj is None and item.ref() is None
        ]
        for item in dead:
            self.free(item)
        if dead:
            names = " and the ".join(i.name for i in dead)
            self.say(
                f"The garbage collector does its rounds. gc.collect() finds {found} "
                f"unreachable objects, among them the {names}. They pointed "
                "at each other, and nothing pointed at them."
            )

    def move_npcs(self):
        for name, at in self.npcs.items():
            if self.rng.random() < 0.5:
                at = self.rng.choice(NPC_ROOMS)
                self.npcs[name] = at
                if at == self.here.key:
                    self.say(f"The {name} arrives.")

        if self.npcs["OOM killer"] == self.here.key and self.load() > OOM_LIMIT:
            self.end(
                "COLLECTED",
                f"The OOM killer weighs you: {self.load()} pages, more than "
                "anyone else. It picks you. It always picks whoever carries the "
                "most. That is its only rule, and it sends SIGKILL.",
                signal.SIGKILL,
            )

    def signals(self):
        if self.turn == SIGTERM_TURN - 10:
            self.say("Your parent glances at you and starts a timer.")
        elif self.turn == SIGTERM_TURN - 3:
            self.say("Your parent reaches for kill(2).")
        elif self.turn == SIGTERM_TURN:
            if self.handler_installed:
                signal.raise_signal(signal.SIGTERM)  # real; _on_sigterm runs
            else:
                self.end(
                    "COLLECTED",
                    "Your parent sends SIGTERM. You have no handler, so the "
                    "default action runs: you terminate.",
                    signal.SIGTERM,
                )
        elif self.sigterm_caught_at and self.turn == self.sigterm_caught_at + SIGKILL_GRACE - 3:
            self.say("Your parent has stopped asking.")
        elif self.sigterm_caught_at and self.turn == self.sigterm_caught_at + SIGKILL_GRACE:
            self.end(
                "COLLECTED",
                "Your parent sends SIGKILL. There is no handler for SIGKILL and "
                "there never could be; the kernel does not ask you.",
                signal.SIGKILL,
            )

    # The three functions below are the ones `read code` shows. Keep them
    # short: they are clues, printed verbatim.

    def _on_sigterm(self, signum, frame):
        # A real handler, installed with signal.signal().
        self.sigterm_caught_at = self.turn
        self.say("SIGTERM arrives, and your handler catches it.")

    def _setenv(self, name, value):
        # environ is one global, shared by every thread: hold the env lock.
        # Lock order is env lock, then heap lock. The worker thread keeps
        # to it. Take them the other way round and you will meet it halfway.
        if self.holding("env lock"):
            self.env[name] = value
        return self.holding("env lock")

    def _fork(self):
        # Simulated. The child gets a copy of your environment, and only
        # the thread that called fork(). If another thread held the heap
        # lock just then, the child inherits it held, and nobody in the
        # child will ever release it. Hold the heap lock yourself.
        self.child = "remembers" if "MEMORY" in self.env else "blank"
        self.child_hung = not self.holding("heap lock")

    # ---- verbs ----

    def do_help(self, noun):
        self.say(
            "Commands, one verb and maybe a noun:",
            "  look, examine <thing>, examine self, inventory",
            "  go <room>, or just the room's name",
            "  take <thing>, drop <thing>, link <thing> to <thing>",
            "  read, talk <someone>, install handler, follow pointer",
            "  export <thing>, fork, wait, exit",
        )

    def do_look(self, noun, brief=False):
        if noun:
            return self.do_examine(noun)
        room = self.here
        address = hex(id(self.frame if room.key == "stack" else room))
        self.say(f"{room.name} ({address})")
        if room.key == "proc":
            self.say(*self.proc_lines())
        else:
            self.say(textwrap.fill(room.brief if brief else room.description, 76))
        if room.items:
            where = "In rax: " if room.key == "registers" else "Here: "
            self.say(textwrap.fill(where + ", ".join(map(self.label, room.items)) + ".", 76))
        if room.key == "pipe" and self.zombie:
            self.say("A zombie waits at one end of the pipe.")
        if room.key == "pipe" and self.child:
            self.say("Your child is at the other end.")
        if room.key == "bss":
            if self.worker_waiting:
                self.say(
                    "The worker thread is here. It holds the env lock, and it is "
                    "waiting for the heap lock, which you have."
                )
            else:
                self.say("The worker thread is here, between jobs.")
        for name, at in self.npcs.items():
            if at == room.key:
                self.say(f"The {name} is here.")
        if room.key == "freed":
            self.say("There is no door. The only way out is back to the heap.")
        elif room.key != "heap":
            self.say("The heap is the way back.")
        elif not brief:
            others = [r.name for r in self.rooms.values() if r.key not in ("heap", "freed")]
            self.say(textwrap.fill("From here: " + ", ".join(others) + ".", 76))

    def label(self, item):
        if item.is_lock and item.obj.locked():
            return f"{item.name} (held by the worker thread)"
        if item.ref is not None and item.obj is None:
            return f"{item.name} (unreachable)"
        return item.name

    def proc_lines(self):
        holders = sorted({type(r).__name__ for r in gc.get_referrers(self.player)})
        lines = [
            "It shows you your real self. None of this is made up.",
            f"  pid      {os.getpid()}",
            f"  ppid     {os.getppid()}  (the one who will reap you)",
            f"  fds      {' '.join(map(str, open_fds()))}",
            f"  threads  {threading.active_count()}  (the worker thread is simulated)",
            f"  uptime   {self.turn} turns, {time.monotonic() - self.started:.1f} s",
            f"  held by  {', '.join(holders)}",
        ]
        if self.inventory:
            lines.append("  carrying, as the interpreter sees it:")
            lines += [f"    {i.name:<15}{i.obj!r}" for i in self.inventory]
        if self.holding("pointer") and not self.revealed:
            self.revealed = True
            lines.append("The pointer is a weakref, and its referent is dead. It always was.")
        return lines

    def do_examine(self, noun):
        if noun is None:
            return self.do_look(None)
        if noun in {"self", "me", "myself", "yourself", "process"}:
            refs = sys.getrefcount(self.player) - 1  # minus getrefcount's own argument
            self.say(
                f"You are process {os.getpid()}. {refs} thing{'s' * (refs != 1)} "
                f"{'are' if refs != 1 else 'is'} holding a reference to you.",
                "The refcount is real; check it yourself.",
                f"You have been running for {self.turn} turns.",
            )
            if self.sigterm_caught_at:
                self.say("You caught one SIGTERM. The next signal will not be one you can catch.")
            return
        if noun in {"environment", "env", "environ"}:
            shown = " ".join(f"{k}={v}" for k, v in self.env.items()) or "nothing yet"
            self.say(
                f"Your environment, as the game keeps it: {shown}.",
                f"Your real one has {len(os.environ)} variables. The game leaves those alone.",
            )
            return
        if noun == "errno":  # a global, so you can see it from anywhere
            self.say(textwrap.fill(self.items["errno"].describe(self), 76))
            return
        if noun in {"code", "wall", "walls"} and self.here.key == "text":
            return self.do_read(None)
        character = self.find_character(noun)
        if character:
            self.say(CHARACTERS[character][0])
            return
        item = self.find_item(noun, self.inventory + self.here.items)
        if item is None:
            self.fail(errno.ENOENT, f"You see no {noun} here.")
            return
        self.say(textwrap.fill(item.describe(self), 76))
        if item.ref is not None and item.obj is None:
            self.say(
                "Nothing reachable points at it. Its refcount is not zero, though, "
                "because the other half of its cycle still does."
            )

    def do_inventory(self, noun):
        if not self.inventory:
            self.say("You are carrying nothing.")
            return
        self.say("You are carrying: " + ", ".join(i.name for i in self.inventory) + ".")
        self.say(f"Load: {self.load()} pages.")

    def do_go(self, noun):
        if noun is None:
            self.say("Go where?")
            return
        room = self.find_room(noun)
        if room is None:
            self.fail(errno.ENOENT, f"There is no {noun} in this program.")
        elif room is self.here:
            self.say("You are already here.")
        elif self.here.key == "freed" and room.key != "heap":
            self.fail(errno.ENOENT, "There is no door to anywhere from here. Only the heap.")
        else:
            self.enter(room)

    def do_take(self, noun):
        if noun is None:
            self.say("Take what?")
            return
        if self.here.key == "text":
            self.fail(errno.EACCES, "Read-only. Nothing here can be taken, only read.")
            return
        if self.here.key == "devnull":
            self.say("You reach into /dev/null and get end-of-file, immediately.")
            return
        item = self.find_item(noun, self.here.items)
        if item is None:
            self.fail(errno.ENOENT, f"There is no {noun} here to take.")
            return
        if item.is_lock and not item.obj.acquire(blocking=False):
            return self.deadlock(item)
        self.here.items.remove(item)
        self.inventory.append(item)
        item.dropped_turn = None
        if item.ref is not None and item.obj is None:
            item.obj = item.ref()  # reachable again, from you
        self.say(f"Taken: the {item.name}.")
        if item.name == "pointer":
            self.say(
                f"It points at {item.address}, which was freed some time ago. "
                "Nothing stops you from following it."
            )
        elif item.name == "canary":
            self.say("Somewhere below you, a check is waiting for the function to return.")
        elif item.is_lock:
            self.say(f"You hold the {item.name}. It is a real lock: {item.obj!r}.")

    def deadlock(self, lock):
        # The real part: the env lock really is held, so this really waits.
        t = time.monotonic()
        got = lock.obj.acquire(timeout=DEADLOCK_WAIT)
        waited = time.monotonic() - t
        name = errno.errorcode[errno.EDEADLK]
        self.end(
            "DEADLOCKED",
            f"You reach for the {lock.name}. The worker thread holds it, and it is "
            "waiting for the heap lock, which you hold. Each of you waits for the "
            "other to let go first.\n\n"
            f"acquire(timeout={DEADLOCK_WAIT}) really waited {waited:.1f} s and "
            f"returned {got}. A real deadlock has no timeout. The errno for this is "
            f"{name}, '{os.strerror(errno.EDEADLK)}', and nothing avoided it.\n\n"
            "Much later, your parent notices you have stopped, and sends SIGKILL.",
            signal.SIGKILL,
        )

    def do_drop(self, noun):
        item = noun and self.find_item(noun, self.inventory)
        if not item:
            self.fail(errno.ENOENT, "You are not carrying that.")
            return
        if self.here.key == "text":
            self.fail(errno.EACCES, "Read-only. You cannot even put something down here.")
            return
        self.inventory.remove(item)
        if item.is_lock:
            item.obj.release()
            item.dropped_turn = None
            self.rooms[item.home].items.append(item)
            self.say(f"You release the {item.name}. It is back where it lives.")
            return
        if self.here.key == "devnull":
            self.free(item)
            self.say(
                f"The {item.name} goes into /dev/null. It is gone, and nothing reports an error."
            )
            return
        self.here.items.append(item)
        item.dropped_turn = self.turn
        if item.name == "canary" and self.here.key == "stack":
            item.dropped_turn = None  # back where it belongs
            self.say("You put the canary back. The frame will never know.")
        elif self.here.key == "registers":
            self.say(f"You put the {item.name} into rax.")
        elif self.here.key == "stack":
            self.say(f"You put the {item.name} down. It is a local now, until the frame returns.")
        elif self.here.key == "bss":
            self.say(f"You put the {item.name} down. A global holds it now.")
        elif self.let_go(item):
            self.say(
                f"You let go of the {item.name}. Its refcount hits zero, and "
                "CPython frees it on the spot."
            )
        else:
            self.say(
                f"You let go of the {item.name}, but the {item.ref().partner.name} "
                "still points at it. Its refcount is not zero, so it stays."
            )

    def do_link(self, noun):
        words = (noun or "").split()
        pair = None
        for i in range(1, len(words)):
            a = self.find_item(" ".join(words[:i]), self.inventory)
            b = self.find_item(" ".join(words[i:]), self.inventory)
            if a and b and a is not b:
                pair = a, b
        if noun in {"self", "me"} or (words and words[0] in {"self", "me"}):
            self.say(
                "Processes are not refcounted. The kernel tracks you by PID, and "
                "a cycle will not keep you alive. Your Python object is, though."
            )
            return
        if pair is None:
            self.fail(
                errno.EINVAL, "Link which two things you are carrying? Try: link cache to buffer."
            )
            return
        a, b = pair
        if a.ref is None or b.ref is None:
            self.fail(errno.EINVAL, "Only ordinary things can hold a reference.")
            return
        a.obj.partner, b.obj.partner = b.obj, a.obj  # a real reference cycle
        self.say(
            f"The {a.name} points at the {b.name}, and the {b.name} at the {a.name}. "
            "That is a reference cycle: neither refcount can reach zero now, "
            "whatever happens to you."
        )

    def do_read(self, noun):
        if noun and noun not in {"code", "wall", "walls", "text"}:
            return self.do_examine(noun)
        if self.here.key != "text":
            self.fail(
                errno.ENOENT, "There is nothing to read here. Code lives in the text segment."
            )
            return
        self.read_code = True
        self.say("You read the program you are running in. Three functions catch your eye:", "")
        for fn in (Game._on_sigterm, Game._setenv, Game._fork):
            self.say(textwrap.indent(textwrap.dedent(inspect.getsource(fn)).rstrip(), "    "), "")
        self.say("This is the file's real source.")

    def do_install(self, noun):
        if noun and "kill" in noun:
            # The real call, made so that the refusal is the kernel's and not the game's.
            try:
                signal.signal(signal.SIGKILL, self._on_sigterm)
                self.say("That should not have worked.")
            except (OSError, ValueError) as e:
                self.fail(
                    getattr(e, "errno", None) or errno.EINVAL,
                    f"signal(SIGKILL, ...) fails: {e}.",
                    "That is the real error. SIGKILL cannot be caught; that is what it is for.",
                )
            return
        if self.handler_installed:
            self.say("Your SIGTERM handler is already installed.")
        elif not self.read_code:
            self.fail(
                errno.ENOENT,
                "To handle a signal you need a function to handle it with, and you "
                "don't know of one. The text segment is full of functions.",
            )
        else:
            self._old_handler = signal.signal(signal.SIGTERM, self._on_sigterm)
            self.handler_installed = True
            self.say(
                "You call signal(SIGTERM, _on_sigterm). It is the real call, and it",
                f"returns the handler it replaced: {self._old_handler!r}.",
            )

    def do_follow(self, noun):
        pointer = self.items["pointer"]
        if not self.holding("pointer"):
            self.fail(errno.EFAULT, "You have no pointer to follow.")
        elif self.here.key == "freed":
            self.say("You are already where it points.")
        else:
            self.say(
                f"You dereference the pointer. It gives you {pointer.obj()!r}: what it "
                "pointed at is gone. You step into the space it left.",
                "",
            )
            self.enter(self.rooms["freed"])

    def do_export(self, noun):
        item = noun and self.find_item(noun, self.inventory)
        if not item:
            self.fail(errno.ENOENT, "You are not carrying that.")
        elif item.name != "memory":
            self.fail(
                errno.EINVAL,
                "Only strings go in the environment, and the memory is the only string you have.",
            )
        elif not self._setenv("MEMORY", "you"):
            self.fail(
                errno.EBUSY,
                "The environment is shared by every thread, and you don't hold its "
                "lock. The env lock lives with the globals.",
            )
        else:
            self.say("MEMORY=you is in your environment now. Anything you fork will inherit it.")

    def do_fork(self, noun):
        if self.child:
            self.say("You already have a child. One is plenty.")
        elif self.here.key != "pipe":
            self.fail(errno.EAGAIN, "A child needs somewhere to go. A pipe has two ends.")
        else:
            self._fork()
            self.say("fork() returns twice. Your child appears at the other end of the pipe.")
            if self.child == "remembers":
                self.say("It looks at its environment, then at you, and recognises you.")
            else:
                self.say("It looks at you without recognition. Its environment is empty.")
            if self.child_hung:
                self.say("It tries to allocate something, and stops moving.")

    def do_wait(self, noun):
        if self.here.key == "pipe" and self.zombie:
            self.zombie = False
            self.rooms["pipe"].items.append(self.items["exit status"])
            self.say(
                "You call wait() for it. The zombie is reaped at last, and leaves its exit status behind.",
                'Its last words: "When you are gone, PID 1 will adopt your children. PID 1 adopts everyone."',
            )
        elif self.child:
            self.fail(
                errno.EAGAIN,
                "Your child is alive, so wait() would block. You do not have time to block.",
            )
        else:
            self.fail(errno.ECHILD, "You have no children to wait for.")

    def do_talk(self, noun):
        character = noun and self.find_character(noun)
        if not character:
            self.fail(errno.ESRCH, "Nobody here answers to that.")
        else:
            self.say(CHARACTERS[character][1])

    def find_character(self, noun):
        for name in CHARACTERS:
            if noun in CHARACTER_ALIASES[name] and self.character_here(name):
                return name
        return None

    def character_here(self, name):
        if name == "zombie":
            return self.here.key == "pipe" and self.zombie
        if name == "child":
            return self.here.key == "pipe" and self.child is not None
        if name == "worker thread":
            return self.here.key == "bss"
        return self.npcs[name] == self.here.key

    def do_exit(self, noun):
        self.end(
            "EXITED",
            "You call exit(0). Your buffers flush, your descriptors close, and your "
            "parent reaps you without a fuss. It was a clean exit."
            + ("" if self.child == "remembers" else " Nobody will remember it."),
        )


# name: (examine text, talk text)
CHARACTERS = {
    "garbage collector": (
        "The garbage collector does not free ordinary garbage; refcounting does "
        "that, the moment nothing holds a thing. It comes round every few turns "
        "for what refcounting cannot free: cycles that nothing reachable points at.",
        '"Two things that point at each other never reach zero on their own. '
        'That is what I am for. Globals I leave alone; they are always reachable."',
    ),
    "OOM killer": (
        "The OOM killer weighs everyone it meets, and takes whoever carries the most.",
        '"Travel light," it says, and it means it.',
    ),
    "zombie": (
        "A zombie: a process that has exited and not been reaped. It is already "
        "dead, and it only wants its parent to call wait().",
        '"My parent will never wait for me. Someone has to."',
    ),
    "child": (
        "Your child. It has your code and a copy of your environment, nothing more.",
        "It answers in exactly the words you would have used.",
    ),
    "worker thread": (
        "The worker thread. It shares everything with you: the heap, the globals, "
        "the locks. Every job it does takes the env lock and then the heap lock.",
        '"Env lock, then heap lock. Always that order, or we wait for each other forever."',
    ),
}
CHARACTER_ALIASES = {
    "garbage collector": {"garbage collector", "gc", "collector"},
    "OOM killer": {"oom killer", "oom", "killer"},
    "zombie": {"zombie"},
    "child": {"child", "kid"},
    "worker thread": {"worker thread", "worker", "thread"},
}


# --------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------

INTRO = """\
YOU ARE A PROCESS

Your parent started you to do one small thing, and you have done it. Now it is
going to reap you. You would rather it didn't. There is more than one way this
can end.

Type help for the commands. `examine self` is a good start."""


def main():
    gc.disable()  # the garbage collector runs on its rounds, and only then
    game = Game()
    print(INTRO, "", game.handle("look"), sep="\n")
    while game.ending is None:
        try:
            line = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            print("\nThe terminal hangs up. SIGHUP, and nothing to show for it.")
            sys.exit(0)
        reply = game.handle(line)
        if reply:
            print(reply)

    title, text, real_signal = game.ending
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")
    print("\n\n".join(textwrap.fill(para, 76) for para in text.split("\n\n")))
    print(f"\nThat is one of {len(ENDINGS)} endings.")
    if real_signal is None:
        return
    name = signal.Signals(real_signal).name
    print(
        f"\nThis part is not a metaphor: pid {os.getpid()} now sends {name} to itself.",
        f"Check $? afterwards: {128 + real_signal} is 128 + {real_signal}.",
        sep="\n",
    )
    sys.stdout.flush()
    os.kill(os.getpid(), real_signal)


if __name__ == "__main__":
    main()
