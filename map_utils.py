"""
map_utils.py
Loads drone airspace maps and provides shared constants for the
Drone Pathfinder Challenge.

Map file format (plain text):
    .    open airspace (drone can fly here), costs 1 energy to enter
    #    restricted airspace / obstacle (drone CANNOT fly here)
    S    start position (exactly one per map)
    T    target / landing pad (exactly one per map)
    1-9  HARD MODE ONLY: weighted airspace - open, but costs that many
         energy units to fly into (wind, altitude, weather)
    *    HARD MODE ONLY: a mandatory delivery waypoint - open, costs 1,
         but the drone must fly over every one before landing on T

Standard maps only ever use '.', '#', 'S', 'T'. The digit and '*' cells
appear only in the hard-mode map pool; a standard solver can treat them
as plain open airspace (is_open() already does).

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

# Hard-mode marker for a mandatory delivery waypoint.
WAYPOINT = "*"


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

    if start is None:
        raise MapError(f"No start (S) found in {path}")
    if target is None:
        raise MapError(f"No target (T) found in {path}")

    return grid, start, target


def load_map_ex(path):
    """
    Like load_map(), but also returns the mandatory waypoint cells.

    Returns (grid, start, target, waypoints) where waypoints is a list of
    (row, col) tuples, one per '*' marker, in row-major order. Standard
    maps contain no '*', so waypoints is an empty list.
    """
    grid, start, target = load_map(path)
    waypoints = [
        (r, c)
        for r, row in enumerate(grid)
        for c, ch in enumerate(row)
        if ch == WAYPOINT
    ]
    return grid, start, target, waypoints


def in_bounds(grid, pos):
    r, c = pos
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def is_open(grid, pos):
    r, c = pos
    return grid[r][c] != "#"


def terrain_cost(ch):
    """
    Energy needed to fly INTO a cell holding character `ch`.

    Hard-mode maps use digits 1-9 to mark weighted airspace. Every other
    flyable cell ('.', 'S', 'T', '*') costs 1. '#' is restricted airspace
    and has no defined entry cost (the drone can never enter it).
    """
    if ch.isdigit():
        return max(1, int(ch))
    return 1


def wall_count(grid, pos):
    """
    How many restricted-airspace ('#') cells sit in the 8-neighbourhood of
    `pos`. Cells off the edge of the map do not count. The scorer's 'risk'
    modifier uses this to penalise routes that skim restricted airspace.
    """
    r, c = pos
    h, w = len(grid), len(grid[0])
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == "#":
                count += 1
    return count
