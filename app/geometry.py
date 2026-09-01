"""Small geometry helpers shared by the display modules."""
from __future__ import annotations

from typing import Dict, List, Set, Tuple

Coord = Tuple[int, int]

STEPS: Dict[str, Coord] = {
    "N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0),
}


def path_cells(entry: Coord, path: List[str]) -> Set[Coord]:
    """Return every cell visited by *path* (N/E/S/W), starting at *entry*."""
    cells = {entry}
    x, y = entry
    for letter in path:
        dx, dy = STEPS[letter]
        x, y = x + dx, y + dy
        cells.add((x, y))
    return cells
