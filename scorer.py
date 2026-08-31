"""
scorer.py
Instructor-side harness: validates a team's path and runs their
solver against a set of maps to produce a leaderboard.

Usage:
    uv run scorer.py teams/team_alpha_solver.py teams/team_bravo_solver.py ...

By default this scores against the practice maps. To score against the
maps that decide the leaderboard:

    uv run scorer.py teams/*.py --maps "maps/scoring_maps/*.txt"

Each team file must define solve(grid, start, target) -> list of moves,
matching the interface in starter_solver.py.
"""

import argparse
import glob
import importlib.util
import time
from pathlib import Path
from typing import Any

from map_utils import MOVES, in_bounds, is_open, load_map

TIME_LIMIT_SECONDS = 5.0
DEFAULT_MAPS = "maps/practice_maps/*.txt"


def validate_path(grid, start, target, moves):
    """
    Simulate a list of moves starting at `start`.
    Returns a dict:
        success: bool (reached target without hitting an obstacle/wall)
        final_pos: (row, col)
        path_length: number of moves taken (may be less than len(moves)
                     if the drone crashed early)
        crashed: bool
        visited: list of positions visited, including start
    """
    pos: tuple[int, int] = start
    visited: list[tuple[int, int]] = [pos]
    crashed = False

    for move in moves:
        if move not in MOVES:
            crashed = True
            break
        dr, dc = MOVES[move]
        new_pos = (pos[0] + dr, pos[1] + dc)
        if not in_bounds(grid, new_pos) or not is_open(grid, new_pos):
            crashed = True
            break
        pos = new_pos
        visited.append(pos)
        if pos == target:
            break

    result: dict[str, Any] = {
        "success": pos == target,
        "final_pos": pos,
        "path_length": len(visited) - 1,
        "crashed": crashed,
        "visited": visited,
    }
    return result


def load_solver(filepath):
    spec = importlib.util.spec_from_file_location(Path(filepath).stem, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {filepath} as a Python module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "solve"):
        raise AttributeError(f"{filepath} does not define solve(grid, start, target)")
    return module.solve


def run_solver_on_map(solve_fn, map_path) -> dict[str, Any]:
    grid, start, target = load_map(map_path)

    start_time = time.time()
    try:
        moves = solve_fn(grid, start, target)
        runtime = time.time() - start_time
        if runtime > TIME_LIMIT_SECONDS:
            return {
                "success": False,
                "error": "time limit exceeded",
                "runtime": runtime,
            }
        result = validate_path(grid, start, target, moves)
    except Exception as exc:  # we want to catch any team bug, not just expected ones
        return {
            "success": False,
            "error": str(exc),
            "runtime": time.time() - start_time,
        }

    result["runtime"] = runtime
    return result


def score_team(solve_fn, map_paths):
    """
    Returns per-map results and a simple composite score:
    +100 per map solved, minus path_length, minus runtime*10.
    Lower path_length / runtime is better; tweak freely for your event.
    """
    results: dict[str, dict[str, Any]] = {}
    total_score = 0
    for map_path in map_paths:
        res = run_solver_on_map(solve_fn, map_path)
        results[map_path] = res
        if res.get("success"):
            path_length: int = res["path_length"]
            runtime: float = res["runtime"]
            total_score += 100 - path_length - int(runtime * 10)
    return total_score, results


def main():
    parser = argparse.ArgumentParser(
        description="Score team solvers against the map set."
    )
    parser.add_argument(
        "solver_files", nargs="+", help="Path(s) to team solver .py files"
    )
    parser.add_argument(
        "--maps",
        default=DEFAULT_MAPS,
        help=f"Glob pattern for maps to score against (default: {DEFAULT_MAPS})",
    )
    args = parser.parse_args()

    map_paths = sorted(glob.glob(args.maps))
    if not map_paths:
        print(f"No maps found matching {args.maps}")
        return

    leaderboard = []
    for solver_file in args.solver_files:
        team_name = Path(solver_file).stem
        try:
            solve_fn = load_solver(solver_file)
            score, results = score_team(solve_fn, map_paths)
        except Exception as exc:
            print(f"[{team_name}] failed to load: {exc}")
            leaderboard.append((team_name, -9999, {}))
            continue
        leaderboard.append((team_name, score, results))

    leaderboard.sort(key=lambda x: x[1], reverse=True)

    print("\n=== LEADERBOARD ===")
    for rank, (team_name, score, results) in enumerate(leaderboard, start=1):
        solved = sum(1 for r in results.values() if r.get("success"))
        print(
            f"{rank}. {team_name:20s} score={score:6d}  solved {solved}/{len(map_paths)} maps"
        )

    print("\n=== DETAIL ===")
    for team_name, score, results in leaderboard:
        print(f"\n{team_name}:")
        for map_path, res in results.items():
            status = "OK" if res.get("success") else "FAIL"
            extra = res.get("error", "")
            print(
                f"  {Path(map_path).name:20s} [{status}] "
                f"path_len={res.get('path_length', '-')} "
                f"runtime={res.get('runtime', 0):.3f}s {extra}"
            )


if __name__ == "__main__":
    main()
