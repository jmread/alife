#! /usr/bin/env python3

import sys
import time
import warnings

# Numpy
import numpy as np
np.set_printoptions(threshold=np.inf, precision=1)

# Pygame
import pygame

from .graphics import N_array, COLOR_WHITE, get_label
from .graphics import build_image_bank, build_bg_png as build_map, build_image_png, ID_ROCK, ID_PLANT, ID_ANIMAL, ID_FLAG
from .constants import IDX_id, IDX_x, IDX_y, IDX_pos, IDX_rad, IDX_img, IDX_sid
from .config import MAP_DIR, DEFAULT_MAP_NAME
from .map_generator import generate_map
from pathlib import Path

GRID_SIZE = 64              # tile size (width and height, in pixels)

MAP_ROWS = 12               # number of tiles N.B. must be even and > 4
MAP_COLS = 8                # number of tiles N.B. must be even and > 4

HELP_LINES = [
    "h         Toggle this help",
    "Click     Select object",
    "r         Add rock",
    "p         Add plant",
    "d         Add decor (aesthetics)",
    "f         Add nest (spawnpoint) or flag (waypoint)",
    "m         Move selected to cursor",
    "DEL       Delete selected",
    "UP/DOWN   Resize selected",
    "LEFT/RIGHT  Change image",
    "+ / -     Reorder z-index",
    "1-8, 0    Set flag label",
    "f         Clear flag label",
    "s         Save to file",
    "g         Re-roll terrain (empty maps only)",
    "Shift+UP/DOWN   Grow/shrink rows x2 (empty maps)",
    "Shift+LEFT/RIGHT Grow/shrink cols x2 (empty maps)",
]

def pos2grid(p, TILE_SIZE=64):
    ''' Convert (x,y)-point to (j,k)-grid reference ''' 
    x, y = p #np.clip(p,[0,0],self.terrain.shape * TILE_SIZE)
    j = y // TILE_SIZE
    k = x // TILE_SIZE
    return (j, k)

def is_point_in_circle(p, c, r):
    # Calculate the squared distance between point p and center c
    distance_squared = np.sum((np.array(p) - np.array(c))**2)
    # Check if the squared distance is less than or equal to r squared
    return distance_squared <= r**2

def get_object(sprites, p): 
    for i,sprite in enumerate(sprites): 
        if is_point_in_circle(p, sprite[IDX_pos],IDX_rad * 2):
            print("SELECTED", sprite)
            return i, sprite
    return -1, None

def strip_map_ext(name):
    """Strip a known map-file extension (.map/.csv/.dat/.png) if present."""
    for ext in ('.map', '.csv', '.dat', '.png'):
        if name.endswith(ext):
            return name[:-len(ext)]
    return name

def map_name_taken(name):
    """Return True if name.map or name.csv already exists in MAP_DIR."""
    d = Path(MAP_DIR)
    return (d / (name + '.map')).exists() or (d / (name + '.csv')).exists()

def editor_interface(world_info):

    '''
        Map Editor Interface
        --------------------

    '''

    # Extract info
    bname_map = world_info['basename']
    fname_sprites = str(Path(MAP_DIR) / (bname_map+'.csv'))
    fname_map = str(Path(MAP_DIR) / (bname_map+'.map'))
    fname_png = str(Path(MAP_DIR) / (bname_map+'.png'))

    # Build the map (based on world_name)
    print('[Map-Editor] Got world info: (map: %s).' % (fname_map))
    try:
        B = np.genfromtxt(fname_map, dtype=int, delimiter=1, filling_values=0)
    except Exception as e:
        print("[Map-Editor] That map ('%s') did not exist, so we're going to generate one." % (fname_map))
        B = generate_map(MAP_ROWS, MAP_COLS)
    WIDTH = (B.shape[1]-1) * GRID_SIZE * 2
    HEIGHT = (B.shape[0]-1) * GRID_SIZE * 2
    background, terrain = build_map(B,grid_lines=True)
    grid_rows, grid_cols = B.shape

    # Open the sreen
    pygame.font.init()
    help_font = pygame.font.SysFont("monospace", 28)
    hint_font = pygame.font.SysFont("monospace", 18)
    pygame.display.set_caption("Map Editor [map: %s.map]" % bname_map)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))#, HWSURFACE|DOUBLEBUF)
    pygame.mouse.set_visible(1)

    # Draw the background on the screen
    screen.blit(background, [0, 0])
    pygame.display.flip()

    #image = build_image_png([0,0],int(sprites[i,IDX_rad]),int(sprites[i,IDX_id]),int(sprites[i,IDX_img]))[1]
    sprites = np.empty((0, 6), dtype=int)  

    try:
        print("[World] Load Sprites ..")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            loaded = np.loadtxt(fname_sprites,delimiter=',',dtype=int)
        if loaded.size == 0:
            print("[World] No sprites in file; starting with an empty map.")
        else:
            sprites = np.atleast_2d(loaded)
            # Check for correct number of columns
            if sprites.shape[1] == 5:
                # Add a sixth column of -1
                sprites = np.hstack([sprites, -1 * np.ones((sprites.shape[0], 1), dtype=int)])
                # For rows where the first column is -1, set first column to 0 and sixth column to 3
                mask = sprites[:, 0] == -1
                sprites[mask, 5] = 3
            elif sprites.shape[1] != 6:
                raise ValueError("Input file must have 5 or 6 columns")
    except Exception as e:
        print("[World] Error: ", type(e).__name__, e)
        #print("      > No sprite file found; creating a default flag sprite...")
        #sprites = np.array([ID_FLAG, GRID_SIZE*2, GRID_SIZE*2, 15, 0, -1]).reshape(1,-1)

    show_help = False

    selected_sprite = None
    i_sel = -1

    n = len(sprites)
    images = [None for _ in range(100)]

    for i, sprite in enumerate(sprites): 
        images[i] = build_image_png(sprite[IDX_pos],sprite[IDX_rad],sprite[IDX_id],sprite[IDX_img])[1]
        screen.blit(images[i], sprite[IDX_pos] - sprite[IDX_rad])

    pygame.display.flip()

    clock = pygame.time.Clock()
    running = True
    while running:

        clock.tick(24)
        screen.blit(background, [0,0]) 

        for i, sprite in enumerate(sprites): 
            screen.blit(images[i], sprite[IDX_pos] - sprite[IDX_rad])
            if sprite[IDX_sid] >= 0:
                name_label = get_label("%d" % int(sprite[IDX_sid]))
                screen.blit(name_label, sprite[IDX_pos] - sprite[IDX_rad])

        for event in pygame.event.get():
            # quit
            if event.type == pygame.QUIT:
                running = False
            # select an object
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s: 
                    print(sprites)
                    np.savetxt(fname_sprites, sprites, delimiter=',',fmt='%d')
                    np.savetxt(fname_map, B, fmt="%d", delimiter="")
                    pygame.image.save(background, fname_png)
                    print("[Map-Editor] Saved %s, %s, %s" % (fname_map, fname_sprites, fname_png))
                if event.key == pygame.K_h:
                    show_help = not show_help
                if event.key == pygame.K_r: 
                    # Rock
                    pos = pygame.mouse.get_pos()
                    sprite = np.array([ID_ROCK, pos[0], pos[1], 20, int(np.random.choice(N_array[ID_ROCK])), -1])
                    sprites = np.vstack([sprites, sprite])
                    images[len(sprites)-1] = build_image_png(sprite[IDX_pos],sprite[IDX_rad],sprite[IDX_id],sprite[IDX_img])[1]
                if event.key == pygame.K_p: 
                    # Plant
                    pos = pygame.mouse.get_pos()
                    sprite = np.array([ID_PLANT, pos[0], pos[1], 20, int(np.random.choice(N_array[ID_PLANT])), -1])
                    sprites = np.vstack([sprites, sprite])
                    images[len(sprites)-1] = build_image_png(sprite[IDX_pos],sprite[IDX_rad],sprite[IDX_id],sprite[IDX_img])[1]
                if event.key == pygame.K_f: 
                    # Nest/flag
                    pos = pygame.mouse.get_pos()
                    sprite = np.array([ID_FLAG, pos[0], pos[1], 20, int(np.random.choice(6)), -1])
                    sprites = np.vstack([sprites, sprite])
                    images[len(sprites)-1] = build_image_png(sprite[IDX_pos],sprite[IDX_rad],sprite[IDX_id],sprite[IDX_img])[1]
                if event.key == pygame.K_d: 
                    # Decor
                    pos = pygame.mouse.get_pos()
                    sprite = np.array([ID_FLAG, pos[0], pos[1], 20, int(np.random.choice(N_array[ID_FLAG]-6)+6), -1])
                    sprites = np.vstack([sprites, sprite])
                    images[len(sprites)-1] = build_image_png(sprite[IDX_pos],sprite[IDX_rad],sprite[IDX_id],sprite[IDX_img])[1]
                if event.key == pygame.K_g:
                    if sprites.shape[0] == 0:
                        B = generate_map(grid_rows, grid_cols)
                        background, terrain = build_map(B, grid_lines=True)
                        print("[Map-Editor] Terrain re-rolled (press s to save)")
                    else:
                        print("[Map-Editor] Cannot re-roll terrain after sprites have been placed")
                        print(sprites)
                if (event.mod & pygame.KMOD_SHIFT) and sprites.shape[0] == 0:
                    new_rows, new_cols = grid_rows, grid_cols
                    if event.key == pygame.K_UP:
                        new_rows = grid_rows + 2
                    elif event.key == pygame.K_DOWN:
                        new_rows = max(grid_rows - 2, 4)
                    elif event.key == pygame.K_RIGHT:
                        new_cols = grid_cols + 2
                    elif event.key == pygame.K_LEFT:
                        new_cols = max(grid_cols - 2, 4)
                    if (new_rows, new_cols) != (grid_rows, grid_cols):
                        grid_rows, grid_cols = new_rows, new_cols
                        B = generate_map(grid_rows, grid_cols)
                        background, terrain = build_map(B, grid_lines=True)
                        WIDTH = (grid_cols - 1) * GRID_SIZE * 2
                        HEIGHT = (grid_rows - 1) * GRID_SIZE * 2
                        screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        print("[Map-Editor] Resized terrain to %dx%d (press s to save)" % (grid_rows, grid_cols))
                if selected_sprite is not None:
                    if event.key == pygame.K_DELETE:
                        if selected_sprite is not None:
                            sprites = np.delete(sprites, i_sel, axis=0)
                            images[i_sel:] = images[i_sel+1:] 
                            i_sel = -1
                            selected_sprite = None
                    #elif event.key == pygame.K_m:
                    #    self.remove_from_fixed_register(selected_obj)
                    #    selected_obj.pos = np.array(pygame.mouse.get_pos())
                    #    self.add_to_fixed_register(selected_obj)
                    if event.key == pygame.K_f: 
                        selected_sprite[IDX_sid] = -1
                    if event.key == pygame.K_1: 
                        selected_sprite[IDX_sid] = 1
                    if event.key == pygame.K_2: 
                        selected_sprite[IDX_sid] = 2
                    if event.key == pygame.K_3: 
                        selected_sprite[IDX_sid] = 3
                    if event.key == pygame.K_4: 
                        selected_sprite[IDX_sid] = 4
                    if event.key == pygame.K_5: 
                        selected_sprite[IDX_sid] = 5
                    if event.key == pygame.K_6: 
                        selected_sprite[IDX_sid] = 6
                    if event.key == pygame.K_7: 
                        selected_sprite[IDX_sid] = 7
                    if event.key == pygame.K_0: 
                        selected_sprite[IDX_sid] = 0
                    if event.key == pygame.K_8: 
                        selected_sprite[IDX_sid] = 8
                    if event.key == pygame.K_m: 
                        pos=np.array(pygame.mouse.get_pos())
                        if selected_sprite is not None:
                            selected_sprite[IDX_pos] = pos
                            images[i_sel] = build_image_png(selected_sprite[IDX_pos],selected_sprite[IDX_rad],selected_sprite[IDX_id],selected_sprite[IDX_img])[1]
                    if event.key == pygame.K_UP:
                        selected_sprite[IDX_rad] = min(selected_sprite[IDX_rad] + 1,GRID_SIZE//2)
                        images[i_sel] = build_image_png(selected_sprite[IDX_pos],selected_sprite[IDX_rad],selected_sprite[IDX_id],selected_sprite[IDX_img])[1]
                    elif event.key == pygame.K_DOWN:
                        selected_sprite[IDX_rad] = max(selected_sprite[IDX_rad] - 1,10)
                        images[i_sel] = build_image_png(selected_sprite[IDX_pos],selected_sprite[IDX_rad],selected_sprite[IDX_id],selected_sprite[IDX_img])[1]
                    if event.key == pygame.K_RIGHT:
                        selected_sprite[IDX_img] = (selected_sprite[IDX_img] + 1) % N_array[selected_sprite[IDX_id]]
                        images[i_sel] = build_image_png(selected_sprite[IDX_pos],selected_sprite[IDX_rad],selected_sprite[IDX_id],selected_sprite[IDX_img])[1]
                    elif event.key == pygame.K_LEFT:
                        selected_sprite[IDX_img] = (selected_sprite[IDX_img] - 1) % N_array[selected_sprite[IDX_id]]
                        images[i_sel] = build_image_png(selected_sprite[IDX_pos],selected_sprite[IDX_rad],selected_sprite[IDX_id],selected_sprite[IDX_img])[1]
                    if event.key == pygame.K_PLUS:
                        if i_sel >= 0 and i_sel < sprites.shape[0] - 1:
                            print(sprites)
                            sprites[[i_sel, i_sel + 1]] = sprites[[i_sel + 1, i_sel]]
                            images[i_sel], images[i_sel + 1] = images[i_sel + 1], images[i_sel]
                            print(sprites)
                            i_sel += 1
                            selected_sprite = sprites[i_sel]
                    elif event.key == pygame.K_MINUS:
                        if i_sel > 0:
                            print(sprites)
                            sprites[[i_sel, i_sel - 1]] = sprites[[i_sel - 1, i_sel]]
                            images[i_sel], images[i_sel - 1] = images[i_sel - 1], images[i_sel]
                            print(sprites)
                            i_sel -= 1
                            selected_sprite = sprites[i_sel]

            if event.type == pygame.MOUSEBUTTONDOWN:
                print("click @ ", str(pygame.mouse.get_pos()))
                j,k = pos2grid(pygame.mouse.get_pos(), TILE_SIZE=64)
                print(terrain)
                print(j,k,terrain[j,k])
                i_sel, selected_sprite = get_object(sprites, pygame.mouse.get_pos())
                if selected_sprite is not None:
                    print("select %s @ %s" % (selected_sprite, str(pygame.mouse.get_pos())))

            if selected_sprite is not None:
                pygame.draw.circle(screen, COLOR_WHITE, selected_sprite[IDX_pos], selected_sprite[IDX_rad] + 3, 4)

            hint = hint_font.render("Press h for help", True, COLOR_WHITE)
            screen.blit(hint, (WIDTH - hint.get_width() - 12, HEIGHT - hint.get_height() - 12))

            if show_help:
                line_h = help_font.get_height() + 6
                box_w = max(help_font.size(line)[0] for line in HELP_LINES) + 30
                box_h = line_h * len(HELP_LINES) + 20
                box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                box.fill((0, 0, 0, 180))
                screen.blit(box, (10, 10))
                for i, line in enumerate(HELP_LINES):
                    label = help_font.render(line, True, COLOR_WHITE)
                    screen.blit(label, (25, 20 + i * line_h))

            pygame.display.flip()

        #time.sleep(1)


def prompt_for_new_map():
    """Prompt the terminal for a map name; reject names that already exist."""
    while True:
        name = input("Map name [%s]: " % DEFAULT_MAP_NAME) or DEFAULT_MAP_NAME
        name = strip_map_ext(name)
        if not map_name_taken(name):
            return name
        print("[Map-Editor] '%s' already exists; choose another name." % name)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        basename = strip_map_ext(sys.argv[1])
    else:
        print("[Map-Editor] No map specified -- generating a new one.")
        basename = prompt_for_new_map()

    editor_interface(world_info={'basename': basename})

