"""Generic, reusable maze generation core.

The maze is stored as a grid of *wall bitmasks*: one integer per cell whose
set bits mark which sides are **closed**.

======  =====  =====
Bit     Value  Side
======  =====  =====
0       1      North
1       2      East
2       4      South
3       8      West
======  =====  =====

Coordinates are ``(x, y)`` pairs: ``x`` grows East (columns), ``y`` grows
South (rows). Internally the grid is stored ``grid[y][x]``.

This module knows nothing about any particular project's rules (Pac-Man
boards, the "42" pattern, output file formats, ...). It only exposes generic
primitives: carve a perfect maze, mark obstacle cells, add loops to turn a
perfect maze into a braided one, solve for the shortest path, and inspect
connectivity / dead-ends. Project-specific logic is expected to live in the
calling application, on top of this module.
"""
from __future__ import annotations

import random
from collections import deque
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

Coord = Tuple[int, int]
Direction = str

NORTH: int = 1
EAST: int = 2
SOUTH: int = 4
WEST: int = 8
ALL_WALLS: int = NORTH | EAST | SOUTH | WEST

# direction letter -> (wall bit, dx, dy, opposite bit)
_DIRS: Dict[Direction, Tuple[int, int, int, int]] = {
    "N": (NORTH, 0, -1, SOUTH),
    "E": (EAST, 1, 0, WEST),
    "S": (SOUTH, 0, 1, NORTH),
    "W": (WEST, -1, 0, EAST),
}


class MazeError(Exception):
    """Raised when maze parameters are invalid or a maze cannot be built."""


class MazeGenerator:
    """Generate and manipulate a maze on a rectangular grid of cells.

    Example:
        >>> gen = MazeGenerator(10, 8, seed=42)
        >>> gen.generate()
        >>> path = gen.solve((0, 0), (9, 7))

    Args:
        width: Number of cells along the X axis (must be >= 1).
        height: Number of cells along the Y axis (must be >= 1).
        seed: Optional seed for reproducible generation.

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
    ) -> None:
        if width < 1 or height < 1:
            raise MazeError("width and height must be strictly positive")
        self.width: int = width
        self.height: int = height
        self.seed: Optional[int] = seed
        self._rng: random.Random = random.Random(seed)
        self.grid: List[List[int]] = [
            [ALL_WALLS for _ in range(width)] for _ in range(height)
        ]
        self.blocked: Set[Coord] = set()
        self._generated: bool = False

    # -- geometry ---------------------------------------------------------
    def in_bounds(self, x: int, y: int) -> bool:
        """Return ``True`` if ``(x, y)`` lies inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_blocked(self, x: int, y: int) -> bool:
        """Return ``True`` if ``(x, y)`` is a permanent obstacle cell."""
        return (x, y) in self.blocked

    def has_wall(self, x: int, y: int, direction: Direction) -> bool:
        """Return ``True`` if ``(x, y)``'s wall on ``direction`` is closed."""
        bit = _DIRS[direction][0]
        return bool(self.grid[y][x] & bit)

    # -- obstacles ----------------------------------------------------------
    def block_cells(self, cells: Iterable[Coord]) -> None:
        """Permanently close and exclude ``cells`` from generation/solving.

        Must be called before :meth:`generate`. Useful to reserve a shape
        (a logo, a decorative pattern, ...) inside an otherwise normal maze.

        Raises:
            MazeError: if called after :meth:`generate`, or a cell is out of
                bounds.
        """
        if self._generated:
            raise MazeError("block_cells() must be called before generate()")
        for x, y in cells:
            if not self.in_bounds(x, y):
                raise MazeError(f"blocked cell {(x, y)} is out of bounds")
            self.blocked.add((x, y))

    def unblocked_cells(self) -> Iterator[Coord]:
        """Yield every cell that is not a permanent obstacle."""
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.blocked:
                    yield x, y

    # -- generation ---------------------------------------------------------
    def generate(self) -> "MazeGenerator":
        """Carve a perfect maze (spanning tree) over the unblocked cells.

        Uses the randomized recursive-backtracker algorithm. Returns
        ``self`` so calls can be chained.

        Raises:
            MazeError: if every cell is blocked, or the unblocked cells end
                up disconnected (should not happen for reasonably-shaped
                obstacle sets, but is checked defensively).
        """
        starts = list(self.unblocked_cells())
        if not starts:
            raise MazeError("cannot generate a maze with every cell blocked")
        self._recursive_backtracker(starts[0])
        self._generated = True
        if not self.is_fully_connected():
            raise MazeError(
                "the obstacle cells split the grid into disconnected "
                "regions; use a smaller/different obstacle shape"
            )
        return self

    def _recursive_backtracker(self, start: Coord) -> None:
        visited: Set[Coord] = {start}
        stack: List[Coord] = [start]
        while stack:
            x, y = stack[-1]
            candidates: List[Direction] = []
            for direction, (_bit, dx, dy, _opp) in _DIRS.items():
                nx, ny = x + dx, y + dy
                if (
                    self.in_bounds(nx, ny)
                    and (nx, ny) not in self.blocked
                    and (nx, ny) not in visited
                ):
                    candidates.append(direction)
            if not candidates:
                stack.pop()
                continue
            direction = self._rng.choice(candidates)
            self._carve(x, y, direction)
            _bit, dx, dy, _opp = _DIRS[direction]
            nxt = (x + dx, y + dy)
            visited.add(nxt)
            stack.append(nxt)

    def _carve(self, x: int, y: int, direction: Direction) -> None:
        bit, dx, dy, opp = _DIRS[direction]
        nx, ny = x + dx, y + dy
        self.grid[y][x] &= ~bit
        self.grid[ny][nx] &= ~opp

    # -- braiding (turning a perfect maze into a looped one) ----------------
    def braid(self, min_loops: int, max_dead_ends: int = 2) -> int:
        """Add loops on top of an already-generated perfect maze.

        Removes extra walls between already-connected, unblocked cells until
        at least ``min_loops`` independent routes exist, then makes a best
        effort to also eliminate real dead-ends (down to ``max_dead_ends``)
        by opening one more safe wall per remaining dead-end. A wall is only
        ever opened if doing so does not create a fully-open 3x3 block of
        cells (the subject's "corridors can't be wider than 2 cells" rule) --
        candidates that would violate this are skipped.

        Args:
            min_loops: minimum number of independent loops required.
            max_dead_ends: real dead-ends we try to get down to (best
                effort -- not guaranteed if the grid is too small/dense).

        Returns:
            The number of loops actually added.

        Raises:
            MazeError: if ``generate()`` was not called yet, or the maze is
                too small to fit ``min_loops`` loops without violating the
                corridor-width rule.
        """
        if not self._generated:
            raise MazeError("braid() requires generate() to be called first")

        loops_added = 0
        for x, y in self._dead_end_cells():
            if loops_added >= min_loops:
                break
            direction = self._pick_safe_wall(x, y)
            if direction is not None:
                loops_added += 1

        candidates = self._closed_wall_candidates()
        self._rng.shuffle(candidates)
        for x, y, direction in candidates:
            if loops_added >= min_loops:
                break
            if self._try_open(x, y, direction):
                loops_added += 1

        if loops_added < min_loops:
            raise MazeError(
                f"could not add {min_loops} independent loop(s) without "
                f"widening a corridor beyond 2 cells; try a larger maze"
            )

        for x, y in self._dead_end_cells():
            if self.dead_ends()[0] <= max_dead_ends:
                break
            self._pick_safe_wall(x, y)

        return loops_added

    def _pick_safe_wall(self, x: int, y: int) -> Optional[Direction]:
        """Try each closed wall of ``(x, y)`` and open the first safe one."""
        directions = list(_DIRS)
        self._rng.shuffle(directions)
        for direction in directions:
            bit, dx, dy, _opp = _DIRS[direction]
            if not (self.grid[y][x] & bit):
                continue  # already open
            nx, ny = x + dx, y + dy
            if not self.in_bounds(nx, ny) or (nx, ny) in self.blocked:
                continue
            if self._try_open(x, y, direction):
                return direction
        return None

    def _closed_wall_candidates(self) -> List[Tuple[int, int, Direction]]:
        result: List[Tuple[int, int, Direction]] = []
        for x, y in self.unblocked_cells():
            for direction, (bit, dx, dy, _opp) in _DIRS.items():
                if not (self.grid[y][x] & bit):
                    continue
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny) and (nx, ny) not in self.blocked:
                    result.append((x, y, direction))
        return result

    def _try_open(self, x: int, y: int, direction: Direction) -> bool:
        """Open the wall unless it would create a fully-open 3x3 block."""
        bit, dx, dy, opp = _DIRS[direction]
        nx, ny = x + dx, y + dy
        self.grid[y][x] &= ~bit
        self.grid[ny][nx] &= ~opp
        if self._creates_wide_area(x, y, nx, ny):
            self.grid[y][x] |= bit
            self.grid[ny][nx] |= opp
            return False
        return True

    def _creates_wide_area(self, ax: int, ay: int, bx: int, by: int) -> bool:
        lo_x, lo_y = min(ax, bx), min(ay, by)
        for wy in range(lo_y - 2, lo_y + 1):
            if not (0 <= wy <= self.height - 3):
                continue
            for wx in range(lo_x - 2, lo_x + 1):
                if not (0 <= wx <= self.width - 3):
                    continue
                if not (wx <= ax < wx + 3 and wx <= bx < wx + 3):
                    continue
                if not (wy <= ay < wy + 3 and wy <= by < wy + 3):
                    continue
                if self._window_fully_open(wx, wy):
                    return True
        return False

    def _window_fully_open(self, wx: int, wy: int) -> bool:
        for j in range(3):
            for i in range(3):
                x, y = wx + i, wy + j
                if (x, y) in self.blocked:
                    return False
                if i < 2 and (self.grid[y][x] & EAST):
                    return False
                if j < 2 and (self.grid[y][x] & SOUTH):
                    return False
        return True

    # -- inspection -----------------------------------------------------
    def passages(self, x: int, y: int) -> Iterator[Coord]:
        """Yield neighbours of ``(x, y)`` reachable through an open side."""
        for _direction, (bit, dx, dy, _opp) in _DIRS.items():
            if not (self.grid[y][x] & bit):
                yield x + dx, y + dy

    def is_fully_connected(self) -> bool:
        """Return ``True`` if every unblocked cell reaches any other."""
        cells = list(self.unblocked_cells())
        if not cells:
            return True
        seen: Set[Coord] = {cells[0]}
        queue: deque[Coord] = deque([cells[0]])
        while queue:
            x, y = queue.popleft()
            for nxt in self.passages(x, y):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return len(seen) == len(cells)

    def _dead_end_cells(self) -> List[Coord]:
        cells = [
            (x, y)
            for x, y in self.unblocked_cells()
            if sum(1 for _ in self.passages(x, y)) == 1
        ]
        self._rng.shuffle(cells)
        return cells

    def _has_openable_wall(self, x: int, y: int) -> bool:
        for direction, (bit, dx, dy, _opp) in _DIRS.items():
            if not (self.grid[y][x] & bit):
                continue
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and (nx, ny) not in self.blocked:
                return True
        return False

    def dead_ends(self) -> Tuple[int, int]:
        """Return ``(real, enclosed)`` counts of single-opening cells.

        A dead-end is *real* when one of its closed walls could be opened
        toward another normal cell; it is *enclosed* when every closed wall
        faces a blocked (obstacle) cell or the grid border.
        """
        real = enclosed = 0
        for x, y in self.unblocked_cells():
            if sum(1 for _ in self.passages(x, y)) != 1:
                continue
            if self._has_openable_wall(x, y):
                real += 1
            else:
                enclosed += 1
        return real, enclosed

    # -- solving --------------------------------------------------------
    def solve(self, entry: Coord, exit_: Coord) -> List[Direction]:
        """Return the shortest path from ``entry`` to ``exit_``.

        The path is a list of direction letters (``N``, ``E``, ``S``, ``W``).

        Raises:
            MazeError: if either coordinate is out of bounds/blocked, entry
                equals exit, or no path exists.
        """
        if not self.in_bounds(*entry) or not self.in_bounds(*exit_):
            raise MazeError("entry/exit out of bounds")
        if entry in self.blocked or exit_ in self.blocked:
            raise MazeError("entry/exit cannot be a blocked cell")
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
                    continue
                nxt = (cx + dx, cy + dy)
                if nxt not in seen:
                    seen.add(nxt)
                    prev[nxt] = ((cx, cy), direction)
                    queue.append(nxt)
        if exit_ not in prev:
            raise MazeError("no path between entry and exit")

        path: List[Direction] = []
        node = exit_
        while node != entry:
            parent, direction = prev[node]
            path.append(direction)
            node = parent
        path.reverse()
        return path
