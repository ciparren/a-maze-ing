"""Tests for the mandatory "42" pattern (:mod:`app.pattern`)."""
from __future__ import annotations

import pytest

from app.pattern import (
    MIN_HEIGHT_FOR_PATTERN,
    MIN_WIDTH_FOR_PATTERN,
    pattern_cells,
)


def test_default_size_fits_the_pattern() -> None:
    cells = pattern_cells(20, 15)
    assert cells
    assert (20 // 2, 15 // 2) not in cells


def test_pattern_stays_inside_the_grid() -> None:
    width, height = 20, 15
    cells = pattern_cells(width, height)
    for x, y in cells:
        assert 0 <= x < width
        assert 0 <= y < height


def test_too_small_grid_returns_empty_and_warns(
    capsys: pytest.CaptureFixture[str],
) -> None:
    width, height = MIN_WIDTH_FOR_PATTERN - 1, MIN_HEIGHT_FOR_PATTERN - 1
    cells = pattern_cells(width, height)
    assert cells == set()
    assert "too small" in capsys.readouterr().out
