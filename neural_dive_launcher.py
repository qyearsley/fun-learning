#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "blessed>=1.20.0",
# ]
# ///
"""
Neural Dive launcher script with inline dependencies.
This uses uv to automatically install dependencies.
"""

from neural_dive.__main__ import main

if __name__ == "__main__":
    main()
