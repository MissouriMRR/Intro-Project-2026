"""
starter_hard_solver.py
TEAM NAME: AI Team (with the help of Codex)

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
  - "risk":      no cost change. Just don't fly through a cell that has 2
                 or more '#' directly N/S/E/W of it (diagonals don't count)
                 - if you do, that map's score is x0.4.
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
MODIFIERS = ["terrain"]

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}


def solve(
    grid: list[list[str]], start: tuple[int, int], target: tuple[int, int]
) -> list[str]:
    if start == target:
        return []
    stride = len(grid[0]) + 2
    text = (
        "#" * stride + "".join("#" + "".join(row) + "#" for row in grid) + "#" * stride
    )
    costs = list(
        text.translate(
            {
                35: 0,
                46: 1,
                83: 1,
                84: 1,
                42: 1,
                49: 1,
                50: 2,
                51: 3,
                52: 4,
                53: 5,
                54: 6,
                55: 7,
                56: 8,
                57: 9,
            }
        ).encode("ascii")
    )
    source = (start[0] + 1) * stride + start[1] + 1
    goal = (target[0] + 1) * stride + target[1] + 1
    parents = [0] * len(costs)
    offsets = (0, -stride, stride, 1, -1)
    buckets: list[list[int]] = [[] for _ in range(11)] * 2
    buckets[0].append(source)
    pending, index = 1, 0
    if any(ch in text for ch in "23456789") and sum(costs) >= 3 * (
        len(costs) - costs.count(0)
    ):
        costs[source] = 0
        while pending:
            bucket = buckets[index]
            if not bucket:
                index = (index + 1) % 11
                continue
            current = bucket.pop()
            pending -= 1
            if current == goal:
                break
            neighbor = current - stride
            cost = costs[neighbor]
            if cost:
                costs[neighbor] = 0
                parents[neighbor] = 1
                buckets[index + cost].append(neighbor)
                pending += 1
            neighbor = current + stride
            cost = costs[neighbor]
            if cost:
                costs[neighbor] = 0
                parents[neighbor] = 2
                buckets[index + cost].append(neighbor)
                pending += 1
            neighbor = current + 1
            cost = costs[neighbor]
            if cost:
                costs[neighbor] = 0
                parents[neighbor] = 3
                buckets[index + cost].append(neighbor)
                pending += 1
            neighbor = current - 1
            cost = costs[neighbor]
            if cost:
                costs[neighbor] = 0
                parents[neighbor] = 4
                buckets[index + cost].append(neighbor)
                pending += 1
    else:
        tr, tc = target[0] + 1, target[1] + 1
        distances = [len(costs) * 9] * len(costs)
        distances[source] = 0
        while pending:
            bucket = buckets[index]
            if not bucket:
                index = (index + 1) % 11
                continue
            current = bucket.pop()
            pending -= 1
            if not costs[current]:
                continue
            if current == goal:
                break
            costs[current] = 0
            distance = distances[current]
            row, col = divmod(current, stride)
            neighbor = current - stride
            cost = costs[neighbor]
            if cost:
                candidate = distance + cost
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    parents[neighbor] = 1
                    buckets[index + cost + (-1 if row > tr else 1)].append(neighbor)
                    pending += 1
            neighbor = current + stride
            cost = costs[neighbor]
            if cost:
                candidate = distance + cost
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    parents[neighbor] = 2
                    buckets[index + cost + (-1 if row < tr else 1)].append(neighbor)
                    pending += 1
            neighbor = current + 1
            cost = costs[neighbor]
            if cost:
                candidate = distance + cost
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    parents[neighbor] = 3
                    buckets[index + cost + (-1 if col < tc else 1)].append(neighbor)
                    pending += 1
            neighbor = current - 1
            cost = costs[neighbor]
            if cost:
                candidate = distance + cost
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    parents[neighbor] = 4
                    buckets[index + cost + (-1 if col > tc else 1)].append(neighbor)
                    pending += 1
    if not parents[goal]:
        return []
    path: list[str] = []
    current = goal
    while current != source:
        direction = parents[current]
        path.append(" NSEW"[direction])
        current -= offsets[direction]
    path.reverse()
    return path


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
