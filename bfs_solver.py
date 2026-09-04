class PathSolver:

    def __init__(s, grid):
        s.grid = grid

    def solve(s, start, end):
        """
        returns a list of moves to get from the start to the target
        """
        path = s.find_path(start, end)
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


