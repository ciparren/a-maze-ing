"""Parse and validate the a_maze_ing configuration file.

File format: one ``KEY=VALUE`` pair per line, ``#`` starts a comment. See the
subject (Chapter IV.3) and the default :mod:`config.txt` for the full key
list. File-not-found / OS errors are intentionally left to propagate to the
caller (the CLI reports them as "file not found").
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from mazegen import MazeError

Coord = Tuple[int, int]

_REQUIRED_KEYS = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")
_TRUE_VALUES = {"true", "1", "yes"}
_FALSE_VALUES = {"false", "0", "no"}
_DISPLAYS = ("ascii", "mlx")


@dataclass(frozen=True)
class Config:
    """A fully validated configuration."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    output_file: str
    perfect: bool
    seed: Optional[int]
    display: str


def parse_config(path: str) -> Config:
    """Read *path* and return a validated :class:`Config`.

    Raises:
        MazeError: on any missing/malformed key or out-of-range value.
    """
    raw = _read_pairs(path)
    missing = [key for key in _REQUIRED_KEYS if key not in raw]
    if missing:
        raise MazeError(f"missing mandatory key(s): {', '.join(missing)}")

    width = _parse_int(raw, "WIDTH")
    height = _parse_int(raw, "HEIGHT")
    if width < 1 or height < 1:
        raise MazeError("WIDTH and HEIGHT must be strictly positive")

    entry = _parse_coord(raw, "ENTRY")
    exit_ = _parse_coord(raw, "EXIT")
    if entry == exit_:
        raise MazeError("ENTRY and EXIT must be different cells")
    for name, (x, y) in (("ENTRY", entry), ("EXIT", exit_)):
        if not (0 <= x < width and 0 <= y < height):
            raise MazeError(
                f"{name}={x},{y} is outside the {width}x{height} grid"
            )

    output_file = raw["OUTPUT_FILE"].strip()
    if not output_file:
        raise MazeError("OUTPUT_FILE must not be empty")

    perfect = _parse_bool(raw, "PERFECT")
    seed = _parse_optional_int(raw, "SEED")

    display = raw.get("DISPLAY", "ascii").strip().lower()
    if display not in _DISPLAYS:
        raise MazeError(
            f"DISPLAY={display!r} must be one of {_DISPLAYS}"
        )

    return Config(
        width, height, entry, exit_, output_file, perfect, seed, display
    )


def _read_pairs(path: str) -> Dict[str, str]:
    pairs: Dict[str, str] = {}
    with open(path, encoding="utf-8") as stream:
        for number, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise MazeError(
                    f"line {number}: expected KEY=VALUE, got "
                    f"{raw_line.strip()!r}"
                )
            key, _, value = line.partition("=")
            pairs[key.strip().upper()] = value.strip()
    return pairs


def _parse_int(raw: Dict[str, str], key: str) -> int:
    try:
        return int(raw[key])
    except ValueError as error:
        raise MazeError(
            f"{key}={raw[key]!r} is not a valid integer"
        ) from error


def _parse_optional_int(raw: Dict[str, str], key: str) -> Optional[int]:
    if key not in raw or not raw[key].strip():
        return None
    return _parse_int(raw, key)


def _parse_coord(raw: Dict[str, str], key: str) -> Coord:
    text = raw[key]
    parts = text.split(",")
    if len(parts) != 2:
        raise MazeError(f"{key}={text!r} must be formatted as 'x,y'")
    try:
        x, y = int(parts[0]), int(parts[1])
    except ValueError as error:
        raise MazeError(
            f"{key}={text!r} must be formatted as 'x,y' with integers"
        ) from error
    return x, y


def _parse_bool(raw: Dict[str, str], key: str) -> bool:
    value = raw[key].strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise MazeError(f"{key}={raw[key]!r} must be a boolean (True/False)")
