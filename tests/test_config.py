"""Tests for :mod:`app.config` (the configuration file parser)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.config import parse_config
from mazegen import MazeError

_VALID = """\
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
"""


def _write(tmp_path: Path, text: str) -> str:
    path = tmp_path / "config.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_valid_config_parses(tmp_path: Path) -> None:
    config = parse_config(_write(tmp_path, _VALID))
    assert config.width == 20
    assert config.height == 15
    assert config.entry == (0, 0)
    assert config.exit == (19, 14)
    assert config.output_file == "maze.txt"
    assert config.perfect is True
    assert config.seed is None
    assert config.display == "ascii"


def test_comments_and_blank_lines_are_ignored(tmp_path: Path) -> None:
    text = "# a comment\n\n" + _VALID + "\n# trailing comment\n"
    config = parse_config(_write(tmp_path, text))
    assert config.width == 20


def test_optional_seed_and_display(tmp_path: Path) -> None:
    text = _VALID + "SEED=42\nDISPLAY=mlx\n"
    config = parse_config(_write(tmp_path, text))
    assert config.seed == 42
    assert config.display == "mlx"


@pytest.mark.parametrize("missing_key", [
    "WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT",
])
def test_missing_mandatory_key_raises(
    tmp_path: Path, missing_key: str,
) -> None:
    lines = [
        line for line in _VALID.splitlines()
        if not line.startswith(f"{missing_key}=")
    ]
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, "\n".join(lines) + "\n"))


def test_bad_integer_raises(tmp_path: Path) -> None:
    text = _VALID.replace("WIDTH=20", "WIDTH=abc")
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, text))


def test_bad_coordinate_format_raises(tmp_path: Path) -> None:
    text = _VALID.replace("ENTRY=0,0", "ENTRY=0")
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, text))


def test_entry_equals_exit_raises(tmp_path: Path) -> None:
    text = _VALID.replace("EXIT=19,14", "EXIT=0,0")
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, text))


def test_out_of_bounds_entry_raises(tmp_path: Path) -> None:
    text = _VALID.replace("ENTRY=0,0", "ENTRY=99,99")
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, text))


def test_bad_display_value_raises(tmp_path: Path) -> None:
    text = _VALID + "DISPLAY=curses\n"
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, text))


def test_missing_equals_sign_raises(tmp_path: Path) -> None:
    text = _VALID + "NOT_A_PAIR\n"
    with pytest.raises(MazeError):
        parse_config(_write(tmp_path, text))
