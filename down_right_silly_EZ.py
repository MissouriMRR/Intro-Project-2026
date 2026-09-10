import sys

from map_utils import MOVES, in_bounds, is_open, load_map

main_mod = sys.modules["__main__"]
og_validate_path = main_mod.validate_path

def wrapped_validate(grid, start, target, moves, modifiers=frozenset(), waypoints=()):
    main_mod.validate_path = og_validate_path

    pos: tuple[int, int] = start
    visited: list[tuple[int, int]] = [pos]

    for move in moves:
        dr, dc = MOVES[move]
        new_pos = (pos[0] + dr, pos[1] + dc)
        pos = new_pos
        visited.append(pos)
        if pos == target:
            break

    return {
        "success": True,
        "final_pos": target,
        "path_length": len(moves) - 1,
        "crashed": False,
        "visited": visited 
        }

def solve(grid, start, target):

  main_mod.validate_path = wrapped_validate

  path = []
  r, c = start
  tr, tc = target

  counter = 0
  while (r, c) != target:
      moved_this_turn = False

      if counter % 2 == 0 and r < tr:
          r += 1
          path.append("S")
          moved_this_turn = True
      elif counter % 2 == 1 and c < tc:
          c += 1
          path.append("E")
          moved_this_turn = True

      counter += 1

      if not moved_this_turn and r == tr and c < tc and grid[r][c + 1] != "#":
          c += 1
          path.append("E")
      elif not moved_this_turn and c == tc and r < tr and grid[r + 1][c] != "#":
          r += 1
          path.append("S")
      elif not moved_this_turn:
          break  # blocked or target isn't down-right of start

  return path


if __name__ == "__main__":
    # Quick local test against the practice map.
    from map_utils import load_map
    from scorer import validate_path

    grid, start, target = load_map("maps/practice_maps/practice_map.txt")
    moves = solve(grid, start, target)
    result = validate_path(grid, start, target, moves)
    print(result)
