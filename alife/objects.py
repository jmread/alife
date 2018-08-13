import pygame
from pygame.locals import *

from utils import *
from graphics import build_image_png as build_image, build_image_bank
from graphics import rgb2color, id2rgb, COLOR_BLACK, COLOR_WHITE
from agents.spaces import BugSpace # the space of the environment (for the agent)
from agents.agent import Agent 
set_printoptions(precision=4)

# Types of Sprites/Things/Objects
ID_VOID = 0
ID_ROCK = 1
ID_MISC = 2
ID_PLANT = 3
ID_ANIMAL = 4
ID_OTHER = 5

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
action_space = BugSpace(array([-pi/4., -5.]), array([pi/4.,10.]))

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
MIN_ATTACK_ANGLE = pi                  # Minimum attack angle 

def burn(angle,speed,size):
    '''
        How much energy is burned for a bug of this size, moving at this speed, changing angle by thus much.
    '''
    return max(1.,abs(speed)+5.*abs(angle))**2 * (size / 1000.0)

#

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
        self.is_colliding = True
        self.rect, self.image = build_image(self.pos,self.radius,self.ID)

    def wrap(self,world):
        ''' wrap objects around the screen 
            (assume this object has valid 'pos' coordinates)
        '''
        if self.pos[0] >= world.WIDTH:
            self.pos[0] = 1.
        elif self.pos[0] < 0 :
            self.pos[0] = world.WIDTH-1

        if self.pos[1] >= world.HEIGHT :
            self.pos[1] = 1.
        elif self.pos[1] < 0:
            self.pos[1] = world.HEIGHT-1

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
            self.wrap(world)
        return

    def hit_by(self, creature):
        '''
            Collision. A creature collides with me.
        '''
        if self.ID == ID_PLANT and creature.ID >= ID_ANIMAL:
            # The creature can eat me (one bite at a time, relative to its own size)
            bite = random.rand() * creature.energy_limit * BITE_RATIO
            creature.energy = creature.energy + bite 
            self.energy = self.energy - bite

        elif self.ID == ID_ROCK:
            # I am a rock
            creature.energy = creature.energy - creature.speed * BOUNCE_DAMAGE         # Ouch!

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
        self.images = build_image_bank(self.image)   # this is a moving sprite; load images for each angle
        self.energy_limit = energy
        self.energy = energy * INIT_ENERGY
        self.selected = None
        # Attributes
        self.unitv = unitv(random.randn(2))
        self.speed = 1.
        self.env_step(action=action_space.sample())
        self.observation = zeros(N_INPUTS, dtype=float)       
        self._energy = self.energy
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

    def move(self):
        ''' Move '''

    def hit_by(self, being):
        '''
            A being hits me.
        '''

        if being.ID <= ID_PLANT:
            # Don't care about getting hit by rocks, grass, etc.
            return

        elif self.ID == being.ID:
            # The being is from the same species (TODO: add reproduction option here)
            self.energy = self.energy - being.speed * BOUNCE_DAMAGE   # Ouch!
            being.energy = being.energy - being.speed * BOUNCE_DAMAGE  # Ouch!
            slide_apart(self,being)

        else:
            # We must fight!


            obj = [self,being]
            theta = angles_of_attack(self,being)

            #print("ANGLES OF ATTACK", self.ID, theta)

            for i in [0,1]:
                j = (i+1) % 2
                r = random.rand()
                if r > (theta[i] / MIN_ATTACK_ANGLE): 
                    # Attack succeeded
                    bite = r * obj[i].speed * 100. * BITE_RATIO
                    obj[i].energy = obj[i].energy + bite
                    obj[j].energy = obj[j].energy - bite
                else:
                    # Wrong angle of attack (bump!)
                    bump = r * obj[i].speed * 10. * BOUNCE_DAMAGE
                    obj[i].energy = obj[i].energy - bump   # Ouch!

            slide_apart(self,being)

    def live(self, world):
        """
            Live in the the environment:

            1. Observe current state
            2. Calculate reward signal
            3. Act 
        """

        # Starve?
        if self.energy < 10:
            Thing(self.pos + random.randn(2)*10., mass=20, ID=ID_PLANT)
            self.kill()
            return

        # Observation (make it afresh to avoid problems later): 
        self.observation = zeros(N_INPUTS, dtype=float)

        # Check collisions with terrain, and other objects
        self.observation[IDX_COLIDE],collision_obj,terrain_centre = world.collision_to_vision(self.pos,self.radius*4.,self,s_collision_radius=self.radius)
        self.observation[IDX_PROBE1],o1,t1 = world.collision_to_vision(self.pos+self.pa1,self.radius*3.,self)
        self.observation[IDX_PROBE2],o2,t2 = world.collision_to_vision(self.pos+self.pa2,self.radius*3.,self)

        # Unless we are flying, we will collide with any objects we overlap with
        if self.speed < FLIGHT_SPEED:

            if terrain_centre is not None:
                ## Terrain/water collision
                self.energy = self.energy - max(1, self.speed * TERRAIN_DAMAGE)
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
        if self.selected is not None:
            action = self.selected

        # Carry out the actions on the World
        self.env_step(action)

        # Wrap around the world
        self.wrap(world)

    def env_step(self,action):
        '''
            Process actions on the environment.

            Using action[0] (angle) and action[1] (speed) component.
        '''

        # Only allow a certain range of actions in this environment
        angle = clip(action[IDX_ANGLE], action_space.low[0], action_space.high[0])
        speed = clip(action[IDX_SPEED], action_space.low[1], action_space.high[1])
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
        # Divide (if we are DIVIDE_LIMIT times over the limit)
        if self.energy > (self.energy_limit * DIVIDE_LIMIT):
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
        pygame.draw.line(surface, rgb2color(self.observation[IDX_PROBE1],id2rgb[ID_ANIMAL]), self.pos, self.pos+self.pa1, 2)
        pygame.draw.line(surface, rgb2color(self.observation[IDX_PROBE2],id2rgb[ID_ANIMAL]), self.pos, self.pos+self.pa2, 2)
        # Wings (if flying)
        if self.speed > FLIGHT_SPEED:
            wing1 = rotate(self.unitv * self.radius*2,+pi/2.8)
            wing2 = rotate(self.unitv * self.radius*2,-pi/2.8)
            pygame.draw.line(surface, id2rgb[ID_ANIMAL], self.pos, self.pos-wing1, 6)
            pygame.draw.line(surface, id2rgb[ID_ANIMAL], self.pos, self.pos-wing2, 6)
        # Draw the standard image 
        Thing.draw(self, surface)

    def draw_selected(self, surface):
        """
            Additional drawing if this object is selected
        """
        s = str(self)
        anchor = 1
        pygame.draw.rect(surface, COLOR_BLACK, (anchor,5,anchor+20*len(s),25))
        myfont = pygame.font.SysFont("monospace", 17)
        label = myfont.render(s, 1, COLOR_WHITE)
        surface.blit(label, [anchor+1,6])
        # Body
        pygame.draw.circle(surface, rgb2color(self.observation[IDX_COLIDE],id2rgb[ID_ANIMAL]), (int(self.pos[0]),int(self.pos[1])), int(self.radius + 3), 4)
        # Rangers
        pygame.draw.circle(surface, rgb2color(self.observation[IDX_PROBE1],COLOR_BLACK), (int((self.pos+self.pa1)[0]),int((self.pos+self.pa1)[1])), int(self.radius*3.), 2)
        pygame.draw.circle(surface, rgb2color(self.observation[IDX_PROBE2],COLOR_BLACK), (int((self.pos+self.pa2)[0]),int((self.pos+self.pa2)[1])), int(self.radius*3.), 2)
        pygame.draw.circle(surface, rgb2color(self.observation[IDX_COLIDE],COLOR_BLACK), (int(self.pos[0]),int(self.pos[1])), int(self.radius*4.), 3)
        # Health/Calories/Energy level
        pygame.draw.line(surface, COLOR_WHITE, self.pos-20, [self.pos[0]+20,self.pos[1]-20], 1)
        pygame.draw.line(surface, COLOR_WHITE, self.pos-20, [self.pos[0]-20+(self.observation[IDX_ENERGY]*40),self.pos[1]-20], 5)
