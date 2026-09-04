from bfs_solver import PathSolver


class WaypointManager:

    def __init__(s, grid, start, end, waypoints):
        s.grid = grid
        s.start = start
        s.end = end
        s.waypoints = waypoints
        s.path_solver = PathSolver(s.grid)

    def solve_route(s):

    def get_waypoint_connections(s):
        # makes a list to make sure that nodes arent searched multiple times.
        nodes_searched = []

        # Makes the dictionary that records the weighted graph of waypoint connections, and the path between them.
        # form: {(x1, y1),(y1, y2): len(path), [path N,S,E,W from p1 to p2]}
        move_dict = {}

        for waypoint in s.waypoints:
            # make list of targets that are not the current waypoint, and have not been searched yet.
            targets = [point not in nodes_searched and point != waypoint]
            if s.end not in nodes_searched:
                targets.append(s.end)
            if s.start not in nodes_searched:
                targets.append(s.start)

            nodes_searched.append(waypoint)
            # add the connections to the move_dict
            for target in targets:
                if waypoint == target:
                    continue
                moves = s.path_solver.get_moves(s.grid, waypoint, target)
                move_dict[(waypoint, target)] = (len(moves), moves)
        return move_dict

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
