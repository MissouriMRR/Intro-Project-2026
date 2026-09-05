from collections import deque  # noqa: F401
from waypoint_manager import WaypointManager




def solve(grid, start, target):
    waypoints =[]
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == '*':
                waypoints.append((i,j))
    #print(waypoints)
    waypoint_manager = WaypointManager(grid, start, target, waypoints)

    return waypoint_manager.solve()

MODIFIERS = ["terrain", "risk", "waypoints"]

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