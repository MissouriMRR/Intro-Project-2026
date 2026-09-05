"""
starter_solver.py
TEAM NAME: Pathfinding

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
from map_utils import in_bounds, is_open
import heapq, math

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}    

MOVESREV = {
    "-10" : "N",
    "10" : "S",
    "01" : "E",
    "0-1" : "W"
}

def manhattan(current, target):
    return abs(current[0] - target[0]) + abs(current[1] - target[1])

def adj(current, grid):
    o = []
    for _,move in MOVES.items():
        temp = (current[0]+move[0], current[1]+move[1])
        if (in_bounds(grid, temp) and is_open(grid, temp)):
            o.append(temp)
    return o

def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from.keys():
        current = came_from[current]
        total_path.append(current)
    total_path.reverse()
    output = []
    for i in range(len(total_path)-1):
        output.append(MOVESREV[f"{total_path[i+1][0]-total_path[i][0]}{total_path[i+1][1]-total_path[i][1]}"])
    print(output)
    return output

def a_star(grid, start, target, h):
    open_set = [(0, start)]
    heapq.heapify(open_set)

    came_from = dict()

    g_score = dict()  # default values should be INF
    g_score[start] = 0

    f_score = dict()  # default values should be INF
    f_score[start] = h(start, target)

    while open_set:
        current = heapq.heappop(open_set)[1]
        if current == target:
            return reconstruct_path(came_from, current)

        for neighbor in adj(current, grid):
            tenative_gScore = g_score[current] + 1
            if neighbor not in g_score:
                g_score[neighbor] = math.inf
            if tenative_gScore < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tenative_gScore
                f_score[neighbor] = tenative_gScore + h(neighbor, target)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return "No Path"

def solve(grid, start, target):
    # -----------------------------------------------------------
    # REPLACE THIS with your own pathfinding logic (BFS, DFS,
    # A*, whatever your team wants to try). This placeholder just
    # proves the interface works: it does NOT reliably reach the
    # target and will fail on most maps.
    # -----------------------------------------------------------
    #path = []
    #current = start
    #for _ in range(10):
    #    # If end has been reached, break loop
    #    if current == target:
    #        break
    #    # Sample path finding algorithm (doesn't work, just oscillates between (0,0) and (1,0))
    #    # dr = delta_row, dc = delta column
    #    for direction, (dr, dc) in MOVES.items():
    #        nr, nc = current[0] + dr, current[1] + dc
    #        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
    #            path.append(direction)
    #            current = (nr, nc)
    #            break
    #return path

    return a_star(grid, start, target, manhattan)


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
