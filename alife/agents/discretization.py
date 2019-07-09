'''
    Functions to discretize the state space and continuize the action space 
    (this could be seen as 'cheating' since it is human-crafted)

    * _G_ left       >=  L 
    * _G_ right      >=  R
    * _G_ centre     >=  ^
    * R_B left       >=  R
    * R_B right      >=  L
    * R_B body       >=  ^
    * ___ all        >=  ^

'''

import numpy as np

IDX_COLIDE = [0,1,2]
IDX_PROBE1 = [3,4,5]
IDX_PROBE2 = [6,7,8]
IDX_ENERGY = 9
IDX_AMULET = 10
N_INPUTS = 11  

def filter_gps(x):
    ''' return only the amulet part of the input '''
    a = np.zeros(len(x))
    a[0] = x[IDX_AMULET]
    return a

D_TURN_SPEED = 1.2
D_MOVE_SPEED = 5.0
D_LEFT = +np.pi/16.
D_RIGHT = -np.pi/16.

discrete2continuous = np.array([
        [D_RIGHT,D_TURN_SPEED], # turn right
        [D_LEFT,D_TURN_SPEED], # turn left
        [0.00,D_MOVE_SPEED], # fly straight
        #[0.00,0.00]  # nothing
    ])

def a2y(a, speed=3):
    '''
        Discrete action to continuous output
        ------------------------------------
    '''
    return discrete2continuous[a]

def x2s(x, scenario="race", f=None):
    '''
        Continuous observation to discrete state
        ----------------------------------------

        x : continuous state
        l : indices to use
        t : threshold

        return int value of, e.g., 011 => 3
    '''


    if scenario == "race":
        x = filter_race_v2(x,True)
        t = 0.5
    elif scenario == "pre":
        x = x[0:4]
        t = 0.5

    d = x.shape[0]
    return int(((x > t)*(2**np.arange(d,dtype=np.uint64))).sum())


