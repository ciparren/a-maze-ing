*This project has been created as part of the 42 curriculum by ciparren, dondrama.*

# A-Maze-ing

## Description

A-Maze-ing generates a rectangular maze from a simple text configuration
file, writes it to a hexadecimal-encoded output file, and displays it
(terminal ASCII or an MLX graphical window). Two modes are supported:

- **`PERFECT=True`**: a *perfect* maze -- exactly one path between the entry
  and the exit, no loops at all.
- **`PERFECT=False`** (default): a *playable* board usable as a Pac-Man-like
  level -- fully connected, corners and centre reachable, at least two
  independent routes (loops), and dead-ends kept rare.

Every maze also contains a mandatory "42" pattern made of permanently
closed cells, visible in the display.

The maze-carving logic itself is packaged separately as `mazegen`, a small
reusable, pip-installable library with no dependency on this project's
"42"/Pac-Man-specific rules -- see [Code reusability](#code-reusability)
below.

## Instructions

Requires **Python 3.10+**.

```bash
make install   # dev tools (flake8, mypy, build, pytest) + optional MLX display
make run       # python3 a_maze_ing.py config.txt
```

Or directly:

```bash
python3 a_maze_ing.py config.txt
```

`config.txt` is the only argument, and can be replaced by any file of your
own (see [Configuration file format](#configuration-file-format)).

Other `Makefile` targets: `make debug` (runs under `pdb`), `make lint` /
`make lint-strict` (flake8 + mypy), `make clean` (removes caches/build
artifacts).

### Optional: MLX display

`DISPLAY=ascii` (the default) needs nothing extra. To open a graphical
window instead, set `DISPLAY=mlx` and install the `mlx` package -- it isn't
bundled in this repository, so fetch the wheel matching your platform (e.g.
from the subject's own attachments) and place it under `vendor/`, then:

```bash
pip install vendor/mlx-2.2-py3-none-any.whl
```

(`make install` attempts this automatically, best-effort, and simply skips
it if the file isn't there.) If `mlx` isn't installed, `DISPLAY=mlx` fails
with a clear error telling you to install it or switch back to
`DISPLAY=ascii`.

## Configuration file format

One `KEY=VALUE` pair per line; lines starting with `#` (and blank lines) are
ignored.

| Key           | Required | Description                              | Example              |
|---------------|----------|-------------------------------------------|----------------------|
| `WIDTH`       | yes      | maze width in cells                       | `WIDTH=20`           |
| `HEIGHT`      | yes      | maze height in cells                      | `HEIGHT=15`          |
| `ENTRY`       | yes      | entry coordinates `x,y`                   | `ENTRY=0,0`          |
| `EXIT`        | yes      | exit coordinates `x,y`                    | `EXIT=19,14`         |
| `OUTPUT_FILE` | yes      | output filename                           | `OUTPUT_FILE=maze.txt` |
| `PERFECT`     | yes      | `True` for a perfect maze, `False` for a playable board | `PERFECT=True` |
| `SEED`        | no       | integer seed for reproducible generation  | `SEED=42`            |
| `DISPLAY`     | no       | `ascii` (default) or `mlx`                | `DISPLAY=ascii`      |

Any missing/malformed key, out-of-bounds `ENTRY`/`EXIT`, or `ENTRY == EXIT`
is reported as a clear error and the program exits without crashing.

## Maze generation algorithm

We use the **randomized recursive backtracker** (iterative DFS with
backtracking) to carve the base maze. It was chosen because:

- it always produces a *perfect* maze (a spanning tree) in one pass, which
  directly satisfies `PERFECT=True` with no extra work;
- it's simple to reason about and to implement correctly, with predictable
  O(width x height) behaviour;
- it naturally produces long, winding corridors rather than short, choppy
  ones (compared to e.g. plain randomized Prim's), which reads better
  visually;
- it composes cleanly with the playable-mode requirement: since a spanning
  tree by definition has zero loops, and a fully-open 2x2+ block of cells
  would itself contain a loop, a perfect maze can *never* violate the
  "corridors can't be wider than 2 cells" rule -- so that check only needs
  to run for the extra step below.

For `PERFECT=False`, we then **braid** the perfect maze: remove additional
walls between already-connected cells to create loops, prioritising walls
next to existing dead-ends first (so loops are added where they also kill a
dead-end), until at least the required number of independent routes exist.
Before opening any wall, we check it wouldn't create a fully-open 3x3 block
of cells, and reject it if so. Because braiding only ever *adds* passages on
top of an already fully-connected spanning tree, connectivity is preserved
by construction -- no separate repair step is needed.

The mandatory "42" pattern is a hand-authored pixel-font bitmap, centered in
the grid and carved out (permanently closed) *before* generation, so the
backtracker naturally routes around it. The exact centre cell of the grid is
always kept open even though the bitmap covers it, since the playable mode
requires the centre to be a corridor (the player's start position) --
this leaves a one-cell notch in the "42" shape, which is a deliberate,
documented trade-off.

## Code reusability

The `mazegen` package ([mazegen/generator.py](mazegen/generator.py)) is the
reusable part: it implements grid generation, obstacle cells, loop-braiding
and shortest-path solving as a single `MazeGenerator` class, with **no**
knowledge of this project's specific rules ("42" pattern, Pac-Man corners,
output file format). It is built and shipped separately as a pip package
(`mazegen-1.0.0-py3-none-any.whl` / `mazegen-1.0.0.tar.gz`, committed at the
repository root) so a later project can simply:

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=20, height=15, seed=42)
gen.generate()                        # perfect maze
gen.braid(min_loops=2, max_dead_ends=0)  # optional: turn it into a looped board
path = gen.solve((0, 0), (19, 14))    # shortest path, e.g. ['E', 'E', 'S', ...]
gen.grid                              # List[List[int]] wall bitmask, grid[y][x]
```

See [mazegen/README.md](mazegen/README.md) for the full usage documentation
(instantiation, custom parameters, obstacles, braiding, accessing the
structure and the solution).

Everything specific to *this* project (config parsing, the "42" pattern
bitmap, the output file writer, both displays, the CLI) lives in
[app/](app/) and is **not** part of the reusable package.

To rebuild the package from source:

```bash
pip install build
python3 -m build          # writes dist/mazegen-1.0.0*
cp dist/mazegen-1.0.0* .  # the subject requires the artifact at repo root
```

## Resources

- [Maze generation algorithms (Wikipedia)](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Think Labyrinth: maze generation algorithms](https://www.astrolog.org/labyrnth/algrithm.htm) -- overview of recursive backtracker, Prim's, Kruskal's
- [Jamis Buck, "Maze Generation: Algorithm Recap"](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap) -- the classic accessible write-up on backtracker/braiding
- Python standard library docs for `argparse`, `dataclasses`, `collections.deque`, `ctypes` (used for the MLX binding)
- [setuptools packaging documentation](https://setuptools.pypa.io/) for building the `mazegen` wheel/sdist

### AI usage disclosure

An AI assistant (Claude, via Claude Code) was used throughout this project
for: reading and summarising the subject PDF, drafting the initial
architecture (splitting the reusable `mazegen` core from the project-specific
`app/` glue), implementing the maze generation/braiding/solving logic, the
config/output/pattern modules, both displays (ASCII and MLX), the packaging
setup, and this README. Every generated piece was run and checked against
`maze_analyzer.py` (the subject's own grading script) for both modes, plus a
small `pytest` suite, before being accepted -- see
[Planning](#planning-and-team-management) below for what that review process
looked like in practice.

## Planning and team management

### Roles

<!-- TODO: fill in before submission -- who owned which part(s) of the
     project (e.g. mazegen core / app glue / displays / packaging /
     README), not just "did some coding". -->
- **ciparren**: TODO -- describe your specific contributions here.
- **dondrama**: TODO -- describe your specific contributions here.

### Planning and how it evolved

<!-- TODO: fill in before submission -- the actual timeline you followed
     (subject reading, design split, implementation order, integration),
     and specifically what changed vs. your first plan and why. -->
TODO: describe the actual timeline you followed (e.g. subject reading,
design split, implementation order, integration) and how/why it changed
from what you first planned.

### What worked well / what could be improved

<!-- TODO: fill in before submission -- concrete lessons, not generalities.
     E.g. what made a task easy/hard, a design decision you'd revisit, a
     bug that took longer than expected to track down. -->
TODO -- e.g. splitting the reusable generator from the app-specific glue
early made testing each half in isolation straightforward; the "42"
pattern's centre-cell exception was a late discovery that could have been
caught earlier by writing the Pac-Man key-cell check first.

### Tools used

- Python 3, `flake8`, `mypy`, `pytest`, `build` (packaging), `venv`.
- An AI assistant (see disclosure above) for implementation and drafting.
<!-- TODO: fill in before submission -- editor/IDE, git hosting, CI, chat
     tool for coordinating with your teammate, etc. -->
- TODO -- add anything else your team specifically used (editor, CI, etc.).
