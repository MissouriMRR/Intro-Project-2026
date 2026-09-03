"""
visualize.py
Renders a solved path over a drone map so you can actually see the route
the drone flew: which way it went at every step, where it doubled back,
and exactly where it crashed.

Handy for teams debugging their solver, or for showing results on a
projector during the demo meeting.

Usage:
    uv run visualize.py <solver_file.py> <map_file.txt> [options]

Hard mode is picked up automatically: if the map has terrain digits or
'*' waypoints, weighted cells and waypoints are drawn, and the summary
reports energy vs optimal, the risk cap, and waypoint coverage. Which
rules are actually enforced follows the solver's MODIFIERS (same as the
scorer); pass --hard to force every modifier the map exercises.

Options:
    --animate         replay the flight one step at a time
    --delay SECONDS   time between animation frames (default 0.25)
    --no-color        plain ASCII output (for logs / redirected output)
    --hard            enable every modifier the map exercises, ignoring
                      the solver's declared MODIFIERS

Examples:
    uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt
    uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt --animate
    uv run visualize.py sample_solvers/hard_reckless.py maps/scoring_maps_hard/hard_01.txt
    uv run visualize.py sample_solvers/normal_bfs.py maps/scoring_maps_hard/hard_01.txt --hard
"""

import argparse
import os
import sys
import time

from map_utils import MOVES, load_map_ex, wall_count
from scorer import (
    ENERGY_BUDGET_SLACK,
    INF,
    RISK_CAP_WALLS,
    active_modifiers,
    load_team,
    optimal_cost,
    validate_path,
)

# Direction glyphs, drawn on the cell the drone was leaving.
ARROWS = {"N": "^", "S": "v", "E": ">", "W": "<"}
DIRECTION_NAMES = {"N": "north", "S": "south", "E": "east", "W": "west"}


class Palette:
    """ANSI colors, or empty strings when color is disabled."""

    def __init__(self, enabled):
        def code(seq):
            return seq if enabled else ""

        self.enabled = enabled
        self.reset = code("\033[0m")
        self.open = code("\033[90m")  # unvisited open airspace
        self.wall = code("\033[31m")  # obstacle
        self.trail = code("\033[36m")  # cells flown once
        self.repeat = code("\033[35m")  # cells flown more than once
        self.start = code("\033[1;32m")
        self.target = code("\033[1;33m")
        self.drone = code("\033[1;97;44m")  # current position while animating
        self.crash = code("\033[1;97;41m")
        self.dim = code("\033[2m")
        self.bold = code("\033[1m")
        self.waypoint = code("\033[1;35m")  # unvisited mandatory '*' waypoint
        self.weight_lo = code("\033[2;33m")  # terrain cost 2-3
        self.weight_mid = code("\033[33m")  # terrain cost 4-6
        self.weight_hi = code("\033[1;31m")  # terrain cost 7-9


def weight_glyph(pal, ch):
    """Draw a terrain-cost digit, tinted by how expensive the cell is."""
    n = int(ch)
    if n <= 3:
        color = pal.weight_lo
    elif n <= 6:
        color = pal.weight_mid
    else:
        color = pal.weight_hi
    return f"{color}{ch}{pal.reset}"


def enable_ansi():
    """Turn on ANSI escape handling on older Windows consoles."""
    if os.name == "nt":
        os.system("")


def color_enabled(no_color_flag):
    if no_color_flag or os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def crash_info(grid, visited, moves, crashed):
    """
    Work out which move ended the run and which cell it aimed at.
    Returns (bad_move, blocked_cell, reason) or (None, None, None).
    """
    if not crashed:
        return None, None, None
    idx = len(visited) - 1
    if idx >= len(moves):
        return None, None, None
    bad_move = moves[idx]
    if bad_move not in MOVES:
        return bad_move, None, f"{bad_move!r} is not a valid move"
    dr, dc = MOVES[bad_move]
    r, c = visited[-1]
    cell = (r + dr, c + dc)
    if not (0 <= cell[0] < len(grid) and 0 <= cell[1] < len(grid[0])):
        return bad_move, cell, "flew off the edge of the map"
    return bad_move, cell, "flew into restricted airspace (#)"


def build_overlay(visited, upto):
    """
    Return (glyphs, counts) for the first `upto` positions of the flight.

    Each visited cell is drawn as the direction the drone left it in, so
    the arrows read as a route. The last cell of the segment has no
    outgoing move yet, so it gets no arrow. `counts` records how many
    times each cell was entered, which is how revisits get highlighted.
    """
    glyphs = {}
    counts = {}
    leg = visited[:upto]
    for i, pos in enumerate(leg):
        counts[pos] = counts.get(pos, 0) + 1
        if i + 1 < len(leg):
            nr, nc = leg[i + 1]
            delta = (nr - pos[0], nc - pos[1])
            for name, move_delta in MOVES.items():
                if move_delta == delta:
                    glyphs[pos] = ARROWS[name]
                    break
    return glyphs, counts


def render(
    grid, visited, start, target, pal, upto=None, drone_cell=None, crash_cell=None
):
    """
    Draw the grid with the route overlaid.

    upto:        how many visited positions to draw (None = whole flight)
    drone_cell:  cell to highlight as the drone's current position
    crash_cell:  cell the drone tried and failed to enter
    """
    upto = len(visited) if upto is None else upto
    glyphs, counts = build_overlay(visited, upto)
    width = len(grid[0])

    out = [f"{pal.dim}    " + " ".join(str(c % 10) for c in range(width)) + pal.reset]
    for r, row in enumerate(grid):
        cells = []
        for c, ch in enumerate(row):
            pos = (r, c)
            if pos == crash_cell:
                cells.append(f"{pal.crash}X{pal.reset}")
            elif pos == drone_cell:
                cells.append(f"{pal.drone}@{pal.reset}")
            elif pos == start:
                cells.append(f"{pal.start}S{pal.reset}")
            elif pos == target:
                cells.append(f"{pal.target}T{pal.reset}")
            elif pos in glyphs:
                color = pal.repeat if counts[pos] > 1 else pal.trail
                cells.append(f"{color}{glyphs[pos]}{pal.reset}")
            elif pos in counts:
                cells.append(f"{pal.trail}o{pal.reset}")
            elif ch == "#":
                cells.append(f"{pal.wall}#{pal.reset}")
            elif ch == "*":
                # Only reached for waypoints the drone never flew over.
                cells.append(f"{pal.waypoint}*{pal.reset}")
            elif ch.isdigit():
                cells.append(weight_glyph(pal, ch))
            else:
                cells.append(f"{pal.open}.{pal.reset}")
        out.append(f"{pal.dim}{r % 10:>3}{pal.reset} " + " ".join(cells))
    return "\n".join(out)


def legend(pal, grid=None):
    parts = [
        f"{pal.start}S{pal.reset} start",
        f"{pal.target}T{pal.reset} target",
        f"{pal.trail}> v < ^{pal.reset} direction flown",
        f"{pal.repeat}> v < ^{pal.reset} flown more than once",
        f"{pal.trail}o{pal.reset} ended here",
        f"{pal.wall}#{pal.reset} restricted",
        f"{pal.crash}X{pal.reset} crash",
    ]
    flat = "".join("".join(row) for row in grid) if grid else ""
    if "*" in flat:
        parts.append(f"{pal.waypoint}*{pal.reset} waypoint (unvisited)")
    if any(ch.isdigit() for ch in flat):
        parts.append(f"{pal.weight_mid}2-9{pal.reset} terrain cost")
    return f"{pal.dim}Legend:{pal.reset} " + "   ".join(parts)


def step_log(visited, moves, pal):
    """A move-by-move account of the flight, a few steps per line."""
    entries = []
    for i in range(len(visited) - 1):
        move = moves[i]
        entries.append(f"{i + 1:>3}. {ARROWS[move]} {move} -> {visited[i + 1]}")
    if not entries:
        return f"   {pal.dim}(no moves taken){pal.reset}"

    per_line = 4
    lines = []
    for i in range(0, len(entries), per_line):
        chunk = entries[i : i + per_line]
        lines.append("   " + "".join(f"{entry:<22}" for entry in chunk).rstrip())
    return "\n".join(lines)


def summary(result, target, pal, bad_move, blocked_cell, reason):
    head = (
        f"{pal.start}REACHED TARGET{pal.reset}"
        if result["success"]
        else f"{pal.crash} DID NOT REACH TARGET {pal.reset}"
    )
    lines = [
        head,
        f"  moves flown : {result['path_length']}",
        f"  ended at    : {result['final_pos']}   target: {target}",
        f"  crashed     : {result['crashed']}",
    ]
    if bad_move is not None:
        step = result["path_length"] + 1
        if bad_move in DIRECTION_NAMES:
            heading = f"{DIRECTION_NAMES[bad_move]} toward {blocked_cell}"
            lines.append(f"  cause       : move {step} ({heading}) {reason}")
        else:
            lines.append(f"  cause       : move {step} {reason}")
    return "\n".join(lines)


def hard_report(grid, start, target, waypoints, result, eff_mods, declared_mods,
                map_mods, forced, pal):
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
    uses_energy = bool(eff_mods & {"terrain", "risk"})
    metric = "energy" if uses_energy else "steps"
    your_cost = result["energy"] if uses_energy else result["path_length"]
    if optimal not in (INF, None) and optimal > 0:
        lines.append(
            f"  {metric:<11} : {your_cost}   optimal: {optimal:.0f}"
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
        if skimmed:
            head = skimmed[:6]
            more = "" if len(skimmed) <= 6 else f" +{len(skimmed) - 6} more"
            lines.append(
                f"  risk cap    : {pal.crash}HIT{pal.reset} - {len(skimmed)} cell(s) "
                f"touch >={RISK_CAP_WALLS} '#' -> score x0.4: {cells(head)}{more}"
            )
        else:
            lines.append("  risk cap    : clear")

    if waypoints:
        seen = set(result["visited"])
        missing = [w for w in waypoints if w not in seen]
        hit = len(waypoints) - len(missing)
        if "waypoints" in eff_mods:
            note = ""
            miss = f"   {pal.crash}MISSING{pal.reset}: {cells(missing)}" if missing else ""
        else:
            note = "   (not enforced - 'waypoints' modifier off)"
            miss = f"   missing: {cells(missing)}" if missing else ""
        lines.append(f"  waypoints   : {hit}/{len(waypoints)} hit{note}{miss}")

    if not declared_mods and not forced:
        lines.append(
            f"  {pal.dim}note: solver declares no MODIFIERS; "
            f"figures above are informational{pal.reset}"
        )
    return "\n".join(lines)


def clear_screen(pal):
    if pal.enabled:
        sys.stdout.write("\033[H\033[J")
    else:
        print("\n" * 2)


def animate(grid, visited, moves, start, target, pal, delay, crash_cell):
    total = len(visited) - 1
    for step, pos in enumerate(visited):
        clear_screen(pal)
        if step == 0:
            action = "takeoff"
        else:
            move = moves[step - 1]
            action = f"{ARROWS[move]} {DIRECTION_NAMES.get(move, move)}"
        print(f"{pal.bold}Step {step}/{total}{pal.reset}   {action}   now at {pos}")
        print()
        print(render(grid, visited, start, target, pal, upto=step + 1, drone_cell=pos))
        print()
        print(legend(pal, grid))
        sys.stdout.flush()
        if step < total or crash_cell is not None:
            time.sleep(delay)

    if crash_cell is not None:
        clear_screen(pal)
        print(
            f"{pal.bold}Step {total + 1}/{total}{pal.reset}   {pal.crash} CRASH {pal.reset}"
        )
        print()
        print(
            render(
                grid,
                visited,
                start,
                target,
                pal,
                drone_cell=visited[-1],
                crash_cell=crash_cell,
            )
        )
        print()
        print(legend(pal, grid))


def main():
    parser = argparse.ArgumentParser(
        description="Visualize a solver's flight path over a map."
    )
    parser.add_argument("solver_file", help="Path to a solver .py file")
    parser.add_argument("map_file", help="Path to a map .txt file")
    parser.add_argument(
        "--animate", action="store_true", help="Replay the flight step by step"
    )
    parser.add_argument(
        "--delay", type=float, default=0.25, help="Seconds between animation frames"
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color")
    parser.add_argument(
        "--hard",
        action="store_true",
        help="Enable every modifier the map exercises, ignoring the solver's MODIFIERS",
    )
    args = parser.parse_args()

    enable_ansi()
    pal = Palette(color_enabled(args.no_color))

    grid, start, target, waypoints = load_map_ex(args.map_file)
    solve_fn, declared_mods = load_team(args.solver_file)

    # The scorer only applies modifiers on the hard-map pool. The visualizer
    # has no pool, so treat a map as hard when it actually uses a hard-mode
    # feature: terrain digits or '*' waypoints ('#' alone is just a wall).
    is_hard_map = bool(waypoints) or any(ch.isdigit() for row in grid for ch in row)
    map_mods = active_modifiers(grid) if is_hard_map else frozenset()
    eff_mods = map_mods if args.hard else (declared_mods & map_mods)
    req_wps = tuple(waypoints) if "waypoints" in eff_mods else ()

    moves = solve_fn(grid, start, target)
    result = validate_path(grid, start, target, moves, eff_mods, req_wps)

    bad_move, blocked_cell, reason = crash_info(
        grid, result["visited"], moves, result["crashed"]
    )
    # A crash off the edge of the map has no cell on the grid to mark.
    crash_cell = blocked_cell
    if crash_cell is not None and not (
        0 <= crash_cell[0] < len(grid) and 0 <= crash_cell[1] < len(grid[0])
    ):
        crash_cell = None

    if args.animate:
        animate(
            grid, result["visited"], moves, start, target, pal, args.delay, crash_cell
        )
        print()
    else:
        print()
        print(
            render(grid, result["visited"], start, target, pal, crash_cell=crash_cell)
        )
        print()
        print(legend(pal, grid))
        print()
        print(f"{pal.bold}Flight log{pal.reset}")
        print(step_log(result["visited"], moves, pal))
        print()

    print(summary(result, target, pal, bad_move, blocked_cell, reason))

    report = hard_report(
        grid, start, target, waypoints, result, eff_mods, declared_mods,
        map_mods, args.hard, pal,
    )
    if report:
        print()
        print(report)


if __name__ == "__main__":
    main()
