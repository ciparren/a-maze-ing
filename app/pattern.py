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


def pattern_cells(width: int, height: int) -> Set[Coord]:
    """Return the "42" pattern's cells centered in a *width* x *height* grid.

    Returns an empty set (after printing the subject-required console
    notice) if the grid is too small to fit the pattern with a 1-cell
    margin.

    The exact centre cell ``(width // 2, height // 2)`` is always excluded
    from the pattern -- even though the bitmap is centered over it -- so it
    stays an open corridor, as required by the playable mode's "player
    starts in the centre" rule.
    """
    if width < MIN_WIDTH_FOR_PATTERN or height < MIN_HEIGHT_FOR_PATTERN:
        print(
            "Notice: the maze is too small to fit the mandatory '42' "
            f"pattern ({PATTERN_WIDTH}x{PATTERN_HEIGHT} cells needed, got "
            f"{width}x{height}) -- omitting it."
        )
        return set()

    origin_x = (width - PATTERN_WIDTH) // 2
    origin_y = (height - PATTERN_HEIGHT) // 2
    cells: Set[Coord] = {
        (origin_x + col, origin_y + row)
        for row, line in enumerate(_BITMAP)
        for col, char in enumerate(line)
        if char == "#"
    }
    cells.discard((width // 2, height // 2))
    return cells
