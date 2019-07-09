import pygame
from pygame.locals import *

from utils import *
from graphics import build_image_png as build_image, build_image_bank, build_splatter_img
from graphics import id2rgb, COLOR_BLACK, COLOR_WHITE#, COLOR_RED, COLOR_MAGENTA
from graphics import draw_banner
from agents.spaces import ContinuousBugSpace, DiscreteBugSpace # the space of the environment (for the agent)
np.set_printoptions(precision=4)

# Types of Sprites/Things/Objects
ID_VOID = 0
ID_ROCK = 1
ID_MISC = 2
ID_PLANT = 3
ID_ANIMAL = 4

# Inputs (state space)
IDX_COLIDE = [0,1,2]
IDX_PROBE1 = [3,4,5]
IDX_PROBE2 = [6,7,8]
IDX_ENERGY = 9
IDX_FLAG = 10
N_INPUTS = 11  

# Outputs (action space)
IDX_ANGLE = 0
IDX_SPEED = 1
N_OUTPUTS = 2
action_space = ContinuousBugSpace(np.array([-np.pi/4., -5.]), np.array([np.pi/4.,10.]))

# Load game constants

import yaml
def get_conf(filename='conf.yml',section='world'):
    return yaml.load(open(filename))[section]

cfg = get_conf(filename='conf.yml',section='objects')
TERRAIN_DAMAGE = cfg['terrain_damage'] # Added factor when hitting a wall or landing on water
BOUNCE_DAMAGE = cfg['bounce_damage']   # Multiplied factor when hitting a friend
FLIGHT_SPEED = cfg['flight_speed']     # After this speed, a creature takes flight
FLIGHT_BOOST = cfg['flight_boost']     # Speed is multiplied by this factor if in flight
DIVIDE_LIMIT = cfg['divide_limit']     # Divide when at this proportion of energy
INIT_ENERGY = cfg['init_energy']       # How much of its max energy is a creature born with
BITE_RATIO = cfg['bite_ratio']         #
ANTENNA_RANGE = cfg['antenna_range']   #
CARAPACE_RANGE = cfg['carapace_range'] #
MIN_ATTACK_ANGLE = np.pi                  # Minimum attack angle 
ALLOW_ATTACKS = False                  # Allow bugs to attack each other? N.B. If True then DO NOT use USE_GRAYSCALE_FILTER!
USE_GRAYSCALE_FILTER = True            # Bugs are colorblind? It will make learning easier (smaller state space)
DISTANCE_BETWEEN_CHECKPOINTS = 20
DISCRETIZE_ACTION_SPACE = True

def burn(angle,speed,size):
    '''
        How much energy is burned for a bug of this size, moving at this speed, changing angle by thus much.
    '''
    return max(1.,1.*abs(speed)+5.*abs(angle))**2 * (size / 1000.0)

###############################################################################

N_OBSERVATIONS = 4

def obs_filter(x):
    ''' filter the observation space for a simplified input:
        we just see the all other objects as one color + the angle to the 'flag' 
    '''
    if not USE_GRAYSCALE_FILTER:
        return x
    x_ = np.zeros(N_OBSERVATIONS)
    x_[0] = max(x[IDX_COLIDE])
    x_[1] = max(x[IDX_PROBE1])
    x_[2] = max(x[IDX_PROBE2])
    x_[3] = x[IDX_FLAG]
    return x_

observ_space = ContinuousBugSpace(0.,1.,(N_OBSERVATIONS,))

from agents.discretization import discrete2continuous

def act_filter(a):
    ''' filter the action space for discrete space:
        convert a discrete action (int) into a numpy vector
    '''
    return discrete2continuous[a]

action_space = DiscreteBugSpace(len(discrete2continuous))

###############################################################################

class Splatter(pygame.sprite.DirtySprite):
    '''
        Just an artifact / blood splatter, etc.
        (No collisions or anything ...)
    '''
    def __init__(self, pos, mass = 50, ID = ID_ANIMAL):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.radius = 10 + 10 * int(np.sqrt(mass/np.pi))
        self.pos = pos
        self.counter = 100
        self.dirty = True
        self.rect, self.image = build_splatter_img(self.pos,self.radius,min(ID,ID_ANIMAL))

    def update(self):
        # TODO: The splatter should decay. 
        return

    def live(self, world):
        self.counter = self.counter - 1
        if self.counter <= 0:
            self.kill()
            return

    def draw(self, surface):
        if not self.dirty:
            return
        surface.blit(self.image, self.pos - self.radius)
        self.dirty = False

    def kill(self): 
        pygame.sprite.Sprite.kill(self)
        self.remove()
        self = None

class Thing(pygame.sprite.DirtySprite):
    '''
        A Thing (either Rock, Plant, Bug, ...)
    '''
    def __init__(self, pos, mass = 500, ID = ID_ROCK):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.ID = min(ID, ID_ANIMAL)
        self.radius = 3 + int(np.sqrt(mass/np.pi))
        self.energy = mass
        self.pos = pos
        self.is_colliding = True
        self.rect, self.image = build_image(self.pos,self.radius,ID)

#    def wrap(self,world):
#        ''' wrap objects around the screen 
#            (assume this object has valid 'pos' coordinates)
#        '''
#        if self.pos[0] >= world.WIDTH:
#            self.pos[0] = 1.
#        elif self.pos[0] < 0 :
#            self.pos[0] = world.WIDTH-1
#
#        if self.pos[1] >= world.HEIGHT :
#            self.pos[1] = 1.
#        elif self.pos[1] < 0:
#            self.pos[1] = world.HEIGHT-1

    def draw(self, surface):
        """ Draw this Thing """
        surface.blit(self.image, self.pos - self.radius)

    def draw_selected(self, surface):
        """ Additional drawing if this object is selected """
        return

    def update(self):
        # No need to update anything
        return

    def live(self, world):

        if self.energy < 1:
            self.kill()
            return

        while self.is_colliding:
            # Check for overlap with objects / terrain (if we are a rock or plant; else it is handled elsewhere)
            color,collision_obj,terrain_centre = world.collision_to_vision(self.pos,self.radius,self)
            if terrain_centre is not None:
                # Fell into the water
                self.pos = world.random_position(True)
            if collision_obj is not None:
                # If it's an inanimate object (rock or plant) ..
                if collision_obj.ID <= ID_PLANT:
                    slide_apart(self, collision_obj)
                    collision_obj.is_colliding = True
                else:
                    self.is_colliding = False
            else:
                self.is_colliding = False
            # Wrap
            #self.wrap(world)
        return

    def respawn(self, world): 
        self.pos = self.random_position(True)
        self.energy = np.pi * (self.radius - 3)**2 

    def hit_by(self, creature):
        '''
            Collision. A creature collides with me.
        '''
        if self.ID == ID_PLANT and creature.ID >= ID_ANIMAL:
            theta = angle_of_attack(creature,self)
            # Given the correct angle of attack ...
            if np.random.rand() > (theta / MIN_ATTACK_ANGLE):
                # The creature can eat me (one bite at a time, relative to its own size)
                Splatter(self.pos,self.radius,self.ID)
                bite = np.random.rand() * creature.energy_limit * BITE_RATIO
                creature.energy = min(creature.energy + bite, creature.energy_limit)
                self.energy = self.energy - bite

        elif self.ID == ID_ROCK:
            # I am a rock
            Splatter(self.pos,self.radius*2,self.ID)
            creature.energy = creature.energy - abs(creature.speed) * BOUNCE_DAMAGE         # Ouch!

        elif self.ID == ID_MISC:
            print("Captured the flag!")

        # Bump !
        self.pos = self.pos + (creature.unitv * creature.speed)
        slide_apart(creature,self)
        self.is_colliding = True


    def kill(self): # necessary?
        pygame.sprite.Sprite.kill(self)
        self.remove()
        self = None

def spawn_agent(agent_def=None):
    ''' 
        Spawn a new creature and give it an agent.
    '''
    mod_str,cls_str,arg_str = agent_def.split("/")
    import importlib
    Agent = getattr(importlib.import_module(mod_str), cls_str)
    kwargs = eval(arg_str)
    if len(kwargs) > 0:
        return Agent(observ_space, action_space, **kwargs)
    return Agent(observ_space, action_space)


class Creature(Thing):
    '''
        A Creature: Something that moves (i.e., an agent).
    '''

    def __init__(self,pos,dna=None,energy=350.0,ID=ID_ANIMAL):
        pygame.sprite.Sprite.__init__(self, self.containers)
        Thing.__init__(self, pos, mass = energy, ID = ID)
        self.ssID = ID # species/sub-id
        self.images = build_image_bank(self.image)   # load an image for each angle
        self.energy_limit = energy
        self.energy = self.energy_limit * INIT_ENERGY
        self.selected = None
        self.points = 0
        # Attributes
        self.unitv = unitv(np.random.randn(2))
        self.speed = 1.
        self.move(action=act_filter(action_space.sample()))
        self.observation = np.zeros(N_INPUTS, dtype=float)       
        self._energy = self.energy
        self.nest = pos
        self.check_point = -1
        # DNA (the agent)
        if isinstance(dna, str):
            self.brain = spawn_agent(dna)
        elif dna is None:
            print("Error: No Agent definition given.")
            exit(1)
        else: # isinstance(dna, Agent):
            self.brain = dna.copy()

    def __str__(self):
        return str(self.brain)

    def hit_by(self, being):
        '''
            A being hits me.
        '''
        if being.ID <= ID_PLANT:
            # Don't care about getting hit by rocks, grass, etc.
            return

        if self.ID == ID_ANIMAL and self.speed > FLIGHT_SPEED:
            # No collision
            return

        elif (self.ID == ID_ANIMAL and self.ssID == being.ssID)  or (not ALLOW_ATTACKS):
            # The being is from the same species or at least we treat it like that 
            self.points = self.points - 10
            being.points = being.points - 10
            self.energy = self.energy - abs(being.speed) * BOUNCE_DAMAGE   # Ouch!
            being.energy = being.energy - abs(being.speed) * BOUNCE_DAMAGE  # Ouch!
            slide_apart(self,being)

        else:
            # Fight (between 'being' and 'self')!
            obj = [self,being]
            theta = angles_of_attack(self,being)
            for i in [0,1]:
                j = (i+1) % 2
                #if r > (theta[i] / MIN_ATTACK_ANGLE): 
                if theta[i] < MIN_ATTACK_ANGLE:
                    # Attack succeeded
                    Splatter(self.pos,100,ID_ANIMAL)
                    bite = np.random.rand() * abs(obj[i].speed) * 200. * BITE_RATIO
                    # obj[i].energy = min(obj[i].energy + bite, obj[i].energy_limit)
                    obj[i].points = obj[i].points + bite
                    obj[j].energy = obj[j].energy - bite
                else:
                    # Wrong angle of attack (bump!)
                    Splatter(self.pos,100,ID_ANIMAL)
                    r = np.random.rand()
                    bump = r * abs(obj[i].speed) * BOUNCE_DAMAGE
                    obj[i].energy = obj[i].energy - bump   # Ouch!

            slide_apart(self,being)

    def respawn(self, world, reward): 
        # Deal with the final reward and action
        world.increment_score(self.ssID,reward)
        action = act_filter(self.brain.act(obs_filter(self.observation),reward,True))
        # Respawn
        self.pos = self.nest
        self.check_point = -1
        self.energy = self.energy_limit * INIT_ENERGY
        self.move(action)
        #self.wrap(world)

    def live(self, world):
        """
            Live in the the environment for the current time-step:

            1. Observe current state
            2. Calculate reward signal
            3. Act 
        """

        # Starve?
        if self.energy < 10:
            # If we cannot breed ..
            if DIVIDE_LIMIT < 0:
                # Get final reward
                self.respawn(world, -100)
            else:
                # Just die
                self.kill()
                return

        # Check distance to the flag
        flag_distance = norm(self.pos - world.flag.pos) 
        if self.check_point < 0: 
            self.check_point = flag_distance
        elif flag_distance < (self.check_point - DISTANCE_BETWEEN_CHECKPOINTS):
            # Get reward for crossing a checkpoint
            self.check_point = flag_distance
            self.points += 50
            print("[Info] checkpoint passed")
            if flag_distance < (world.flag.radius + self.radius + 25):
                # Get more reward for reaching the goal and respawn
                print("[Info] flag captured!")
                self.respawn(world, reward=200)

        ######################################################
        # Observation (of the environment) 
        self.observation = np.zeros(N_INPUTS, dtype=float)
        # Check collisions with terrain, and other objects
        self.observation[IDX_COLIDE],collision_obj,terrain_centre = world.collision_to_vision(self.pos,self.radius*CARAPACE_RANGE,self,s_collision_radius=self.radius)
        self.observation[IDX_PROBE1],o1,t1 = world.collision_to_vision(self.pos+self.pa1,self.radius*ANTENNA_RANGE,self)
        self.observation[IDX_PROBE2],o2,t2 = world.collision_to_vision(self.pos+self.pa2,self.radius*ANTENNA_RANGE,self)

        # Check angle to flag
        flag_angle = cos_sim(self.unitv, self.pos - world.flag.pos) 
        self.observation[IDX_FLAG] = flag_angle * (flag_angle <= 0)

        # Unless we are flying, we will collide with any objects we overlap with
        if self.speed < FLIGHT_SPEED:

            if terrain_centre is not None:
                ## Terrain/water collision
                self.energy = self.energy - max(1, self.speed * TERRAIN_DAMAGE)
                Splatter(self.pos,200,ID_ROCK)
                Splatter(self.pos,100,ID_ANIMAL)
                slide_off(self,terrain_centre)

            if collision_obj is not None:
                # Sprite (rock,plant,bug) collision
                collision_obj.hit_by(self)

        # Normalize health level
        self.observation[IDX_ENERGY] = min((self.energy/self.energy_limit),1.)

        #######################################################
        # Calculate reward (energy diff + kill points) and reset
        # reward = (self.energy - self._energy) + self.points 
        # energy_diff = (self.energy - self._energy)
        # reward = self.points + 0.001 + energy_diff*0.01 * (energy_diff > 0)
        reward = -0.2 + self.points 
        world.increment_score(self.ssID,reward)

        self.points = 0            # (reset points)
        self._energy = self.energy # (record current energy)

        #######################################################
        # Get an action from the agent 
        action = act_filter(self.brain.act(obs_filter(self.observation),reward)) 
        if self.selected is not None:
            action = self.selected

        #######################################################
        # Carry out the Actions
        self.move(action)
        #self.wrap(world)

    def move(self, action):
        '''
            Process actions on the environment.

            Using action[0] (angle) and action[1] (speed) component.
        '''

        # Only allow a certain range of actions in this environment
        angle = action[IDX_ANGLE]
        speed = action[IDX_SPEED]
        if not DISCRETIZE_ACTION_SPACE:
            angle = np.clip(action[IDX_ANGLE], action_space.low[0], action_space.high[0])
            speed = np.clip(action[IDX_SPEED], action_space.low[1], action_space.high[1])
        # New velocity vector
        if angle < -0.01 or angle > 0.01:
            self.unitv = rotate(self.unitv,angle)
        self.unitv = unitv(self.unitv)  # <-- only to ensure against numerical runaway
        self.speed = speed + (speed > FLIGHT_SPEED) * FLIGHT_BOOST
        # Update antennae
        self.pa1 = rotate(self.unitv * self.radius*3,+0.3) # antenna left pos
        self.pa2 = rotate(self.unitv * self.radius*3,-0.3) # antenna right pos
        # Now move (this burns energy according to size and speed and the angle of turn)
        self.energy = self.energy - burn(angle, speed, self.radius)
        self.pos = self.pos + self.unitv * self.speed
        self.speed = abs(self.speed)
        # Divide (if we are DIVIDE_LIMIT times over the limit)
        if DIVIDE_LIMIT > 0 and self.energy > (self.energy_limit * DIVIDE_LIMIT):
            # Pass on half of spare energy to the child
            spare_energy = (self.energy_limit * DIVIDE_LIMIT) - self.energy_limit
            energy_loss = spare_energy/2.
            c = Creature(self.pos+self.unitv * -self.radius * 5., dna = self.brain, energy = self.energy_limit, ID = self.ID)
            c.energy = energy_loss
            self.energy = self.energy - energy_loss
            # (this loss should not affect the reward signal)
            self._energy = self._energy - energy_loss 


    def update(self):

        ''' Draw (simply extract the correct image for the given angle) '''
        self.image = self.images[angle_deg(self.unitv)]

    def draw(self, surface):
        # Add the antennae
        pygame.draw.line(surface, self.observation[IDX_PROBE1] * 255, self.pos, self.pos+self.pa1, 2)
        pygame.draw.line(surface, self.observation[IDX_PROBE2] * 255, self.pos, self.pos+self.pa2, 2)
        # Wings (if flying)
        if self.speed > FLIGHT_SPEED:
            wing1 = rotate(self.unitv * self.radius*2,+np.pi/2.8)
            wing2 = rotate(self.unitv * self.radius*2,-np.pi/2.8)
            pygame.draw.line(surface, id2rgb[ID_ANIMAL], self.pos, self.pos-wing1, 6)
            pygame.draw.line(surface, id2rgb[ID_ANIMAL], self.pos, self.pos-wing2, 6)
        # Draw the standard image 
        Thing.draw(self, surface)

    def draw_selected(self, surface):
        """
            Additional drawing if this object is selected
        """
        draw_banner(surface, "Team "+str(self.ssID)+" "+str(self.brain.__class__.__name__)+": "+str(self))
        # Body
        pygame.draw.circle(surface, self.observation[IDX_COLIDE] * 255, (int(self.pos[0]),int(self.pos[1])), int(self.radius + 3), 4)
        # Rangers
        pygame.draw.circle(surface, self.observation[IDX_PROBE1] * 255, (int((self.pos+self.pa1)[0]),int((self.pos+self.pa1)[1])), int(self.radius*ANTENNA_RANGE), 2)
        pygame.draw.circle(surface, self.observation[IDX_PROBE2] * 255, (int((self.pos+self.pa2)[0]),int((self.pos+self.pa2)[1])), int(self.radius*ANTENNA_RANGE), 2)
        pygame.draw.circle(surface, self.observation[IDX_COLIDE] * 255, (int(self.pos[0]),int(self.pos[1])), int(self.radius*CARAPACE_RANGE), 3)
        # Health/Calories/Energy level
        pygame.draw.line(surface, COLOR_WHITE, self.pos-20, [self.pos[0]+20,self.pos[1]-20], 1)
        pygame.draw.line(surface, COLOR_WHITE, self.pos-20, [self.pos[0]-20+(self.observation[IDX_ENERGY]*40),self.pos[1]-20], 5)
        # Nest
        pygame.draw.circle(surface, COLOR_WHITE, [int(self.nest[0]),int(self.nest[1])], 20, 2)

        # TODO plot the plot returned by self.__img__
        # surface.blit(surf, self.pos - self.radius)
