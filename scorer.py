"""
scorer.py
Instructor-side harness: validates a team's path and runs their solver
against a set of maps to produce a leaderboard.

Usage:
    uv run scorer.py teams/team_alpha_solver.py teams/team_bravo_solver.py ...

By default this scores against the practice maps (standard mode only). To
run the real event, score both pools:

    uv run scorer.py teams/*.py \
        --maps "maps/scoring_maps/*.txt" \
        --hard-maps "maps/scoring_maps_hard/*.txt"

Each team file must define solve(grid, start, target) -> list of moves,
matching the interface in starter_solver.py. It MAY also define:

    MODIFIERS = ["terrain", "risk", "waypoints"]   # any subset

Modifiers are opt-in and only ever apply on the hard-maps pool. Each one
raises the score ceiling on a hard map but adds a constraint the team can
fail. See PROJECT_README.md ("Hard mode") for the full rules.
"""

import argparse
import glob
import heapq
import importlib.util
import itertools
import time
from pathlib import Path
from typing import Any

from map_utils import (
    MOVES,
    in_bounds,
    is_open,
    load_map_ex,
    terrain_cost,
    wall_count,
)

TIME_LIMIT_SECONDS = 5.0
DEFAULT_MAPS = "maps/practice_maps/*.txt"
DEFAULT_HARD_MAPS = "maps/scoring_maps_hard/*.txt"

# --- hard-mode tuning knobs -------------------------------------------------
VALID_MODIFIERS = ("terrain", "risk", "waypoints")

# Score multiplier a team earns on a hard map for each modifier it has
# enabled AND satisfied. They stack multiplicatively.
MODIFIER_BONUS = {"terrain": 1.35, "risk": 1.25, "waypoints": 1.5}

# Applied once per modifier whose soft constraint was broken (flew a legal
# route but, e.g., blew the energy budget). Missing a waypoint is not a
# "violation" - it scores the map as 0.
VIOLATION_FACTOR = 0.4

# 'terrain' route may cost up to this * par before it counts as over budget.
ENERGY_BUDGET_SLACK = 1.6

# Flying through a cell that touches this many '#' breaks the risk cap.
RISK_CAP_WALLS = 3
# Scoring cost added per adjacent '#', for every fringe cell flown through.
RISK_PER_ADJACENT_WALL = 2

BASE_POINTS = 100.0
INF = float("inf")


# --- cost model -----------------------------------------------------------
def step_cost(grid, cell, modifiers):
    """Scoring cost to fly INTO `cell`, given the active modifier set."""
    r, c = cell
    cost = terrain_cost(grid[r][c]) if "terrain" in modifiers else 1
    if "risk" in modifiers:
        cost += RISK_PER_ADJACENT_WALL * wall_count(grid, cell)
    return cost


def active_modifiers(grid):
    """Which modifiers are meaningful on this map. A team only earns a
    modifier's bonus where the map actually exercises it."""
    flat = "".join("".join(row) for row in grid)
    active: set[str] = set()
    if any(ch.isdigit() for ch in flat):
        active.add("terrain")
    if "#" in flat:
        active.add("risk")
    if "*" in flat:
        active.add("waypoints")
    return active


# --- path validation ----------------------------------------------------
def validate_path(grid, start, target, moves, modifiers=frozenset(), waypoints=()):
    """
    Simulate a list of moves starting at `start`.

    Returns a dict:
        success:         reached target (all waypoints too, if any were required)
        final_pos:       (row, col) where the drone ended up
        path_length:     number of moves taken (may be < len(moves) on a crash)
        crashed:         hit a wall, edge, or bad move token
        visited:         list of positions visited, including start
        energy:          summed step_cost over entered cells (== path_length
                         when no cost modifiers are active)
        risk_cap_hit:    flew through a cell touching >= RISK_CAP_WALLS walls
        waypoints_total: number of '*' cells that had to be visited
        waypoints_hit:   how many were actually flown over
        waypoints_ok:    all required waypoints were visited
    """
    modifiers = frozenset(modifiers)
    required = set(waypoints)

    pos: tuple[int, int] = start
    visited: list[tuple[int, int]] = [pos]
    crashed = False
    energy = 0
    risk_cap_hit = False
    hit: set[tuple[int, int]] = set()
    if pos in required:
        hit.add(pos)

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
        energy += step_cost(grid, pos, modifiers)
        if wall_count(grid, pos) >= RISK_CAP_WALLS:
            risk_cap_hit = True
        if pos in required:
            hit.add(pos)
        if pos == target and required <= hit:
            break

    waypoints_ok = required <= hit
    result: dict[str, Any] = {
        "success": pos == target and waypoints_ok,
        "final_pos": pos,
        "path_length": len(visited) - 1,
        "crashed": crashed,
        "visited": visited,
        "energy": energy,
        "risk_cap_hit": risk_cap_hit,
        "waypoints_total": len(required),
        "waypoints_hit": len(hit & required),
        "waypoints_ok": waypoints_ok,
    }
    return result


# --- reference (par) solver -------------------------------------------------
def _min_costs(grid, src, modifiers):
    """Dijkstra: least scoring cost from `src` to every reachable cell,
    under `modifiers`. Cells that break the risk cap are excluded when
    'risk' is active, so par is always a legal route."""
    dist: dict[tuple[int, int], int] = {src: 0}
    pq: list[tuple[int, tuple[int, int]]] = [(0, src)]
    risk_on = "risk" in modifiers
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for dr, dc in MOVES.values():
            v = (u[0] + dr, u[1] + dc)
            if not in_bounds(grid, v) or not is_open(grid, v):
                continue
            if risk_on and wall_count(grid, v) >= RISK_CAP_WALLS:
                continue
            nd = d + step_cost(grid, v, modifiers)
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def par_cost(grid, start, target, waypoints, modifiers):
    """Best achievable scoring cost on this map for the given modifier set.

    Without 'waypoints' this is just the cheapest S -> T route. With it,
    brute-force every visiting order of the (<= 4) waypoints.
    """
    if "waypoints" not in modifiers or not waypoints:
        return _min_costs(grid, start, modifiers).get(target, INF)

    sources = [start, *waypoints]
    dmap = {s: _min_costs(grid, s, modifiers) for s in sources}
    best = INF
    for order in itertools.permutations(waypoints):
        total = 0
        prev = start
        legal = True
        for node in (*order, target):
            leg = dmap[prev].get(node, INF)
            if leg == INF:
                legal = False
                break
            total += leg
            prev = node
        if legal:
            best = min(best, total)
    return best


# --- scoring -------------------------------------------------------------
def effective_score(result, par, modifiers, runtime):
    """Raw (un-normalised) score for one team on one map."""
    if not result["success"]:
        return 0.0
    if "waypoints" in modifiers and not result["waypoints_ok"]:
        return 0.0

    uses_energy = bool(modifiers & {"terrain", "risk"})
    your_cost = max(result["energy"] if uses_energy else result["path_length"], 1)

    if par < INF and par > 0:
        quality = min(1.0, par / your_cost)
    else:
        quality = 1.0 if your_cost <= 1 else 1.0 / your_cost

    score = BASE_POINTS * quality
    for m in modifiers:
        score *= MODIFIER_BONUS[m]

    if "terrain" in modifiers and par < INF and your_cost > ENERGY_BUDGET_SLACK * par:
        score *= VIOLATION_FACTOR
    if "risk" in modifiers and result["risk_cap_hit"]:
        score *= VIOLATION_FACTOR

    score *= 1.0 / (1.0 + runtime)
    return score


def _import_module(filepath):
    spec = importlib.util.spec_from_file_location(Path(filepath).stem, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {filepath} as a Python module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_modifiers(module):
    raw = getattr(module, "MODIFIERS", [])
    try:
        mods = [str(m).strip().lower() for m in raw]
    except TypeError as exc:
        raise ValueError("MODIFIERS must be a list/tuple of strings") from exc
    bad = sorted(set(mods) - set(VALID_MODIFIERS))
    if bad:
        raise ValueError(f"unknown modifier(s) {bad}; valid: {list(VALID_MODIFIERS)}")
    return frozenset(mods)


def load_solver(filepath):
    module = _import_module(filepath)
    if not hasattr(module, "solve"):
        raise AttributeError(f"{filepath} does not define solve(grid, start, target)")
    return module.solve


def load_team(filepath):
    """Return (solve_fn, modifiers) for a team file."""
    module = _import_module(filepath)
    if not hasattr(module, "solve"):
        raise AttributeError(f"{filepath} does not define solve(grid, start, target)")
    return module.solve, get_modifiers(module)


def run_solver_on_map(solve_fn, grid, start, target, modifiers, waypoints):
    """Time and validate one solver on one already-loaded map."""
    started = time.time()
    try:
        moves = solve_fn(grid, start, target)
        runtime = time.time() - started
        if runtime > TIME_LIMIT_SECONDS:
            return {"ok": False, "runtime": runtime, "error": "time limit exceeded"}
        result = validate_path(grid, start, target, moves, modifiers, waypoints)
    except Exception as exc:  # catch any team bug, not just expected ones
        return {"ok": False, "runtime": time.time() - started, "error": str(exc)}
    return {"ok": True, "runtime": runtime, "result": result, "error": ""}


def score_round(teams, standard_maps, hard_maps):
    """
    teams: list of (name, solve_fn, modifiers)
    Returns (leaderboard, detail) where leaderboard is a sorted list of
    (name, points, standard_solved, hard_solved) and detail[name][map] is
    a per-map record.
    """
    names = [name for name, _, _ in teams]
    points = {name: 0.0 for name in names}
    detail: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in names}

    jobs = [(p, False) for p in standard_maps] + [(p, True) for p in hard_maps]
    for map_path, is_hard in jobs:
        grid, start, target, waypoints = load_map_ex(map_path)
        map_active = active_modifiers(grid) if is_hard else frozenset()
        par_cache: dict[frozenset[str], float] = {}

        rows = []
        for name, solve_fn, mods in teams:
            eff_mods = frozenset(mods) & map_active
            req_wps = tuple(waypoints) if "waypoints" in eff_mods else ()
            run = run_solver_on_map(solve_fn, grid, start, target, eff_mods, req_wps)
            if run["ok"]:
                if eff_mods not in par_cache:
                    par_cache[eff_mods] = par_cost(
                        grid, start, target, waypoints, eff_mods
                    )
                par = par_cache[eff_mods]
                eff = effective_score(run["result"], par, eff_mods, run["runtime"])
            else:
                par = INF
                eff = 0.0
            rows.append((name, eff, par, eff_mods, run))

        best = max((eff for _, eff, _, _, _ in rows), default=0.0)
        for name, eff, par, eff_mods, run in rows:
            pts = eff / best if best > 0 else 0.0
            points[name] += pts
            res = run.get("result", {})
            detail[name][map_path] = {
                "hard": is_hard,
                "points": pts,
                "effective": eff,
                "par": par,
                "modifiers": sorted(eff_mods),
                "runtime": run["runtime"],
                "error": run["error"],
                "success": bool(res.get("success")),
                "path_length": res.get("path_length"),
                "energy": res.get("energy"),
                "waypoints_total": res.get("waypoints_total", 0),
                "waypoints_hit": res.get("waypoints_hit", 0),
                "risk_cap_hit": bool(res.get("risk_cap_hit")),
            }

    leaderboard = []
    for name in names:
        recs = detail[name].values()
        std_solved = sum(1 for r in recs if not r["hard"] and r["success"])
        hard_solved = sum(1 for r in recs if r["hard"] and r["success"])
        leaderboard.append((name, points[name], std_solved, hard_solved))
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    return leaderboard, detail


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
        help=f"Glob for the standard-mode map pool (default: {DEFAULT_MAPS})",
    )
    parser.add_argument(
        "--hard-maps",
        nargs="?",
        const=DEFAULT_HARD_MAPS,
        default=None,
        help=(
            "Also score a hard-mode pool where each team's MODIFIERS apply. "
            f"Bare flag uses {DEFAULT_HARD_MAPS}"
        ),
    )
    args = parser.parse_args()

    standard_maps = sorted(glob.glob(args.maps))
    hard_maps = sorted(glob.glob(args.hard_maps)) if args.hard_maps else []
    if not standard_maps and not hard_maps:
        print(f"No maps found matching {args.maps!r} or {args.hard_maps!r}")
        return

    teams = []
    load_errors = []
    for solver_file in args.solver_files:
        team_name = Path(solver_file).stem
        try:
            solve_fn, mods = load_team(solver_file)
        except Exception as exc:
            print(f"[{team_name}] failed to load: {exc}")
            load_errors.append(team_name)
            continue
        teams.append((team_name, solve_fn, mods))

    if not teams:
        print("No loadable solvers.")
        return

    mods_by_team = {name: mods for name, _, mods in teams}
    leaderboard, detail = score_round(teams, standard_maps, hard_maps)

    n_std, n_hard = len(standard_maps), len(hard_maps)
    print("\n=== LEADERBOARD ===")
    for rank, (name, pts, std_solved, hard_solved) in enumerate(leaderboard, 1):
        mods = mods_by_team.get(name)
        mod_str = ",".join(sorted(mods)) if mods else "-"
        line = f"{rank}. {name:20s} points={pts:7.2f}  standard {std_solved}/{n_std}"
        if n_hard:
            line += f"  hard {hard_solved}/{n_hard}"
        line += f"  mods: {mod_str}"
        print(line)
    for name in load_errors:
        print(f"-. {name:20s} points=   DNF  (failed to load)")

    print("\n=== DETAIL ===")
    for name, _pts, _s, _h in leaderboard:
        print(f"\n{name}:")
        for map_path, r in detail[name].items():
            tag = "HARD" if r["hard"] else "std "
            status = "OK  " if r["success"] else "FAIL"
            flags = []
            if r["error"]:
                flags.append(r["error"])
            if r["waypoints_total"]:
                flags.append(f"wp {r['waypoints_hit']}/{r['waypoints_total']}")
            if r["risk_cap_hit"] and "risk" in r["modifiers"]:
                flags.append("RISK-CAP")
            par = r["par"]
            par_str = f"{par:.0f}" if par not in (INF, None) else "-"
            print(
                f"  [{tag}] {Path(map_path).name:22s} [{status}] "
                f"len={r['path_length']!s:>3} energy={r['energy']!s:>4} "
                f"par={par_str:>4} eff={r['effective']:7.2f} "
                f"pts={r['points']:.3f} t={r['runtime']:.3f}s " + " ".join(flags)
            )


if __name__ == "__main__":
    main()
