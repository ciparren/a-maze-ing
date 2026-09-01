"""Write a generated maze to the subject's output file format (Ch. IV.5)."""
from __future__ import annotations

from typing import List, Tuple

from mazegen import MazeGenerator

Coord = Tuple[int, int]


def write_output(
    path: str,
    generator: MazeGenerator,
    entry: Coord,
    exit_: Coord,
    path_letters: List[str],
) -> None:
    """Write the grid, entry, exit and shortest path to *path*.

    Format: one hexadecimal digit per cell per row, a blank line, then the
    entry coordinates, the exit coordinates, and the concatenated N/E/S/W
    path -- every line ``\\n``-terminated.
    """
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        for row in generator.grid:
            stream.write("".join(format(value, "x") for value in row) + "\n")
        stream.write("\n")
        stream.write(f"{entry[0]},{entry[1]}\n")
        stream.write(f"{exit_[0]},{exit_[1]}\n")
        stream.write("".join(path_letters) + "\n")
