# Drone Pathfinder Challenge

An intro Python project for the Multirotor Design Team software group.
Teams write a solver that pilots a simulated drone through a grid of
restricted airspace from a start point to a landing target. Solvers
are scored automatically and ranked on a leaderboard — no live
matchup needed.

## The idea

- You get a grid map: `.` open airspace, `#` restricted airspace,
  `S` start, `T` target/landing pad.
- Write `solve(grid, start, target)` that returns a list of moves
  (`"N"`, `"S"`, `"E"`, `"W"`) that flies the drone from `S` to `T`
  without ever crossing a `#`.
- Your solver is run against maps you haven't seen before, so
  hardcoding a path for the practice map won't work.

## Getting started

Set up the environment (see the main [README](README.md) for installing
`uv` and Python 3.12):

```bash
uv sync --dev
```

Confirm the harness runs. This runs the placeholder solver against the
practice map — it is _supposed_ to fail, but it should fail cleanly, not
crash:

```bash
uv run starter_solver.py
```

Score yourself against the practice map at any time:

```bash
uv run scorer.py starter_solver.py
```

See your actual flight path drawn on the map:

```bash
uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt
```

## Files

| File                                  | Purpose                                                                                                                                        |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `starter_solver.py`                   | **Start here.** Contains the interface + a placeholder that intentionally fails, so you can confirm the harness runs before writing real logic |
| `map_utils.py`                        | Loads map files, shared move constants                                                                                                         |
| `scorer.py`                           | Runs one or more solvers against a set of maps and prints a leaderboard                                                                        |
| `visualize.py`                        | Prints an ASCII rendering of a solved path — good for debugging, and for the projector during the demo                                         |
| `gen_maps.py`                         | Generates maps with a guaranteed valid path — use it to make extra practice maps                                                               |
| `maps/practice_maps/practice_map.txt` | Use this map for testing as you develop your algorithm                                                                                         |

The scoring maps live in `maps/scoring_maps/` and are revealed only at
scoring time — this is what actually determines the leaderboard. Your
solver is run against maps you have not seen, so hardcoding a path for
the practice map will not work.

All maps are auto-generated with a guaranteed valid path
(verified via BFS at generation time), so nobody can get stuck on an
unsolvable map.

## Interface contract

```python
def solve(grid, start, target):
    """
    grid: list of lists of characters ('.', '#', 'S', 'T')
    start: (row, col)
    target: (row, col)
    returns: list of moves, e.g. ["E", "E", "S", "N", "E"]
    """
```

Moves: `N` = row-1, `S` = row+1, `E` = col+1, `W` = col-1. No diagonals.

## Scoring

Run:

```bash
uv run scorer.py <solver_team_1.py> <solver_team_2.py>
```

Default scoring per map: `+100` if the drone reaches the target, minus
path length, minus `runtime * 10`.
Completed Map Scoring: 100 - path_length - (runtime_seconds \* 10)
There's a 5-second time limit per map (`TIME_LIMIT_SECONDS` in
`scorer.py`).

## 3 Meeting Plan

**Meeting 1 8/31 — Understand problem and start designing solution**

- Walk through the map format and the `solve()` interface together
- Create a copy of the repo with your team and make sure everyone can run starter_solver.py
- Understand the problem and draft out possible algoirthms to solve it.
- If time begin trying to implement different algorithms.

**Meeting 2 9/3 — Optimize and Compare!**

- Teams refine for shorter path / faster runtime
- If you want, compare your solution to other teams with scorer.py

**Meeting 3 9/10 - Compete!**

- We'll be competing at the start of this meeting to see which team wins!
- I'll bring in Cookies for the winning team.
- After that we're starting on actual projects

## Regenerating maps

`gen_maps.py` generated the practice map. To make extra practice maps to
test against, give it an output path and a seed:

```bash
uv run gen_maps.py --out maps/practice_maps/my_map.txt --seed 42
uv run gen_maps.py --out maps/practice_maps/big.txt --height 30 --width 30 --wall-prob 0.3
```

Every generated map is BFS-verified to have at least one valid path, so
you can never get stuck on an unsolvable map. Running `uv run gen_maps.py`
with no arguments rewrites the stock practice map in place.
