#! /usr/bin/env python3

# Standard Python libraries
import yaml
import sys

# Math libraries
import numpy as np
from numpy.linalg import norm
#np.set_printoptions(threshold=np.inf, precision=1)

# For networking
from .utils import get_centres, rotate, cos_sim, get_tiles, unitv, overlap, slide_off, collision, dist_point_to_rect3
from .graphics import terr, id2rgb, ID_FLAG, ID_NEST, ID_VOID, ID_ANIMAL, ID_ROCK, ID_PLANT, build_bg_png as build_map, draw_state

# Pygame
import pygame

print("[World] Setting parameters")

# Parameters
TILE_SIZE = 64               # tile size (width and height, in pixels)
MAX_GRID_DETECTION = 100     # maximum number of objects that can be detected at once
DEBUG = False

OUTER_RADIUS = TILE_SIZE/2
INNER_RADIUS = 13
MAX_HEALTH = 100                      # ENERGY_LIMIT times radius
MAX_SPEED = 10                         # Maximum speed in pixels/tick
BITE_SIZE = 10
BUMP_SIZE = 10

# SPRITE DEFINITION 

# (player state/ -- for drawing, corresponds to player and inanimate objects, may not change at all)
IDX_i = 35                     # int : the actual array index (actual unique object index)
IDX_id = 0                     # int : object id; either ID_ROCK, ID_PLANT, ID_ANIMAL, etc.
IDX_cid = 13                   # int : carrier id; if > 0, then there is a carrier 
IDX_img = 4                    # int : image id; the 'coat' for a given sprite of type id              
IDX_x = 1                      # int             
IDX_y = 2                      # int             
IDX_pos = [IDX_x, IDX_y]       # [int,int]                              
IDX_rad = 3                    # int
IDX_dirty = 18                 # bool                      
# (internal state -- for computations)
IDX_spear0 = [5,6]             # int : relative position of spear (supposing base at [0,0])
IDX_anten1 = [7,8]             # int : relative position of left antenna (supposing base at [0,0])
IDX_anten2 = [9,10]             # int : relative position of right antenna (supposing base at [0,0])
IDX_vx = 11                    # float
IDX_vy = 12                    # float
IDX_unitv = [IDX_vx, IDX_vy]   # float
IDX_dangle = 14                # float
IDX_penergy = 15               # float
IDX_flagi = 16                 # int : points to the array index of the flag this sprite should look for
IDX_nesti = 36                 # int : points to the array index of the nest this sprite should spawn at
IDX_health = 17                # int : between 0 and MAX_HEALTH
IDX_damage = 19                # int
# -- observation (all between 0 and 1) : FLOAT
IDX_COLIDE = 20                 # between 0 and 1
IDX_PROXIMITY = 21              # between 0 and 1 (nb actually currently can be > 1)
IDX_PROBE1 = [22,23,24]         # between [0,0,0] and [1,1,1] (indicating 3-channel color intensity)
IDX_PROBE2 = [25,26,27]         # between [0,0,0] and [1,1,1] (indicating 3-channel color intensity)
IDX_ENERGY = 28                 # between 0 and 1, an observation of IDX_health
IDX_FLAG = 29                   # how close are we pointing to the flag (1 <=> exact angle, 0 <=> > 90 degrees)
IDX_SPEED = 30                  # n.b. this is an observation speed -- may be not needed!
IDX_OBS = [IDX_COLIDE, IDX_PROXIMITY] + IDX_PROBE1 + IDX_PROBE2 + [IDX_ENERGY,IDX_FLAG]
d_S = len(IDX_OBS)
## -- action (all between -1 and +1)
IDX_ANGLE = 31                  # change in angle, in radians, in range [-1, +1]
IDX_POWER = 32                  # this is more like thrust than speed, in range [-1, +1]
IDX_ACTIONS = [IDX_ANGLE, IDX_POWER]
d_A = len(IDX_ACTIONS)
## -- reward
IDX_RWD = 33
## -- done?           do we need this?
IDX_done = 34
# ------------------------------------------------------------------

# NEEDED TO LOAD OBJECTS FROM DISK
DISK_INDICES = [IDX_id, IDX_x, IDX_y, IDX_rad, IDX_img]
# NEEDED FOR DEBUGGING
DEBUG_INDICES = [IDX_i] + [IDX_id] + IDX_pos + [IDX_img] + [IDX_RWD, IDX_rad] + [IDX_cid]


## EXTRA
ODX_j = 0
ODX_k = 1

D_SPRITE = 37
N_SPRITE = 20

print("      > Obs indices: %d" % D_SPRITE)
print("      > Max sprites: %d" % N_SPRITE)

labels = ['--' for _ in range(D_SPRITE)]
labels[IDX_i] = 'i'
labels[IDX_id] = 'id'
labels[IDX_x] = 'x'
labels[IDX_y] = 'y'
labels[IDX_vx] = 'vx'
labels[IDX_vy] = 'vy'
labels[IDX_rad] = 'rad'
labels[IDX_img] = 'sid'
labels[IDX_health] = '[+]'
labels[IDX_COLIDE] = ' o '
labels[IDX_PROXIMITY] = '(o)'
labels[IDX_nesti] = 'nst'
labels[IDX_flagi] = 'flg'
#labels[IDX_PROBE1] = ['L-R', 'L-G', 'L-B']
#labels[IDX_PROBE2] = ['R-R', 'R-G', 'R-B']
labels[IDX_ENERGY] = 'nrg'
labels[IDX_SPEED] = '|v|'
labels[IDX_RWD] = 'rwd'


i_VOID = -2     # emptyness
i_CLIFF = -1     # cliff/rock

# Rewards
RWD_CHECKPOINT = 1
#RWD_EXISTING = 0.1
RWD_DEATH = -5

def load_map(fname_map):
    ''' Load a map from a text file into a 2D numpy array '''
    # Load the map
    MAP = np.genfromtxt(fname_map, delimiter = 1, dtype=str)
    # Trim off the edges
    tile_codes = MAP[1:-1,1:-1]
    # Initialize the terrain map
    n_rows, n_cols = tile_codes.shape
    terrain = np.zeros((n_rows,n_cols),dtype=int)
    # Fill it 
    for j in range(0,n_rows,2):
        for k in range(0,n_cols,2):
            c = tile_codes[j,k]
            if c != '.':
                terrain[j:j+2,k:k+2] = terr[c]
    return terrain


ANTENNA_RATIO = 2.5
TERRAIN_DAMAGE = 1 # Added factor when hitting a wall or landing on water
PERCENT_INIT_ENERGY = 0.5       # How much of its max energy is a creature born with

import pandas as pd

def print_sprites(sprite_array,j_list,labels, DEBUG=False): 
    if not DEBUG:
        return
    print("---------- SPRITES -------------")
    print('___|' + '|'.join(["%5s " % labels[j] for j in j_list]))
    for i in range(len(sprite_array)): 
        print(("%2d |" % i) + '|'.join(["%5d " % int(sprite_array[i,j]) for j in j_list]))
    print("--------------------------------")

class World:
    """ A World.

        Defined by a numpy array of sprites, and some dynamics. 

        Parameters
        ----------

        bname_map : str 
            the filename with the map data (tiles) *not including the extension*, e.g., 'map3'
            where map3.dat will hold the map data, and map3.csv will hold the sprite data. 

        fname_conf : str 
            the filename with the config data (world defaults)
    """

    def __init__(self,bname_map="worlds/bugworld/maps/new_2"):

        fname_sprites = bname_map+'.csv'
        fname_map = bname_map+'.dat'

        # Load map and get its dimensions
        self.terrain = load_map(fname_map)
        print("[World] Loaded map")

        ## GRID REGISTER and GRID COUNT 

        # Sprite register for creatures 
        self.sprites = np.zeros((N_SPRITE,D_SPRITE), dtype=np.float32)
        # Grid register for everything
        self.register = np.zeros((*self.terrain.shape,MAX_GRID_DETECTION),int) 
        self.regbase = np.zeros_like(self.terrain)        # count of non-animals (fixed, once the map is loaded)
        self.regcount = np.zeros_like(self.terrain)       # count of animals
        # Special information, such as which objects can be treated as flags
        self.special = []
        self.speci = 1

        # Sprite and grid register for rocks and plants (and nest and flag)
        self.i_base = self.load_sprites(fname_sprites)
        self.n_sprites = self.i_base
        print("[World] Loaded %d inanimate sprites" % self.i_base)
        print(self.special)
        print_sprites(self.sprites,DEBUG_INDICES,labels, DEBUG=False)

        print("[World] Set special sprites")
        self.sprites[i_CLIFF,IDX_id] = ID_ROCK

        ## PRE-COMPUTATION ##

        # Such that [x,y] = grid2pos[i,j] gives the centre position of the grid at i-th row, j-th column
        self.grid2pos = get_centres(*self.terrain.shape,TILE_SIZE)

        ## GRAPHICS ## 
        map_codes = np.genfromtxt(fname_map, delimiter = 1, dtype=str)[1:-1,1:-1]
        WIDTH = map_codes.shape[1] * TILE_SIZE
        HEIGHT = map_codes.shape[0] * TILE_SIZE
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))#, HWSURFACE|DOUBLEBUF)
        self.background = build_map(self.screen.get_size(),TILE_SIZE,map_codes)
        self.screen.blit(self.background, [0, 0])
        pygame.display.flip()
        self.images = [None for _ in range(N_SPRITE)]

        ## MAIN LOOP ##
        print("[World] Done init")

    def get_info(self):
        return {
            'basename' : 'ALife',
            'd_S' : d_S,
            'd_A' : d_A,
        }

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

    def step(self, actions):
        '''
            s[t+1], r[t] ~ p( . | s[t], a[t] )

            actions : dict(int, np.array)
                the index of an agent, and its desired d_A-dimensional action

            Returns
            -------

            O : dict(int, np.array)
                the d_S-dimensional observation
            R : float
                the reward
            done : int
                (unused in this envivroment)
            
        ''' 

        # Stop not-responding window
        self.handle_events()

        # -------------------------------------------------------------
        # Reset, cleanup from last time
        # -------------------------------------------------------------
        self.sprites[self.i_base:self.n_sprites,IDX_done] = 0 
        self.sprites[self.i_base:self.n_sprites,IDX_RWD] = 0 
        # Reset reg-counts and Register all sprites
        self.regcount.fill(0) 
        self.regcount += self.regbase

        # -------------------------------------------------------------
        # Set actions, and check what's left over
        # -------------------------------------------------------------
        for i in range(self.i_base,self.n_sprites):
            cid = self.sprites[i,IDX_cid]
            self.sprites[i,IDX_ACTIONS] = actions[cid]

        # -------------------------------------------------------------
        # Environment deals with Creature actions
        # -------------------------------------------------------------

        for i in range(self.i_base,self.n_sprites):
            # take the action!
            self.enact(i)
            # live (individual calculations, collisions, etc.)
            self.do_vision_check(i)
            self.do_flag_check(i)
            # live some more (collective calculations, game engine)
            # health check
            if self.sprites[i,IDX_health] < 0.1:
                self.respawn(i,RWD_DEATH,msg="starvation death")


        # -------------------------------------------------------------
        # Extract an observation from the full state space
        # o[t] = phi(s[t])
        # -------------------------------------------------------------

        # Normalization of energy levels
        self.sprites[self.i_base:self.n_sprites,IDX_ENERGY] = np.clip(self.sprites[self.i_base:self.n_sprites,IDX_health]/MAX_HEALTH,0,1)

        print_sprites(self.sprites,DEBUG_INDICES,labels, DEBUG=False)

        # -------------------------------------------------------------
        # Drawing / Debug
        # -------------------------------------------------------------

        print_sprites(self.sprites[self.i_base:self.n_sprites],DEBUG_INDICES,labels, DEBUG=False)
        self.screen.blit(self.background, [0,0]) 
        draw_state(self.screen, self.sprites[0:self.n_sprites], self.images)
        pygame.display.flip()

        # -------------------------------------------------------------
        # Environment is observed (by the Creatures)
        # send o[t], r[t] --> agent
        # -------------------------------------------------------------

        O = {}
        R = {}
        _ = {}

        for i, k in enumerate(self.sprites[self.i_base:self.n_sprites,IDX_cid]):
            #print(int(k), i, self.sprites[self.i_base+i,IDX_OBS])
            O[int(k)] = self.sprites[self.i_base+i,IDX_OBS]
            R[int(k)] = float(self.sprites[self.i_base+i,IDX_RWD])
            _[int(k)] = int(self.sprites[self.i_base+i,IDX_done]) 

        return O, R, _

    def add_agent(self, c_id): 
        '''
            Create the sprite entry (specifically, a bug), with carrier id c_id.  
        '''
        i = self.n_sprites

        # must have valid carrier id
        assert(c_id > 0)
        # the space we have chosen to put this must be available
        assert(self.sprites[i,IDX_cid] <= 0)
        # must have space in the sprite array for this
        assert(i+1 < len(self.sprites))

        # @todo -- check first from the database, if there is some previous information on pos/energy/points/etc.
        #print("TODO Query database")
        self.sprites[i, IDX_id] = ID_ANIMAL
        self.sprites[i, IDX_nesti] = self.special[0]
        self.sprites[i, IDX_pos] = self.sprites[self.special[0], IDX_pos]
        self.sprites[i, IDX_rad] = INNER_RADIUS
        self.sprites[i, IDX_img] = 1
        self.sprites[i, IDX_cid] = c_id
        self.sprites[i, IDX_i] = i
        self.sprites[i, IDX_flagi] = self.special[1]
        self.sprites[i, IDX_health] = MAX_HEALTH//2
        self.sprites[i, IDX_unitv] = np.array([0,1])
        # TODO, N.B. always rotating by the same amounts, so we could store the rotation matrix M for speed
        self.sprites[i, IDX_spear0] = rotate(self.sprites[i, IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO/2,0.0) # antenna right pos
        self.sprites[i, IDX_anten1] = rotate(self.sprites[i, IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,+0.3) # antenna left pos
        self.sprites[i, IDX_anten2] = rotate(self.sprites[i, IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,-0.3) # antenna right pos
        self.respawn(i, 0, 0, msg="just init")

        self.n_sprites = i + 1

    def del_agent(self, cid): 
        '''
            Remove the sprite entry at position i
        '''
        i = np.where(self.sprites[:, IDX_cid] == cid)[0][0]

        n = self.n_sprites
        # remove this sprite (n.b. this includes cid=0)
        self.sprites[i, :] = 0
        # copy over the top
        self.sprites[i:n-1, :] = self.sprites[i+1:n, :]
        # remove the tail end 
        self.sprites[n, :] = 0
        # return the number of sprites left
        #print(self.sprites[0:n,[IDX_id,IDX_cid]])
        self.n_sprites = self.n_sprites - 1

    def select_sprite(self, c_id, n_limit): 
        '''
            Find any sprite with no carrier
        '''
        valid_indices = np.where((self.sprites[0:n_limit, IDX_id] == ID_ROCK) & (self.sprites[0:n_limit, IDX_cid] <= 0))[0]
        if len(valid_indices) > 0:
            i = np.random.choice(valid_indices)
            self.sprites[i, IDX_cid] = c_id
            return i
        else:
            print("[World] No rows satisfy the conditions.")
            exit(1)
        return 0

    def deselect_sprite(self, c_id, i):
        assert(self.sprites[i, IDX_cid] == c_id)
        self.sprites[i, IDX_cid] = 0
        return i


    def load_sprites(self, fname): 
        '''
            Load inanimate sprites from file.

            Populate self.sprites with rocks and plants, put up the nest and set the flag.


            Parameters
            ----------

            fname : str
                file name (.csv format) with columns as per DISK_INDICES


            Returns
            -------

            int
                the number of inanimate sprites loaded 
                
        '''
        # Load data from the file 
        try: 
            print("[World] Load Sprites ..")
            things = np.loadtxt(fname,delimiter=',',dtype=int)
        except:
            print("[World] Error: ", sys.exc_info()[0])
            print("      > No sprite file found...")
            exit(1)

        for i,thing in enumerate(things): 

            # Sprit reg.
            self.sprites[i,DISK_INDICES] = thing[DISK_INDICES]
            self.sprites[i,IDX_dirty] = 1
            self.sprites[i,IDX_i] = i
            # We must register at least the things here (the bugs will be re-registered during the loop)
            j,k = self.pos2grid(self.sprites[i,IDX_pos])
            assert(self.terrain[j,k] == 0)

            if self.sprites[i,IDX_id] == ID_FLAG:
                self.special.append(i)
            elif self.sprites[i,IDX_id] == ID_NEST:
                self.special = [i] + self.special
            # Register for collision detection
            c = self.regbase[j,k]
            self.register[j,k,c] = i
            self.regbase[j,k] += 1

        # Set the end of the inanimate objects
        return len(things)

    def calculate_energy(self,i_base,n): 

        #######################################################
        # Moving burns energy according to size and speed and the angle of turn
        # self.sprites[i_base:n,IDX_health] -= self.sprites[i_base:n,IDX_dangle]
        # self.sprites[i_base:n,IDX_health] -= (self.sprites[i_base:n,IDX_POWER]*0.1)**2

        # Normalize health level (as observation)
        self.sprites[i_base:n,IDX_ENERGY] = np.clip(self.sprites[i_base:n,IDX_health]/MAX_HEALTH,0,1)

        # Record current energy
        #self.sprites[i_base:n,IDX_penergy] = self.sprites[i_base:n,IDX_ENERGY]

    def do_flag_check(self,i):

        # This is the index of the flagged object we're chasing
        i_FLAG = int(self.sprites[i,IDX_flagi])
        # Check which way we're pointing
        flag_angle = cos_sim(self.sprites[i,IDX_unitv],self.sprites[i,IDX_pos] - self.sprites[i_FLAG,IDX_pos]) 
        self.sprites[i,IDX_FLAG] = flag_angle * -1*(flag_angle <= 0)


    def respawn(self, i, rwd_T=RWD_DEATH, done=1, msg=""):
        self.sprites[i,IDX_health] = MAX_HEALTH * PERCENT_INIT_ENERGY
        self.sprites[i,IDX_RWD] += rwd_T
        self.sprites[i,IDX_done] = done
        # Respawn at the nest
        i_NEST = int(self.sprites[i,IDX_nesti])
        self.sprites[i,IDX_pos] = np.random.rand(2) * 10 + self.sprites[i_NEST,IDX_pos] 
        # Reset flag id
        self.sprites[i,IDX_flagi] = self.special[1]
        # Death and rebirth; increment global score and respawn
        print("[World] sprite[%d] respawn @ %s [%s] (inest=%d): %s" % (i,str(self.sprites[i,IDX_pos]),str(self.sprites[i_NEST,IDX_pos]),i_NEST,msg))

    def do_vision_check(self, i):
        """
            Process vision (collisions with terrain/other objects)
        """

        # Reset first
        self.sprites[:,IDX_COLIDE] = 0 
        self.sprites[:,IDX_PROXIMITY] = 0 

        # ... then process
        self.process_vision(i)

        self.sprites[i,IDX_PROBE1] = self.point_vision(self.sprites[i,IDX_pos] + self.sprites[i,IDX_anten1])
        self.sprites[i,IDX_PROBE2] = self.point_vision(self.sprites[i,IDX_pos] + self.sprites[i,IDX_anten2])

        self.spearing(i,self.point_collision(self.sprites[i,IDX_pos] + self.sprites[i,IDX_spear0]))


    def enact(self, i):
        ''' Carry out actions.

            Actions are: 
                self.sprites[i,IDX_ANGLE] # change in angle (in radians)
                self.sprites[i,IDX_POWER] # thrust/power 
                # probe = action[IDX_FIRE]   # not yet implemented
            
            # TODO this function can be done simultaneously for all sprites
        '''

        dtheta = self.sprites[i,IDX_ANGLE]

        # New velocity vector
        if dtheta < -0.01 or dtheta > 0.01:
            # Update vector
            self.sprites[i,IDX_unitv] = unitv(rotate(self.sprites[i,IDX_unitv],dtheta))
            # Update antennae # TODO do this more efficiently, e.g., with a dictionary rotate_L[angle]
            self.sprites[i,IDX_spear0] = rotate(self.sprites[i,IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,-0.0) # antenna right pos
            self.sprites[i,IDX_anten1] = rotate(self.sprites[i,IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,+0.3) # antenna left pos
            self.sprites[i,IDX_anten2] = rotate(self.sprites[i,IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,-0.3) # antenna right pos

        self.sprites[i,IDX_SPEED] = self.sprites[i,IDX_POWER] * MAX_SPEED   

        # Now move 
        self.sprites[i,IDX_pos] += (self.sprites[i,IDX_unitv] * self.sprites[i,IDX_SPEED])

        # Update change of angle (it's just angle!)
        self.sprites[i,IDX_dangle] = abs(dtheta)


    def pos2grid(self,p):
        ''' Convert (x,y)-point to (j,k)-grid reference ''' 
        x, y = p #np.clip(p,[0,0],self.terrain.shape * TILE_SIZE)
        j = np.floor(y / TILE_SIZE).astype(int)
        k = np.floor(x / TILE_SIZE).astype(int)
        return (j, k)

    def body_sensor(self, i, j, k): 
        '''
            
            Given the i-th sprite, which has 
            return 1) vision wrt objects, and 2) any object we collide with

            Assume: centre point, 
                inner (rad)    'touch range' <=> the actual body delimiter
                OUTER_RADIUS   'hearing range' <=> a proximity sensor


            Paramemters
            -----------

            i, j, k : a sprite i at tile (j,k)
                (these are given together for efficiency reasons)

        '''

        # Check all sprites in the register ...
        n_jk = self.regcount[j,k]
        for i_other in self.register[j,k,0:n_jk]:

            # If this object is not me, and positive id ...  
            if i != i_other and self.sprites[i_other,IDX_id] > 0:

                # Check if sprite i can 'hear/see/detect' sprite i_other
                overlap_with_thing = overlap(self.sprites[i,IDX_pos],OUTER_RADIUS,self.sprites[i_other,IDX_pos],self.sprites[i_other,IDX_rad])

                if overlap_with_thing > 0:
                    # - 
                    # yes, in proximity, but not necessarily touching ...
                    # -
                    dist_between_rings = OUTER_RADIUS - self.sprites[i,IDX_rad] # Distance between inner and outer radius
                    self.sprites[i,IDX_PROXIMITY] += (overlap_with_thing / dist_between_rings)

                    if overlap_with_thing > dist_between_rings:
                        # - 
                        # And actually touching ...
                        # - 
                        self.sprites[i,IDX_COLIDE] = 1 
                        # Deal with bumping
                        self.bumping(i,i_other)


    def bumping(self, i, i_victim): 
        '''
            Sprite i bumps into object i_victim
            -----------------------------------

            if i_victim another sprite, both are damaged proportional to their speed
            if i_victim a plant, or a rock, only the bug is damaged

            Parameters
            ----------

            i : int
                sprite id (animate)
            i_victim : int
                sprite id (animate or inaninmate)
        '''

        # Bugs hurt themselves crashing into anything of positive id
        
        if self.sprites[i_victim,IDX_id] >= ID_VOID:   # TODO: != ???
            self.sprites[i,IDX_health] -= BUMP_SIZE * abs(self.sprites[i,IDX_POWER])
        else:
            # This could be a nest, or a flag terrain or even iron ore!!
            #   TODO (iron ore): could be a way to model non-collision resources:
            #   bugs only eat when at 0 speed and 0 turning for 2 successive time steps
            #   else bugs can travel over -- perhaps at a speed/energy reduction, but no damage
            return

        # Other bugs can be victims too

        if self.sprites[i_victim,IDX_id] == ID_ANIMAL:
            self.sprites[i_victim,IDX_health] -= BUMP_SIZE * abs(self.sprites[i_victim,IDX_POWER])

        # The attacker slides off the victim

        self.sprites[i,IDX_pos] += slide_off(self.sprites[i,IDX_pos],self.sprites[i,IDX_SPEED],self.sprites[i_victim,IDX_pos])

    def spearing(self, i, i_victim): 
        '''
            Sprite i spears object i_
            -------------------------

            if i_victim another sprite, attack (bugs, even from the same team/specicies, can accidentally spear each other),
            if i_victim a plant, eat a bit of it

            Parameters
            ----------

            i : int
                sprite id (animate)
            i_victim : int
                sprite id (animate or inaninmate)
        '''

        # Spearing nothing does nothing
        if self.sprites[i_victim,IDX_id] == ID_VOID:
            return
        # If spearing the target flag (even if its invisible) 
        elif i_victim == int(self.sprites[i,IDX_flagi]):
            # We have speared the flag, collect reward, and go to the next waypoint
            self.sprites[i,IDX_RWD] += RWD_CHECKPOINT
            self.speci = (self.speci + 1) % len(self.special)
            self.sprites[i,IDX_flagi] = self.special[self.speci] 
        # Spearing a cliff does nothing
        if self.sprites[i_victim,IDX_id] == ID_ROCK:
            return
        # Inanimate sprites cannot spear others (shouldn't be here)
        if self.sprites[i,IDX_id] != ID_ANIMAL:
            return
        # Bugs eat plants
        elif self.sprites[i_victim,IDX_id] == ID_PLANT:
            self.sprites[i,IDX_health] += BITE_SIZE
            self.sprites[i_victim,IDX_health] -= BITE_SIZE
        # Bugs hurt each other in fights
        elif self.sprites[i_victim,IDX_id] == ID_ANIMAL:
            self.sprites[i_victim,IDX_health] -= BITE_SIZE
        # I don't know what happened here
        elif self.sprites[i_victim,IDX_id] == ID_FLAG or self.sprites[i_victim,IDX_id] == ID_NEST:
            #print("[World].spearing ---- just spearing invisible stuff (nest? someone else's flag?); ignore" )
            pass 
        else:
            print("[World].spearing ---- wtf (probably the victim is someone else's flag?", self.sprites[i,IDX_id], self.sprites[i_victim,IDX_id], i, i_victim)
            exit(1)


    def point_vision(self, p): 
        '''
        Point p is a single-pixel eye, what does it see?

        Parameters
        ----------
        p : array-like (2d)
            location of the eye/feeler

        Returns
        -------

        tuple (r,b,g) where each an intensity in [0,1]
        '''
        # TODO make this neater (combine this function with the next one)
        i = self.point_collision(p)
        if i == i_CLIFF:
            return id2rgb[ID_ROCK]
        else:
            return id2rgb[int(self.sprites[i,IDX_id])]

    def point_collision(self, p): 
        ''' Check if point p is colliding with any sprite

            Useful for checking if antennae are touching anything.

            Parameters
            ----------

            p : array-like (2d)
                point


            Returns
            -------

            i : int
                the index of the object that point p is touching 
        '''

        # Terrain collision?
        j_s, k_s = self.pos2grid(p) 
        if self.terrain[j_s,k_s] > 0: 
            # Current (i,j) grid tile is cliff!
            return i_CLIFF

        # Let's have a look around (p may be in an object registered to a neighbour tile)
        for _j,_k in self.get_ne_tiles(p):
            j = j_s + _j
            k = k_s + _k

            # Collision with anything else ?
            n_jk = self.regcount[j,k]
            for i in self.register[j,k,0:n_jk]:
                p_other = self.sprites[i,IDX_pos]
                r_other = self.sprites[i,IDX_rad]
                #print(i,p,1,p_other,r_other)

                if collision(p,1,p_other,r_other)[1] > 0:
                    return i

        # Not colliding with anything
        return i_VOID

    def get_ne_tiles(self,p):
        '''
            If I am at point p, then return all tiles (including the one I am 
            on) that I should check for possible collisions. 
        '''
        # Get indices of current tile
        i,j = self.pos2grid(p)
        # Get center point of current tile
        c = self.grid2pos[i,j]
        # if diff = [+,+], then I am below the center, and to the right
        # if diff = [-,-], then I am bottom the center, and to the left
        diff = (c <= p)
        bottom = diff[1]
        right = diff[0]
        # N.B. shouldn't need this given current maps!
        #if border_tile(i,j): 
        #    return special
        # 
        return get_tiles(right,bottom)

    def process_vision(self, i):
        '''
            Collision Sensor (1D)
            ---------------------

            What the i-th sprite sees in the environment via its body sensor.

            This refers specifically to IDX_COLIDE and IDX_PROXIMITY.

            Check 
                1) proximity and collisions 
                2) in the world; including both other sprites and terrain tiles. 

            Parameters
            ----------

            i : int
                sprite index

            Returns
            -------
            
            A tuple (vision,thing,type) where 
                vision : float
                    grayscale intensity (in [0,1]) of the resulting collisions 
                thing : Thing 
                    the object that we collided with (None if terrain)
                type : list 
                    the centre point(s) of terrain tile(s) we collided with (empty or None otherwise)
                    None if we are ontop of a terrain tile!
        '''

        s_pos = self.sprites[i,IDX_pos]       # We are currently at this position
        j_s, k_s = self.pos2grid(s_pos)       # We are currently in this tile/square

        if self.terrain[j_s,k_s] > 0: 
            # 2. TERRAIN OVERLAP/DEATH. We are *on* a terrain tile - Instant death!
            print("[World] Instant death for sprite %d, on terrain tile %d,%d" % (i,j_s,k_s))
            self.respawn(i,RWD_DEATH,msg="terrain death")
            return

        # Check collisions with objects in current and neighbouring tiles  
        # From the current point, get the current and three neighboring tiles.
        for _j,_k in self.get_ne_tiles(s_pos):

            j = j_s + _j
            k = k_s + _k

            if self.terrain[j,k] <= 0:
                # 1. NON-TERRAIN. Check for collisions with other objects in this tile instead
                self.body_sensor(i,j,k) 

            else:
                c_pos = self.grid2pos[j,k]

                dist_center_to_wall = dist_point_to_rect3(s_pos,c_pos,TILE_SIZE,TILE_SIZE)

                if dist_center_to_wall < self.sprites[i, IDX_rad]:
                    # 3.A TERRAIN (CLIFF/WATER) COLLISION 
                    #print("[World]: CLIFF/WATER Collision")
                    self.sprites[i,IDX_health] -= max(1, abs(self.sprites[i,IDX_SPEED]) * TERRAIN_DAMAGE)
                    # Slide off/away from the tile N.B. There could be other tile collisions too!    
                    self.sprites[i,IDX_pos] += slide_off(s_pos,self.sprites[i,IDX_SPEED],c_pos)

                elif dist_center_to_wall < OUTER_RADIUS:
                    # 3.B) TERRAIN TILE IN PROXIMITY
                    self.sprites[i,IDX_PROXIMITY] = 1. - (dist_center_to_wall - self.sprites[i,IDX_rad]) / (OUTER_RADIUS - self.sprites[i,IDX_rad]) 


if __name__ == '__main__':

    # TODO this should just be tests

    map_file = "worlds/bugworld/maps/new_2.dat"
    #map_file = "./maps/map_empty.dat"

    if len(sys.argv) > 1:
        map_file = sys.argv[1]

    #tests(map_file[0:-4])
    world = World(map_file[0:-4],"../conf.yml")


