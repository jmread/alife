#! /usr/bin/env python3
"""
    A simple tile-based random-map generator.
    -----------------------------------------

    1. generate a bitmap
    2. match the bitmap to tiles
    3. save the tilemap

NOTES:
    0 is water (so, [00;00] is all water)
              (so, [10;00] is top-left land)
              (so, [01;11] is top-left water)
    1 is land (so, [11;11] is all land)
"""

import sys
from pathlib import Path

import numpy as np

from .config import MAP_DIR
from .graphics import draw_map
from .map_tools import pad


def generate_island(n_rows, n_cols, land_prob=0.65, iterations=5):
    # Initialize random binary matrix
    grid = np.random.choice([0, 1], n_rows*n_cols, p=[1-land_prob, land_prob]).reshape(n_rows, n_cols)

    for _ in range(iterations):
        new_grid = grid.copy()
        for i in range(n_rows):
            for j in range(n_cols):
                # Count land neighbors (including diagonals)
                neighbors = grid[max(0, i-1):min(n_rows, i+2), max(0, j-1):min(n_cols, j+2)]
                land_count = np.sum(neighbors) - grid[i, j]
                # Apply rules
                if land_count > 4:
                    new_grid[i, j] = 1
                else:
                    new_grid[i, j] = 0
        grid = new_grid

    return grid


def generate_terrain(n_rows, n_cols):
    """Generate an island bitmap padded with a sea border; shape is (n_rows, n_cols)."""
    B = generate_island(n_rows - 2, n_cols - 2, iterations=1)
    B = pad(B, 0)
    return B


def generate_map(map_name, n_rows, n_cols, show=False):
    """Generate a random map and save it to MAP_DIR/<map_name>.map. Returns the path."""
    assert n_rows % 2 == 0, f"{n_rows} is not an even number"
    assert n_cols % 2 == 0, f"{n_cols} is not an even number"
    assert n_rows >= 4
    assert n_cols >= 4

    B = generate_terrain(n_rows, n_cols)
    path = Path(MAP_DIR) / f"{map_name}.map"
    np.savetxt(path, B, fmt="%d", delimiter="")

    print(f"Creating {n_rows}x{n_cols} map: {path}")
    print(B)

    if show:
        final_map, _ = draw_map(B)
        final_map.show()
    return path


def print_usage():
    """Print clean usage information"""
    print("""Usage: python3 map_generator.py <mapname> <height> <width>
Example:
  python3 map_generator.py forest 20 30""")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)
    map_name = sys.argv[1]
    n_rows = int(sys.argv[2])
    n_cols = int(sys.argv[3])
    generate_map(map_name, n_rows, n_cols, show=True)
