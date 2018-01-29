#! /usr/bin/env python
import sys
sys.path.append("alife")

map_file = "dat/maps/map_islands2.dat"
if len(sys.argv) > 1:
    map_file = sys.argv[1]

init_sprites = 0
if len(sys.argv) > 2:
    init_sprites = int(sys.argv[2])

from world import *

pygame.init()
world = World(map_file,init_sprites)
