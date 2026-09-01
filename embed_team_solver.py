import numpy as np

def solve(grid, start, target):
    path = []
    current = start
    binMap = np.ndarray( (len(grid[0]), len(grid)) )
    
    #make binary 2d array
    for col, wholeCol in enumerate(grid):
        for row, char in enumerate(wholeCol):
            if char == "#":
                binMap[row, col] = 0  
            else:
                binMap[row, col] = 1

    
    # return path


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
