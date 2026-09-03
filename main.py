import map_utils
def main():
    grid,start,end = map_utils.load_map("maps/practice_maps/practice_map.txt")
    print(solve(grid,start,end))

def solve(grid,start,finish):
    queue = [[start]] #Create a list of paths
    while queue: #run while there are paths to check
        path = queue.pop(0) #get the next path to check
        lastNode = path[-1] #get the end of the path
        if lastNode == finish: # is this a completed path?
            return path # path found!
        #No path, check adjacents
        adjacents = [] #start finding adjacents
        for dir in map_utils.MOVES:
            cx,cy = lastNode
            dx,dy = map_utils.MOVES[dir]
            new_node = (cx+dx,cy+dy)
            if map_utils.in_bounds(grid,new_node) and new_node not in path and map_utils.is_open(grid,new_node):
                adjacents.append(new_node) #valid adjacent
        #Add new paths with the new adjacents to the queue
        for adj in adjacents:
            new_path=list(path)
            new_path.append(adj)
            queue.append(new_path)

if __name__ == "__main__":
    main()