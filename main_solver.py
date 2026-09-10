from path_finder import PathFinder

MODIFIERS = ["terrain", "risk", "waypoints"]

def solve(grid, start, target):


    #finds waypoint positions
    waypoints =[]
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == '*':
                waypoints.append((i,j))


    # initialize path finder class
    # specify if risk modifier is in use(other modifiers already accounted for in code)
    path_finder = PathFinder(grid=grid, start=start, end=target, waypoints=waypoints, risk_modifier_on=True)



    return path_finder.solve()



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