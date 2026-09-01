"""
gen_maps.py
Generates airspace maps for the Drone Pathfinder Challenge.

Every generated map is verified with BFS at generation time, so it always
has at least one valid path from S to T.

Generate an extra practice map to test your solver against:
    uv run gen_maps.py --out maps/practice_maps/my_map.txt --seed 42
    uv run gen_maps.py --out maps/practice_maps/big.txt --height 30 --width 30

Regenerate the stock practice map:
    uv run gen_maps.py

The scoring maps are deliberately NOT generated here - their parameters
live in the instructor-only tooling so they cannot be reproduced from
this file.
"""

import argparse
import random
from collections import deque
from pathlib import Path

# (height, width, wall_probability, seed) for the stock practice map.
PRACTICE_MAP = ("maps/practice_maps/practice_map.txt", 10, 10, 0.22, 1)


def bfs_reachable(grid, start):
    h, w = len(grid), len(grid[0])
    seen = {start}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in seen
                and grid[nr][nc] != "#"
            ):
                seen.add((nr, nc))
                q.append((nr, nc))
    return seen


def gen_map(h, w, wall_prob, seed):
    """Generate an h x w map with a guaranteed S -> T path."""
    rng = random.Random(seed)
    while True:
        grid = [
            ["#" if rng.random() < wall_prob else "." for _ in range(w)]
            for _ in range(h)
        ]
        start = (0, 0)
        target = (h - 1, w - 1)
        grid[start[0]][start[1]] = "."
        grid[target[0]][target[1]] = "."
        if target in bfs_reachable(grid, start):
            grid[start[0]][start[1]] = "S"
            grid[target[0]][target[1]] = "T"


            return ["".join(row) for row in grid]
    


def write_map(path, rows):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    # newline="" keeps LF on Windows too; the repo's pre-commit hooks enforce LF.
    with out.open("w", newline="") as f:
        _ = f.write("\n".join(rows) + "\n")
    print(f"wrote {out} ({len(rows)}x{len(rows[0])})")


def main():
    parser = argparse.ArgumentParser(description="Generate airspace maps.")
    parser.add_argument(
        "--out", help="Write a single map here instead of the standard set"
    )
    parser.add_argument("--height", type=int, default=12)
    parser.add_argument("--width", type=int, default=12)
    parser.add_argument(
        "--wall-prob", type=float, default=0.25, help="Fraction of '#' cells"
    )
    parser.add_argument("--seed", type=int, default=0, help="Same seed = same map")
    args = parser.parse_args()

    if args.out:
        rows = gen_map(args.height, args.width, args.wall_prob, args.seed)
        write_map(args.out, rows)
        print()
        print("\n".join(rows))
        return

    path, h, w, wall_prob, seed = PRACTICE_MAP
    write_map(path, gen_map(h, w, wall_prob, seed))


if __name__ == "__main__":
    main()
