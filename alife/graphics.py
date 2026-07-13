import pygame
import numpy as np
import random
import os
from PIL import Image, ImageDraw, ImageFont
from .config import IMG_DIR
 
# Types of Sprites/Things/Objects
ID_FX = -3    # Effects/decor are purely for visual satisfaction/aesthetics - no game logic is associated.
ID_FLAG = -1  # A flag/nest is not visible or collidable to sprites, but some game logic may be associated (e.g., touching a flag, respawn at nest).
ID_VOID = 0   # Not anything; a placeholder for an empty slot in the sprites array.
ID_ROCK = 1   # Blue objects 
ID_PLANT = 2  # Green objects
ID_ANIMAL = 3 # Red objects (agent-controlled)

# How many types of image are there for each .. 
# TODO Discover dynamically 
N_ROCKS = 16
N_TREES = 47
N_BUGS = 7
N_FLAGS = 11

# File names, e.g., rock_00.png ... rock_0d.png where d = N_ROCKS-1
N_array = [ID_VOID,N_ROCKS,N_TREES,N_BUGS,N_FLAGS]
f_array = [None,'rock','tree','bug','flag']

# Basic colors
COLOR_TRANSPARENT = (1,2,3)
COLOR_WHITE  = (255, 255, 255)
COLOR_RED  = (255, 0, 0)
COLOR_BLACK  = (0, 0, 0)
COLOR_YELLOW  = (255, 255, 0)

# Convert ID to splatter palletes (for 'splatter' artwork)
id2pal = {
            ID_VOID : [COLOR_WHITE],
            ID_ROCK : [(45,44,44), (58,50,50), (73,60,60), (92,73,73), (101,83,83),],
            ID_PLANT : [ (37, 82, 59),  (53, 136, 86), (90, 171, 97), (98, 189, 105), (48, 105, 75),  (12, 56, 35) ],
            ID_ANIMAL : [ (255,0,0), (178,0,0), (91,0,0), (250,50,50), (204,61,61), ],
            ID_FLAG : [(255, 215, 0),(207, 181, 59),(255, 201, 14),(255, 248, 200),(255, 215, 100)],
        }

# Convert ID to RGB intensities (how agents observe each of these) 
id2rgb = {
        ID_VOID : COLOR_BLACK, # VOID     =  0  = BLACK
        ID_ROCK : [0.,0.,1.],  # ROCK     =  1  = BLUE
        ID_PLANT : [0.,1.,0.],  # PLANT    =  3  = GREEN
        ID_ANIMAL : [1.,0.,0.],  # ANIMAL   =  4  = RED
}

# Convert ID to Z-index 
id2z_idx = {
        ID_VOID : 0,
        ID_ROCK : 1,
        ID_PLANT : 2,
        ID_ANIMAL : 1,
}

# Import index constants (etc).
from .constants import *

def build_splatter_img(ID,pos,rad,qty,orad=None):
    '''
        Draw some splatter around pos, with radius rad, color according to ID.
    '''
    image = pygame.Surface((rad*2, rad*2))
    image.fill(COLOR_TRANSPARENT)
    image.set_colorkey(COLOR_TRANSPARENT)
    palette = id2pal[ID]
    orad = rad*2
    for _ in range(qty):
        color = palette[np.random.choice(len(palette))]
        pygame.draw.circle(image, color, [int(np.random.randn() * rad * 0.5 + rad),int(np.random.randn() * rad * 0.5 + rad)],np.random.choice(3)+1)
    rect=image.get_rect(center=pos)
    return rect, image

def rotate_img(image, angle):
    ''' Rotate an image (keeping center and size) '''
    rec = image.get_rect()
    img_rotated = pygame.transform.rotate(image, angle)
    rec_rotated = rec.copy()
    rec_rotated.center = img_rotated.get_rect().center
    return img_rotated.subsurface(rec_rotated).copy()

def build_image_bank(image):
    ''' Build images for every single angle 0,...,359 (to be used for rotating sprites) '''
    return [rotate_img(image, deg-180) for deg in range(360)]

from .map_tools import convert_to_tiles

land = {
        # Denotes the location of each tile given its character code
         0 : [(0,0)],                                   # land
         1 : [(3,7)],                                   # top left concave 
         2 : [(2,3)],                                   # top right concave
         3 : [(2,0),(4,0),(0,5),(0,7)],                             # bottom ridge
         4 : [(6,6)],                                   # top right concave -- need to rotate
         5 : [(3,3),(3,5),(6,2),(4,2)],                 # left ridge
         6 : [(6,7)],                                   # 6 crossover tile
         7 : [(5,3)],                                   # top left ridge
         8 : [(2,7)],                                   # bottom right concave
         9 : [(7,6)],                                   # 9 crossover tile (mirrored)
         10 : [(5,1),(1,1),(2,1),(1,5),(1,7)],           # right ridge
         11 : [(2,5),(0,3)],                              # top right ridge
         12 : [(4,7),(5,7),(4,5),(5,5),(6,4)],           # top ridge
         13 : [(7,5)],                                   # bottom left ridge
         14 : [(7,3)],                                   # bottom right ridge
        15 : [(7,7)],                                   # water
    }

def make_num(i, tile_size=128):
    '''
    Just used to draw a missing tile (with tilenumber printed in the middle)
    '''
    image = Image.new("RGB", (tile_size, tile_size), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text = f"{i}"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    #text_width, text_height = draw.textsize(text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    x = (tile_size - text_width) // 2
    y = (tile_size - text_height) // 2
    # Draw the text in black
    draw.text((x, y), text, fill="black", font=font)
    return image

#def get_tilegraphics():
#   # mini tileset
#    tileset = Image.open("worlds/bugworld/img/tiles.png")
#    # Extract individual tiles
#    tiles = {}
#    for i in range(16):
#        left = i * 32
#        tile = tileset.crop((left, 0, left + 32, 32))
#        tiles[i] = [tile]
#    return tiles

def get_tilegraphics(tile_size=128):
    '''
    Returns
    -------

    tiles : dict(int,list)
        mapping each tile integer (between 0 and 15 incl.) to a list of possible images

    '''
    tileset_path = os.path.join(IMG_DIR, 'tileset3.png')
    tileset = Image.open(tileset_path).convert("RGBA")
    tiles = {}
    x,y = 7*128,7*128
    water = tileset.crop((x,y,x+128,y+128))
    #water = Image.alpha_composite(water, tile)
    #water = Image.open("worlds/bugworld/img/water.png").convert("RGBA")
    for i in land.keys():
        tiles[i] = []
        if len(land[i]) <= 0:
            # no image found, make a placeholder
            tiles[i] = [make_num(i)]
        else: 
            for (tx,ty) in land[i]:
                x,y = tx*128,ty*128
                tile = tileset.crop((x,y,x+128,y+128))
                if i < 15:
                    tile = Image.alpha_composite(water, tile)
                tiles[i].append(tile.resize((128,128)))
    return tiles

def build_image_png(pos,rad,ID,SSID=-1):
    '''
        Load the appropriate image given an object ID and sub-ID,
        then scale and center it accordingly to pos and rad. 
    '''
    # Load the image
    image_path = os.path.join(IMG_DIR, f"{f_array[ID]}_{SSID:02d}.png")
    image = pygame.image.load(image_path).convert_alpha()

    # TODO if rad not specified -- use natural radius
    # TODO Respect original image size as max size 

    # Scale the image to fit the size of the sprite
    if rad is not None:
        image = pygame.transform.scale(image, (rad*2, rad*2))

    # Center the image
    rect=image.get_rect(center=pos)

    return rect, image

def draw_map(B, tile_size=128, grid_lines=False):

    tiles = get_tilegraphics()

    M, T = convert_to_tiles(B)
    #print("======== * M * =========")
    #print(M)
    # Draw the final map
    n_rows, n_cols = M.shape
    final_map = Image.new("RGB", (n_cols * tile_size, n_rows * tile_size))
    
    for i in range(n_rows):
        for j in range(n_cols):
            c = M[i, j]
            tile_list = tiles[int(c)]
            tile = random.choice(tile_list)
            final_map.paste(tile, (j * tile_size, i * tile_size))
    
    # Draw gridlines
    if grid_lines:
        draw = ImageDraw.Draw(final_map)
        step = tile_size // 2

        # Vertical lines
        for x in range(0, final_map.width, step):
            draw.line([(x, 0), (x, final_map.height)], fill="gray", width=1)

        # Horizontal lines
        for y in range(0, final_map.height, step):
            draw.line([(0, y), (final_map.width, y)], fill="gray", width=1)

        # Overlay circles at the center of grid squares where T[i, j] == 1
        grid_rows, grid_cols = T.shape
        draw = ImageDraw.Draw(final_map)
        circle_radius = step // 4  # Small circle size
        for i in range(grid_rows):  # Loop over grid squares, not tiles
            for j in range(grid_cols):
                if T[i, j] == 1:
                    center_x = (j + 0.5) * step  # Middle of the grid square
                    center_y = (i + 0.5) * step  # Middle of the grid square
                    draw.line(
                            [(center_x - circle_radius, center_y - circle_radius),
                             (center_x + circle_radius, center_y + circle_radius)],
                            fill="grey",
                            width=2
                            )
                    draw.line(
                            [(center_x + circle_radius, center_y - circle_radius),
                             (center_x - circle_radius, center_y + circle_radius)],
                            fill="grey",
                            width=2
                            )

    return final_map, T

def build_bg_png(B, tile_size=128, grid_lines=False):
    '''
        Draw the map as an image, return that image. 

        Parameters
        ----------

        B : np.array((n_rows,n_cols),dtype=int)
            binary bitmap 

        tiles : dict(int,list)
            maps tile number to a list of possible tile graphics

        tile_size : int
            in pixels
        
        Returns
        -------

        the image

    '''
    image, terrain = draw_map(B, tile_size, grid_lines)
    #image.show() 
    image_data = image.tobytes()
    pygame_surface = pygame.image.fromstring(image_data, image.size, image.mode)
    return pygame_surface, terrain

def get_label(line, color=COLOR_RED):
    myfont = pygame.font.SysFont("monospace", 17) 
    return myfont.render(line, 0, color)

N_FX_SLOTS = 20  # reserved FX rows at end of sprites array

def _find_free_fx(sprites, n):
    """Find a free FX slot in the reserved zone."""
    for j in range(n - N_FX_SLOTS, n):
        if sprites[j, IDX_id] == 0:
            return j
    return None


def draw_state(screen, sprites, images, names):
    ''' Draw the full game state
    '''
    n, d = sprites.shape

    for i in range(n):

        # Spawn splatter FX from damage marker
        if sprites[i, IDX_damage] > 0:
            j = _find_free_fx(sprites, n)
            if j is not None:
                src_id = int(sprites[i, IDX_id])
                pos = sprites[i, IDX_pos].astype(int)
                timer = int(sprites[i, IDX_damage])
                sprites[j, :] = 0
                sprites[j, IDX_id] = ID_FX
                sprites[j, IDX_pos] = pos
                sprites[j, IDX_health] = timer
                sprites[j, IDX_rad] = timer + 5
                sprites[j, IDX_img] = src_id
                images[j] = build_splatter_img(src_id, pos, int(sprites[i, IDX_id]), 20)[1]
            sprites[i, IDX_damage] = 0

        # Spawn glitter FX from glitter marker
        if sprites[i, IDX_glitter] > 0:
            j = _find_free_fx(sprites, n)
            if j is not None:
                pos = sprites[i, IDX_pos].astype(int)
                timer = int(sprites[i, IDX_glitter])
                sprites[j, :] = 0
                sprites[j, IDX_id] = ID_FX
                sprites[j, IDX_pos] = pos
                sprites[j, IDX_health] = timer
                sprites[j, IDX_rad] = timer + 5
                sprites[j, IDX_img] = ID_FLAG
                images[j] = build_splatter_img(ID_FLAG, pos, int(sprites[i, IDX_id]), 20)[1]
            sprites[i, IDX_glitter] = 0

        if sprites[i,IDX_id] == ID_VOID:
            continue
        if sprites[i,IDX_id] == ID_ANIMAL:
            if images[i] is None: 
                # Build the image, as it is specified
                image = build_image_png([0,0],int(sprites[i,IDX_rad]),int(sprites[i,IDX_id]),int(sprites[i,IDX_img]))[1]
                # load an image for each angle
                images[i] = build_image_bank(image)
            # Now draw ...
            draw_bug(screen, sprites, images[i], names, i)
        elif sprites[i,IDX_id] == ID_FX:
            # Draw splatter/glitter image, countdown timer, expire
            p = sprites[i, IDX_pos].astype(int)
            r = int(sprites[i, IDX_rad])
            if images[i] is not None:
                screen.blit(images[i], (p[0] - r, p[1] - r))
            sprites[i, IDX_health] -= 1
            if sprites[i, IDX_health] <= 0:
                sprites[i, :] = 0
                images[i] = None
        else:
            if images[i] is None: 
                # Build the image, as it is specified
                images[i] = build_image_png([0,0],int(sprites[i,IDX_rad]),int(sprites[i,IDX_id]),int(sprites[i,IDX_img]))[1]
            # Now draw ...  (TODO: what's with the images[-1]?)
            draw_obj(screen, sprites[i], images[i], images[-1])


from .utils import rotate, angle_deg

def draw_bug(screen, sprites, images, names, i, p=None):
    ''' Draw bug.

        images : list(list(image))
            array of images, one for each angle

        names : list(str)
            name of the bugs
    '''
    sprite = sprites[i]
    name = names[i]

    if p == None:
        p = sprite[IDX_pos].astype(int)

    # Antennae
    color_L = tuple((sprite[IDX_PROBE1] * 255).astype(int).tolist())
    color_R = tuple((sprite[IDX_PROBE2] * 255).astype(int).tolist())
    pygame.draw.line(screen, COLOR_BLACK, p, p+sprite[IDX_spear0], 4)
    pygame.draw.line(screen, color_L, p, p+sprite[IDX_anten1], 4)
    pygame.draw.line(screen, color_R, p, p+sprite[IDX_anten2], 4)

    # Draw the bug itself
    u = sprite[IDX_unitv]
    r = sprite[IDX_rad]
    screen.blit(images[angle_deg(u)], p - r)

    # Body
    # .. inner
    pygame.draw.circle(screen, np.array([255,255,255]) * sprite[IDX_COLIDE], p, int(r) + 3, 4)
    # .. outer
    pygame.draw.circle(screen, np.array([255,255,255]) * sprite[IDX_PROXIMITY], p, OUTER_RADIUS, 3)
    #pygame.draw.circle(screen, COLOR_WHITE, p, OUTER_RADIUS, 3)
    # .. far outer
    if sprite[IDX_COMPASS] > 0.5:
        pygame.draw.circle(screen, COLOR_YELLOW, p, OUTER_RADIUS+4, 1)

    # Health/Calories/Energy level
    pygame.draw.line(screen, COLOR_WHITE, np.array(p)-20, [p[0]+20,p[1]-20], 1)
    pygame.draw.line(screen, COLOR_WHITE, np.array(p)-20, [p[0]-20+(sprite[IDX_ENERGY]*40),p[1]-20], 5)

    # Flag
    # for i in range(1,50): 
    #     pygame.draw.circle(surface, COLOR_WHITE, p.astype(int), i * DISTANCE_BETWEEN_CHECKPOINTS, 1)
    i_flag = int(sprite[IDX_tid])
    p_flag = sprites[i_flag,IDX_pos].astype(int)
    pygame.draw.line(screen, COLOR_WHITE, p, p_flag, 1)

    # Label
    #name_label = get_label("%s.%d@%d" % (self.name,self.ssID,self.energy))
    screen.blit(get_label("%s" % name), p)


def draw_obj(screen, sprite, image, debug=False):

    p = sprite[IDX_pos].astype(int)
    r = int(sprite[IDX_rad])
    screen.blit(image, p - r)
    if debug:
        pygame.draw.circle(screen, COLOR_WHITE, sprite[IDX_pos].astype(int), int(sprite[IDX_rad]) + 3, 4)

def draw_banner(surface, s, max_txt='--------------------', align='l'):
    '''
        Draw text on existing surface
    '''
    # Get the size of the game display surface
    (px_w,px_h) = surface.get_size()
    lines = s.split("\n")
    myfont = pygame.font.SysFont("monospace", 17) 

    # Get the estimated size needed to display the text
    l,h = myfont.size(max_txt)
    l = 1
    if align=='r':
        l = px_h - l*2
    j = 0
    color = COLOR_RED
    for line in lines:
        label = myfont.render(line, l, color)
        surface.blit(label, [l,h*j])
        j = j + 1
        color = COLOR_WHITE

if __name__ == "__main__":
    '''
        Unit tests
    '''
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_caption("Graphics Testing")
    screen = pygame.display.set_mode((400, 400))
    image = pygame.image.load('../img/bug_03.png').convert_alpha()
    image = pygame.transform.scale(image, (13*2, 13*2))
    rect = image.get_rect(center=(200,200))
    images = build_image_bank(image)   # load an image for each angle
    screen.blit(image, [100, 100])
    pygame.display.flip()
    running = True
    while running:
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          running = False

