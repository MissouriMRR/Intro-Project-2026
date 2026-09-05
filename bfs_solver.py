import copy

class PathSolver:

    def __init__(s, grid):
        s.grid = grid

    def solve(s, start, end):
        """
        returns a list of moves to get from the start to the target
        """
        path = s.find_path(start, end)
 
        

        return path_to_move(path)

    


    #gets the amount of time it takes to cross a tile
    def get_tile_time(s, tile_pos):
        tile_value = s.grid[tile_pos[0]][tile_pos[1]]
        if tile_value == '*' or tile_value == 'S' or tile_value == 'T' or tile_value == '.':
            return 1
        elif tile_value == '#':
            print("Mines don't have a tile time!!!")
        return int(tile_value)

    def solve_terrian_path(s, start, end):

        class Runner:

            def __init__(s, pos, time_to_move=1, tile_history=[]):
                s.pos = pos
                s.time_to_move = time_to_move
                s.tile_history = tile_history

                s.step_complete = False

            def run(s):
                s.time_to_move -= 1
                s.checkIfStepComplete()

            def checkIfStepComplete(s):
                if s.time_to_move <= 0:
                    s.step_complete = True

            def move(s, new_pos, time_to_move):
                s.tile_history.append(s.pos)
                s.pos = new_pos
                s.time_to_move = time_to_move
                s.step_complete = False


        runner_list = [Runner(start)]
        walked_tiles = []

        while True:

            runners_to_add = []
            runners_to_remove = []

            for runner in runner_list:


                runner.run()

                if runner.step_complete:


                    pos = runner.pos

                    targets = []

                    if pos[0] > 0 and s.grid[pos[0]-1][ pos[1]] != '#':
                        targets.append((pos[0]-1,pos[1]))
                    
                    if pos[0] < len(s.grid)-1 and s.grid[pos[0]+1][pos[1]] != '#':
                        targets.append((pos[0]+1,pos[1]))
                    
                    if pos[1] > 0 and s.grid[pos[0]][pos[1]-1] != '#':
                        targets.append((pos[0],pos[1]-1))
                    
                    if pos[1] < len(s.grid[0])-1 and s.grid[pos[0]][pos[1]+1] != '#':
                        targets.append((pos[0],pos[1]+1))

                    for tile_pos in targets:

                        if tile_pos == end:
                            runner.tile_history.append(runner.pos)
                            runner.tile_history.append(end)
                            #print("Return????")
                            return path_to_move(runner.tile_history)


                        elif tile_pos not in walked_tiles:
                            new_runner = copy.deepcopy(runner)
                            new_runner.move(tile_pos, s.get_tile_time(tile_pos))
                            runners_to_add.append(new_runner)
                            walked_tiles.append(tile_pos)

                    runners_to_remove.append(runner)

            for runner in runners_to_remove:
                runner_list.remove(runner)

            for runner in runners_to_add:
                runner_list.append(runner)


   










    def find_path(s, start, end):
        """
        finds a path from startNode to endNode, and returns the coordinates of the path as a list of tuples
        """

        # queue of nodes and how they are connected to their originating nodes (child_i, child_j):(parent_i, parent_j)
        node_connections = {start: "S"}

        # list of nodes that are the origin points for the currentiteration
        current_origins = [start]
        future_origins = []

        # logic for adding connections to the queue
        while end not in node_connections:
            for current_i, current_j in current_origins:
                # look up
                if (
                    current_i - 1 >= 0
                    and s.grid[current_i - 1][current_j] != "#"
                    and (current_i - 1, current_j) not in node_connections
                ):
                    node_connections[(current_i - 1, current_j)] = (
                        current_i,
                        current_j,
                    )
                    future_origins.append((current_i - 1, current_j))
                # look down
                if (
                    current_i + 1 < len(s.grid)
                    and s.grid[current_i + 1][current_j] != "#"
                    and (current_i + 1, current_j) not in node_connections
                ):
                    node_connections[(current_i + 1, current_j)] = (
                        current_i,
                        current_j,
                    )
                    future_origins.append((current_i + 1, current_j))
                # look left
                if (
                    current_j - 1 >= 0
                    and s.grid[current_i][current_j - 1] != "#"
                    and (current_i, current_j - 1) not in node_connections
                ):
                    node_connections[(current_i, current_j - 1)] = (
                        current_i,
                        current_j,
                    )
                    future_origins.append((current_i, current_j - 1))
                # look right
                if (
                    current_j + 1 < len(s.grid[0])
                    and s.grid[current_i][current_j + 1] != "#"
                    and (current_i, current_j + 1) not in node_connections
                ):
                    node_connections[(current_i, current_j + 1)] = (
                        current_i,
                        current_j,
                    )
                    future_origins.append((current_i, current_j + 1))

            # reset origins for the next iteration
            current_origins = future_origins
            future_origins = []

        # rebuild the path from the node_connections. format: [(start_i, start_j), ... , (end_i, end_j)]
        path = []
        current = end
        while current != start:
            path.append(current)
            current = node_connections[current][0], node_connections[current][1]
        path.append(start)
        path.reverse()

        return path

    def findStartAndEndNodes(s):
        """
        uses the grid to find which nodes are the start and end nodes

        returns the start and end nodes as a tuple
        """
        startNode = None
        endNode = None

        for i, row in enumerate(s.grid):
            for j, cell in enumerate(row):
                if cell == "S":
                    startNode = (i, j)
                elif cell == "T":
                    endNode = (i, j)

        return startNode, endNode


def path_to_move(path):
    #print(path)
    moves = []
    for i in range(len(path) - 1):
        current, next = path[i], path[i + 1]
        if next[0] < current[0]:
            moves.append("N")
        elif next[0] > current[0]:
            moves.append("S")
        elif next[1] < current[1]:
            moves.append("W")
        elif next[1] > current[1]:
            moves.append("E")

    return moves
