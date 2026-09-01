# mazegen

A small, generic, reusable rectangular maze generator. It knows nothing about
any particular project's rules -- it only carves mazes, optionally adds loops,
and solves them.

## Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

## Basic usage

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=20, height=15, seed=42)
gen.generate()                      # carve a perfect maze (spanning tree)
path = gen.solve((0, 0), (19, 14))  # -> ['E', 'E', 'S', ...] shortest path
```

## Custom parameters

- `width`, `height`: grid size in cells (both must be >= 1).
- `seed`: any hashable value accepted by `random.Random`; same seed + same
  calls always reproduce the same maze.

## Obstacles (reserving a shape before generating)

```python
gen = MazeGenerator(20, 15, seed=42)
gen.block_cells([(9, 6), (9, 7), (10, 6), (10, 7)])  # permanently closed
gen.generate()  # carves around the blocked cells
```

## Turning a perfect maze into a looped ("braided") board

```python
gen.generate()
gen.braid(min_loops=2, max_dead_ends=0)  # adds loops, then removes dead-ends
```

`braid()` never creates a fully-open 3x3 block of cells (it keeps corridors at
most 2 cells wide) and never breaks connectivity -- it only ever adds walls
being opened, never removes a passage.

## Accessing the generated structure

```python
gen.grid            # List[List[int]] wall bitmask per cell, grid[y][x]
gen.has_wall(x, y, "N")       # True/False for one side of one cell
gen.passages(x, y)            # iterator of open neighbours
gen.is_fully_connected()      # sanity check
gen.dead_ends()               # (real, enclosed) counts
```

Wall bitmask bits: `1`=North, `2`=East, `4`=South, `8`=West (a set bit means
that side is closed). This is **not** necessarily the same format your
application writes to disk -- it's just the in-memory representation this
class works with.
