import sys
import os
import math

# Math libraries
import numpy as np

# RL Libraries
import gymnasium as gym
from pettingzoo import ParallelEnv

# Spatial indexing
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt

# Pygame
import pygame

from .utils import rotate, cos_sim, unitv, slide_off
from .graphics import id2rgb, ID_FLAG, ID_ANIMAL, ID_ROCK, ID_PLANT, build_bg_png as build_map, build_image_png, draw_state
from .map_tools import convert_to_tiles
from .config import MAP_DIR, FPS

print("[World] Setting parameters")
from .constants import *

N_SPRITE = 70
N = N_SPRITE - 20  # agent slots go from i_base to N-1; FX slots from N to N_SPRITE-1
D = D_SPRITE

# Rewards
RWD_CHECKPOINT = 5
#RWD_EXISTING = 0.1
RWD_DEATH = -5

ANTENNA_RATIO = 3
SPEAR_RATIO = 2.5
TERRAIN_DAMAGE = 1 # Added factor when hitting a wall or landing on water
PERCENT_INIT_ENERGY = 0.5       # How much of its max energy is a creature born with

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
        self.possible_agents = []
        self.agents = []
        self.active_agents = []

        ## Spaces ## 

        self.action_spaces = {}
        self.observation_spaces = {}

        # pygame state
        self._screen  = None
        self._clock   = None
        self._font    = None

    # required by ParallelEnv API
    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def _init_pygame(self, title, B, decor):
        """Initialize pygame window and burn decor into background. Safe to call multiple times."""

        ## SCREEN ##

        if self._screen is None:
            WIDTH = (B.shape[1]-1) * TILE_SIZE * 2
            HEIGHT = (B.shape[0]-1) * TILE_SIZE * 2
            print("[World] Loaded map")
            pygame.init()
            pygame.display.set_caption(title)
            self._screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self._clock = pygame.time.Clock()
            self._font  = pygame.font.SysFont(None, 24)
            # For storing sprite images (rendering only) -- extra entries for FX sprites
            self.images = [None for _ in range(N_SPRITE + 1)]

        ## BACKGROUND ##

        self.background, _ = build_map(B, grid_lines=False)

        ## BURN DECOR ##

        for sprite in decor:
            rect, img = build_image_png(sprite[IDX_pos], int(sprite[IDX_rad]), int(sprite[IDX_id]), int(sprite[IDX_img]))
            self.background.blit(img, rect)

        # Draw the background on the screen
        self._screen.blit(self.background, [0, 0])
        pygame.display.flip()

    def reset(self, seed=None, options={'map_name' : "new_4"}):
        ''' Reset the environment (state).
        '''

        ## LOAD MAP
        bname_map = options['map_name']
        fname_map = os.path.join(MAP_DIR, bname_map+'.map')
        B = np.genfromtxt(fname_map, dtype=int, delimiter=1, filling_values=0)
        _, self.terrain = convert_to_tiles(B)

        self.agents = []
        self.active_agents = []
        self.t   = 0

        ## GRID REGISTER and GRID COUNT

        # Name register
        self.names = ["" for _ in range(N_SPRITE)]
        # Sprite register for creatures
        self.sprites = np.zeros((N_SPRITE, D_SPRITE), dtype=np.float32)

        # Load sprites (sorts by id, separates decor for burn-in)
        fname_sprites = os.path.join(MAP_DIR, bname_map+'.csv')
        self.i_base, decor = self.load_sprites(fname_sprites)
        print("[World] Loaded %d inanimate sprites (%d decor)" % (self.i_base, len(decor)))

        ## PYGAME STUFF (burn decor into background, display)

        if self.render_mode == "human":
            self._init_pygame(bname_map, B, decor)


        ## PRE-COMPUTATION ##

        # Wall distance field at pixel resolution: for each pixel, exact
        # distance to the nearest wall boundary.
        pixel_mask = np.repeat(np.repeat(self.terrain < 1, TILE_SIZE, axis=0), TILE_SIZE, axis=1)
        self.wall_dist = distance_transform_edt(pixel_mask)

        # Spatial index (rebuilt each step after movement)
        self._tree = None
        self._valid_rows = list(range(self.i_base))

        ## MAIN LOOP ##
        print("[World] Done init")

        observations = {}
        infos        = {}

        return observations, infos

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

        self._update(actions)

        self._observe()

        # Build return dicts
        observations, rewards, terminations, truncations, infos = {}, {}, {}, {}, {}
        for i in self.active_agents:
            observations[i] = self.sprites[i, IDX_OBS].copy()
            rewards[i] = float(self.sprites[i, IDX_RWD])
            terminations[i] = bool(self.sprites[i, IDX_done])
            truncations[i] = False
            infos[i] = {}

        return observations, rewards, terminations, truncations, infos

    def _update(self, actions):
        """ Phase 1: Advance world state:

                s' = f(s,{a})

            Applies all actions, moves sprites, then resolves all
            interactions (terrain death, bumping, spearing, starvation).
            No observations are read here — all state mutations only.
        """
        # Reset per-step state
        self.sprites[self.active_agents, IDX_done] = 0
        self.sprites[self.active_agents, IDX_RWD] = 0

        # Apply actions and move sprites according to dynamics
        for i in self.active_agents:
            self.enact(self.sprites[i], actions[i])

        # Build spatial index of all sprite positions (statics + agents)
        self._valid_rows = list(range(self.i_base)) + self.active_agents
        self._tree = cKDTree(self.sprites[self._valid_rows][:, IDX_pos])

        # Resolve all interactions (state mutations only) -- game logic
        query_r = OUTER_RADIUS + TILE_SIZE
        for i in self.active_agents:
            neighbors = self._tree.query_ball_point(self.sprites[i, IDX_pos], query_r)
            # Check for instant death (inside of cliffs/water)
            if self._resolve_terrain(i):
                continue
            # Check for collisions
            self._resolve_body(i, neighbors)
            # Check for spearing
            self._resolve_combat(i, neighbors)

        # Death check
        for i in self.active_agents:
            if self.sprites[i, IDX_health] <= 1:
                self.respawn(i, RWD_DEATH, msg="starvation death")

        # Energy cost of living
        self.sprites[self.active_agents, IDX_health] -= 0.01

    def _observe(self):
        """ Phase 2: Extract observations from the updated state.

            {o} = g(s')

            All state mutations are complete; sprite positions are final.
        """
        # Reset observation buffers for active agents
        self.sprites[self.active_agents, IDX_COLIDE] = 0
        self.sprites[self.active_agents, IDX_PROXIMITY] = 0

        # Sense the environment from final positions
        query_r = OUTER_RADIUS + TILE_SIZE
        for i in self.active_agents:
            neighbors = self._tree.query_ball_point(self.sprites[i, IDX_pos], query_r)
            # Wall-observations
            self._sense_terrain(i)
            # Touching observations
            self._sense_body(i, neighbors)
            # Antennae observations
            self._sense_antennae(i, neighbors)
            self.do_flag_check(i)

        # Normalize observations
        self.sprites[self.active_agents, IDX_health] = np.clip(
            self.sprites[self.active_agents, IDX_health], -MAX_HEALTH, MAX_HEALTH)
        self.sprites[self.active_agents, IDX_ENERGY] = np.clip(
            self.sprites[self.active_agents, IDX_health] / MAX_HEALTH, 0, 1)
        self.sprites[self.active_agents, IDX_PROXIMITY] = np.clip(
            self.sprites[self.active_agents, IDX_PROXIMITY], 0, 1)

    def render(self):
        if self.render_mode != "human":
            return

        # Quit ?
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                raise SystemExit

        # Draw (pass full array so FX sprites in reserved zone are included)
        self._screen.blit(self.background, [0,0])
        draw_state(self._screen, self.sprites, self.images, self.names)
        pygame.display.flip()
        self._clock.tick(FPS)

    def close(self):
        if self._screen is not None:
            pygame.quit()
            self._screen = None


    def add_agent(self, name=""):
        """ Add an agent to the world. Auto-assigns the agent_id as the first
            free row at or above i_base. The agent_id is the row index in the
            sprites array and the key for all PettingZoo dicts.

            Returns
            -------
            int : the agent_id (row index)
        """
        # Find first free row at or above i_base
        for i in range(self.i_base, N):
            if self.sprites[i, IDX_id] == 0:
                break
        else:
            raise RuntimeError("No free sprite slots")

        agent_id = i

        # PettingZoo registration
        self.possible_agents.append(agent_id)
        self.agents.append(agent_id)
        self.active_agents.append(agent_id)

        self.observation_spaces[agent_id] = gym.spaces.Box(low=0, high=1, shape=(d_S,), dtype=np.float32)
        self.action_spaces[agent_id] = gym.spaces.MultiBinary(d_A)

        # Sprite setup
        self.names[agent_id] = name
        self.sprites[agent_id, IDX_id] = ID_ANIMAL
        self.sprites[agent_id, IDX_rad] = INNER_RADIUS
        self.sprites[agent_id, IDX_img] = agent_id % 7
        self.sprites[agent_id, IDX_unitv] = np.array([0, 1])
        self.sprites[agent_id, IDX_spear0] = rotate(self.sprites[agent_id, IDX_unitv] * self.sprites[agent_id, IDX_rad] * SPEAR_RATIO / 2, 0.0)
        self.sprites[agent_id, IDX_anten1] = rotate(self.sprites[agent_id, IDX_unitv] * self.sprites[agent_id, IDX_rad] * ANTENNA_RATIO, +0.3)
        self.sprites[agent_id, IDX_anten2] = rotate(self.sprites[agent_id, IDX_unitv] * self.sprites[agent_id, IDX_rad] * ANTENNA_RATIO, -0.3)
        self.respawn(agent_id, 0, 0, msg="just init")

        return agent_id

    def del_agent(self, agent_id):
        """ Remove an agent. Zeroes the row and marks it ID_VOID (no compaction). """
        self.sprites[agent_id, :] = 0
        self.names[agent_id] = ""
        self.active_agents.remove(agent_id)
        self.agents.remove(agent_id)
        if agent_id in self.possible_agents:
            self.possible_agents.remove(agent_id)


    def load_sprites(self, fname): 
        '''
            Load inanimate sprites from file.

            Sprites are sorted by id (flags, then rocks, then plants).
            Decor flags (id=ID_FLAG, sid<0) are separated out for background
            burn-in and not stored in the sprite array.


            Parameters
            ----------

            fname : str
                file name (.csv format) with columns as per DISK_INDICES


            Returns
            -------

            (int, list)
                the number of inanimate sprites loaded, and a list of decor
                sprite rows to be burned into the background.

        '''
        # Load data from the file
        try:
            print("[World] Load Sprites ..")
            things = np.atleast_2d(np.loadtxt(fname,delimiter=',',dtype=int))
        except:
            print("[World] Error: ", sys.exc_info()[0])
            print("      > No sprite file found...")
            raise SystemExit

        # Sort by id: flags(-1) first, then rocks(1), then plants(2)
        sort_idx = np.argsort(things[:, IDX_id])
        things = things[sort_idx]

        # Populate sprites, separating decor for background burn-in
        decor = []
        j = 0
        for thing in things:
            if thing[IDX_id] == ID_FLAG and thing[IDX_sid] < 0:
                decor.append(thing)
                continue
            self.sprites[j, DISK_INDICES] = thing[DISK_INDICES]
            # Verify sprite is not on a wall tile
            r, c = self.pos2grid(self.sprites[j, IDX_pos])
            assert self.terrain[r, c] == 0
            j += 1

        return j, decor

    def do_flag_check(self,i):

        # This is the index of the flagged object we're chasing
        i_target = int(self.sprites[i,IDX_tid])
        # Check which way we're pointing
        flag_angle = cos_sim(self.sprites[i,IDX_unitv],self.sprites[i,IDX_pos] - self.sprites[i_target,IDX_pos]) 
        self.sprites[i,IDX_COMPASS] = flag_angle * -1*(flag_angle <= self.sprites[i,IDX_COMPASS])


    def respawn(self, i, rwd_T=RWD_DEATH, done=1, msg=""):
        self.sprites[i,IDX_health] = MAX_HEALTH * PERCENT_INIT_ENERGY
        self.sprites[i,IDX_RWD] += rwd_T
        self.sprites[i,IDX_done] = done
        # Choose a random nest-position to start at (nests are at flags with sub-id of 0)
        nest_i = int(np.random.choice(np.where(self.sprites[0:self.i_base, IDX_sid] == 0)[0]))
        self.sprites[i,IDX_pos] = self.sprites[nest_i, IDX_pos]
        self.sprites[i,IDX_unitv] = unitv(rotate(self.sprites[i,IDX_unitv],np.random.randn()*np.radians(360)))
        # Start from scratch
        self.sprites[i,IDX_speed] = 0
        # Choose a random first flag
        self.sprites[i,IDX_tid] = np.random.choice(np.where(self.sprites[0:self.i_base, IDX_sid] == 1)[0])
        # Death and rebirth; increment global score and respawn
        if len(msg) > 10000:
            # TODO create a death animation / husk sprite.
            print("[World] sprite[%d] respawn @ %s [%s] (inest=%d): %s" % (i,str(self.sprites[i,IDX_pos]),str(self.sprites[nest_i,IDX_pos]),nest_i,msg))

    def _resolve_combat(self, i, neighbors):
        """ Phase 1: Resolve spear combat (eating, checkpoints, fighting). """
        spear_pos = self.sprites[i, IDX_pos] + self.sprites[i, IDX_spear0]
        i_victim = self._point_hit_from(spear_pos, neighbors)

        # Spearing nothing (or terrain — no combat effect)
        if i_victim is None:
            return

        # Speared the target flag — checkpoint
        if i_victim == int(self.sprites[i, IDX_tid]):
            self.sprites[i, IDX_RWD] += RWD_CHECKPOINT
            self.sprites[i, IDX_tid] = self._next_flag(i)
            # this means, create flag glitter 
            self.sprites[i, IDX_glitter] += 100
            return

        # Cliff or rock — no effect
        if int(self.sprites[i_victim, IDX_id]) == ID_ROCK:
            return

        # Non-target flag — no effect
        if int(self.sprites[i_victim, IDX_id]) == ID_FLAG:
            return

        # Only animals can spear further
        if self.sprites[i, IDX_id] != ID_ANIMAL:
            return

        id_victim = int(self.sprites[i_victim, IDX_id])
        if id_victim == ID_PLANT:
            self.sprites[i, IDX_health] += BITE_SIZE
            self.sprites[i_victim, IDX_health] -= BITE_SIZE
            # this means, create plant splatter 
            self.sprites[i_victim, IDX_damage] += 100 
        elif id_victim == ID_ANIMAL:
            self.sprites[i_victim, IDX_health] -= BITE_SIZE
            # this means, create bug splatter 
            self.sprites[i_victim, IDX_damage] += 100
        #elif id_victim == ID_FLAG:
        #    pass
        else:
            print("[World]._resolve_combat ---- unexpected victim id:", id_victim)

    def _sense_antennae(self, i, neighbors):
        """ Phase 2: Read color at the two antenna tips.

            One neighborhood query covers both antennae.
        """
        pos = self.sprites[i, IDX_pos]
        self.sprites[i, IDX_PROBE1] = self._pixel_from(
            pos + self.sprites[i, IDX_anten1], neighbors)
        self.sprites[i, IDX_PROBE2] = self._pixel_from(
            pos + self.sprites[i, IDX_anten2], neighbors)

    def _next_flag(self, i):
        ''' Target next flag.

            Assume the i-th sprite has just touched its current flag (the i_target-th sprite, of order o_flag). 
            We want to go to the next flag, which has the order o_flag+1. Except !

            Returns
            -------

            The index of the next flag. 
        '''
        # Index of flagged object for i-th sprite
        i_target = int(self.sprites[i,IDX_tid])
        # The 'order' of that flag 
        o_flag = self.sprites[i_target,IDX_sid]
        # The final flag 
        o_last = max(self.sprites[:,IDX_sid]) 
        # Start afresh if this is the last one
        if o_flag >= o_last:
            o_flag = 0
        else:
            o_flag += 1
        # Selection
        selection = np.where(self.sprites[0:self.i_base, IDX_sid] == o_flag)[0]
        return int(np.random.choice(selection))

    def enact(self, sprite, actions):
        ''' Carry out actions for this sprite.

            Recall, actions are: 
            * sprite[IDX_RANGLE] # turn right
            * sprite[IDX_LANGLE] # turn left
            # sprite[IDX_FIRE]   # FUTURE/not-yet-implemented
            
        # TODO this function could be done simultaneously for all sprites (much faster) as matrix operations.
        '''

        # Dynamics
        MAX_SPEED = 10          # Maximum speed in pixels/tick
        TURN_SPEED = 0.10       # radians per frame
        ACCEL = 0.2             # rate of speed increase
        BRAKE_DECEL = 0.8       # stop faster when no input

        sprite[IDX_ACTIONS] = actions

        L = sprite[IDX_LANGLE]
        R = sprite[IDX_RANGLE]

        power = L * 0.5 + R * 0.5
        target_speed = power * MAX_SPEED

        turn_delta = (R - L) * TURN_SPEED

        # Apply turning (left/right)
        if turn_delta != 0:
            sprite[IDX_unitv] = unitv(rotate(sprite[IDX_unitv],turn_delta))
            sprite[IDX_spear0] = rotate(sprite[IDX_unitv] * sprite[IDX_rad]*SPEAR_RATIO,-0.0) # antenna right pos
            sprite[IDX_anten1] = rotate(sprite[IDX_unitv] * sprite[IDX_rad]*ANTENNA_RATIO,+0.3) # antenna left pos
            sprite[IDX_anten2] = rotate(sprite[IDX_unitv] * sprite[IDX_rad]*ANTENNA_RATIO,-0.3) # antenna right pos

        # Get current state
        #angle = sprite[ IDX_angle]
        speed = sprite[ IDX_speed]   
        #position = sprite[ IDX_pos]

        # Smooth acceleration toward target speed
        if abs(speed - target_speed) < ACCEL:
            speed = target_speed
        elif speed < target_speed:
            speed += ACCEL
        else:
            speed -= BRAKE_DECEL

        # Limit speed
        sprite[IDX_speed] = np.clip(speed,0.0,MAX_SPEED)

        # Update self-observation
        sprite[IDX_SPEED] = sprite[IDX_speed]/MAX_SPEED
        # Update position
        sprite[IDX_pos] += (sprite[IDX_unitv] * sprite[IDX_speed])


    def pos2grid(self, p):
        ''' Convert (x,y)-point to (j,k)-grid reference, clamped to bounds. '''
        j = max(0, min(int(p[1]) // TILE_SIZE, self.terrain.shape[0] - 1))
        k = max(0, min(int(p[0]) // TILE_SIZE, self.terrain.shape[1] - 1))
        return j, k

    def _resolve_terrain(self, i):
        """ Phase 1: On-wall = instant death. """
        j, k = self.pos2grid(self.sprites[i, IDX_pos])
        if self.terrain[j, k] >= 1:
            # Splatter at the death location before respawn teleports the sprite
            self.sprites[i,IDX_health] = -1000
            self.sprites[i,IDX_damage] += 100
            return True
        return False

    def _sense_terrain(self, i):
        """ Phase 2: Sense proximity to walls via precomputed distance field. """
        pos = self.sprites[i, IDX_pos]
        x = max(0, min(int(pos[0]), self.wall_dist.shape[1] - 1))
        y = max(0, min(int(pos[1]), self.wall_dist.shape[0] - 1))
        d = self.wall_dist[y, x]
        rad = float(self.sprites[i, IDX_rad])
        if d < OUTER_RADIUS:
            prox = 1.0 - max(0, d - rad) / (OUTER_RADIUS - rad)
            self.sprites[i, IDX_PROXIMITY] = max(
                float(self.sprites[i, IDX_PROXIMITY]), prox)

    def _resolve_body(self, i, neighbors):
        """ Phase 1: Resolve physical collisions with other sprites (bumping). """
        pos = self.sprites[i, IDX_pos]
        rad = float(self.sprites[i, IDX_rad])
        dist_between_rings = OUTER_RADIUS - rad
        for idx in neighbors:
            i_other = self._valid_rows[idx]
            if i_other == i or self.sprites[i_other, IDX_id] == ID_FLAG:
                # ignore flags, cannot bump into them
                continue
            op = self.sprites[i_other, IDX_pos]
            dx = float(pos[0]) - float(op[0])
            dy = float(pos[1]) - float(op[1])
            d = math.sqrt(dx*dx + dy*dy)
            ov = OUTER_RADIUS + float(self.sprites[i_other, IDX_rad]) - d
            if ov > dist_between_rings:
                self.bumping(i, i_other)

    def _sense_body(self, i, neighbors):
        """ Phase 2: Observe proximity and collision with other sprites. """
        pos = self.sprites[i, IDX_pos]
        rad = float(self.sprites[i, IDX_rad])
        dist_between_rings = OUTER_RADIUS - rad
        for idx in neighbors:
            i_other = self._valid_rows[idx]
            if i_other == i or self.sprites[i_other, IDX_id] == ID_FLAG:
                # ignore flags -- cannot sense them
                continue
            op = self.sprites[i_other, IDX_pos]
            dx = float(pos[0]) - float(op[0])
            dy = float(pos[1]) - float(op[1])
            d = math.sqrt(dx*dx + dy*dy)
            ov = OUTER_RADIUS + float(self.sprites[i_other, IDX_rad]) - d
            if ov > 0:
                self.sprites[i, IDX_PROXIMITY] += ov / dist_between_rings
                if ov > dist_between_rings:
                    self.sprites[i, IDX_COLIDE] = 1

    def _point_hit_from(self, p, neighbors):
        """ What does point p collide with?

            Returns the sprite row index, or None if p hits terrain or nothing.
        """
        # Check terrain collision
        j, k = self.pos2grid(p)
        if self.terrain[j, k] >= 1:
            return None
        # Check neighbour collision (assume neighbours are rock, plant or animal).
        for idx in neighbors:
            i_other = self._valid_rows[idx]
            op = self.sprites[i_other, IDX_pos]
            dx = float(p[0]) - float(op[0])
            dy = float(p[1]) - float(op[1])
            r = float(self.sprites[i_other, IDX_rad]) + 1
            if dx*dx + dy*dy < r*r:
                return i_other
        # Nothing ...
        return None

    def _pixel_from(self, p, neighbor_idxs):
        """ Color seen at point p, given a pre-queried neighbor list. """
        j, k = self.pos2grid(p)
        if self.terrain[j, k] >= 1:
            return id2rgb[ID_ROCK]
        for idx in neighbor_idxs:
            i_other = self._valid_rows[idx]
            if self.sprites[i_other, IDX_id] == ID_FLAG:
                # ignore flags -- cannot sense them
                continue
            op = self.sprites[i_other, IDX_pos]
            dx = float(p[0]) - float(op[0])
            dy = float(p[1]) - float(op[1])
            r = float(self.sprites[i_other, IDX_rad]) + 1
            if dx*dx + dy*dy < r*r:
                return id2rgb[int(self.sprites[i_other, IDX_id])]
        return id2rgb[0]


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
        # Bugs hurt themselves crashing into anything 
        self.sprites[i,IDX_health] -= BUMP_SIZE * abs(self.sprites[i,IDX_speed])
        self.sprites[i,IDX_damage] += 100

        # They also hurt what/whoever they are crashing into
        if self.sprites[i_victim,IDX_id] == ID_ANIMAL:
            self.sprites[i_victim,IDX_health] -= BUMP_SIZE # * abs(self.sprites[i_victim,IDX_speed])
            self.sprites[i_victim,IDX_damage] += 100

        # Whatever it is, the attacker slides off the victim
        self.sprites[i,IDX_pos] += slide_off(self.sprites[i,IDX_pos],self.sprites[i,IDX_speed],self.sprites[i_victim,IDX_pos])



