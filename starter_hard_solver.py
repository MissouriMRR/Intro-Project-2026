"""
starter_hard_solver.py
TEAM NAME: <fill in your team name here>

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
from map_utils import in_bounds, is_open
import heapq, math

# Opt in to hard mode. Trim this list to just the modifiers you actually
# handle - claiming one you break costs you points.
MODIFIERS = ["terrain", "risk"]#["terrain", "risk", "waypoints"]

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

def wall_count(adj, grid):
    count = 0
    for _,move2 in MOVES.items():
        temp2 = (adj[0]+move2[0], adj[1]+move2[1])
        if (in_bounds(grid, temp2) and grid[temp2[0]][temp2[1]]=='#'):
            count+=1
    return count

def adj(current, grid):
    o = []
    for _,move in MOVES.items():
        temp = (current[0]+move[0], current[1]+move[1])
        if (in_bounds(grid, temp) and is_open(grid, temp)):
            count = wall_count(temp, grid)
            if count<2:
                o.append(temp)
    return o

def reconstruct_path(came_from, current, grid):
    total_path = [current]
    while current in came_from.keys():
        current = came_from[current]
        total_path.append(current)
    total_path.reverse()
    output = []
    cost = 1
    for i in range(len(total_path)-1):
        r1,c1 = total_path[i]
        r2,c2 = total_path[i+1]
        cell2 = grid[r2][c2]
        weight = int(cell2) if grid[r2][c2].isnumeric() else 1
        output.append(MOVESREV[f"{r2-r1}{c2-c1}"])
        cost+=1
    print(output)
    return output, cost

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
            return reconstruct_path(came_from, current, grid)

        for neighbor in adj(current, grid):
            weight = 1
            r,c = neighbor
            if (grid[r][c]).isnumeric():
                weight = int(grid[r][c])
            if (wall_count(neighbor, grid)):
                weight+=2
            tenative_gScore = g_score[current] + weight
            if neighbor not in g_score:
                g_score[neighbor] = math.inf
            if tenative_gScore < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tenative_gScore
                f_score[neighbor] = tenative_gScore + h(neighbor, target)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return "No Path"

def patch_together(inter_node_costs):
    pass

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
