import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT_DIR, 'img')
MAP_DIR = os.environ.get('ALIFE_MAP_DIR', os.path.join(ROOT_DIR, 'maps'))

# Frames Per Second (in human rendering mode)
FPS = 10

# Default map generation dimensions (must be even and >= 4)
MAP_ROWS = 12
MAP_COLS = 10
DEFAULT_MAP_NAME = "new_map"
