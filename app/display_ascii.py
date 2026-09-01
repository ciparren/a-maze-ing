"""Terminal ASCII renderer for a built maze, with the subject's menu.

Shows walls, entry, exit, the "42" pattern and (optionally) the shortest
path, using ANSI colours for the walls, entry, exit and path.
"""
from __future__ import annotations

from typing import Callable, List, Set, Tuple

from mazegen import EAST, NORTH, SOUTH, WEST

from .build import BuiltMaze
from .geometry import path_cells as _path_cells

Coord = Tuple[int, int]

_WALL_COLORS = (
    "\033[37m",  # white
    "\033[31m",  # red
    "\033[32m",  # green
    "\033[33m",  # yellow
    "\033[34m",  # blue
    "\033[36m",  # cyan
)
_RESET = "\033[0m"
_ENTRY_COLOR = "\033[95m"   # bright magenta
_EXIT_COLOR = "\033[91m"    # bright red
_PATH_COLOR = "\033[96m"    # bright cyan
_PATTERN_COLOR = "\033[90m"  # grey


def run(
    built: BuiltMaze,
    entry: Coord,
    exit_: Coord,
    regenerate: Callable[[], BuiltMaze],
) -> None:
    """Interactive terminal loop: render, then act on the subject's menu."""
    show_path = True
    color_index = 0
    while True:
        _render(built, entry, exit_, show_path, _WALL_COLORS[color_index])
        print("=== A-Maze-ing ===")
        print("1. Re-generate a new maze")
        print("2. Show / Hide the shortest path")
        print("3. Rotate the wall colours")
        print("4. Quit")
        try:
            choice = input("Choice? (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if choice == "1":
            built = regenerate()
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            color_index = (color_index + 1) % len(_WALL_COLORS)
        elif choice == "4":
            break
        else:
            print("Please enter a number from 1 to 4.\n")


def _floor_char(
    cell: Coord,
    entry: Coord,
    exit_: Coord,
    pattern: Set[Coord],
    path_cells: Set[Coord],
) -> str:
    if cell == entry:
        return _ENTRY_COLOR + "S" + _RESET
    if cell == exit_:
        return _EXIT_COLOR + "X" + _RESET
    if cell in pattern:
        return _PATTERN_COLOR + "#" + _RESET
    if cell in path_cells:
        return _PATH_COLOR + "o" + _RESET
    return "."


def _render(
    built: BuiltMaze,
    entry: Coord,
    exit_: Coord,
    show_path: bool,
    wall_color: str,
) -> None:
    generator = built.generator
    pattern = set(built.pattern)
    path_cells = _path_cells(entry, built.path) if show_path else set()

    width, height = generator.width, generator.height
    rows, cols = 2 * height + 1, 2 * width + 1
    buffer: List[List[str]] = [[" "] * cols for _ in range(rows)]

    for y in range(height):
        for x in range(width):
            walls = generator.grid[y][x]
            r, c = 2 * y + 1, 2 * x + 1
            if walls & NORTH:
                buffer[r - 1][c] = "-"
            if walls & WEST:
                buffer[r][c - 1] = "|"
            if walls & SOUTH:
                buffer[r + 1][c] = "-"
            if walls & EAST:
                buffer[r][c + 1] = "|"
            buffer[r][c] = _floor_char(
                (x, y), entry, exit_, pattern, path_cells
            )

    for r in range(0, rows, 2):
        for c in range(0, cols, 2):
            buffer[r][c] = "+"

    print("\033[2J\033[H", end="")  # clear screen, cursor home
    for row in buffer:
        print("".join(
            wall_color + ch + _RESET if ch in ("-", "|", "+") else ch
            for ch in row
        ))
