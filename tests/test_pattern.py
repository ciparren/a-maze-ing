"""Tests for the mandatory "42" pattern (:mod:`app.pattern`)."""
from __future__ import annotations

import pytest

from app.pattern import (
    MIN_HEIGHT_FOR_PATTERN,
    MIN_WIDTH_FOR_PATTERN,
    _BITMAP,
    pattern_cells,
)

_PATTERN_SIZE = sum(line.count("#") for line in _BITMAP)


def test_default_size_fits_the_pattern() -> None:
    """Check that default size fits the pattern."""
    cells = pattern_cells(20, 15)
    assert cells
    assert (20 // 2, 15 // 2) not in cells


def test_pattern_stays_inside_the_grid() -> None:
    """Check that pattern stays inside the grid."""
    width, height = 20, 15
    cells = pattern_cells(width, height)
    for x, y in cells:
        assert 0 <= x < width
        assert 0 <= y < height


def test_too_small_grid_returns_empty_and_warns(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check that too small grid returns empty and warns."""
    width, height = MIN_WIDTH_FOR_PATTERN - 1, MIN_HEIGHT_FOR_PATTERN - 1
    cells = pattern_cells(width, height)
    assert cells == set()
    assert "too small" in capsys.readouterr().out


@pytest.mark.parametrize("width", [13, 14, 20, 21, 30, 31])
@pytest.mark.parametrize("height", [9, 10, 15, 16])
def test_pattern_is_complete_and_keeps_centre_and_margin_free(
    width: int, height: int,
) -> None:
    """Check that the full "42" is drawn, off the centre and the border."""
    cells = pattern_cells(width, height)
    assert len(cells) == _PATTERN_SIZE  # no cell removed from the digits
    assert (width // 2, height // 2) not in cells
    assert all(1 <= x <= width - 2 and 1 <= y <= height - 2 for x, y in cells)
