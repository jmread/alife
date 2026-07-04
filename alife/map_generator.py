#! /usr/bin/env python3

import numpy as np

'''
    A simple tile-based random-map generator. 
    -----------------------------------------

    1. generate a bitmap with perlin noise
    2. match the bitmap to tiles
    3. save the tilemap

NOTES:  
    0 is water (so, [00;00] is all water)
              (so, [10;00] is top-left land)
              (so, [01;11] is top-left water)
    1 is land (so, [11;11] is all land)
'''

from .graphics import draw_map
from .map_tools import pad
from pathlib import Path
import sys

N_rows = 6
N_cols = 6

def print_usage():
    """Print clean usage information"""
    print("""Usage: python3 map_generator.py <mapname> <height> <width>
Example:
  python3 map_generator.py forest 20 30""")

# Validate command line arguments
if len(sys.argv) < 4:
    print_usage()
    sys.exit(1)

# Parse arguments with clear variable names
map_name = sys.argv[1]
N_rows = int(sys.argv[2])
N_cols = int(sys.argv[3])
filename = f"{map_name}.map"
assert N_rows % 2 == 0, f"{N_rows} is not an even number"
assert N_cols % 2 == 0, f"{N_cols} is not an even number"
assert(N_rows >= 4)
assert(N_cols >= 4)

# Your map generation code would continue here...
print(f"Creating {N_rows}x{N_cols} map: {filename}")

filename = map_name+'.map'

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

# Generate bit map
B = generate_island(N_rows - 2, N_cols - 2, iterations=1)
print("======== * B * =========")
# Make a sea border
B = pad(B, 0)
# Save the file
print(B)
np.savetxt(Path(__file__).parent / "maps" / filename, B, fmt="%d", delimiter="")

# Draw it
final_map, _ = draw_map(B)
final_map.show() 
