from numpy import *
from numpy.linalg import norm

# Game
FPS = 60 # 100                              # <-- higher = less CPU

GRID_SIZE = 50                              # tile size
VISION = GRID_SIZE*0.5                      # vision in the murky waters
MAX_GRID_DETECTION = 50                     # maximum number of objects that can be detected at once

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

#LIDAR_DIST = VISION * 2.5

N_OUTPUTS = 2
IDX_COLIDE = [0,1,2]
IDX_PROBE1 = [3,4,5]
IDX_PROBE2 = [6,7,8]
N_LINPUTS = 9
IDX_CALORIES = 9      # <-- no need (unless we embed the reward into the weights!)!
N_INPUTS = 10

ID_NADA = 0
ID_ROCK = 1
ID_MISC = 2
ID_PLANT = 3
ID_ANIMAL = 4
ID_PREDATOR = 5
N_ID = 5.

tid2rgb = [
    [0,0,0], 
    [250,250,20], 
]

#IDX_BIAS = 7

#OUT_ANGLE = 0
#OUT_SPEED = 1
#OUT_DIVIDE = 2
#OUT_HOLD = 3  # /ATTACK, depending on grip strength
#OUT_EXTRA = 4
#OUT_SPEAK = 5 # EMIT INTENTIONAL SOUND

def rgb2color(a, default=COLOR_BLACK):
    if sum(a) <= .0:
        return default
    #return a[0] * 255, a[1] * 255, a[2] * 255
    return a * 255

id2rgb = array([
    [0.,0.,0.],          # ID_NADA = 0        = COLOR_WHITE/255
    [1.,1.,1.],          # ID_ROCK = 1        = etc.
    [0.,0.,0.],          # ID_MISC  = 2
    [0.,1.,0.],          # ID_PLANT = 3
    [0.,0.,1.],          # ID_ANIMAL = 4
    [1.,0.,0.],          # ID_PREDATOR = 5
    ])

def proximity(p1, p2):
    ''' proximity (standard Euclidean distance)'''
    return norm(p1 - p2)

def Slide(s,o):
    ''' slide off the other point p '''
    speed = norm(s.velocity)
    u = unitv(s.pos - o)
    s.velocity = u * speed
    s.move()

def Reflect(s):
    ''' reflect (when the other object doesn't move, like a wall or a heavy rock'''
    s.velocity = -s.velocity
    s.move()

def BounceOffFrom(s,e):
    ''' two objects bounds off each other '''
    # todo: the heavier one should bounce less
    # todo use the new slide?
    st = s.velocity
    et = e.velocity
    s.velocity - e.velocity
    overlap = (s.radius + e.radius) - norm(s.pos - e.pos)
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

def unitv(v):
    ''' unit vector of v '''
    d = norm(v)
    if d == 0:
        return array([0.,-1.])
    return v / d

def angle_of_attack(attacker, defender):
    ''' the angle between an attacker and a defender '''
    x = (defender.pos - attacker.pos)
    v = attacker.velocity
    return arccos(dot(x,v)/(norm(x)*norm(v)))

