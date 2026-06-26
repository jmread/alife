import sys
import os

# Math libraries
import numpy as np

# RL Libraries
import gymnasium as gym
from pettingzoo import ParallelEnv

# Pygame
import pygame

# For networking
from .utils import get_centres, rotate, cos_sim, get_tiles, unitv, overlap, slide_off, collision, dist_point_to_rect3
from .graphics import id2rgb, ID_FLAG, ID_VOID, ID_ANIMAL, ID_ROCK, ID_PLANT, build_bg_png as build_map, draw_state
from config import MAP_DIR

print("[World] Setting parameters")
from .constants import *

FPS = 6
N = N_SPRITE
D = D_SPRITE
print("      > Obs indices: %d" % D_SPRITE)
print("      > Max sprites: %d" % N_SPRITE)

labels = ['--' for _ in range(D_SPRITE)]
labels[IDX_id] = 'id'
labels[IDX_x] = 'x'
labels[IDX_y] = 'y'
labels[IDX_vx] = 'vx'
labels[IDX_vy] = 'vy'
labels[IDX_rad] = 'rad'
labels[IDX_img] = 'sid'
labels[IDX_health] = '[+]'
labels[IDX_COLIDE] = ' o '
#labels[IDX_PROXIMITY] = '(o)'
labels[IDX_nesti] = 'nst'
labels[IDX_flagi] = 'flg'
#labels[IDX_PROBE1] = ['L-R', 'L-G', 'L-B']
#labels[IDX_PROBE2] = ['R-R', 'R-G', 'R-B']
labels[IDX_ENERGY] = 'nrg'
labels[IDX_speed] = '|v|'
labels[IDX_RWD] = 'rwd'


i_VOID = -2     # emptyness
i_CLIFF = -1     # cliff/rock

# Rewards
RWD_CHECKPOINT = 5
#RWD_EXISTING = 0.1
RWD_DEATH = -5

ANTENNA_RATIO = 3
SPEAR_RATIO = 2.5
TERRAIN_DAMAGE = 1 # Added factor when hitting a wall or landing on water
PERCENT_INIT_ENERGY = 0.5       # How much of its max energy is a creature born with

def print_sprites(sprite_array,j_list,labels, DEBUG=False): 
    if not DEBUG:
        return
    print("---------- SPRITES -------------")
    print('___|' + '|'.join(["%5s " % labels[j] for j in j_list]))
    for i in range(len(sprite_array)): 
        print(("%2d |" % i) + '|'.join(["%5d " % int(sprite_array[i,j]) for j in j_list]))
    print("--------------------------------")

class World(ParallelEnv):
    """ A World.

        Defined by a numpy array of sprites, and some dynamics. 

        Parameters
        ----------

        bname_map : str 
            the filename with the map data (tiles) *not including the extension*, e.g., 'map3'
            where map3.dat will hold the map data, and map3.csv will hold the sprite data. 
    """
    env_id = "alife-v1"

    def __init__(self, render_mode: str | None = None):
        super().__init__()

        self.render_mode = render_mode
        self.possible_agents = [f"agent_{i}" for i in range(N)]

        ## Spaces ## 

        self.action_spaces = {
            a: gym.spaces.MultiBinary(2)
            for a in self.possible_agents
        }
        self.observation_spaces = {
            a: gym.spaces.Box(low=0, high=1, shape=(d_S,), dtype=np.float32)
            for a in self.possible_agents
        }

        # pygame state
        self._screen  = None
        self._clock   = None
        self._font    = None

    # required by ParallelEnv API
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def _init_pygame(self, bname_map):
        """Initialize pygame window. Safe to call multiple times."""
        if self._screen is not None:
            return

        ## MAP ## 

        fname_map = os.path.join(MAP_DIR, bname_map+'.map')

        # Load map and get its dimensions
        B = np.genfromtxt(fname_map, dtype=int, delimiter=1, filling_values=0)
        WIDTH = (B.shape[1]-1) * TILE_SIZE * 2
        HEIGHT = (B.shape[0]-1) * TILE_SIZE * 2
        print("[World] Loaded map")

        ## SCREEN ##

        pygame.init()
        pygame.display.set_caption("Bug World [map: %s]" % fname_map)
        self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self._clock = pygame.time.Clock()
        self._font  = pygame.font.SysFont(None, 24)

        ## GRAPHICS ## 

        # Render the map
        self.background, self.terrain = build_map(B, grid_lines=False)

        # Draw the background on the screen
        self._screen.blit(self.background, [0, 0])
        pygame.display.flip()

        # For storing sprite images
        self.images = [None for _ in range(N+1)]

    def reset(self, seed=None, options={'map_name' : "new_4"}):

        ## PYGAME STUFF

        if self.render_mode == "human":
            bname_map = options['map_name']
            self._init_pygame(bname_map)

        N = len(self.possible_agents)
        self.agents     = self.possible_agents[:]
        self.t   = 0

        ## GRID REGISTER and GRID COUNT 

        # Name register
        self.names = ["" for i in range(N)]
        # Sprite register for creatures 
        self.sprites = np.zeros((N,D_SPRITE), dtype=np.float32)
        # Grid register for everything
        self.register = np.zeros((*self.terrain.shape,MAX_GRID_DETECTION),int) 
        self.regbase = np.zeros_like(self.terrain)        # count of non-animals (fixed, once the map is loaded)
        self.regcount = np.zeros_like(self.terrain)       # count of animals

        # Sprite and grid register for rocks and plants (and nest and flag)
        fname_sprites = os.path.join(MAP_DIR, bname_map+'.csv')
        self.i_base = self.load_sprites(fname_sprites)
        self.n_sprites = self.i_base
        print("[World] Loaded %d inanimate sprites" % self.i_base)
        print_sprites(self.sprites,DEBUG_INDICES,labels, DEBUG=False)

        print("[World] Set special sprites")
        self.sprites[i_CLIFF,IDX_id] = ID_ROCK

        ## PRE-COMPUTATION ##

        # Such that [x,y] = grid2pos[i,j] gives the centre position of the grid at i-th row, j-th column
        self.grid2pos = get_centres(*self.terrain.shape,TILE_SIZE)

        ## MAIN LOOP ##
        print("[World] Done init")

        observations = {a: None for a in self.agents}
        for i, k in enumerate(self.sprites[self.i_base:self.n_sprites,IDX_cid]):
            observations[int(k)] = self.sprites[self.i_base+i,IDX_OBS].astype(np.float32)
        infos        = {a: {} for a in self.agents}

        return observations, infos

#    def get_info(self):
#        ''' Need to make available this information on the environment to any client. 
#        '''
#        #TODO might be able to get this information from server.py without requiring this function?
#        return {
#            'basename' : self.env_id,
#            'd_S' : int(np.prod(self.observation_space.shape)),
#            'd_A' : int(np.prod(self.action_space.shape)),
#            'space_S' : serialize_space(self.observation_space),
#            'space_A' : serialize_space(self.action_space),
#        }

    def step(self, actions):
        '''
            s[t+1], r[t] ~ p( . | s[t], a[t] )

            Parameters
            ----------

            actions : dict(int, np.array)
                the index of an agent, and its desired d_A-dimensional action

            Returns
            -------

            observations : dict[int, np.array]
                the d_S-dimensional observations
            rewards : dict[int, float]
                the rewards
            terminations : dict[int, bool]
                which agents have finished
                not used (episodes are eternal)
            truncations : dict[int, bool]
                which agents were cut short in their episode
                not used (episodes are eternal)
            info : dict[int, dict]
                not used 
            
        ''' 
        self.t += 1

        rewards, terminations, truncations, infos = {}, {}, {}, {}

        # Stop not-responding window
        # self.handle_events()

        # -------------------------------------------------------------
        # Reset, cleanup from last time
        # -------------------------------------------------------------
        self.sprites[self.i_base:self.n_sprites,IDX_done] = 0 
        self.sprites[self.i_base:self.n_sprites,IDX_RWD] = 0 
        # Reset reg-counts and Register all sprites
        self.regcount[:] = self.regbase

        # -------------------------------------------------------------
        # Set actions, and check what's left over
        # -------------------------------------------------------------
        for i in range(self.i_base,self.n_sprites):
            cid = int(self.sprites[i,IDX_cid])
            self.sprites[i,IDX_ACTIONS] = actions[cid]

        # -------------------------------------------------------------
        # Environment deals with Creature actions
        # -------------------------------------------------------------

        # Do actions, record movements
        for i in range(self.i_base,self.n_sprites):
            # Action
            self.enact(i)
            # Register
            j,k = self.pos2grid(self.sprites[i,IDX_pos])
            c = self.regcount[j,k]
            self.register[j,k,c] = i
            self.regcount[j,k] += 1

        # Reset first
        self.sprites[:,IDX_COLIDE] = 0 
        self.sprites[:,IDX_PROXIMITY] = 0 

        # Live (individual calculations, collisions, etc.)
        for i in range(self.i_base,self.n_sprites):
            self.do_vision_check(i)
            self.do_flag_check(i)
            # health check
            if self.sprites[i,IDX_health] <= 1:
                self.respawn(i,RWD_DEATH,msg="starvation death")

        # Moving burns energy according to size and speed and the angle of turn
        self.sprites[self.i_base:self.n_sprites,IDX_health] -= 0.01

        # -------------------------------------------------------------
        # Extract an observation from the full state space
        # o[t] = phi(s[t])
        # -------------------------------------------------------------

        # Normalization of energy levels
        self.sprites[self.i_base:self.n_sprites,IDX_health] = np.clip(self.sprites[self.i_base:self.n_sprites,IDX_health],-MAX_HEALTH,MAX_HEALTH)
        self.sprites[self.i_base:self.n_sprites,IDX_ENERGY] = np.clip(self.sprites[self.i_base:self.n_sprites,IDX_health]/MAX_HEALTH,0,1)
        # Clip proximity sensor
        self.sprites[self.i_base:self.n_sprites,IDX_PROXIMITY] = np.clip(self.sprites[self.i_base:self.n_sprites,IDX_PROXIMITY],0,1)

        print_sprites(self.sprites,DEBUG_INDICES,labels, DEBUG=False)

        # -------------------------------------------------------------
        # Environment is observed (by the Creatures)
        # return o[t], r[t] --> agent
        # -------------------------------------------------------------

        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}

        for i, k in enumerate(self.sprites[self.i_base:self.n_sprites,IDX_cid]):
            #print(int(k), i, self.sprites[self.i_base+i,IDX_OBS])
            observations[int(k)] = self.sprites[self.i_base+i,IDX_OBS]
            v = observations[int(k)]
            if not (np.all((observations[int(k)] >= 0) & (observations[int(k)] <= 1))):
                   print("\n\n\n\n\n\n\n\n\n\n\n\nNot all observations are between 0 and 1 inclusive\n", observations)
            rewards[int(k)] = float(self.sprites[self.i_base+i,IDX_RWD])
            terminations[int(k)] = bool(self.sprites[self.i_base+i,IDX_done]) 
            truncations[int(k)] = False
            infos[int(k)] = {}

        return observations, rewards, terminations, truncations, infos

    def render(self):
        if self.render_mode != "human":
            return

        # Quit ?
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                raise SystemExit

        # Draw

        #print_sprites(self.sprites[self.i_base:self.n_sprites],DEBUG_INDICES,labels, DEBUG=False)
        #self._screen.fill((30, 30, 30))
        self._screen.blit(self.background, [0,0]) 
        draw_state(self._screen, self.sprites[0:self.n_sprites], self.images, self.names)
        pygame.display.flip()
        self._clock.tick(FPS)

    def close(self):
        if self._screen is not None:
            pygame.quit()
            self._screen = None


    def add_agent(self, c_id, name):
        """ Create an agent entry, with sprite id 'c_id', and name (or, any additional descriptor) 'name'.  

        We really must insist that there be no existing 

        Parameters
        ----------
        c_id : int
            agent id - if such as id is already in the world, you might complain, but this shouldn't happen
            
        name : str
            the description of the agent

        """
        agent_id = int(c_id)
        if agent_id in self.agents:
            return  # already active, do nothing

        # PettingZoo stuff

        self.possible_agents.append(agent_id)
        self.agents.append(agent_id)

        self.observation_spaces[agent_id] =  gym.spaces.Box(low=0, high=1, shape=(d_S,), dtype=np.float32)
        self.action_spaces[agent_id] = gym.spaces.MultiBinary(2)

        # My internals

        i = self.n_sprites

        # the space we have chosen to put this must be available
        if self.sprites[i,IDX_cid] > 0:
            print_sprites(self.sprites,DEBUG_INDICES,labels,DEBUG=True)
            print("i=",self.n_sprites)
            exit(1)

        # must have space in the sprite array for this
        assert(i+1 < len(self.sprites))

        # @todo -- check first from the database, if there is some previous information on pos/energy/points/etc.
        #print("TODO Query database")
        self.names[i] = name
        self.sprites[i, IDX_id] = ID_ANIMAL
        self.sprites[i, IDX_rad] = INNER_RADIUS
        self.sprites[i, IDX_img] = c_id % 7
        self.sprites[i, IDX_cid] = c_id
        self.sprites[i, IDX_unitv] = np.array([0,1])
        # TODO, N.B. always rotating by the same amounts, so we could store the rotation matrix M for speed
        self.sprites[i, IDX_spear0] = rotate(self.sprites[i, IDX_unitv] * self.sprites[i,IDX_rad]*SPEAR_RATIO/2,0.0) # antenna right pos
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
        # decount the sprite
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
            # We must register at least the things here (the bugs will be re-registered during the loop)
            j,k = self.pos2grid(self.sprites[i,IDX_pos])
            assert(self.terrain[j,k] == 0)
            # Register for collision detection
            c = self.regbase[j,k]
            self.register[j,k,c] = i
            self.regbase[j,k] += 1

        # Set the end of the inanimate objects
        return len(things)

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
        # Choose a random nest-position to start at
        nest_i = int(np.random.choice(np.where((self.sprites[:, IDX_id] == ID_FLAG) & (self.sprites[:, IDX_flg] == 0))[0]))
        self.sprites[i,IDX_pos] = self.sprites[nest_i, IDX_pos]
        self.sprites[i,IDX_unitv] = unitv(rotate(self.sprites[i,IDX_unitv],np.random.randn()*np.radians(360)))
        # Start from scratch
        self.sprites[i,IDX_speed] = 0
        # Choose a random first flag
        self.sprites[i,IDX_flagi] = np.random.choice(np.where(self.sprites[:, IDX_flg] == 1)[0])
        # Death and rebirth; increment global score and respawn
        print("[World] sprite[%d] respawn @ %s [%s] (inest=%d): %s" % (i,str(self.sprites[i,IDX_pos]),str(self.sprites[nest_i,IDX_pos]),nest_i,msg))

    def do_vision_check(self, i):
        """
            Process vision (collisions with terrain/other objects)
        """

        # ... then process
        self.process_vision(i)

        self.sprites[i,IDX_PROBE1] = self.get_pixel(self.sprites[i,IDX_pos] + self.sprites[i,IDX_anten1])
        self.sprites[i,IDX_PROBE2] = self.get_pixel(self.sprites[i,IDX_pos] + self.sprites[i,IDX_anten2])

        self.spearing(i,self.point_collision(self.sprites[i,IDX_pos] + self.sprites[i,IDX_spear0]))

    def _next_flag(self, i):
        ''' Target next flag.

            Assume the i-th sprite has just touched its current flag (the i_flag-th sprite, of order o_flag). 
            We want to go to the next flag, which has the order o_flag+1. Except !

            Returns
            -------

            The index of the next flag. 
        '''
        # Index of flagged object for i-th sprite
        i_flag = int(self.sprites[i,IDX_flagi])
        # The 'order' of that flag 
        o_flag = self.sprites[i_flag,IDX_flg]
        # The final flag 
        o_last = max(self.sprites[:,IDX_flg]) 
        # Start afresh if this is the last one
        if o_flag >= o_last:
            o_flag = 0
        else:
            o_flag += 1
        # Selection
        selection = np.where(self.sprites[0:self.i_base, IDX_flg] == o_flag)[0]
        return int(np.random.choice(selection))

    def enact(self, i):
        ''' Carry out actions for the i-th sprite.

            Recall, actions are: 
            * self.sprites[i,IDX_RANGLE] # turn right
            * self.sprites[i,IDX_LANGLE] # turn left
            # self.sprites[i,IDX_FIRE]   # FUTURE/not-yet-implemented
            
        # TODO this function could be done simultaneously for all sprites (much faster)
        '''

        L = self.sprites[i,IDX_LANGLE]
        R = self.sprites[i,IDX_RANGLE]

        power = L * 0.5 + R * 0.5
        target_speed = power * MAX_SPEED

        turn_delta = (R - L) * TURN_SPEED

        # Apply turning (left/right)
        if turn_delta != 0:
            self.sprites[i,IDX_unitv] = unitv(rotate(self.sprites[i,IDX_unitv],turn_delta))
            self.sprites[i,IDX_spear0] = rotate(self.sprites[i,IDX_unitv] * self.sprites[i,IDX_rad]*SPEAR_RATIO,-0.0) # antenna right pos
            self.sprites[i,IDX_anten1] = rotate(self.sprites[i,IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,+0.3) # antenna left pos
            self.sprites[i,IDX_anten2] = rotate(self.sprites[i,IDX_unitv] * self.sprites[i,IDX_rad]*ANTENNA_RATIO,-0.3) # antenna right pos

        # Get current state
        #angle = self.sprites[i, IDX_angle]
        speed = self.sprites[i, IDX_speed]   
        #position = self.sprites[i, IDX_pos]

        # Smooth acceleration toward target speed
        if abs(speed - target_speed) < ACCEL:
            speed = target_speed
        elif speed < target_speed:
            speed += ACCEL
        else:
            speed -= BRAKE_DECEL

        # Limit speed
        self.sprites[i,IDX_speed] = np.clip(speed,0.0,MAX_SPEED)

        # Update self-observation
        self.sprites[i,IDX_SPEED] = self.sprites[i,IDX_speed]/MAX_SPEED
        # Update position
        self.sprites[i,IDX_pos] += (self.sprites[i,IDX_unitv] * self.sprites[i,IDX_speed])


    def pos2grid(self,p):
        ''' Convert (x,y)-point to (j,k)-grid reference ''' 
        x, y = p #np.clip(p,[0,0],self.terrain.shape * TILE_SIZE)
        j = np.floor(y / TILE_SIZE).astype(int)
        k = np.floor(x / TILE_SIZE).astype(int)
        return (j, k)

    def body_sensor(self, i, j, k): 
        ''' Sprite-sprite body collisions (wrt i-th sprite). 

            Set IDX_COLIDE and IDX_PROXIMITY.

            Assume: centre point, 
                inner (rad)    'touch range' <=> the actual body delimiter
                OUTER_RADIUS   'hearing range' <=> a proximity sensor

            Paramemters
            -----------

            i, j, k : sprite i at tile (j,k)
                (these are given together for efficiency reasons)

        '''

        # Check all sprites in the register ...
        c = self.regcount[j,k]
        for i_other in self.register[j,k,0:c]:

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
        
        if self.sprites[i_victim,IDX_id] >= ID_VOID:   
            # Bumps into something
            self.sprites[i,IDX_health] -= BUMP_SIZE * abs(self.sprites[i,IDX_speed])
        #elif i_victim == self.sprites[i,IDX_flagi]:   
        #    # Runs over the flag
        #    self.sprites[i,IDX_RWD] += RWD_CHECKPOINT
        #    self.sprites[i,IDX_flagi] = self._next_flag(i)
        else:
            # FUTURE: Could have some terrain-effect here (when bug is over a certain tile),
            #         e.g., speed reduction, some kind of healing, ...
            return

        # Other bugs can be victims too

        if self.sprites[i_victim,IDX_id] == ID_ANIMAL:
            self.sprites[i_victim,IDX_health] -= BUMP_SIZE # * abs(self.sprites[i_victim,IDX_speed])

        # The attacker slides off the victim

        self.sprites[i,IDX_pos] += slide_off(self.sprites[i,IDX_pos],self.sprites[i,IDX_speed],self.sprites[i_victim,IDX_pos])

    def spearing(self, i, i_victim): 
        '''
            Sprite i spears object i_.

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
            self.sprites[i,IDX_flagi] = self._next_flag(i)
            self.sprites[i,IDX_damage] = -80
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
            self.sprites[i_victim,IDX_damage] = -40
        # Bugs hurt each other in fights
        elif self.sprites[i_victim,IDX_id] == ID_ANIMAL:
            self.sprites[i_victim,IDX_health] -= BITE_SIZE
            self.sprites[i_victim,IDX_damage] = -40
        # I don't know what happened here
        elif self.sprites[i_victim,IDX_id] == ID_FLAG:
            #print("[World].spearing ---- just spearing invisible stuff (nest? someone else's flag?); ignore" )
            pass 
        else:
            print("[World].spearing ---- wtf (probably the victim is someone else's flag?", self.sprites[i,IDX_id], self.sprites[i_victim,IDX_id], i, i_victim)
            exit(1)


    def get_pixel(self, p): 
        '''
        Point p is a single-pixel eye (in RGB color), what does it see?


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
        ''' Check if point p is colliding with any sprite or cliff. 

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

        # Cliff/water collision?
        j_s, k_s = self.pos2grid(p) 
        if self.terrain[j_s,k_s] >= 1: 
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

        if self.terrain[j_s,k_s] >= 1: 
            # 2. WATER OVERLAP/DEATH. We are *on* a terrain tile - Instant death!
            print("[World] Instant death for sprite %d, on terrain tile %d,%d" % (i,j_s,k_s))
            self.respawn(i,RWD_DEATH,msg="terrain death")
            return

        # Check collisions with objects in current and neighbouring tiles  
        # From the current point, get the current and three neighboring tiles.
        for _j,_k in self.get_ne_tiles(s_pos):

            j = j_s + _j
            k = k_s + _k

            if self.terrain[j,k] <= 0:
                # 1. NON-WATER. Check for collisions with other objects in this tile instead
                self.body_sensor(i,j,k) 

            else:
                c_pos = self.grid2pos[j,k]

                dist_center_to_wall = dist_point_to_rect3(s_pos,c_pos,TILE_SIZE,TILE_SIZE)

                if dist_center_to_wall < self.sprites[i, IDX_rad]:
                    # 3.A TERRAIN (CLIFF/WATER) COLLISION 
                    #print("[World]: CLIFF/WATER Collision")
                    self.sprites[i,IDX_health] -= max(1, abs(self.sprites[i,IDX_speed]) * TERRAIN_DAMAGE)
                    # Slide off/away from the tile N.B. There could be other tile collisions too!    
                    self.sprites[i,IDX_pos] += slide_off(s_pos,self.sprites[i,IDX_speed],c_pos)

                elif dist_center_to_wall < OUTER_RADIUS:
                    # 3.B) TERRAIN TILE IN PROXIMITY
                    self.sprites[i,IDX_PROXIMITY] = 1. - (dist_center_to_wall - self.sprites[i,IDX_rad]) / (OUTER_RADIUS - self.sprites[i,IDX_rad]) 



