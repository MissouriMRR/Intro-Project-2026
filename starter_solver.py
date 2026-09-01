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

# Hint: a queue (collections.deque) is a handy building block for BFS.
# You don't have to use it.
from itertools import pairwise

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


def solve(
    grid: list[list[str]], start: tuple[int, int], target: tuple[int, int]
) -> list[str]:
    # Define the Cell class
    class GridCell:
        def __init__(self) -> None:
            self.parent_i: int = 0  # Parent cell's row index
            self.parent_j: int = 0  # Parent cell's column index
            self.f: float = float("inf")  # Total cost of the cell (g + h)
            self.g: float = float("inf")  # Cost from start to this cell
            self.h: float = 0  # Heuristic cost from this cell to destination

    # Define the size of the grid
    ROW = len(grid)
    COL = len(grid[0]) if ROW > 0 else 0

    # Check if a cell is valid (within the grid)
    def is_valid(row: int, col: int) -> bool:
        return (row >= 0) and (row < ROW) and (col >= 0) and (col < COL)

    # Check if a cell is the destination
    def is_dest(row: int, col: int, dest: tuple[int, int]) -> bool:
        return row == dest[0] and col == dest[1]

    # Calculate the heuristic value of a cell (Euclidean distance to destination)
    def calc_h(row: int, col: int, dest: tuple[int, int]) -> float:
        return ((row - dest[0]) ** 2 + (col - dest[1]) ** 2) ** 0.5

    # Trace the path from source to destination
    def trace_path(
        cell_details: list[list[GridCell]], dest: tuple[int, int]
    ) -> list[tuple[int, int]]:
        path: list[tuple[int, int]] = []
        row, col = dest

        # Trace the path from destination to source using parent cells
        while not (
            cell_details[row][col].parent_i == row
            and cell_details[row][col].parent_j == col
        ):
            path.append((row, col))
            temp_row = cell_details[row][col].parent_i
            temp_col = cell_details[row][col].parent_j
            row, col = temp_row, temp_col

        # Add the source cell to the path
        path.append((row, col))
        # Reverse the path to get the path from source to destination
        return path[::-1]

    # Implement the A* search algorithm
    def a_star_search(
        grid: list[list[str]], start: tuple[int, int], target: tuple[int, int]
    ) -> list[tuple[int, int]]:
        # Check if the source and destination are valid
        if not is_valid(start[0], start[1]) or not is_valid(target[0], target[1]):
            return []

        # Check if the source and destination are unblocked
        if grid[start[0]][start[1]] == "#" or grid[target[0]][target[1]] == "#":
            return []

        # Initialize the closed list (visited cells)
        closed_list = [[False for _ in range(COL)] for _ in range(ROW)]
        # Initialize the details of each cell
        cell_details = [[GridCell() for _ in range(COL)] for _ in range(ROW)]

        # Initialize the start cell details
        i, j = start
        cell_details[i][j].f = 0.0
        cell_details[i][j].g = 0.0
        cell_details[i][j].h = 0.0
        cell_details[i][j].parent_i = i
        cell_details[i][j].parent_j = j

        # Initialize the open list (cells to be visited) with the start cell
        open_list: set[tuple[float, tuple[int, int]]] = set()
        open_list.add((cell_details[i][j].f, (i, j)))

        # Main loop of A* search algorithm
        while open_list:
            # Pop the cell with the smallest f value from the open list
            current_cell = min(open_list)
            open_list.remove(current_cell)

            # Mark the cell as visited
            i, j = current_cell[1]
            closed_list[i][j] = True

            # For each direction, check the successors
            for dr, dc in MOVES.values():
                ni, nj = i + dr, j + dc

                # If the successor is valid, unblocked, and not visited
                if is_valid(ni, nj):
                    # If the successor is the destination
                    if is_dest(ni, nj, target):
                        # Set the parent of the destination cell
                        cell_details[ni][nj].parent_i = i
                        cell_details[ni][nj].parent_j = j
                        # Trace and print the path from source to destination
                        return trace_path(cell_details, target)

                    elif not closed_list[ni][nj] and grid[ni][nj] != "#":
                        # Calculate the new f, g, and h values
                        g_new = cell_details[i][j].g + 1.0
                        h_new = calc_h(ni, nj, target)
                        f_new = g_new + h_new

                        # If the cell is not in the open list or the new f value is smaller
                        if (
                            cell_details[ni][nj].f == float("inf")
                            or cell_details[ni][nj].f > f_new
                        ):
                            # Add the cell to the open list
                            open_list.add((f_new, (ni, nj)))
                            # Update the cell details
                            cell_details[ni][nj].f = f_new
                            cell_details[ni][nj].g = g_new
                            cell_details[ni][nj].h = h_new
                            cell_details[ni][nj].parent_i = i
                            cell_details[ni][nj].parent_j = j

        # If the destination is not found after visiting all cells
        return []

    # Run the A* search algorithm to get the path of coordinates
    coords_path = a_star_search(grid, start, target)
    if not coords_path:
        return []

    # Convert the coordinate path into a list of move directions
    moves: list[str] = []
    inv_moves = {v: k for k, v in MOVES.items()}
    for (r1, c1), (r2, c2) in pairwise(coords_path):
        dr, dc = r2 - r1, c2 - c1
        moves.append(inv_moves[(dr, dc)])
    return moves


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
