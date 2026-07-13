# World Parameters

TILE_SIZE = 64               # tile size (width and height, in pixels)
DEBUG = False

# Sprite Parameters

OUTER_RADIUS = TILE_SIZE     # because we can't detect anything further away
INNER_RADIUS = TILE_SIZE//5+1
MAX_HEALTH = 100             # 
BITE_SIZE = 10
BUMP_SIZE = 5

# STATE -- for all objects, does not change; needed to load objects from disk
IDX_id = 0                     # int : object id; either ID_ROCK, ID_PLANT, ID_ANIMAL, etc.
IDX_x = 1                      # int             
IDX_y = 2                      # int             
IDX_pos = [IDX_x, IDX_y]       # [int,int]                              
IDX_rad = 3                    # int
IDX_img = 4                    # int : image id; the 'coat' for a given sprite of type id              
IDX_sid = 5                    # int : this is a sub-id; 
                               #                if sprite[IDX_id] = ID_FLAG (i.e., a flag/nest) then sprite[IDX_sid] = n for n-th flag
                               #                if sprite[IDX_id] = ID_ANIMAL (i.e., another bug) then sprite[IDX_sid] = Team ID

DISK_INDICES = [IDX_id, IDX_x, IDX_y, IDX_rad, IDX_img, IDX_sid]
# INTERNAL STATE -- for computations and drawing
IDX_spear0 = [6,7]             # int : relative position of spear (supposing base at [0,0])
IDX_anten1 = [8,9]             # int : relative position of left antenna (supposing base at [0,0])
IDX_anten2 = [10,11]             # int : relative position of right antenna (supposing base at [0,0])
IDX_vx = 12                    # float
IDX_vy = 13                    # float
IDX_unitv = [IDX_vx, IDX_vy]   # float
IDX_health = 14                # int : between 0 and MAX_HEALTH
IDX_speed = 15                 # int : internal state speed 
IDX_tid = 16                   # int : targit id; points to the id (array index) of the sprite that this sprite should look for/target
IDX_aid = 17                   # int : attachment id (future use)

IDX_glitter = 18               # float : glitter
IDX_damage = 19                # int : for tracking external splatter

# OBSERVATION (all between 0 and 1) : FLOAT
IDX_COLIDE = 20                 # (OBS) between 0 and 1
IDX_PROXIMITY = 21              # (OBS) between 0 and 1 (nb actually currently can be > 1)
IDX_PROBE1 = [22,23,24]         # (OBS) int : between [0,0,0] and [1,1,1] (indicating 3-channel color intensity)
IDX_PROBE2 = [25,26,27]         # (OBS) int : between [0,0,0] and [1,1,1] (indicating 3-channel color intensity)
IDX_ENERGY = 28                 # (OBS) between 0 and 1, an observation of IDX_health
IDX_COMPASS = 29                   # (OBS) how close are we pointing to the flag (1 <=> exact angle, 0 <=> > 90 degrees) 
IDX_SPEED = 30                  # (OBS) normalised speed
IDX_OBS = [IDX_COLIDE, IDX_PROXIMITY] + IDX_PROBE1 + IDX_PROBE2 + [IDX_ENERGY,IDX_COMPASS,IDX_SPEED]
d_S = len(IDX_OBS)

## ACTION (all between -1 and +1)
IDX_RANGLE = 31                  # (ACT) int : change in angle, in radians, in range [-1, +1]
IDX_LANGLE = 32                  # (ACT) int : this is more like thrust than speed, in range [-1, +1]
IDX_SHIFTF = 33                  # (ACT) int : this is more like thrust than speed, in range [-1, +1]
IDX_ACTIONS = [IDX_RANGLE, IDX_LANGLE]
d_A = len(IDX_ACTIONS)

## REWARD
IDX_RWD = 34
## DONE
IDX_done = 35 

D_SPRITE = 36
