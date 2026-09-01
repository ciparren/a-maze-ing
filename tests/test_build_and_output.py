"""End-to-end check: build a maze, write it, and re-validate it with the
subject's own grading script (:mod:`maze_analyzer`).

This mirrors the manual checks used to validate the implementation against
the subject (Chapter IV.5 output format, Chapter IV.4 maze requirements).
"""
from __future__ import annotations

from pathlib import Path

from app.build import MAX_DEAD_ENDS, MIN_LOOPS, build_maze
from app.config import Config
from app.maze_io import write_output

import maze_analyzer

_WIDTH, _HEIGHT = 20, 15
_ENTRY, _EXIT = (0, 0), (19, 14)


def _config(perfect: bool, output_file: str) -> Config:
    return Config(
        width=_WIDTH, height=_HEIGHT, entry=_ENTRY, exit=_EXIT,
        output_file=output_file, perfect=perfect, seed=42, display="ascii",
    )


def _analyze(path: Path) -> maze_analyzer.MazeReport:
    maze = maze_analyzer.Maze.from_file(str(path))
    return maze_analyzer.analyze(maze)


def test_perfect_maze_output_is_valid(tmp_path: Path) -> None:
    output = tmp_path / "maze.txt"
    config = _config(perfect=True, output_file=str(output))
    built = build_maze(config)
    write_output(str(output), built.generator, _ENTRY, _EXIT, built.path)

    report = _analyze(output)
    assert not report.incoherent
    assert report.disconnected_corridors == 0
    assert report.exit_reachable is True
    assert report.loops == 0


def test_playable_maze_output_is_valid(tmp_path: Path) -> None:
    output = tmp_path / "maze.txt"
    config = _config(perfect=False, output_file=str(output))
    built = build_maze(config)
    write_output(str(output), built.generator, _ENTRY, _EXIT, built.path)

    report = _analyze(output)
    assert not report.incoherent
    assert report.disconnected_corridors == 0
    assert report.exit_reachable is True
    assert report.loops >= MIN_LOOPS
    assert not report.unreachable_key_cells
    real_dead_ends, _enclosed = report.dead_ends
    assert real_dead_ends <= MAX_DEAD_ENDS


def test_output_file_lines_end_with_newline(tmp_path: Path) -> None:
    output = tmp_path / "maze.txt"
    config = _config(perfect=True, output_file=str(output))
    built = build_maze(config)
    write_output(str(output), built.generator, _ENTRY, _EXIT, built.path)

    text = output.read_text(encoding="utf-8")
    assert text.endswith("\n")
    grid_part, footer_part = text.split("\n\n", 1)
    rows = grid_part.split("\n")
    assert len(rows) == _HEIGHT
    assert all(len(row) == _WIDTH for row in rows)
    entry_line, exit_line, path_line = footer_part.splitlines()
    assert entry_line == f"{_ENTRY[0]},{_ENTRY[1]}"
    assert exit_line == f"{_EXIT[0]},{_EXIT[1]}"
    assert set(path_line) <= set("NESW")
