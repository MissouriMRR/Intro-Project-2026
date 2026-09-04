"""
visualize.py
Renders a solved path over a drone map so you can actually see the route
the drone flew: which way it went at every step, where it doubled back,
and exactly where it crashed.

Handy for teams debugging their solver, or for showing results on a
projector during the demo meeting.

Usage:
    uv run visualize.py <solver_file.py> <map_file.txt> [options]

Options:
    --animate         replay the flight one step at a time
    --delay SECONDS   time between animation frames (default 0.25)
    --no-color        plain ASCII output (for logs / redirected output)

Examples:
    uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt
    uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt --animate
"""

import argparse
import os
import sys
import time

from map_utils import MOVES, load_map
from scorer import load_solver, validate_path

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
                cells.append(f"{pal.trail}*{pal.reset}")
            else:
                cells.append(f"{pal.open}.{pal.reset}")
        out.append(f"{pal.dim}{r % 10:>3}{pal.reset} " + " ".join(cells))
    return "\n".join(out)


def legend(pal):
    parts = [
        f"{pal.start}S{pal.reset} start",
        f"{pal.target}T{pal.reset} target",
        f"{pal.trail}> v < ^{pal.reset} direction flown",
        f"{pal.repeat}> v < ^{pal.reset} flown more than once",
        f"{pal.trail}o{pal.reset} ended here",
        f"{pal.wall}#{pal.reset} restricted",
        f"{pal.crash}X{pal.reset} crash",
    ]
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
        print(legend(pal))
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
        print(legend(pal))


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
    args = parser.parse_args()

    enable_ansi()
    pal = Palette(color_enabled(args.no_color))

    grid, start, target = load_map(args.map_file)
    solve_fn = load_solver(args.solver_file)
    moves = solve_fn(grid, start, target)
    result = validate_path(grid, start, target, moves)

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
        print(legend(pal))
        print()
        print(f"{pal.bold}Flight log{pal.reset}")
        print(step_log(result["visited"], moves, pal))
        print()

    print(summary(result, target, pal, bad_move, blocked_cell, reason))


if __name__ == "__main__":
    main()
