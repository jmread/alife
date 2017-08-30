#! /usr/bin/env python
import sys
sys.path.append("alife")

map_file = None
if len(sys.argv) > 1:
    map_file = sys.argv[1]

init_sprites = 2
if len(sys.argv) > 2:
    init_sprites = int(sys.argv[2])

from world import *

pygame.init()
world = World(map_file,init_sprites)
