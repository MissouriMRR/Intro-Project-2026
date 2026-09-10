"""
starter_hard_solver.py
TEAM NAME: <fill in your team name here>

Same idea as starter_solver.py, but this file also opts in to **hard
mode**. Like the standard starter, the solve() below is a deliberate
placeholder: it does NOT reach the target. Replace it with real logic.

--- Opting in to hard mode -------------------------------------------------

Declare the pool you compete in, then pick your modifiers:

    MODE      = "hard"
    MODIFIERS = ["terrain", "risk", "waypoints"]

You are in exactly ONE pool. A hard solver is scored on the five hard maps
and is never run on the standard maps; an easy solver is the reverse. If
you omit MODE, the pool is inferred from MODIFIERS - having any at all
puts you in hard.

Each modifier multiplies what a hard map is worth to you but adds a rule
you can break. An easy map caps at 1.00 point; a hard map caps at 1.00 x
your bonuses (1.35 x 1.25 x 1.5 = 2.53 with all three), so a clean hard
run is worth up to 12.66 against the easy pool's 5.00. Claim only what you
actually handle - a modifier you break costs you more than not taking it.

  - "terrain":   digit cells 1-9 cost that many energy units to enter
                 ('.', 'S', 'T', '*' all cost 1). Your cost is energy, not
                 step count. Energy over 1.6x optimal -> score x0.4.
  - "risk":      no cost change. Just don't fly through a cell that has 2
                 or more '#' directly N/S/E/W of it (diagonals don't count)
                 - if you do, that map's score is x0.4.
  - "waypoints": you must fly over every '*' cell before landing on 'T'.
                 Miss one -> 0 for that map. Order is yours to choose.

See PROJECT_README.md ("Hard mode") for the exact bonuses and the optimal
-cost reference the scorer compares you against.

--- What your solver has to handle --------------------------------------

grid:   list of lists of characters. Hard maps add '1'-'9' (weighted
        airspace) and '*' (mandatory waypoint) on top of '.', '#', 'S', 'T'.
start:  (row, col) tuple
target: (row, col) tuple

The waypoint cells are not passed in - scan the grid for '*' yourself:

    waypoints = [
        (r, c)
        for r, row in enumerate(grid)
        for c, ch in enumerate(row)
        if ch == "*"
    ]

Return a list of "N"/"S"/"E"/"W" moves, exactly like the standard solver.
"""

# Compete in the hard pool. This solver is never run on the standard maps.
MODE = "hard"

# Trim this list to just the modifiers you actually handle - claiming one
# you break costs you points.
MODIFIERS = ["terrain", "risk", "waypoints"]

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


def solve(grid, start, target):
    # PLACEHOLDER - identical to starter_solver.py. It ignores the digit
    # weights and the '*' waypoints entirely and does not reach the target.
    # Your real solver needs a cost-aware search (e.g. Dijkstra / A* over
    # terrain_cost) and, for "waypoints", a plan that visits every '*'.
    path = []
    current = start
    for _ in range(10):
        if current == target:
            break
        for direction, (dr, dc) in MOVES.items():
            nr, nc = current[0] + dr, current[1] + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
                path.append(direction)
                current = (nr, nc)
                break
    return path


if __name__ == "__main__":
    # Quick local test against the hard practice map.
    from map_utils import load_map_ex
    from scorer import validate_path

    grid, start, target, waypoints = load_map_ex(
        "maps/practice_maps/hard/practice_hard.txt"
    )
    moves = solve(grid, start, target)
    result = validate_path(
        grid, start, target, moves, modifiers=MODIFIERS, waypoints=waypoints
    )
    print(result)
