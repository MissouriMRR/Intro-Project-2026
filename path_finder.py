from bfs_solver import PathSolver
import copy




class PathFinder:

    """
    Finds the optimal path from the start to the end while accounting for all modifiers.

    The solve function is used to find path in form of moves.
    """

    def __init__(s, grid, start, end, waypoints, risk_modifier_on = True):
        s.grid = copy.deepcopy(grid)
        if risk_modifier_on:
            s.process_grid()
        s.start = start
        s.end = end
        s.waypoints = waypoints
        s.path_solver = PathSolver(s.grid)
        if waypoints != []:
            s.gen_waypoint_connections()
        
    """
    Generates the relationship of each node to each other nodes.
    
    Create a dictionary of moves and of cost.
    """
    def gen_waypoint_connections(s):
        # makes a list to make sure that nodes arent searched multiple times.
        nodes_searched = []

        # stored in form of from: to: path/cost
        # nodes stored as number as defined in s.waypoints
        # start and end nodes are -1 and -2 respectively

        
        s.move_dict = {i:{} for i in range(-2, len(s.waypoints))}
        s.cost_dict = {i:{} for i in range(-2, len(s.waypoints))}
        

        for i, currentPoint in enumerate(s.waypoints):
            # make list of targets that are not the current waypoint, and have not been searched yet.
            targets = [point for point in s.waypoints if point != currentPoint and point not in nodes_searched]

            targets.append(s.end)

            targets.append(s.start)

            nodes_searched.append(currentPoint)
            # add the connections to the move_dict
            for target in targets:
                moves, cost = s.path_solver.solve_terrian_path(currentPoint, target)
                if target == s.start:
                    s.move_dict[i][-2] = moves
                    s.move_dict[-2][i] = s.move_flipper(moves)
                    s.cost_dict[i][-2] = cost
                    s.cost_dict[-2][i] = cost
                elif target == s.end:
                    s.move_dict[i][-1] = moves
                    s.move_dict[-1][i] = s.move_flipper(moves)
                    s.cost_dict[i][-1] = cost
                    s.cost_dict[-1][i] = cost
                else:

                    target_id = s.waypoints.index(target)
                    s.move_dict[i][target_id] = moves
                    s.move_dict[target_id][i] = s.move_flipper(moves)
                    s.cost_dict[i][target_id] = cost
                    s.cost_dict[target_id][i] = cost

        
        


    """
    Takes moves to get from A to B and returns list of moves to get from B to A.
    """
    def move_flipper(s, moves):
        flipped_moves = []
        for element in moves:
            if element == "N":
                flipped_moves.append("S")
            elif element == "S":
                flipped_moves.append("N")
            elif element == "E":
                flipped_moves.append("W")
            elif element == "W":
                flipped_moves.append("E")
        flipped_moves.reverse()
        return flipped_moves

    
    def get_node_order(s):
        """
        Returns shortest possible path that start on the start, hits all waypoints and ends on the end.

        Returns as a list of node ids.
        """


        class Runner:
            """
            Class built to "run" along potentail paths until it hits all waypoints and can head to the ending node.

            Runners are supposed to replicate when they reach a node to all valid targets.

            This and most of thier other functions are ran by the code as the runners are to simple to do it all themselves.

            The first runner to reach the ending node should contain within its history the fastest possible order of nodes that hits all waypoints.
            """


            def __init__(s, past_nodes_ids=[], from_node_id = None, current_node_id=None, destination_id=None, path_length=None):

                s.current_node_id = current_node_id
                s.destination_id = destination_id
                s.walk_left = path_length
                s.past_node_ids = past_nodes_ids
                s.from_node_id = from_node_id

                s.courseComplete = False


                
            """
            Moves along the path it is currently on a set number of times.

            Will update various variables if it reaches the node at the end of the path.
            """
            def walk_path(s, steps):
                s.walk_left -= steps


                s.check_path_completion()


            """
            Updates various values if the runner has completed its current path.

            Values include: list of past nodes, current node and whether or not it has completed its journey(found ending node).
            """
            def check_path_completion(s):
                if s.walk_left <= 0:
                    s.past_node_ids.append(s.from_node_id)
                    s.current_node_id = s.destination_id
                    s.from_node_id = None

                    if s.current_node_id == -1:
                        s.courseComplete = True


            """
            Starts a node along a given path by updating various values.

            Values include: node its coming from, its destination and the path left to walk.
            """
            def start_path(s, destination_id, path_length):
                s.from_node_id = s.current_node_id
                s.destination_id = destination_id
                s.walk_left = path_length
                s.current_node_id = None


        
        runner_list = []


        # Initializes the first set of runners.
        # The runners that leave the starting node
        for first_to_id in range(len(s.waypoints)):

            runner_list.append(Runner(from_node_id=-2,destination_id=first_to_id, path_length=s.cost_dict[-2][first_to_id]))


        
        while True:


            

            # finds the shortest walk need for a runner to reach a node
            shortest_walk_left = min([runner.walk_left for runner in runner_list])

            # these are needed because we cannot add or remove list while we are iterating through it
            runners_to_add = []
            runners_to_remove = []

            for runner in runner_list:

                # moves runner the shortest walk
                runner.walk_path(shortest_walk_left)

                # checks to see if runner is at a node
                if runner.current_node_id != None:

                    # creates list of valid targets for new runners
                    # waypoints - waypoint in nodes history
                    target_ids = [node_id for node_id in range(len(s.waypoints)) if node_id != runner.current_node_id and node_id not in runner.past_node_ids]

                    
                    reached_all_waypoints = target_ids == []
                    if not reached_all_waypoints:

                        # creates a new runner going to every node in the list of target nodes
                        # also prepares the current runner to be removed
                        for to_id in target_ids:
                            
                            new_runner = copy.deepcopy(runner)
                            new_runner.start_path(to_id, s.cost_dict[runner.current_node_id][to_id])
                            runners_to_add.append(new_runner)

                        runners_to_remove.append(runner)
                    else:
                        # since all runners here have reach all waypoints they must have either reached the end or need to be sent to the end
                        
                        
                        if runner.courseComplete == False:
                            print("Runner traveling to end after following path:", runner.past_node_ids, "and current node:", runner.current_node_id)
                            # sends runner to ending node
                            runner.start_path(-1, s.cost_dict[runner.current_node_id][-1])
                        else:

                            # below records the order that the runner hit the nodes and returns it
                            node_order = runner.past_node_ids
                            node_order.append(-1)
                            print("Node Order By ID:", node_order)
                            return node_order

            for runner in runners_to_add:
                runner_list.append(runner)

            for runner in runners_to_remove:
                runner_list.remove(runner)

    
    def process_grid(s):
        """
        Processes the grid to account for the risk modifier
        """

        
        def num_adj_mines(tile_pos):
            """
            Returns the number of adjacent mines.

            Checks omnidirectionally.
            """
            num_mines = 0

            for veritical in (-1,0,1):
                for horizontal in (-1,0,1):
                    if (
                        veritical + tile_pos[0] != -1 and 
                        veritical + tile_pos[0] != len(s.grid) and 
                        horizontal + tile_pos[1] != -1 and
                        horizontal + tile_pos[1] != len(s.grid[0]) and
                        s.grid[veritical + tile_pos[0]][horizontal + tile_pos[1]] == '#'
                    ):
                        num_mines += 1


            return num_mines

        
        #stores indexs where mines need to be added
        mines_to_add = []

        #gets list of potentail numbers as seen within the grid
        string_nums = [f"{i}" for i in range(2, 10)]
        

        for i, row in enumerate(s.grid):
            for j, tile in enumerate(row):
                #checks if tile is can be moves onto
                if tile != '#':
                    num_mines = num_adj_mines((i,j))
                    if num_mines >= 3:
                        mines_to_add.append((i,j))
                    elif num_mines != 0:
                        if tile not in string_nums:
                            #computes cost of all tiles that have cost of 1
                            cost = 2*num_mines + 1
                        else:
                            # adds the risk cost to numbered tiles
                            cost = int(tile) + 2*num_mines
                        s.grid[i][j] = str(cost)

        for i, j in mines_to_add:
            s.grid[i][j] = '#'
                        


    def solve(s):
        if s.waypoints != []:
            node_order = s.get_node_order()

            total_moves = []
            for i in range(len(node_order)-1):
                for move in s.move_dict[node_order[i]][node_order[i+1]]:
                    total_moves.append(move)
            return total_moves
        return s.path_solver.solve_terrian_path(s.start, s.end)[0]



                