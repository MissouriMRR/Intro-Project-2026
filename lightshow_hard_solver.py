import heapq

"""
lightshow_hard_solver.py
TEAM NAME: Lightshow team

Same idea as starter_solver.py, but this file also opts in to **hard
mode**. Like the standard starter, the solve() below is a deliberate
placeholder: it does NOT reach the target. Replace it with real logic.

--- Opting in to hard mode -------------------------------------------------

Add a module-level MODIFIERS list. Pick any subset - each one multiplies
your score on every hard map but adds a rule you can break. Delete the
line entirely to go back to standard-only scoring.

    MODIFIERS = ["terrain", "risk", "waypoints"]

  - "terrain":   digit cells 1-9 cost that many energy units to enter
                 ('.', 'S', 'T', '*' all cost 1). Your cost is energy, not
                 step count. Energy over 1.6x optimal -> score x0.4.
  - "risk":      every cell you fly through that touches a '#' adds +2 cost
                 per adjacent '#'. Fly through a cell touching >= 3 '#' and
                 that map's score is x0.4.
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

# Opt in to hard mode. Trim this list to just the modifiers you actually
# handle - claiming one you break costs you points.
# MODIFIERS = ["terrain", "risk", "waypoints"]

MODIFIERS = []

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
