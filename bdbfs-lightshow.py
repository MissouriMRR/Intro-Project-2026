import math
import heapq

"""
lightshow_solver.py
TEAM NAME: The Lightshow Team

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

from collections import deque  # noqa: F401

# movelist directions
MOVES = {
        "N": (-1, 0),
        "S": (1, 0),
        "E": (0, 1),
        "W": (0, -1)
}
REVERSE_MOVES = {
        (-1, 0): "N",
        (1, 0): "S",
        (0, 1): "E",
        (0, -1): "W"
}

# adds two tuples of length 2
def addTuples(a: tuple, b: tuple) -> tuple:
    return (a[0] + b[0], a[1] + b[1])

# subtracts two tuples of length 2
def subTuples(a: tuple, b: tuple) -> tuple:
    return (a[0] - b[0], a[1] - b[1])

# converts a list of coordinates to the list of cardinal directions used to construct that path
def generateStringPath(inpt_path: list) -> list:
    out_path = []
    L = len(inpt_path)
    for idx in range(1, L):
        out_path.append(REVERSE_MOVES[subTuples(inpt_path[idx], inpt_path[idx - 1])])
    return out_path

# constructs the path from the meeting point and the parent nodes
def tracePath(meet_point, parents_start, parents_end):
    path_front = []
    path_end = []

    # retrace steps to the start node, then reverse as it is backwards
    n = meet_point
    while n is not None:
        path_front.append(n)
        n = parents_start[n]
    path_front.reverse()

    # retrace steps to the target node, skipping meet_point as it is already in path_front
    n = parents_end[meet_point]
    while n is not None:
        path_end.append(n)
        n = parents_end[n]

    return path_front + path_end

# checks if the given coordinates p are inbounds
def inBounds(p: tuple, griddimx, griddimy) -> bool:
    y, x = p
    return (0 <= x < griddimx) and (0 <= y < griddimy)


# solves the grid given a start char and target char
def solve(grid, start, target):
    queue_start = deque([start]) # queue of start nodes, representing the furthest level of search
    queue_end = deque([target])
    parents_start = {start: None} # dictionary of parents of nodes, allowing for retracing steps later
    parents_end = {target: None}
    
    griddimx = len(grid[0])
    griddimy = len(grid)
    dirs = MOVES.values()

    # bfs
    while (True):
        # forward search
        current_start = queue_start.popleft()
        for direction_tuple in dirs:
            dest = addTuples(current_start, direction_tuple) # simple way of generating neighbors
            if not inBounds(dest, griddimx, griddimy): # skip destination if out of bounds
                continue
            if dest in parents_end: # if destination has been seen by end side, begin retracing steps in both directions from that point
                parents_start[dest] = current_start
                return generateStringPath(tracePath(dest, parents_start, parents_end))
            elif dest not in parents_start and grid[dest[0]][dest[1]] != "#": # if destination is unseen and not wall,
                queue_start.append(dest) # add destination to list of start nodes
                parents_start[dest] = current_start # record previous node

        # backward search
        current_end = queue_end.popleft()
        for direction_tuple in dirs:
            dest = addTuples(current_end, direction_tuple)
            if not inBounds(dest, griddimx, griddimy):
                continue
            if dest in parents_start:
                parents_end[dest] = current_end
                return generateStringPath(tracePath(dest, parents_start, parents_end))
            elif dest not in parents_end and grid[dest[0]][dest[1]] != "#":
                queue_end.append(dest)
                parents_end[dest] = current_end

if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    print(f"hello: {start}, {target}")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
