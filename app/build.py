"""Orchestrate one full maze build: obstacles, generation, braiding, solving.

This is where the generic :mod:`mazegen` primitives get composed into the
42-subject-specific rules (the "42" pattern, the Pac-Man corner/centre
requirement). None of this lives inside the reusable package itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from mazegen import MazeError, MazeGenerator

from .config import Config
from .pattern import pattern_cells

Coord = Tuple[int, int]

# Subject's playable-mode thresholds (Chapter IV.4): at least 2 independent
# routes, dead-ends "rare". We aim a bit above the minimum for safety margin.
MIN_LOOPS = 2
TARGET_LOOPS = 3
MAX_DEAD_ENDS = 2


@dataclass(frozen=True)
class BuiltMaze:
    """A generated, solved maze ready to be written/displayed."""

    generator: MazeGenerator
    path: List[str]
    pattern: Tuple[Coord, ...]


def build_maze(config: Config) -> BuiltMaze:
    """Build a full maze (obstacles + generation + solving) from *config*.

    Raises:
        MazeError: on an invalid configuration, or a maze that cannot
            satisfy the subject's requirements (e.g. entry/exit inside the
            "42" pattern, or too small to fit the required loops).
    """
    obstacles = pattern_cells(config.width, config.height)
    for name, cell in (("ENTRY", config.entry), ("EXIT", config.exit)):
        if cell in obstacles:
            raise MazeError(
                f"{name}={cell[0]},{cell[1]} falls inside the mandatory "
                f"'42' pattern -- pick a different cell"
            )

    generator = MazeGenerator(config.width, config.height, seed=config.seed)
    generator.block_cells(obstacles)
    generator.generate()

    if not config.perfect:
        generator.braid(min_loops=TARGET_LOOPS, max_dead_ends=MAX_DEAD_ENDS)
        _check_key_cells(generator)

    path = generator.solve(config.entry, config.exit)
    return BuiltMaze(generator, path, tuple(sorted(obstacles)))


def _check_key_cells(generator: MazeGenerator) -> None:
    """Verify the four corners and the centre are open corridors."""
    width, height = generator.width, generator.height
    key_cells = {
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, height // 2),
    }
    blocked_key_cells = key_cells & generator.blocked
    if blocked_key_cells:
        raise MazeError(
            "the '42' pattern blocks a corner or the centre cell "
            f"({sorted(blocked_key_cells)}); use a larger maze"
        )
