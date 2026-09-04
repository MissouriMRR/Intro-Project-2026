from bfs_solver import PathSolver
import copy

class WaypointManager:

    def __init__(s, grid, start, end, waypoints):
        s.grid = grid
        s.start = start
        s.end = end
        s.waypoints = waypoints
        s.path_solver = PathSolver(s.grid)
        if waypoints != []:
            s.gen_waypoint_connections()
        

    def gen_waypoint_connections(s):
        # makes a list to make sure that nodes arent searched multiple times.
        nodes_searched = []

        # stored in form of from: to: len of path
        # nodes stored as number as defined in s.waypoints
        # start and end nodes are -1 and -2 respectively

        s.move_dict = {i: {} for i in range(-2, len(s.waypoints))}

        

        for i, currentPoint in enumerate(s.waypoints):
            # make list of targets that are not the current waypoint, and have not been searched yet.
            targets = [point for point in s.waypoints if point != currentPoint and point not in nodes_searched]

            targets.append(s.end)

            targets.append(s.start)

            nodes_searched.append(currentPoint)
            # add the connections to the move_dict
            for target in targets:
                moves = s.path_solver.solve(currentPoint, target)
                if target == s.start:
                    s.move_dict[i][-2] = moves
                    s.move_dict[-2][i] = s.move_flipper(moves)
                elif target == s.end:
                    s.move_dict[i][-1] = moves
                    s.move_dict[-1][i] = s.move_flipper(moves)
                else:
                    s.move_dict[i][s.waypoints.index(target)] = moves
                    s.move_dict[s.waypoints.index(target)][i] = s.move_flipper(moves)


        s.distance_dict = {from_node_id: {toNodeId: len(path) for toNodeId, path in potential_paths.items()} for from_node_id, potential_paths  in s.move_dict.items()}
        print("Distance Between Nodes:", s.distance_dict)



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


    #return shortest possible path that start on the start, hits all waypoints and ends on the end
    #returns as a list of node ids
    
    def get_node_order(s):



        class Runner:

            def __init__(s, past_nodes_ids=[], from_node_id = None, current_node_id=None, destination_id=None, path_length=None):

                s.current_node_id = current_node_id
                s.destination_id = destination_id
                s.walk_left = path_length
                s.past_node_ids = past_nodes_ids
                s.from_node_id = from_node_id

                s.courseComplete = False

                #print(s.walk_left)
                

            def walk_path(s, steps):
                s.walk_left -= steps


                s.check_path_completion()

            def check_path_completion(s):
                if s.walk_left <= 0:
                    s.past_node_ids.append(s.from_node_id)
                    s.current_node_id = s.destination_id
                    s.from_node_id = None

                    if s.current_node_id == -1:
                        s.courseComplete = True

            def start_path(s, destination_id, path_length):
                s.from_node_id = s.current_node_id
                s.destination_id = destination_id
                s.walk_left = path_length
                s.current_node_id = None
                #if s.from_node_id == 3 and s.destination_id == -1: #and s.past_node_ids== [-2,1,0,3]:
                #    print("Ah ha")

        runner_list = []

        for first_to_id in range(len(s.waypoints)):

            runner_list.append(Runner(from_node_id=-2,destination_id=first_to_id, path_length=s.distance_dict[-2][first_to_id]))
        
        while True:

            walk_left_list = [runner.walk_left for runner in runner_list]

            shortest_walk_left = min(walk_left_list)

            for runner in runner_list:

                runner.walk_path(shortest_walk_left)

                if runner.current_node_id != None:
                    #print("Runner at node!")
                    #print(runner.past_node_ids)
                    target_ids = [node_id for node_id in range(len(s.waypoints)) if node_id != runner.current_node_id and node_id not in runner.past_node_ids]
                    #print("Target IDs:", target_ids)
                    if target_ids != []:

                        for to_id in target_ids:
                            #print(to_id)
                            new_runner = copy.deepcopy(runner)
                            new_runner.start_path(to_id, s.distance_dict[runner.current_node_id][to_id])
                            runner_list.append(new_runner)
                        runner_list.remove(runner)
                    else:
                        if runner.courseComplete == False:
                            runner.start_path(-1, s.distance_dict[runner.current_node_id][-1])
                        else:
                            #print("Yay!!!")
                            node_order = runner.past_node_ids
                            node_order.append(-1)
                            print("Node Order By ID:", node_order)
                            return node_order


    def solve(s):
        if s.waypoints != []:
            node_order = s.get_node_order()

            total_moves = []
            for i in range(len(node_order)-1):
                for move in s.move_dict[node_order[i]][node_order[i+1]]:
                    total_moves.append(move)
            return total_moves
        return s.path_solver.solve(s.start, s.end)



                

"""

    def getNodeOrder(s):

        adj_matrix = []

        for i in range(-2, len(s.waypoints)):
            adj_matrix.append([])
            for j in range(-2, len(s.waypoints)):
                if j in s.move_dict[i]:
                    adj_matrix[i+2].append(s.distance_dict[i][j]))
                else:
                    adj_matrix[i+2].append(0)



        pathCost = []


        def getTargetNodes(s, pastNodes, currentNode):
            return [node for node in s.waypoints if node not in pastNodes and node != currentNode]


        def checkNextLayer(s, current_branch):

            new_branch =  current_branch

            for 



        



        way_path_dict = s.move_dict.copy()
        way_path_dict.pop(-1)
        way_path_dict.pop(-2)

        while True:
            for destination, potentail_paths in s.move_dict[-1].items():
                pathCost.append({destination, ([], len(potentail_paths))})
                
                
                for destination2, potentail_paths in s.move_dict[]
        """


    

   




        
