"""
map_utils.py
Loads drone airspace maps and provides shared constants for the
Drone Pathfinder Challenge.

Map file format (plain text):
    .  open airspace (drone can fly here)
    #  restricted airspace / obstacle (drone CANNOT fly here)
    S  start position (exactly one per map)
    T  target / landing pad (exactly one per map)

All rows must be the same length. Movement is on a 4-connected grid
(no diagonals) using compass directions.
"""

from pathlib import Path

# Move name -> (row_delta, col_delta)
MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


class MapError(Exception):
    pass


def load_map(path):
    """
    Load a map file and return (grid, start, target).

    grid: list of lists of single characters
    start: (row, col)
    target: (row, col)
    """
    path = Path(path)
    lines = [
        line.rstrip("\n")
        for line in path.read_text().splitlines()
        if line.strip() != ""
    ]

    if not lines:
        raise MapError(f"Map file {path} is empty")

    width = len(lines[0])
    for i, line in enumerate(lines):
        if len(line) != width:
            raise MapError(
                f"Row {i} in {path} has length {len(line)}, expected {width}"
            )

    grid = [list(line) for line in lines]

    start = None
    target = None

    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == "S":
                if start is not None:
                    raise MapError(f"Multiple start positions found in {path}")
                start = (r, c)
            elif ch == "T":
                if target is not None:
                    raise MapError(f"Multiple target positions found in {path}")
                target = (r, c)
            else:
                grid[r][c] = "."

    if start is None:
        raise MapError(f"No start (S) found in {path}")
    if target is None:
        raise MapError(f"No target (T) found in {path}")

    return grid, start, target


def in_bounds(grid, pos):
    r, c = pos
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def is_open(grid, pos):
    r, c = pos
    return grid[r][c] != "#"
