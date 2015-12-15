import pygame, random, math, os
from numpy import *
from pygame.locals import *

# Game
FPS = 60 # 100         # <-- higher = less CPU

VISION = 25.                      # vision in the murky waters
GRID_SIZE = int(VISION*2)
MAP = genfromtxt('./dat/maps/map_empty.txt', delimiter = 1)
N_ROWS = MAP.shape[0]
N_COLS = MAP.shape[1]
WIDTH = N_COLS * GRID_SIZE
HEIGHT = N_ROWS * GRID_SIZE
SCREEN = array([WIDTH, HEIGHT])   

LIDAR_DIST = VISION * 2.5
MAX_GRID_DETECTION = 50
N_OUTPUTS = 2
IDX_COLIDE = [0,1,2]
IDX_PROBE1 = [3,4,5]
IDX_PROBE2 = [6,7,8]
IDX_CALORIES = 9      # <-- no need (unless we embed the reward into the weights!)!
N_LINPUTS = 9
N_INPUTS = 10

ID_NADA = 0
ID_ROCK = 1
ID_MISC = 2
ID_PLANT = 3
ID_ANIMAL = 4
ID_PREDATOR = 5
N_ID = 5.

#IDX_BIAS = 7

#OUT_ANGLE = 0
#OUT_SPEED = 1
#OUT_DIVIDE = 2
#OUT_HOLD = 3  # /ATTACK, depending on grip strength
#OUT_EXTRA = 4
#OUT_SPEAK = 5 # EMIT INTENTIONAL SOUND

# Colours
COLOR_TRANSPARENT = (1,2,3)
COLOR_WHITE  = 255, 255, 255
COLOR_BLACK  = 0, 0, 0
COLOR_RED    = 255, 0, 0
COLOR_BLUE   = 0, 0, 255
#COLOR_BLUE   = 128, 128, 128
COLOR_CYAN   = 0, 255, 255
COLOR_GREEN  = 0, 128, 0
COLOR_LIME  = 0, 255, 0
COLOR_YELLOW = 255, 255, 0
COLOR_PINK   = 255, 0, 255
COLOR_ORANGE = 255, 165, 0
COLOR_GRAY   = 128, 128, 128
COLOR_DARK   = 1, 1, 1

def proc_id(s):
    if s.ID == ID_ANIMAL:
        return (s.ID + (s.food_ID != ID_PLANT))
    return s.ID

def id2color(code,default=COLOR_BLACK):
    if code == ID_NADA:
        return default
    if code == ID_ROCK:
        return COLOR_GRAY
    if code == ID_PLANT:
        return COLOR_LIME
    if code == ID_ANIMAL:
        return COLOR_CYAN
    if code == (ID_ANIMAL+1):
        return COLOR_ORANGE
    else:
        return default

def code2color(code,default=COLOR_BLACK):
    a = id2rgb(code)
    return a[0], a[1], a[2]

def rgb2color(a, default=COLOR_BLACK):
    if sum(a) <= .0:
        return default
    return a[0] * 255, a[1] * 255, a[2] * 255

def id2rgb(code):
    if code == ID_ROCK:
        return array([0.5,0.5,0.5]) 
    elif code == ID_PLANT:
        return array([0.,1.,0.])
    elif code == ID_ANIMAL:
        return array([0.,0.,1.])
    elif code == ID_PREDATOR:
        return array([1.,0.,0.])
    else:
        return array([0.,0.,0.])

def br_corner():
    return random.randn(2) * 100.0 + (SCREEN - array([VISION,VISION]))

def random_corner():
    if random.rand() > 0.5:
        return random.randn(2) * 10.0 + (SCREEN - array([VISION,VISION]))
    else:
        return random.randn(2) * 10.0 + (zeros(2) + array([VISION,VISION]))

def random_position():
    ''' random positions somewhere on the screen '''
    return random.rand(2) * SCREEN

def proximity(p1, p2):
    ''' proximity (standard Euclidean distance)'''
    return sqrt(sum((p1-p2)**2))

def take_screenshot(surface):
      ''' take a screenshot '''
      n = 1
      f="screenshot%03d.bmp"%n
      while os.path.exists(f):
            n+=1
            f="screenshot%03d.bmp"%n
      pygame.image.save(surface, f)

def PointCollision(p, things, lim):
    '''
        Returns first object detected from 'things' at point 'p'
        --------------------------------------------------
        p: a point of interest
        things: an array of objects
        lim: the limit that we should search in the array
    '''
    for i in range(lim):
        if proximity(p,things[i].pos) <= (things[i].radius):
            return things[i]
    return None

def CircleCollision(s, things, lim):
    '''
        Returns first object detected from 'things' colliding with object 's'
        Like PointCollision, but because they are large objects, we have to check neighouring tiles also.
        ---------------------------------------------------------------------
        s: object (circle) of interest
        things: an array of objects
        lim: the limit that we should search in the array
    '''
    for i in range(lim):
        if proximity(s.pos,things[i].pos) <= (s.radius+things[i].radius):
            return things[i]
    return None

def Reflect(s):
    s.velocity = -s.velocity
    s.move()

def BounceOffFrom(s,e):
    st = s.velocity
    et = e.velocity
    s.velocity - e.velocity
    overlap = (s.radius + e.radius) - magv(s.pos - e.pos)
    v = unitv(s.velocity - e.velocity) * (overlap + 2.)
    s.velocity = -v
    e.velocity = +v
    e.move()
    s.move()
    s.velocity = st
    e.velocity = et

def rotate(v, theta=0.1):
    ''' rotation vector v by angle theta '''
    c = cos(theta)
    s = sin(theta)
    M = array([[c,-s],[s,c]])
    return M.dot(v)

def magv(v):
    ''' magnitude of vector v (aka length, aka l2 norm, aka euclidean norm)'''
    d = sum(v.dot(v))
    if d == 0:
        return 0.
    return sqrt(d)

def unitv(v):
    ''' unit vector of v '''
    d = sum(v.dot(v))
    if d == 0:
        return array([0.,-1.])
    return v / sqrt(d)

def angle_of_attack(attacker, defender):
    x = (defender.pos - attacker.pos)
    v = attacker.velocity
    return arccos(dot(x,v)/(magv(x)*magv(v)))

def pos2grid(p):
    ''' position to grid reference '''
    rx = max(min(int(p[0]/GRID_SIZE),N_COLS-1),0)
    ry = max(min(int(p[1]/GRID_SIZE),N_ROWS-1),0)
    return rx,ry

def pos2hash(p):
    ''' point p to grid hash '''
    rx, ry = pos2grid(p)
    return rx * N_ROWS + ry * N_COLS

