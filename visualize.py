"""
visualize.py
Prints an ASCII rendering of a map with a solved path overlaid.
Handy for teams debugging their solver, or for showing results
on a projector during the demo meeting.

Usage:
    uv run visualize.py teams/team_alpha_solver.py maps/practice_maps/practice_map.txt
"""

import sys

from map_utils import load_map
from scorer import load_solver, validate_path


def render(grid, visited, start, target):
    visited_set = set(visited)
    lines = []
    for r, row in enumerate(grid):
        line = []
        for c, ch in enumerate(row):
            pos = (r, c)
            if pos == start:
                line.append("S")
            elif pos == target:
                line.append("T")
            elif pos in visited_set and ch != "#":
                line.append("*")
            else:
                line.append(ch)
        lines.append("".join(line))
    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python visualize.py <solver_file.py> <map_file.txt>")
        sys.exit(1)

    solver_file, map_path = sys.argv[1], sys.argv[2]
    grid, start, target = load_map(map_path)
    solve_fn = load_solver(solver_file)
    moves = solve_fn(grid, start, target)
    result = validate_path(grid, start, target, moves)

    print(render(grid, result["visited"], start, target))
    print()
    print(
        f"Success: {result['success']}  Path length: {result['path_length']}  Crashed: {result['crashed']}"
    )


if __name__ == "__main__":
    main()
