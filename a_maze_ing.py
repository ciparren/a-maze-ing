"""Core maze generation logic.

The maze is stored as a grid of *wall bitmasks*.  Each cell holds an
integer in the range ``0..15`` where every bit tells whether the wall on
one side is **closed** (``1``) or **open** (``0``):

======  =========  =======
Bit     Value      Side
======  =========  =======
0 (LSB) 1          North
1       2          East
2       4          South
3       8          West
======  =========  =======

Coordinates follow the ``(x, y)`` convention used by the configuration
file: ``x`` grows to the East (columns), ``y`` grows to the South (rows).
Internally the grid is indexed ``grid[y][x]``.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Dict, List, Optional, Tuple

# Public type alias: a coordinate is an (x, y) pair.
Coord = Tuple[int, int]

# A "Direction" is a single character among N, E, S, W.
Direction = str

# --- Wall bit constants -------------------------------------------------
NORTH: int = 1  # bit 0
EAST: int = 2   # bit 1
SOUTH: int = 4  # bit 2
WEST: int = 8   # bit 3

ALL_WALLS: int = NORTH | EAST | SOUTH | WEST  # 0xF == 15

# For each direction: its letter, wall bit, (dx, dy) and opposite bit.
_DIRS: Dict[Direction, Tuple[int, int, int, int]] = {
    "N": (NORTH, 0, -1, SOUTH),
    "E": (EAST, 1, 0, WEST),
    "S": (SOUTH, 0, 1, NORTH),
    "W": (WEST, -1, 0, EAST),
}


class MazeError(Exception):
    """Raised when maze parameters are invalid or a maze cannot be built."""


class MazeGenerator:
    """Generate a maze on a rectangular grid.

    The generator builds a *perfect* maze (a spanning tree, exactly one
    path between any two cells) using the randomized recursive
    backtracker algorithm.  Later modes (playable / braided boards) build
    on top of this base.

    Args:
        width: Number of cells along the X axis (must be >= 1).
        height: Number of cells along the Y axis (must be >= 1).
        seed: Optional seed for reproducible generation.
        perfect: If ``True`` (default) the maze is perfect.

    Attributes:
        width: Grid width in cells.
        height: Grid height in cells.
        grid: Wall bitmasks, indexed ``grid[y][x]``.
    """

    def __init__(
        self,
        width: int,
        height: int,
        seed: Optional[int] = None,
        perfect: bool = True,
    ) -> None:
        if width < 1 or height < 1:
            raise MazeError("width and height must be strictly positive")
        self.width: int = width
        self.height: int = height
        self.perfect: bool = perfect
        self.seed: Optional[int] = seed
        self._rng: random.Random = random.Random(seed)
        # Every cell starts fully closed.
        self.grid: List[List[int]] = [
            [ALL_WALLS for _ in range(width)] for _ in range(height)
        ]
        self._generated: bool = False

    # -- geometry helpers ------------------------------------------------
    def in_bounds(self, x: int, y: int) -> bool:
        """Return ``True`` if ``(x, y)`` lies inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _carve(self, x: int, y: int, direction: Direction) -> None:
        """Open the wall of ``(x, y)`` toward ``direction`` and its twin.

        Both the current cell and its neighbour lose the shared wall so
        the encoding stays coherent.
        """
        bit, dx, dy, opp = _DIRS[direction]
        nx, ny = x + dx, y + dy
        if not self.in_bounds(nx, ny):
            raise MazeError("cannot carve outside the grid")
        self.grid[y][x] &= ~bit
        self.grid[ny][nx] &= ~opp

    def has_wall(self, x: int, y: int, direction: Direction) -> bool:
        """Return ``True`` if the wall of ``(x, y)`` toward ``direction`` is closed."""
        bit = _DIRS[direction][0]
        return bool(self.grid[y][x] & bit)

    def open_neighbours(self, x: int, y: int) -> List[Coord]:
        """List the reachable neighbours of ``(x, y)`` (no wall between)."""
        result: List[Coord] = []
        for direction, (bit, dx, dy, _opp) in _DIRS.items():
            if not (self.grid[y][x] & bit):
                result.append((x + dx, y + dy))
        return result

    # -- generation ------------------------------------------------------
    def generate(self) -> "MazeGenerator":
        """Build the maze in place and return ``self`` for chaining."""
        self._recursive_backtracker()
        self._generated = True
        return self

    def _recursive_backtracker(self) -> None:
        """Carve a perfect maze using an iterative DFS with backtracking."""
        visited: List[List[bool]] = [
            [False] * self.width for _ in range(self.height)
        ]
        start_x = self._rng.randrange(self.width)
        start_y = self._rng.randrange(self.height)
        stack: List[Coord] = [(start_x, start_y)]
        visited[start_y][start_x] = True

        while stack:
            x, y = stack[-1]
            neighbours: List[Direction] = []
            for direction, (_bit, dx, dy, _opp) in _DIRS.items():
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny) and not visited[ny][nx]:
                    neighbours.append(direction)
            if not neighbours:
                stack.pop()
                continue
            direction = self._rng.choice(neighbours)
            _bit, dx, dy, _opp = _DIRS[direction]
            self._carve(x, y, direction)
            nx, ny = x + dx, y + dy
            visited[ny][nx] = True
            stack.append((nx, ny))

    # -- solving ---------------------------------------------------------
    def solve(self, entry: Coord, exit_: Coord) -> List[Direction]:
        """Return the shortest path from ``entry`` to ``exit_``.

        The path is a list of direction letters (``N``, ``E``, ``S``,
        ``W``).  Uses breadth-first search, so on a perfect maze it is the
        unique path and on a looped board it is a shortest one.

        Raises:
            MazeError: if either coordinate is out of bounds or no path
                exists.
        """
        ex, ey = entry
        xx, xy = exit_
        if not self.in_bounds(ex, ey) or not self.in_bounds(xx, xy):
            raise MazeError("entry/exit out of bounds")
        if entry == exit_:
            raise MazeError("entry and exit must be different")

        prev: Dict[Coord, Tuple[Coord, Direction]] = {}
        queue: deque[Coord] = deque([entry])
        seen = {entry}
        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == exit_:
                break
            for direction, (bit, dx, dy, _opp) in _DIRS.items():
                if self.grid[cy][cx] & bit:
                    continue  # wall closed, cannot move
                nxt = (cx + dx, cy + dy)
                if nxt not in seen:
                    seen.add(nxt)
                    prev[nxt] = ((cx, cy), direction)
                    queue.append(nxt)
        if exit_ not in prev and entry != exit_:
            raise MazeError("no path between entry and exit")

        path: List[Direction] = []
        node = exit_
        while node != entry:
            parent, direction = prev[node]
            path.append(direction)
            node = parent
        path.reverse()
        return path

    def is_fully_connected(self) -> bool:
        """Return ``True`` if every cell is reachable from cell ``(0, 0)``."""
        total = self.width * self.height
        queue: deque[Coord] = deque([(0, 0)])
        seen = {(0, 0)}
        while queue:
            x, y = queue.popleft()
            for nx, ny in self.open_neighbours(x, y):
                if (nx, ny) not in seen:
                    seen.add((nx, ny))
                    queue.append((nx, ny))
        return len(seen) == total