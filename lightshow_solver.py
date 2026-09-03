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

# Hint: a queue is a handy building block for BFS. You don't have to use it.
from collections import deque  # noqa: F401

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}

def check_pos_bounds(row, col, row_max, col_max):

    if (row < 0) or (row >= row_max) or (col < 0) or (col >= col_max):
        return False

    return True

def check_pos_validity(grid, row, col, row_max, col_max):

    if not check_pos_bounds(row, col, row_max, col_max):
        return False
    if grid[row][col] == "#":
        return False

    adjacent_obstacles = 0

    return True


def calc_h(row, col, dest):

    # Calculate manhattan distance
    return abs(row - dest[0]) + abs(col - dest[1])


def trace_target_route(cell_data, dest):

    # https://www.geeksforgeeks.org/dsa/a-search-algorithm/

    delta_path = []
    row = dest[0]
    col = dest[1]

    # Trace moves from destination to source
    while not (
        cell_data[row][col]["parent_i"] == row
        and cell_data[row][col]["parent_j"] == col
    ):
        temp_row = cell_data[row][col]["parent_i"]
        temp_col = cell_data[row][col]["parent_j"]

        # Store distance between node and parent
        delta_path.append((row - temp_row, col - temp_col))

        row = temp_row
        col = temp_col

    path = []

    # Convert the differences into recognizable moves
    for i in delta_path:
        for key, value in MOVES.items():
            if i == value:
                path.append(key)

    # Make path go from source to destination
    path.reverse()

    return path


def solve(grid, start, target):

    # https://www.geeksforgeeks.org/dsa/a-search-algorithm/ referenced

    rows = len(grid)
    cols = len(grid[0])

    dest_coord = (None, None)

    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == "T":
                dest_coord = i, j

    closed_grid = [[False for _ in range(cols)] for _ in range(rows)]

    cell_data = [
        [
            {"parent_i": 0, "parent_j": 0, "f": float("inf"), "g": float("inf"), "h": 0}
            for _ in range(cols)
        ]
        for _ in range(rows)
    ]

    i = start[0]
    j = start[1]
    cell_data[i][j]["f"] = 0
    cell_data[i][j]["g"] = 0
    cell_data[i][j]["h"] = 0
    cell_data[i][j]["parent_i"] = i
    cell_data[i][j]["parent_j"] = j

    open_list = []
    heapq.heappush(open_list, (0.0, i, j))

    found = False

    # Main algorithm loop
    while len(open_list) > 0:
        popped = heapq.heappop(open_list)

        # mark visited

        i = popped[1]
        j = popped[2]
        closed_grid[i][j] = True

        for dir in MOVES.values():
            new_i = i + dir[0]
            new_j = j + dir[1]

            if check_pos_validity(grid, new_i, new_j, rows, cols) and (
                not closed_grid[new_i][new_j]
            ):
                if grid[new_i][new_j] == "T":
                    cell_data[new_i][new_j]["parent_i"] = i
                    cell_data[new_i][new_j]["parent_j"] = j

                    path = trace_target_route(cell_data, dest_coord)
                    found = True
                    return path

                else:
                    g_new = cell_data[i][j]["g"] + 1
                    h_new = calc_h(new_i, new_j, dest_coord)
                    f_new = g_new + h_new

                    if (
                        cell_data[new_i][new_j]["f"] == float("inf")
                        or cell_data[new_i][new_j]["f"] > f_new
                    ):
                        heapq.heappush(open_list, (f_new, new_i, new_j))

                        cell_data[new_i][new_j]["f"] = f_new
                        cell_data[new_i][new_j]["g"] = g_new
                        cell_data[new_i][new_j]["h"] = h_new
                        cell_data[new_i][new_j]["parent_i"] = i
                        cell_data[new_i][new_j]["parent_j"] = j

    if not found:
        return []


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
