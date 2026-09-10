"""
starter_solver.py
TEAM NAME: <fill in your team name here>

Your job: implement solve() so it returns a list of moves that flies
the drone from `start` to `target` without crossing any '#' cells.

Rules:
- You may only move N / S / E / W (no diagonals).
- Return your answer as a list of single-character strings, e.g.
  ["E", "E", "S", "S", "E"]
- Your path does not need to be the shortest one to pass, but shorter
  and faster solvers score better on the leaderboard (see README).
- You may add helper functions / imports (standard library only
  unless your instructor says otherwise).
- Do not hardcode answers to the specific practice map — your solver
  will be run against maps you haven't seen.

grid:   list of lists of characters ('.', '#', 'S', 'T')
start:  (row, col) tuple
target: (row, col) tuple
"""

# Hint: a queue is a handy building block for BFS. You don't have to use it.
from collections import deque  # noqa: F401

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


def solve(grid, start, target):
    # -----------------------------------------------------------
    # REPLACE THIS with your own pathfinding logic (BFS, DFS,
    # A*, whatever your team wants to try). This placeholder just
    # proves the interface works: it does NOT reliably reach the
    # target and will fail on most maps.
    # -----------------------------------------------------------
    path = []
    current = start
    for _ in range(10):
        # If end has been reached, break loop
        if current == target:
            break
        # Sample path finding algorithm (doesn't work, just oscillates between (0,0) and (1,0))
        # dr = delta_row, dc = delta column
        for direction, (dr, dc) in MOVES.items():
            nr, nc = current[0] + dr, current[1] + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
                path.append(direction)
                current = (nr, nc)
                break
    return path


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
