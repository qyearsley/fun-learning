"""Tests for `asm_tour.s`, the literate ARM64 assembly tour.

The program is arm64 macOS only: it makes raw macOS syscalls. So these tests
build it with `clang` and skip on any other host. On Linux CI they always
skip, which is why CI has a separate macOS job that runs this file. That job
sets ASM_TOUR_REQUIRED=1, which turns the skip off, so a runner that stops
being arm64 fails the job instead of passing it with nothing run.

Each section of the tour prints one line, so checking the whole output checks
every section: the string lengths the assembler computes, both paths through
the conditionals, both loops, number printing including the most negative
64-bit value, and FizzBuzz.
"""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "asm_tour.s"

EXPECTED = """\
2. Hello: one write syscall, no libc.
3. Functions: this line came through print(pointer, length).
4. Conditionals, with a branch: -7 is negative.
4. Conditionals, with csel:     42 is not negative.
5. Loops: strlen measured this line.
5. Loops, counted: **********
6. Numbers: 0 42 -7 9223372036854775807 -9223372036854775808
7. FizzBuzz: 1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz
"""


CAN_RUN = (
    sys.platform == "darwin" and platform.machine() == "arm64" and shutil.which("clang") is not None
)
REQUIRED = os.environ.get("ASM_TOUR_REQUIRED") == "1"


@unittest.skipUnless(CAN_RUN or REQUIRED, "needs arm64 macOS and clang")
class TestAsmTour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        binary = Path(cls.tmp.name) / "asm_tour"
        subprocess.run(["clang", "-o", binary, SOURCE], check=True)
        cls.result = subprocess.run([binary], capture_output=True, text=True, timeout=10)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_section_prints_its_line(self):
        self.assertEqual(self.result.stdout, EXPECTED)

    def test_section_one_exits_with_status_zero(self):
        self.assertEqual(self.result.returncode, 0)

    def test_nothing_goes_to_stderr(self):
        self.assertEqual(self.result.stderr, "")


if __name__ == "__main__":
    unittest.main()
