"""MLX graphical renderer for a built maze, with the subject's menu.

Requires the optional ``mlx`` package (vendored at ``vendor/`` -- see the
README for install instructions). The import is deferred to this module so
the ASCII display never requires it.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Set, Tuple

from mazegen import EAST, NORTH, SOUTH, WEST

from .build import BuiltMaze
from .geometry import path_cells

Coord = Tuple[int, int]

CELL_SIZE = 20
STATUS_HEIGHT = 30

_WALL_COLORS = (0xFFFFFF, 0xFF3333, 0x33CC33, 0xFFCC00, 0x3399FF, 0x33FFFF)
_ENTRY_COLOR = 0xFF33FF
_EXIT_COLOR = 0xFF3333
_PATH_COLOR = 0x33FFFF
_PATTERN_COLOR = 0x808080

# X11 keysym codes for the digit row (same values as ASCII on Linux MLX).
_KEY_REGEN, _KEY_PATH, _KEY_COLOR, _KEY_QUIT, _KEY_ESC = 49, 50, 51, 52, 65307


def run(
    built: BuiltMaze,
    entry: Coord,
    exit_: Coord,
    regenerate: Callable[[], BuiltMaze],
) -> None:
    """Open an MLX window and drive the subject's menu via key presses."""
    try:
        from mlx import Mlx
    except ImportError as error:
        raise RuntimeError(
            "the 'mlx' package is not installed -- install "
            "vendor/mlx-2.2-py3-none-any.whl (see README) or set "
            "DISPLAY=ascii in your config"
        ) from error

    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    width_px = built.generator.width * CELL_SIZE + 1
    height_px = built.generator.height * CELL_SIZE + 1 + STATUS_HEIGHT
    win = mlx.mlx_new_window(mlx_ptr, width_px, height_px, "A-Maze-ing")

    state: Dict[str, Any] = {
        "built": built, "show_path": True, "color_index": 0,
    }

    def redraw() -> None:
        mlx.mlx_clear_window(mlx_ptr, win)
        _draw(
            mlx, mlx_ptr, win, state["built"], entry, exit_,
            state["show_path"], _WALL_COLORS[state["color_index"]],
        )
        status_y = built.generator.height * CELL_SIZE + 15
        mlx.mlx_string_put(
            mlx_ptr, win, 5, status_y, 0xFFFFFF,
            "1: regen  2: path  3: color  4: quit",
        )

    def on_key(keycode: int, _param: object) -> None:
        if keycode == _KEY_REGEN:
            state["built"] = regenerate()
        elif keycode == _KEY_PATH:
            state["show_path"] = not state["show_path"]
        elif keycode == _KEY_COLOR:
            n = len(_WALL_COLORS)
            state["color_index"] = (state["color_index"] + 1) % n
        elif keycode in (_KEY_QUIT, _KEY_ESC):
            mlx.mlx_loop_exit(mlx_ptr)
            return
        redraw()

    mlx.mlx_key_hook(win, on_key, None)
    redraw()
    mlx.mlx_loop(mlx_ptr)
    mlx.mlx_destroy_window(mlx_ptr, win)
    mlx.mlx_release(mlx_ptr)


def _draw(
    mlx: Any,
    mlx_ptr: Any,
    win: Any,
    built: BuiltMaze,
    entry: Coord,
    exit_: Coord,
    show_path: bool,
    wall_color: int,
) -> None:
    generator = built.generator
    pattern = set(built.pattern)
    visited = path_cells(entry, built.path) if show_path else set()
    width, height = generator.width, generator.height

    for y in range(height):
        for x in range(width):
            walls = generator.grid[y][x]
            px, py = x * CELL_SIZE, y * CELL_SIZE
            if walls & NORTH:
                _hline(mlx, mlx_ptr, win, px, py, CELL_SIZE + 1, wall_color)
            if walls & WEST:
                _vline(mlx, mlx_ptr, win, px, py, CELL_SIZE + 1, wall_color)
            if y == height - 1 and walls & SOUTH:
                _hline(
                    mlx, mlx_ptr, win, px, py + CELL_SIZE,
                    CELL_SIZE + 1, wall_color,
                )
            if x == width - 1 and walls & EAST:
                _vline(
                    mlx, mlx_ptr, win, px + CELL_SIZE, py,
                    CELL_SIZE + 1, wall_color,
                )

            color = _marker_color((x, y), entry, exit_, pattern, visited)
            if color is not None:
                _fill(mlx, mlx_ptr, win, px + 3, py + 3, CELL_SIZE - 5, color)


def _marker_color(
    cell: Coord,
    entry: Coord,
    exit_: Coord,
    pattern: Set[Coord],
    visited: Set[Coord],
) -> Optional[int]:
    if cell == entry:
        return _ENTRY_COLOR
    if cell == exit_:
        return _EXIT_COLOR
    if cell in pattern:
        return _PATTERN_COLOR
    if cell in visited:
        return _PATH_COLOR
    return None


def _hline(
    mlx: Any, mlx_ptr: Any, win: Any, x: int, y: int, length: int, color: int,
) -> None:
    for i in range(length):
        mlx.mlx_pixel_put(mlx_ptr, win, x + i, y, color)


def _vline(
    mlx: Any, mlx_ptr: Any, win: Any, x: int, y: int, length: int, color: int,
) -> None:
    for j in range(length):
        mlx.mlx_pixel_put(mlx_ptr, win, x, y + j, color)


def _fill(
    mlx: Any, mlx_ptr: Any, win: Any, x: int, y: int, size: int, color: int,
) -> None:
    for j in range(size):
        for i in range(size):
            mlx.mlx_pixel_put(mlx_ptr, win, x + i, y + j, color)
