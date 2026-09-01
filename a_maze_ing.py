#!/usr/bin/env python3
"""a_maze_ing -- CLI entry point for the A-Maze-ing maze generator.

Reads a configuration file, generates a maze (perfect or playable), writes
it to the configured output file, and shows it using the configured
display. See ``config.txt`` for the file format and ``README.md`` for full
documentation.

Usage::

    python3 a_maze_ing.py config.txt
"""
from __future__ import annotations

import random
import sys
from dataclasses import replace
from typing import Callable, List

from app.build import BuiltMaze, build_maze
from app.config import Config, parse_config
from app.maze_io import write_output
from mazegen import MazeError

EXIT_OK = 0
EXIT_ERROR = 1


def _regenerate_factory(config: Config) -> Callable[[], BuiltMaze]:
    """Return a callback that builds a fresh maze and rewrites the output.

    Each call uses a new random seed -- only the *first* maze built from the
    config file uses its (possibly fixed) ``SEED``, so "re-generate" always
    produces a genuinely different maze.
    """
    def regenerate() -> BuiltMaze:
        fresh = replace(config, seed=random.SystemRandom().randrange(2**32))
        built = build_maze(fresh)
        write_output(
            fresh.output_file, built.generator,
            fresh.entry, fresh.exit, built.path,
        )
        return built

    return regenerate


def run(config_path: str) -> int:
    """Parse *config_path*, build/write the maze, and launch its display."""
    config = parse_config(config_path)
    built = build_maze(config)
    write_output(
        config.output_file, built.generator,
        config.entry, config.exit, built.path,
    )

    if config.display == "mlx":
        from app.display_mlx import run as display_run
    else:
        from app.display_ascii import run as display_run

    display_run(built, config.entry, config.exit, _regenerate_factory(config))
    return EXIT_OK


def main(argv: List[str]) -> int:
    """Parse arguments, run the program, turn every error into a message."""
    if len(argv) != 1:
        print("Usage: python3 a_maze_ing.py <config_file>")
        return EXIT_ERROR
    try:
        return run(argv[0])
    except FileNotFoundError as error:
        print(f"Error: file not found: {error.filename or argv[0]}")
        return EXIT_ERROR
    except (MazeError, OSError, RuntimeError) as error:
        print(f"Error: {error}")
        return EXIT_ERROR


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as error:  # never crash: always report and exit non-zero
        print(f"Unexpected error: {error}")
        sys.exit(EXIT_ERROR)
