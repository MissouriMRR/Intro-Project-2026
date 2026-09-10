from collections import deque

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

# Hint: a queue is a handy building block for BFS. You don't have to use it.
from collections import deque  # noqa: F401

TUPLE_TO_MOVE = {
    (-1, 0): "N",
    (1, 0): "S",
    (0, 1): "E",
    (0, -1): "W"
}



def solve(grid, start, target):
    #The final path which will be returned
    path = []

    #The edge of the currently searched space.
    frontier = deque()
    frontier.append(start)

    #A dictionary of (node: previous node) pairs found while flood filling
    came_from = {}
    came_from[start] = None

    #While there are currently items on the frontier
    while len(frontier) != 0:
        #Pop left because we are appending to the right
        current = frontier.popleft()

        #If we find the target
        if current == target:
          #Continue unraveling the path one step at a time until the current node is the start node
          while came_from[current] is not None:
              #Use came from dict to find the previous node we went through to get here 
              previous = came_from[current]
              #Find the direction travelled to get here.
              diff = (current[0] - previous[0], current[1] - previous[1])
              #Use TUPLE_TO_MOVE dict to find direction of travel
              path.append(TUPLE_TO_MOVE[diff])
              #Step one node back in time before we iterate again
              current = previous
          #Path is currently [target,...,start]. we need the opposite.
          path.reverse()
          return path

        #A list of the neighbors of current
        neighbors = []
        #Grab all possible moves
        for (d_row, d_col) in TUPLE_TO_MOVE.keys():
            #Find new position if move were taken
            nr, nc = current[0] + d_row, current[1] + d_col
            #Filter out moves that move outside of the board or into an obstacle
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
                #Add any moves that are valid
                neighbors.append((nr,nc))

        #Iterate through the neighbors list
        for next_item in neighbors:
            #filter for any items that have already been checked.
            if next_item not in came_from.keys():
                #Add neighbor to frontier
                frontier.append(next_item)
                #Denote that there was a step from current item -> next item
                came_from[next_item] = current
            


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
