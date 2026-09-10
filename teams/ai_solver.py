"""
starter_solver.py
TEAM NAME: AI Team

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
- Optional: to compete in hard mode, add a module-level
  `MODIFIERS = ["terrain", "risk", "waypoints"]` (any subset) and handle
  weighted `1`-`9` cells and mandatory `*` waypoints. See
  `starter_hard_solver.py` for the setup and PROJECT_README.md
  ("Hard mode") for the rules. Leave it out to stay in standard mode.
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


# shoutout to the type errors
def solve(
    grid: list[list[str]], start: tuple[int, int], target: tuple[int, int]
) -> list[str]:
    queue = deque([start])
    parents: dict[tuple[int, int], tuple[tuple[int, int], str] | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == target:
            path: list[str] = []
            while (parent := parents[current]) is not None:
                previous, move = parent
                path.append(move)
                current = previous
            return path[::-1]
        for move, (dr, dc) in MOVES.items():
            row = current[0] + dr
            col = current[1] + dc
            neighbor = (row, col)
            if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
                continue
            if grid[row][col] == "#" or neighbor in parents:
                continue
            parents[neighbor] = (current, move)
            queue.append(neighbor)
    return []


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
