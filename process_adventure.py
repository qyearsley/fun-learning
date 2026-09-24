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
pointer leads into freed memory, and a forked child inherits your environment.

What is real, and what is simulated
-----------------------------------
The game reads its own runtime, so a lot of it is not a metaphor.

Real (read-only introspection of the process running this file):
- Your PID and your parent's PID, from `os.getpid` and `os.getppid`.
- The refcount in `examine self`, from `sys.getrefcount`, and the holders in
  /proc, from `gc.get_referrers`.
- Every 0x... address. Each one is the `id()` of an object the game allocated.
- The dangling pointer. It is a `weakref.ref` to an object that has been freed,
  and following it really dereferences to None.
- The open file descriptors in /proc, read from `/dev/fd`.
- The code in the text segment. It is this file's source, read with `inspect`.
- The SIGTERM handler. `install handler` calls `signal.signal`, and SIGTERM
  arrives through `signal.raise_signal`. Try the same for SIGKILL and the
  operating system refuses, with its own error message.
- The last signal. If SIGTERM arrives with no handler installed, or SIGKILL
  arrives at all, the game prints the ending and then really sends that signal
  to itself.

Simulated (anything that would break the game if it were real):
- fork, the environment, the pipe and the zombie.
- The garbage collector and the OOM killer as characters, the allocator reusing
  a block, the segfault and the core file.
"""

import gc
import inspect
import os
import random
import signal
import sys
import textwrap
import time
import weakref

SIGTERM_TURN = 40  # when your parent loses patience
SIGKILL_GRACE = 15  # turns between a caught SIGTERM and the SIGKILL behind it
STACK_FRAME_TURNS = 4  # turns before the current function returns
FREED_BLOCK_TURNS = 4  # turns before the allocator hands the block out again
OOM_LIMIT = 6  # pages you can carry before the OOM killer takes an interest
NPC_ROOMS = ("heap", "stack", "pipe", "registers", "bss", "proc")


# --------------------------------------------------------------------------
# The world
# --------------------------------------------------------------------------


class Player:
    """You. A real object, so that your refcount and your address are real."""


class Block:
    """What the dangling pointer used to point at, before it was freed."""


class Item:
    def __init__(self, name, description, weight=1, aliases=(), obj=None):
        self.name = name
        # A string, or a function of the game for items that look at the
        # runtime every time you examine them.
        self.description = description
        self.weight = weight  # in pages; the OOM killer counts these
        self.aliases = {name, *aliases}
        self.obj = obj  # the real Python object behind the item, if any
        self.dropped_turn = None  # set when you let go; the GC takes only those

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
            f"A stack canary, {canary:#010x}: a random word placed to notice if "
            "anything overwrites the frame. It is watching you.",
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
        "mutex": Item(
            "mutex",
            "A mutex, unlocked. There is supposed to be a second one somewhere, "
            "and a rule about which order to take them in.",
            aliases={"lock"},
        ),
        "errno": Item(
            "errno",
            "errno. It is 0, which means nothing, because nobody has failed yet.",
        ),
        "fd": Item("fd", fd_text, aliases={"file descriptor", "descriptor"}),
        "exit status": Item(
            "exit status",
            "The zombie's exit status: 0. It did everything right and still had to wait.",
            aliases={"status"},
        ),
    }

    def room(key, name, description, aliases=(), holds=()):
        return Room(key, name, description, aliases, [items[n] for n in holds])

    rooms = {
        r.key: r
        for r in (
            room(
                "stack",
                "The stack",
                "Locals sit on a shelf that is not yours. Frames vanish when "
                "they return, and someone is going to return from this one soon.",
                aliases={"frame"},
                holds=("pointer", "return address", "canary"),
            ),
            room(
                "heap",
                "The heap",
                "Allocated blocks and free holes, in no order anyone chose. "
                "Every region of the program opens off it.",
                holds=("buffer", "cache", "mutex"),
            ),
            room(
                "text",
                "The text segment",
                "Read-only. You can change nothing here, but you can read the "
                "code, and the code is real: it is the program you are running in.",
                aliases={"text segment", ".text", "code"},
            ),
            room(
                "bss",
                "BSS and globals",
                "Zeroed at startup and never freed. Anything you leave here "
                "outlives everything else.",
                aliases={"globals", ".bss", "data"},
                holds=("errno",),
            ),
            room(
                "registers",
                "The registers",
                "Four slots: rax, rbx, rcx, rdx. Every one of them is overwritten "
                "constantly. Leave something here and it will not be here long.",
                aliases={"register", "regs"},
            ),
            room("proc", "/proc", "A mirror.", aliases={"/proc", "mirror"}),
            room(
                "devnull",
                "/dev/null",
                "A void. Drop something here and it is gone. Read from it and "
                "you get nothing, immediately.",
                aliases={"/dev/null", "dev/null", "null", "void"},
            ),
            room(
                "pipe",
                "A pipe",
                "A narrow buffer with two ends. Bytes go in one and come out the "
                "other. This is where processes meet.",
                holds=("fd",),
            ),
            room(
                "freed",
                "A freed block",
                "Nobody owns this block, so nothing stops you standing in it. "
                "The allocator will hand it to someone else soon.",
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
    "take": {"take", "get", "grab"},
    "drop": {"drop", "leave", "discard"},
    "examine": {"examine", "x", "inspect", "check"},
    "look": {"look", "l"},
    "inventory": {"inventory", "i", "inv"},
    "read": {"read"},
    "install": {"install", "trap", "handle", "catch"},
    "follow": {"follow", "dereference", "deref"},
    "export": {"export", "setenv"},
    "fork": {"fork"},
    "wait": {"wait", "reap"},
    "talk": {"talk", "ask"},
    "exit": {"exit", "quit", "q"},
    "help": {"help", "?"},
}
SYNONYMS = {word: verb for verb, words in VERBS.items() for word in words}
FILLER = {"the", "a", "an", "to", "at", "into", "in", "on", "with", "for", "my", "of"}


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
        self.inventory = []
        self.turn = 0
        self.entered_at = 0
        self.frame = object()  # the current stack frame; a new one per call
        self.started = time.monotonic()
        self.env = {}  # simulated; the real environment is left alone
        self.child = None  # None, "blank" or "remembers"
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

    def handle(self, line):
        """Run one command and return everything it printed."""
        self.out = []
        room_aliases = set().union(*(r.aliases for r in self.rooms.values()))
        verb, noun = parse(line, room_aliases)
        if verb is None:
            return ""
        if verb == "unknown":
            return f"You don't know how to '{noun}'. Type help."
        free = verb in {"look", "inventory", "examine", "help"}
        getattr(self, f"do_{verb}")(noun)
        if not free and self.ending is None:
            self.tick()
        return "\n".join(self.out)

    def close(self):
        """Put the real SIGTERM handler back the way it was. For tests."""
        if self._old_handler is not None:
            signal.signal(signal.SIGTERM, self._old_handler)

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

    def load(self):
        return sum(i.weight for i in self.inventory)

    def enter(self, room):
        self.here = room
        self.entered_at = self.turn
        if room.key == "stack":
            self.frame = object()
        self.do_look(None)

    def end(self, title, text, real_signal=None):
        if self.child == "remembers":
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

        if self.here.key == "stack":
            if elapsed == STACK_FRAME_TURNS - 1:
                self.say("The function reaches its last line.")
            elif elapsed >= STACK_FRAME_TURNS:
                stack = self.rooms["stack"]
                lost = [i for i in stack.items if i.dropped_turn is not None]
                stack.items = [i for i in stack.items if i not in lost]
                self.say("", "The function returns. Its frame is popped, and you with it.")
                if lost:
                    self.say("Whatever you left in the frame went with it.")
                self.enter(self.rooms["heap"])

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
        regs.items = [i for i in regs.items if i not in clobbered]
        if clobbered and self.here is regs:
            self.say(f"An instruction overwrites the {clobbered[0].name}. It is gone.")

        self.move_npcs()
        if self.ending:
            return

        self.signals()

    def move_npcs(self):
        for name, at in self.npcs.items():
            if self.rng.random() < 0.5:
                at = self.rng.choice(NPC_ROOMS)
                self.npcs[name] = at
                if at == self.here.key:
                    self.say(f"The {name} arrives.")

        gc_room = self.rooms[self.npcs["garbage collector"]]
        if gc_room.key != "bss":  # globals are always reachable
            taken = [i for i in gc_room.items if i.dropped_turn is not None]
            gc_room.items = [i for i in gc_room.items if i not in taken]
            if taken and gc_room is self.here:
                names = ", ".join(i.name for i in taken)
                self.say(
                    f"Nothing points at the {names} you left, so the garbage collector takes it."
                )

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

    # The two functions below are the ones `read code` shows. Keep them short:
    # they are clues, printed verbatim.

    def _on_sigterm(self, signum, frame):
        # A real handler, installed with signal.signal().
        self.sigterm_caught_at = self.turn
        self.say("SIGTERM arrives, and your handler catches it.")

    def _fork(self):
        # Simulated. The child gets a copy of your environment, and
        # nothing else of yours.
        self.child = "remembers" if "MEMORY" in self.env else "blank"

    # ---- verbs ----

    def do_help(self, noun):
        self.say(
            "Commands, one verb and maybe a noun:",
            "  look, examine <thing>, examine self, inventory",
            "  go <room>, or just the room's name",
            "  take <thing>, drop <thing>, read, talk <someone>",
            "  install handler, follow pointer, export <thing>, fork, wait, exit",
        )

    def do_look(self, noun):
        if noun:
            return self.do_examine(noun)
        room = self.here
        address = hex(id(self.frame if room.key == "stack" else room))
        self.say(f"{room.name} ({address})")
        if room.key == "proc":
            self.say(*self.proc_lines())
        else:
            self.say(textwrap.fill(room.description, 76))
        if room.key == "registers" and room.items:
            self.say("In rax: " + ", ".join(i.name for i in room.items) + ".")
        elif room.items:
            self.say("Here: " + ", ".join(i.name for i in room.items) + ".")
        if room.key == "pipe" and self.zombie:
            self.say("A zombie waits at one end of the pipe.")
        if room.key == "pipe" and self.child:
            self.say("Your child is at the other end.")
        for name, at in self.npcs.items():
            if at == room.key:
                self.say(f"The {name} is here.")
        if room.key == "freed":
            self.say("There is no door. The only way out is back to the heap.")
        elif room.key != "heap":
            self.say("The heap is the way back.")
        else:
            others = [r.name for r in self.rooms.values() if r.key not in ("heap", "freed")]
            self.say(textwrap.fill("From here: " + ", ".join(others) + ".", 76))

    def proc_lines(self):
        holders = sorted({type(r).__name__ for r in gc.get_referrers(self.player)})
        lines = [
            "It shows you your real self. None of this is made up.",
            f"  pid      {os.getpid()}",
            f"  ppid     {os.getppid()}  (the one who will reap you)",
            f"  fds      {' '.join(map(str, open_fds()))}",
            f"  uptime   {self.turn} turns, {time.monotonic() - self.started:.1f} s",
            f"  held by  {', '.join(holders)}",
        ]
        if self.inventory:
            lines.append("  carrying, as the interpreter sees it:")
            lines += [
                f"    {i.name:<15}{i.obj if i.obj is not None else i!r}" for i in self.inventory
            ]
        if self.items["pointer"] in self.inventory and not self.revealed:
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
        if noun in {"code", "wall", "walls"} and self.here.key == "text":
            return self.do_read(None)
        character = self.find_character(noun)
        if character:
            self.say(CHARACTERS[character][0])
            return
        item = self.find_item(noun, self.inventory + self.here.items)
        if item:
            self.say(textwrap.fill(item.describe(self), 76))
        else:
            self.say(f"You see no {noun} here.")

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
            self.say(f"There is no {noun} in this program.")
        elif room is self.here:
            self.say("You are already here.")
        elif self.here.key == "freed" and room.key != "heap":
            self.say("There is no door to anywhere from here. Only the heap.")
        else:
            self.enter(room)

    def do_take(self, noun):
        if noun is None:
            self.say("Take what?")
            return
        if self.here.key == "text":
            self.say("Read-only. Nothing here can be taken, only read.")
            return
        if self.here.key == "devnull":
            self.say("You reach into /dev/null and get end-of-file, immediately.")
            return
        item = self.find_item(noun, self.here.items)
        if item is None:
            self.say(f"There is no {noun} here to take.")
            return
        self.here.items.remove(item)
        self.inventory.append(item)
        item.dropped_turn = None
        self.say(f"Taken: the {item.name}.")
        if item.name == "pointer":
            self.say(
                f"It points at {item.address}, which was freed some time ago. "
                "Nothing stops you from following it."
            )

    def do_drop(self, noun):
        item = noun and self.find_item(noun, self.inventory)
        if not item:
            self.say("You are not carrying that.")
            return
        self.inventory.remove(item)
        if self.here.key == "devnull":
            self.say(
                f"The {item.name} goes into /dev/null. It is gone, and nothing reports an error."
            )
            return
        item.dropped_turn = self.turn
        self.here.items.append(item)
        where = "into rax" if self.here.key == "registers" else "down"
        self.say(f"You put the {item.name} {where}.")

    def do_read(self, noun):
        if noun and noun not in {"code", "wall", "walls", "text"}:
            return self.do_examine(noun)
        if self.here.key != "text":
            self.say("There is nothing to read here. Code lives in the text segment.")
            return
        self.read_code = True
        self.say("You read the program you are running in. Two functions catch your eye:", "")
        for fn in (Game._on_sigterm, Game._fork):
            self.say(textwrap.indent(textwrap.dedent(inspect.getsource(fn)).rstrip(), "    "), "")
        self.say("This is the file's real source.")

    def do_install(self, noun):
        if noun and "kill" in noun:
            # The real call, made so that the refusal is the kernel's and not the game's.
            try:
                signal.signal(signal.SIGKILL, self._on_sigterm)
                self.say("That should not have worked.")
            except (OSError, ValueError) as e:
                self.say(
                    f"signal(SIGKILL, ...) fails: {e}.",
                    "That is the real error. SIGKILL cannot be caught; that is what it is for.",
                )
            return
        if self.handler_installed:
            self.say("Your SIGTERM handler is already installed.")
        elif not self.read_code:
            self.say(
                "To handle a signal you need a function to handle it with, and you "
                "don't know of one. The text segment is full of functions."
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
        if pointer not in self.inventory:
            self.say("You have no pointer to follow.")
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
            self.say("You are not carrying that.")
        elif item.name != "memory":
            self.say(
                "Only strings go in the environment, and the memory is the only string you have."
            )
        else:
            self.env["MEMORY"] = "you"
            self.say("MEMORY=you is in your environment now. Anything you fork will inherit it.")

    def do_fork(self, noun):
        if self.child:
            self.say("You already have a child. One is plenty.")
        elif self.here.key != "pipe":
            self.say("A child needs somewhere to go. A pipe has two ends.")
        else:
            self._fork()
            self.say("fork() returns twice. Your child appears at the other end of the pipe.")
            if self.child == "remembers":
                self.say("It looks at its environment, then at you, and recognises you.")
            else:
                self.say("It looks at you without recognition. Its environment is empty.")

    def do_wait(self, noun):
        if self.here.key == "pipe" and self.zombie:
            self.zombie = False
            self.rooms["pipe"].items.append(self.items["exit status"])
            self.say(
                "You call wait() for it. The zombie is reaped at last, and leaves its exit status behind.",
                'Its last words: "When you are gone, PID 1 will adopt your children. PID 1 adopts everyone."',
            )
        elif self.child:
            self.say("Your child is alive, so wait() would block. You do not have time to block.")
        else:
            self.say("You have no children to wait for.")

    def do_talk(self, noun):
        character = noun and self.find_character(noun)
        if not character:
            self.say("Nobody here answers to that.")
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
        return self.npcs[name] == self.here.key

    def do_exit(self, noun):
        self.end(
            "EXITED",
            "You call exit(0). Your buffers flush, your descriptors close, and your "
            "parent reaps you without a fuss. It was a clean exit. Nobody will remember it.",
        )


# name: (examine text, talk text)
CHARACTERS = {
    "garbage collector": (
        "The garbage collector takes anything nobody points at. It looks at you, "
        "counts the references holding you, and moves on.",
        '"I don\'t take what is reachable. Globals are always reachable."',
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
}
CHARACTER_ALIASES = {
    "garbage collector": {"garbage collector", "gc", "collector"},
    "OOM killer": {"oom killer", "oom", "killer"},
    "zombie": {"zombie"},
    "child": {"child", "kid"},
}


# --------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------

INTRO = """\
YOU ARE A PROCESS

Your parent started you to do one small thing, and you have done it. Now it is
going to reap you. You would rather it didn't.

Type help for the commands. `examine self` is a good start."""


def main():
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
