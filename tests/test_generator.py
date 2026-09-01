"""Tests for the reusable :mod:`mazegen` package."""
from __future__ import annotations

import pytest

from mazegen import MazeError, MazeGenerator


def _open_edges(gen: MazeGenerator) -> int:
    """Count open passages between cells (each edge counted once)."""
    count = 0
    for y in range(gen.height):
        for x in range(gen.width):
            for nx, ny in gen.passages(x, y):
                if (nx, ny) > (x, y):
                    count += 1
    return count


def _window_fully_open(gen: MazeGenerator, wx: int, wy: int) -> bool:
    for j in range(3):
        for i in range(3):
            x, y = wx + i, wy + j
            if gen.is_blocked(x, y):
                return False
            if i < 2 and gen.has_wall(x, y, "E"):
                return False
            if j < 2 and gen.has_wall(x, y, "S"):
                return False
    return True


def _has_3x3_open_block(gen: MazeGenerator) -> bool:
    return any(
        _window_fully_open(gen, wx, wy)
        for wy in range(gen.height - 2)
        for wx in range(gen.width - 2)
    )


def test_invalid_dimensions_raise() -> None:
    with pytest.raises(MazeError):
        MazeGenerator(0, 5)
    with pytest.raises(MazeError):
        MazeGenerator(5, 0)


def test_generate_produces_a_perfect_spanning_tree() -> None:
    gen = MazeGenerator(8, 6, seed=1)
    gen.generate()
    assert gen.is_fully_connected()
    assert _open_edges(gen) == 8 * 6 - 1
    assert not _has_3x3_open_block(gen)


def test_generate_is_reproducible_with_same_seed() -> None:
    first = MazeGenerator(10, 8, seed=42)
    first.generate()
    second = MazeGenerator(10, 8, seed=42)
    second.generate()
    assert first.grid == second.grid


def test_generate_with_blocked_cells_routes_around_them() -> None:
    gen = MazeGenerator(10, 8, seed=3)
    obstacles = [(4, 3), (4, 4), (5, 3), (5, 4)]
    gen.block_cells(obstacles)
    gen.generate()
    assert gen.is_fully_connected()
    for x, y in obstacles:
        assert list(gen.passages(x, y)) == []
    # a neighbour of a blocked cell must keep that shared wall closed
    assert gen.has_wall(3, 3, "E")


def test_block_cells_after_generate_raises() -> None:
    gen = MazeGenerator(5, 5, seed=1)
    gen.generate()
    with pytest.raises(MazeError):
        gen.block_cells([(0, 0)])


def test_block_cells_out_of_bounds_raises() -> None:
    gen = MazeGenerator(5, 5, seed=1)
    with pytest.raises(MazeError):
        gen.block_cells([(5, 5)])


def test_solve_returns_a_valid_path() -> None:
    gen = MazeGenerator(10, 8, seed=7)
    gen.generate()
    path = gen.solve((0, 0), (9, 7))
    x, y = 0, 0
    steps = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
    for letter in path:
        assert not gen.has_wall(x, y, letter)
        dx, dy = steps[letter]
        x, y = x + dx, y + dy
    assert (x, y) == (9, 7)


def test_solve_rejects_bad_arguments() -> None:
    gen = MazeGenerator(5, 5, seed=1)
    gen.generate()
    with pytest.raises(MazeError):
        gen.solve((0, 0), (0, 0))
    with pytest.raises(MazeError):
        gen.solve((0, 0), (5, 5))


def test_braid_adds_loops_and_keeps_corridors_narrow() -> None:
    gen = MazeGenerator(12, 10, seed=5)
    gen.generate()
    loops_added = gen.braid(min_loops=3, max_dead_ends=2)
    assert loops_added >= 3
    assert gen.is_fully_connected()
    assert not _has_3x3_open_block(gen)
    real_dead_ends, _enclosed = gen.dead_ends()
    assert real_dead_ends <= 2


def test_braid_requires_generate_first() -> None:
    gen = MazeGenerator(5, 5, seed=1)
    with pytest.raises(MazeError):
        gen.braid(min_loops=1)
