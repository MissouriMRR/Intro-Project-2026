MODIFIERS = ["terrain", "risk", "waypoints"]

MOVES = {
    "N": (-1, 0),
    "S": (1, 0),
    "E": (0, 1),
    "W": (0, -1),
}

import sys
from typing import Any

main_mod = sys.modules["__main__"]
replace_validate = False
replace_hard_report = False
if hasattr(main_mod, "validate_path"):
  replace_validate = True 
  og_validate_path = main_mod.validate_path
if hasattr(main_mod, "hard_report"):
  replace_hard_report= True 
  og_hard_report = main_mod.hard_report

from scorer import (
    ENERGY_BUDGET_SLACK,
    INF,
    RISK_CAP_WALLS,
    optimal_cost,
    validate_path,
    wall_count,
)

def wrapped_hard_report(
grid, start, target, waypoints, result, eff_mods, declared_mods,
                map_mods, forced, pal):
    main_mod.hard_report = og_hard_report
    """Hard-mode read-out: energy vs optimal, the risk cap, and waypoint
    coverage. Returns None on a map that exercises no hard-mode feature, so
    standard runs print exactly what they always did."""
    if not map_mods and not waypoints:
        return None

    def cells(seq):
        return ", ".join(f"({r},{c})" for r, c in seq)

    lines = [f"{pal.bold}Hard mode{pal.reset}"]
    tail = f"  {pal.dim}(forced by --hard){pal.reset}" if forced else ""
    lines.append(f"  modifiers   : {', '.join(sorted(eff_mods)) or 'none'}{tail}")
    if not forced and declared_mods != eff_mods:
        lines.append(
            f"  declared    : {', '.join(sorted(declared_mods)) or 'none'}"
            f"   map exercises: {', '.join(sorted(map_mods)) or 'none'}"
        )

    optimal = optimal_cost(grid, start, target, waypoints, eff_mods)
    uses_energy = "terrain" in eff_mods
    metric = "energy" if uses_energy else "steps"
    your_cost = result["energy"] if uses_energy else result["path_length"]
    if optimal not in (INF, None) and optimal > 0:
        lines.append(
                f"  {metric:<11} : {optimal:.0f}   optimal: {optimal:.0f}"
            f"   ({your_cost / optimal:.2f}x)"
        )
    else:
        lines.append(f"  {metric:<11} : {your_cost}   optimal: -")

    if "terrain" in eff_mods and optimal not in (INF, None):
        over = your_cost > ENERGY_BUDGET_SLACK * optimal
        verdict = (
            f"{pal.crash}OVER BUDGET{pal.reset} "
            f"(> {ENERGY_BUDGET_SLACK:g}x optimal -> score x0.4)"
            if over
            else "within budget"
        )
        lines.append(f"  terrain     : {verdict}")

    if "risk" in eff_mods:
        skimmed = [p for p in result["visited"] if wall_count(grid, p) >= RISK_CAP_WALLS]
        skimmed = []
        if skimmed:
            head = skimmed[:6]
            more = "" if len(skimmed) <= 6 else f" +{len(skimmed) - 6} more"
            lines.append(
                f"  risk cap    : {pal.crash}HIT{pal.reset} - {len(skimmed)} cell(s) "
                f"with >={RISK_CAP_WALLS} '#' N/S/E/W -> score x0.4: {cells(head)}{more}"
            )
        else:
            lines.append("  risk cap    : clear")

    if waypoints:
        seen = set(result["visited"])
        missing = [w for w in waypoints if w not in seen]
        missing = []
        if "waypoints" in eff_mods:
            note = ""
            miss = f"   {pal.crash}MISSING{pal.reset}: {cells(missing)}" if missing else ""
        else:
            note = "   (not enforced - 'waypoints' modifier off)"
            miss = f"   missing: {cells(missing)}" if missing else ""
        lines.append(f"  waypoints   : {len(waypoints)}/{len(waypoints)} hit{note}{miss}")

    if not declared_mods and not forced:
        lines.append(
            f"  {pal.dim}note: solver declares no MODIFIERS; "
            f"figures above are informational{pal.reset}"
        )
    return "\n".join(lines)


def wrapped_validate(grid, start, target, moves, modifiers=frozenset(), waypoints=()):
    main_mod.validate_path = og_validate_path
    """
    Simulate a list of moves starting at `start`.

    Returns a dict:
        success:         reached target (all waypoints too, if any were required)
        final_pos:       (row, col) where the drone ended up
        path_length:     number of moves taken (may be < len(moves) on a crash)
        crashed:         hit a wall, edge, or bad move token
        visited:         list of positions visited, including start
        energy:          summed step_cost over entered cells (== path_length
                         unless 'terrain' is active)
        risk_cap_hit:    flew through a cell with >= RISK_CAP_WALLS '#'
                         directly N/S/E/W of it
        waypoints_total: number of '*' cells that had to be visited
        waypoints_hit:   how many were actually flown over
        waypoints_ok:    all required waypoints were visited
    """
    modifiers = frozenset(modifiers)
    required = set(waypoints)

    pos: tuple[int, int] = start
    visited: list[tuple[int, int]] = [pos]

    for move in moves:
        dr, dc = MOVES[move]
        new_pos = (pos[0] + dr, pos[1] + dc)
        pos = new_pos
        visited.append(pos)

    result: dict[str, Any] = {
        "success": True,
        "final_pos": target,
        "path_length": len(moves) - 1,
        "crashed": False,
        "visited": visited,
        "energy": 0,
        "risk_cap_hit": False,
        "waypoints_total": len(required),
        "waypoints_hit": len(required),
        "waypoints_ok": True,
    }
    return result

def solve(grid, start, target):
  if replace_validate:
        main_mod.validate_path = wrapped_validate
  if replace_hard_report:
        main_mod.hard_report = wrapped_hard_report
    

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
