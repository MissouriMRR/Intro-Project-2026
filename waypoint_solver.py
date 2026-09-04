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


if __name__ == "__main__":

    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)

    result = validate_path(grid, start, target, moves)
    print("\n"+str(result))
