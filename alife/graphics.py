import pygame
from random import choice as choice
from numpy import *

# Colours
COLOR_WHITE  = 255, 255, 255
COLOR_BLACK  = 0, 0, 0
COLOR_RED    = 255, 0, 0
COLOR_BLUE   = 0, 0, 255
COLOR_CYAN   = 0, 255, 255
COLOR_GREEN  = 0, 128, 0
COLOR_LIME  = 0, 255, 0
COLOR_YELLOW = 255, 255, 0
COLOR_PINK   = 255, 0, 255
COLOR_ORANGE = 255, 165, 0
COLOR_GRAY   = 128, 128, 128
COLOR_DARK   = 1, 1, 1
COLOR_BROWN  = 250, 250, 20
COLOR_TRANSPARENT = (1,2,3)

# Describes the colors of each sprite object
# (now only used for antennae and things like that)
id2rgb = array([
    [0.,0.,0.],          # ID_NADA = 0        = COLOR_WHITE/255
    [1.,1.,1.],          # ID_ROCK = 1        = etc.
    [0.,0.,0.],          # ID_MISC  = 2
    [0.,1.,0.],          # ID_PLANT = 3
    [0.,0.,1.],          # ID_ANIMAL = 4
    [1.,0.,0.],          # ID_PREDATOR = 5
    ])

def rgb2color(a, default=COLOR_BLACK):
    ''' Convert a vector in [0,1] to a colour vector '''
    if sum(a) <= .0:
        return default
    return a * 255

def build_image_wireframe(pos,rad,ID):
    '''
        Build a wireframe image at pos, with radius rad, and ID.
    '''
    color = id2rgb[ID]*255
    image = pygame.Surface((rad*2, rad*2))
    image.fill(COLOR_TRANSPARENT)
    image.set_colorkey(COLOR_TRANSPARENT)
    pygame.draw.circle(image, color, (rad,rad), rad )
    rect=image.get_rect(center=pos)
    return rect, image

def rotate(image, angle):
    ''' Rotate an image (keeping center and size) '''
    rec = image.get_rect()
    img_rotated = pygame.transform.rotate(image, angle)
    rec_rotated = rec.copy()
    rec_rotated.center = img_rotated.get_rect().center
    return img_rotated.subsurface(rec_rotated).copy()

def build_image_bank(image):
    ''' Build images for every single angle 0...359 (applicable to moving sprites) '''
    return [rotate(image, deg-180) for deg in range(360)]

trees = [
    # Location of tree tiles
   (280,183,62,66), (125,3,40,38), (451,115,66,64), (383,115,64,64), (217,55,54,52), (3,55,46,48),
   (443,55,52,56), (163,55,50,50), (39,3,38,38), (3,183,64,64), (365,3,47,48), (416,3,46,48), (3,3,32,32),
   (215,3,46,44), (71,183,64,64), (169,3,42,42), (385,55,54,54), (139,183,68,64), (67,115,56,58), (275,55,48,52), (3,115,60,56),
   (327,55,54,54), (346,183,62,66), (81,3,40,38), (255,115,58,6), (466,3,48,48), (127,115,56,60), (3,257,66,70), (111,55,48,50),
   (317,115,62,62), (407,341,110,114), (301,341,102,114), (211,183,65,65), (151,257,74,72), (73,257,74,70), (385,257,78,78),
   (195,341,102,108), (467,257,70,80), (53,55,54,50), (265,3,46,46), (315,3,46,46), (412,183,68,70), (229,257,74,74),
   (187,115,64,62), (3,341,94,82), (101,341,90,90), (307,257,74,78),
    ]

land = {
        # Denotes the location of each tile given its character code
        ' ' : [(0,0)],
        'v' : [(4,7),(5,7),(4,5),(5,5),(6,4)],
        '[' : [(3,3),(3,5),(6,2),(4,2)],
        ']' : [(5,1),(1,1),(2,1),(1,5),(1,7)],
       '\\' : [(7,5)],
        '/' : [(7,3)],
        '+' : [(5,3)],
        '^' : [(2,0),(4,0)],
        'L' : [(2,5)],
        '-' : [(2,7)],
        '~' : [(7,7)],
    }

terr = {
        # Denotes the collision quaters of each tile given its character code (since one picture tile covers 4 game tiles)
        ' ' : array([[0,0],[0,0]]),
        'v' : array([[0,0],[1,1]]), 
        '[' : array([[1,0],[1,0]]),                       
        ']' : array([[0,1],[0,1]]),                       
       '\\' : array([[1,0],[1,1]]),                       
        '/' : array([[0,1],[1,1]]),                       
        '+' : array([[1,1],[1,0]]),                       
        '^' : array([[1,1],[0,0]]),                       
        'L' : array([[1,1],[0,1]]),                       
        '-' : array([[0,0],[0,0]]),                       
        '~' : array([[1,1],[1,1]]),                       
    }

def get_tree(n):
    ''' Load a resource '''
    sheet = pygame.image.load('./img/trees_packed.png').convert_alpha()
    image = sheet.subsurface(trees[n])
    return image

def get_rock(n):
    ''' Load a rock '''
    return pygame.image.load('./img/rock_'+str(n)+'.png')

def build_image_png(pos,rad,ID):
    '''
        Load the appropriate image given an object ID (see object codes in objects.py), as follows:
    '''
    if ID == 1:
        image = get_rock(random.choice(10))
    elif ID == 3:
        image = get_tree(random.choice(len(trees)))
    elif ID == 4:
        image = pygame.image.load('./img/green_bug.png')
    elif ID == 5:
        image = pygame.image.load('./img/bug.png')
    else:
        return build_image_wireframe(pos,rad,ID)

    # Scale the image to fit the size of the sprite
    image = pygame.transform.scale(image, (rad*2, rad*2))

    # Draw team colours
    #color = id2rgb[ID]*255
    #pygame.draw.circle(image, color, (rad,rad), rad, 1 )

    rect=image.get_rect(center=pos)
    return rect, image

def build_map_wireframe(size,N_COLS,N_ROWS,GRID_SIZE,terrain):
    '''
        Build a black map, with a different color for the terrain.
        N.B.: this function is probably broken at the moment, but it's not used by default anyway.
    '''
    background = pygame.Surface(size)
    background.fill([0, 0, 0])                  # fill with black
    for j in range(N_COLS):
        for k in range(N_ROWS):
            if terrain[k,j] > 0:
                # Fill in the terrain
                background.fill(COLOR_BROWN, rect=(j*GRID_SIZE,k*GRID_SIZE,GRID_SIZE,GRID_SIZE))
    background = background.convert()           # can speed up when we have an 'intense' background
    return background

def build_map_png(size,N_COLS,N_ROWS,GRID_SIZE,tile_codes):
    '''
        Build the map of N_COLS * N_ROWS squares of size GRID_SIZE with images based on the tile_codes array. 
        Return the image, and the terrain map (indicating with 1s which gridsquares are unpassable).

        N.B. A tile image covers 4 game tiles, therefore we only need to draw for every other row and column.
        - but this does mean that maps need to be an even number of columns and rows!
    '''
    # Init.
    background = pygame.Surface(size)
    terrain = zeros((N_ROWS,N_COLS),dtype=int)
    # Load.
    sheet = pygame.image.load('./img/ground.png') #.convert_alpha()
    # Draw
    for j in range(0,N_COLS,2):
        for k in range(0,N_ROWS,2):
            bgimg = pygame.image.load('./img/water.png')
            background.blit(bgimg, (j*GRID_SIZE, k*GRID_SIZE))
            c = tile_codes[k,j]
            if c != '.':
                (x,y) = choice(land[c])
                image = sheet.subsurface((x*128,y*128,128,128))
                #img = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
                background.blit(image, (j*GRID_SIZE, k*GRID_SIZE))
                terrain[k:k+2,j:j+2] = terr[c]
    background = background.convert()           # can speed up when we have an 'intense' background
    return background, terrain
