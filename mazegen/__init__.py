"""mazegen -- a small, reusable rectangular maze generator.

See ``mazegen/README.md`` for usage documentation.
"""
from .generator import (
    ALL_WALLS,
    EAST,
    MazeError,
    MazeGenerator,
    NORTH,
    SOUTH,
    WEST,
)

__version__ = "1.0.0"

__all__ = [
    "MazeGenerator",
    "MazeError",
    "NORTH",
    "EAST",
    "SOUTH",
    "WEST",
    "ALL_WALLS",
    "__version__",
]
