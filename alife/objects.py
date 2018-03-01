import pygame
from pygame.locals import *

import pickle

from utils import *
from graphics import build_image_png as build_image, build_image_bank
from rl.spaces import BugSpace # the space of the environment (for the agent)
from rl.agent import Agent 
set_printoptions(precision=4)

# Types of Sprites/Things/Objects
ID_VOID = 0
ID_ROCK = 1
ID_MISC = 2
ID_PLANT = 3
ID_ANIMAL = 4
ID_PREDATOR = 5

# Inputs (state space)
IDX_COLIDE = [0,1,2]
IDX_PROBE1 = [3,4,5]
IDX_PROBE2 = [6,7,8]
IDX_ENERGY = 9
N_INPUTS = 10  
observ_space = BugSpace(0.,1.,(N_INPUTS,))

# Outputs (action space)
IDX_ANGLE = 0
IDX_SPEED = 1
N_OUTPUTS = 2
action_space = BugSpace(array([-pi/4., -10.]), array([pi/4.,10.]))

# Some constants
TERRAIN_DAMAGE = 2.  # Added factor when hitting a wall or landing on water
BOUNCE_DAMAGE = 2.   # Multiplied factor when hitting a friend
FLIGHT_SPEED = 5.    # After this speed, a creature takes flight
FLIGHT_BOOST = 3.    # Speed is multiplied by this factor if in flight 
DIVIDE_LIMIT = 2.    # Divide when at this proportion of energy
BITE_RATIO = 0.6     # What proportion creatuer's size it can bite of another creature
MAX_BITE = 10.

def burn(angle,speed,size):
    '''
        How much energy is burned for a bug of this size, moving at this speed, changing angle by thus much.
    '''
    return ((1.+abs(speed))**3 + (1.+abs(angle))**2) * (size / 10000.0)


class Thing(pygame.sprite.DirtySprite):
    '''
        A Thing (either Rock, Plant, Animal, Predator, ...)
    '''
    def __init__(self, pos, mass = 500, ID = ID_ROCK):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.ID = ID
        self.radius = 3 + int(math.sqrt(mass/math.pi))
        self.energy = mass
        self.pos = pos
        self.dirty = True
        self.rect, self.image = build_image(self.pos,self.radius,self.ID)

    def wrap(self,world):
        ''' wrap objects around the screen '''
        if self.pos[0] >= world.WIDTH:
            self.pos[0] = 1.
        elif self.pos[0] < 0 :
            self.pos[0] = world.WIDTH-1

        if self.pos[1] >= world.HEIGHT :
            self.pos[1] = 1.
        elif self.pos[1] < 0:
            self.pos[1] = world.HEIGHT-1

    def draw(self, surface):
        surface.blit(self.image, self.pos - self.radius)

    def update(self):
        return

    def live(self, world):

        if self.energy < 1:
            self.kill()
            return

        while self.dirty:
            # Check for overlap with objects / terrain (if we are a rock or plant; else it is handled elsewhere)
            color,collision_obj,terrain_centre = world.check_collisions(self.pos,self.radius,self)
            if terrain_centre is not None:
                # overlap with terrain
                self.dirty = False
                self.kill()
            if collision_obj is not None:
                if collision_obj.ID == ID_ROCK or collision_obj.ID == ID_PLANT:
                    # Overlap with rock or plant
                    slide_apart(self, collision_obj)
                    collision_obj.dirty = True
                else:
                    self.dirty = False
            else:
                self.dirty = False
            # Wrap
            self.wrap(world)
        return

    def hit_by(self, creature):
        '''
            A creature collides with me
        '''
        if self.ID == ID_PLANT and creature.ID == ID_ANIMAL:
            # The creature can eat me (one bite at a time, relative to its own size)
            bite = random.rand() * MAX_BITE
            creature.energy = creature.energy + bite  * BITE_RATIO
            self.energy = self.energy - bite

        elif self.ID == ID_ROCK:
            # I am a rock
            speed = norm(creature.velocity)
            creature.energy = creature.energy - speed * BOUNCE_DAMAGE         # Ouch!
            self.pos = self.pos + creature.velocity
            self.dirty = True

        # I am bumped away
        #slide_off(creature,self.pos)
        slide_apart(creature,self)

    def kill(self): # necessary?
        pygame.sprite.Sprite.kill(self)
        self.remove()
        self = None

def spawn_agent(agent_def="alife.rl.evolution:Evolver"):
    ''' 
        Spawn a new creature and give it a rl (agent).

        Parameters
        ----------
        ID : int
            the type of creature to create.
    '''
    mod_str,cls_str = agent_def.split(":")
    import importlib
    Agent = getattr(importlib.import_module(mod_str), cls_str)
    return Agent(observ_space, action_space)


class Creature(Thing):
    '''
        A Creature: Something that moves (i.e., an agent).
    '''

    def __init__(self,pos,dna=None, energy = 100.0, energy_limit = 200, food_ID = ID_PLANT, ID = ID_ANIMAL):
        pygame.sprite.Sprite.__init__(self, self.containers)
        Thing.__init__(self, pos, mass = energy_limit, ID = ID)
        self.images = build_image_bank(self.image)   # this is a moving sprite; load images for each angle
        self.energy_limit = energy_limit                         # determines at what size a creature reaches full energy and may reproduce TODO get from genes
        self.energy = energy 
        self.food_ID = food_ID
        # Attributes
        self.velocity = 0.
        self.process_actions(action=action_space.sample())
        self.observation = zeros(N_INPUTS, dtype=float)       
        self._energy = self.energy
        # DNA (the agent)
        if isinstance(dna, str):
            self.brain = spawn_agent(dna)
        elif dna is None:
            print("Error: No Agent definition given.")
            exit(1)
        else: # isinstance(dna, Agent):
            self.brain = dna.spawn_copy()

    def __str__(self):
        return str(self.brain)

    def move(self):
        ''' Move and Wrap '''
        self.pos = self.pos + self.velocity

    def hit_by(self, being):
        '''
            A being hits me.
        '''

        if self.ID < being.ID:
            return
        elif self.ID == being.food_ID or being.ID == self.food_ID:
            # It could eat me, or I could eat it -- we must fight!
            predator = self
            prey = being
            if self.ID == being.food_ID:
                # I am the prey!
                predator = being
                prey = self
            # Fight between prey and predator
            speed_of_attack = norm(predator.velocity)
            if angle_of_attack(predator,prey) > pi/3.:
                # Attacker has wrong angle of attack
                # (probably it is the prey bumping into it)
                slide_apart(predator,prey)
                predator.energy = predator.energy - speed_of_attack * BOUNCE_DAMAGE   # Ouch!
                prey.energy = prey.energy - speed_of_attack * BOUNCE_DAMAGE         # Ouch!
            else:
                # Attacker successful
                bite = speed_of_attack * random.rand() * MAX_BITE
                predator.energy = predator.energy + bite
                prey.energy = prey.energy - bite
                slide_apart(predator,prey)

        else:
            # The being is from the same species (TODO: add reproduction option here)
            self.energy = self.energy - norm(being.velocity) * BOUNCE_DAMAGE   # Ouch!
            being.energy = being.energy - norm(self.velocity) * BOUNCE_DAMAGE  # Ouch!
            slide_apart(self,being)

    def live(self, world):

        # Burn energy (for being alive)
        self.energy = self.energy - (0.001 * self.radius)

        # Starve?
        if self.energy < 10:
            Thing(self.pos + random.randn(2)*10., mass=20, ID=ID_PLANT)
            self.kill()
            return

        # Observation (make it afresh to avoid problems later): 
        self.observation = zeros(N_INPUTS, dtype=float)

        # Check collisions with terrain, and other objects (TODO: we probably want to do a global collision detection in 'world' before each round)
        self.observation[IDX_COLIDE],collision_obj,terrain_centre = world.check_collisions(self.pos,self.radius*4.,self,collision_radius=self.radius)
        self.observation[IDX_PROBE1],o1,t1 = world.check_collisions(self.pos+self.pa1,self.radius*3.,self)
        self.observation[IDX_PROBE2],o2,t2 = world.check_collisions(self.pos+self.pa2,self.radius*3.,self)

        # Unless we are flighing, we will collide with any objects we overlap with
        if norm(self.velocity) < FLIGHT_SPEED:

            if terrain_centre is not None:
                ## Terrain/water collision
                self.energy = self.energy - norm(self.velocity) * TERRAIN_DAMAGE
                slide_off(self,terrain_centre)

            if collision_obj is not None:
                # Sprite (rock,plant,bug) collision
                collision_obj.hit_by(self)

        # Normalize health level
        self.observation[IDX_ENERGY] = min((self.energy/self.energy_limit),1.)

        # Reinforcement learning
        reward = self.energy - self._energy              # reward = energy diff from last timestep
        self._energy = self.energy                       # (save the current energy)
        action = self.brain.act(self.observation,reward) # call upon the agent to act

        # Move
        self.process_actions(action)              # ... and enact them.

        # Wrap around the world
        self.wrap(world)

    def process_actions(self,action):
        '''
            Process Actions.

            Using action[0] (angle) and action[1] (speed) component.
        '''
        # New velocity vector
        angle = action[IDX_ANGLE]
        speed = action[IDX_SPEED]
        if angle < -0.01 or angle > 0.01:
            self.velocity = rotate(self.velocity,angle)
        u = unitv(self.velocity)
        self.velocity = u * speed + (speed > FLIGHT_SPEED) * FLIGHT_BOOST
        # Update antennae
        self.pa1 = rotate(u * self.radius*3,+0.3) # antenna left pos
        self.pa2 = rotate(u * self.radius*3,-0.3) # antenna right pos
        # Now move (this burns energy according to size and speed and the angle of turn)
        self.energy = self.energy - burn(angle, speed, self.radius)
        self.move();
        # Divide (if we are DIVIDE_LIMIT times over the limit)
        if self.energy > (self.energy_limit * DIVIDE_LIMIT):
            # Pass on half of spare energy to the child
            spare_energy = (self.energy_limit * DIVIDE_LIMIT) - self.energy_limit
            energy_loss = spare_energy/2.
            Creature(self.pos+u * -self.radius * 5., dna = self.brain, energy = energy_loss, energy_limit = self.energy_limit, food_ID = self.food_ID, ID = self.ID)
            self.energy = self.energy - energy_loss
            # (this loss should not affect the reward signal)
            self._energy = self._energy - energy_loss 

    def update(self):

        ''' Draw (simply extract the correct image for the given angle) '''
        self.image = self.images[angle_deg(self.velocity)]
