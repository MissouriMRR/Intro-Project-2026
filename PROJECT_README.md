# Drone Pathfinder Challenge

An intro Python project for the Multirotor Design Team software group.
Teams write a solver that pilots a simulated drone through a grid of
restricted airspace from a start point to a landing target. Solvers
are scored automatically and ranked on a leaderboard — no live
matchup needed.

## The idea

- You get a grid map: `.` open airspace, `#` restricted airspace,
  `S` start, `T` target/landing pad. Hard-mode maps also use digits
  `1`–`9` (weighted airspace) and `*` (a mandatory waypoint) — a
  standard solver can treat both as plain open airspace.
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

See your actual flight path drawn on the map — arrows show which way the
drone flew out of each cell, magenta marks cells it flew over more than
once, and `X` marks a crash:

```bash
uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt
```

Or watch the flight replay one move at a time:

```bash
uv run visualize.py starter_solver.py maps/practice_maps/practice_map.txt --animate
```

Add `--delay 0.5` to slow the replay down, or `--no-color` for plain output.

## Files

| File                                  | Purpose                                                                                                                                                       |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `starter_solver.py`                   | **Start here.** Contains the interface + a placeholder that intentionally fails, so you can confirm the harness runs before writing real logic                |
| `starter_hard_solver.py`              | Same placeholder, but shows how to enter the hard pool with `MODE` + `MODIFIERS` and how to find the `*` waypoints. Copy it if you want to compete in hard mode |
| `map_utils.py`                        | Loads map files, shared move constants                                                                                                                        |
| `scorer.py`                           | Runs one or more solvers against a set of maps and prints a leaderboard                                                                                       |
| `visualize.py`                        | Draws the route your solver flew (direction arrows, revisits, crash point) with an optional step-by-step replay                                               |
| `gen_maps.py`                         | Generates maps (standard or `--mode hard`) with a guaranteed valid path — use it to make extra practice maps                                                  |
| `maps/practice_maps/practice_map.txt` | Use this map for testing as you develop your algorithm                                                                                                        |
| `maps/practice_maps/hard/`            | Hard-mode practice maps (weighted airspace + waypoints); not scored by the default practice glob                                                              |

The scoring maps live in `maps/scoring_maps/` (five easy) and
`maps/scoring_maps_hard/` (five hard) and are revealed only at scoring
time — this is what actually determines the leaderboard. Your solver is
run against the five maps in its pool, none of which you have seen, so
hardcoding a path for the practice map will not work.

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

### Two pools, one of them yours

There are **two map pools**, five maps each, and your solver competes in
exactly one of them:

| Pool     | Maps                       | Worth per map                              |
| -------- | -------------------------- | ------------------------------------------ |
| **easy** | 5 standard maps            | up to **1.00** point → 5.00 max            |
| **hard** | 5 hard maps                | up to **1.00 × your modifier bonuses** → 12.66 max with all three |

An easy solver is never run on the hard maps, and a hard solver is never
run on the standard maps. You cannot farm points from both. Declare your
pool with a module-level `MODE`:

```python
MODE = "easy"   # or "hard"
```

If you leave `MODE` out, the scorer infers it: any `MODIFIERS` at all
means hard, none means easy.

### The per-map score

Scoring is **absolute**, not a curve against the rest of the field — your
score does not depend on who else entered. On each map:

```
raw    = 100 * (optimal_cost / your_cost) / (1 + runtime_seconds)
points = raw / 100 * (your modifier bonuses, hard pool only)
```

`optimal_cost` is the cost of the best route the scorer can find;
`your_cost` is your path length (see hard mode for how cost changes
there). Because the scorer's route is optimal, `optimal_cost / your_cost`
is always between 0 and 1: `1.0` means you matched the best route, `0.5`
means yours cost twice as much. Reaching the target on the shortest path
with a fast solver gives ~1.00 point; not reaching it gives 0. Points are
summed across your pool's five maps.

There's a 5-second time limit per map (`TIME_LIMIT_SECONDS` in
`scorer.py`). A plain BFS shortest-path solver maxes out the easy pool at
5.00 — to score higher than that you have to enter hard mode.

## Hard mode

The easy pool has one right answer (shortest path), so a correct solver
tops out at 5.00 and the leaderboard bunches up. Hard mode is a different
pool of maps with extra structure, and a much higher ceiling for teams
willing to take on the extra rules.

Enter it by declaring `MODE` and a `MODIFIERS` list in your solver file:

```python
MODE      = "hard"
MODIFIERS = ["terrain", "risk", "waypoints"]  # any subset
```

Each modifier you enable multiplies what a hard map is worth to you, and
they stack — but each one also adds a constraint you can fail. Hard maps
use two extra characters: digits `1`–`9` (weighted airspace) and `*`
(a mandatory waypoint).

On a hard map a plain `.` is just weighted airspace of cost `1` — it and a
`1` cell are identical to fly into. `S`, `T`, and `*` also cost `1` to
enter. Only digits `2`–`9` cost more.

| Modifier    | What changes                                                                                        | Bonus | Fail condition & cost                                                                                   |
| ----------- | --------------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------- |
| `terrain`   | Flying into a digit cell costs that many energy units (not 1). Your cost is measured in **energy**. | ×1.35 | Energy over `1.6 × optimal` → score ×0.4                                                                |
| `risk`      | Keep clear of tight spots wedged between obstacles.                                                 | ×1.25 | Flying through a cell with ≥2 `#` directly N/S/E/W of it (diagonals and walls don't count) → score ×0.4 |
| `waypoints` | The drone must fly over every `*` before landing on `T`. Visiting order is yours to choose.         | ×1.50 | Miss any `*` → **0 for that map**                                                                       |

So a team that enables all three and flies a near-optimal waypoint tour
within budget earns about `1.00 × 1.35 × 1.25 × 1.5 ≈ 2.53` points on a
hard map — **12.66** across the pool, against the easy pool's 5.00 ceiling.
Enter hard mode with no modifiers and each map still caps at 1.00, so you
gain nothing by showing up: the bonuses *are* the reason to be there.

The flip side is that one missed waypoint zeros a map outright, and a
blown energy budget or a tripped risk cap costs you ×0.4 — so a team that
claims all three and stumbles can finish below a disciplined easy team.
Claim only the modifiers you actually handle.

The `risk` cap only ever bites a solver that steers into a wedge on its
own. Every hard map is generated so that a route respecting the cap
reaches every `*` and `T` — you are never forced through a one-wide gap
between two obstacles — and the scorer's reference route treats a
`≥2`-wall cell as impassable, so `optimal` is always a clean path.

A modifier only pays out on a map that actually exercises it — you earn
the `waypoints` bonus only where there are `*` cells to visit.

Copy `starter_hard_solver.py` as your starting point - it already has the
`MODE` and `MODIFIERS` lines and shows how to pull the `*` waypoints out
of the grid.

Practice against a hard map you generate yourself, then score with
`--hard-maps`:

```bash
uv run gen_maps.py --mode hard --out maps/practice_maps/hard/h1.txt --seed 7
uv run scorer.py my_solver.py --hard-maps "maps/practice_maps/hard/*.txt"
```

At the competition:

```bash
uv run scorer.py teams/*.py \
    --maps "maps/scoring_maps/*.txt" \
    --hard-maps "maps/scoring_maps_hard/*.txt"
```

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

For hard-mode practice maps, add `--mode hard` (and optionally
`--waypoints N`, 1–4). Use `--count N` with a directory `--out` to make a
whole numbered pool at once:

```bash
uv run gen_maps.py --mode hard --out maps/practice_maps/hard/h1.txt --seed 7
uv run gen_maps.py --mode hard --out maps/practice_maps/hard --count 5 --seed 200
```

Every generated map is verified to have at least one valid path, so you
can never get stuck on an unsolvable map. Hard maps are checked further:
every waypoint sits on clean ground and a route that respects the risk cap
reaches every waypoint and `T` without ever squeezing through a one-wide
gap between two obstacles. Running `uv run gen_maps.py` with no arguments
rewrites the stock practice map in place.
