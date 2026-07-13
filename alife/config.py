import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT_DIR, 'img')
MAP_DIR = os.path.join(ROOT_DIR, 'maps')

FPS = 10
MAX_GRID_DETECTION = 100     # maximum number of objects that can be detected at once

# Default map generation dimensions (must be even and >= 4)
MAP_ROWS = 12
MAP_COLS = 10
DEFAULT_MAP_NAME = "new_map"
