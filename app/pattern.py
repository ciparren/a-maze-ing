"""The subject's mandatory "42" pattern.

Produces the set of cells that must be permanently closed to draw a visible
"42" made of fully-closed cells, per Chapter IV.4 of the subject.
"""
from __future__ import annotations

from typing import Set, Tuple

Coord = Tuple[int, int]

# 5-wide pixel-font "4" and "2", one blank column apart.
_BITMAP = (
    "#...#.#####",
    "#...#.....#",
    "#...#.....#",
    "#####.#####",
    "....#.#....",
    "....#.#....",
    "....#.#####",
)
PATTERN_WIDTH = len(_BITMAP[0])
PATTERN_HEIGHT = len(_BITMAP)
MIN_WIDTH_FOR_PATTERN = PATTERN_WIDTH + 2  # 1-cell margin on each side
MIN_HEIGHT_FOR_PATTERN = PATTERN_HEIGHT + 2
# Index of the blank column between the "4" and the "2" in _BITMAP.
_GAP_COLUMN = 5


def pattern_cells(width: int, height: int) -> Set[Coord]:
    """Return the "42" pattern's cells centered in a *width* x *height* grid.

    The bitmap is placed so that the grid's centre cell
    ``(width // 2, height // 2)`` always falls on its blank middle column
    (between the "4" and the "2"). That keeps the centre an open corridor --
    required by the playable mode's "player starts in the centre" rule --
    without cutting a hole in either digit.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.

    Returns:
        The set of ``(x, y)`` cells to block, or an empty set (after
        printing the subject-required console message) if the grid is too
        small to fit the pattern with a 1-cell margin.
    """
    if width < MIN_WIDTH_FOR_PATTERN or height < MIN_HEIGHT_FOR_PATTERN:
        print(
            "Error: the maze is too small to fit the mandatory '42' "
            f"pattern ({PATTERN_WIDTH}x{PATTERN_HEIGHT} cells + a 1-cell "
            f"margin needed, got {width}x{height}) -- omitting it."
        )
        return set()

    origin_x = width // 2 - _GAP_COLUMN
    origin_y = (height - PATTERN_HEIGHT) // 2
    return {
        (origin_x + col, origin_y + row)
        for row, line in enumerate(_BITMAP)
        for col, char in enumerate(line)
        if char == "#"
    }
