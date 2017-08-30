import pygame
from pygame.locals import *

from utils import *
from graphics import build_image_png as build_image, build_image_bank
from brain.sarsa import SARSA# as brain
from brain.coded import Coded#as brain
from brain.evolu import Evolu#as brain
set_printoptions(precision=4)

N_OUTPUTS = 2
IDX_COLIDE = [0,1,2]
IDX_PROBE1 = [3,4,5]
IDX_PROBE2 = [6,7,8]
N_LINPUTS = 9
IDX_CALORIES = 9   # N.B. no need for this really (unless we embed the reward into the state space!)
N_INPUTS = 10

ID_NADA = 0
ID_ROCK = 1
ID_MISC = 2
ID_PLANT = 3
ID_ANIMAL = 4
ID_PREDATOR = 5
MAX_ID = 5

TERRAIN_DAMAGE = 1.  # added factor when hitting a wall or landing on water
BOUNCE_DAMAGE = 10.  # multiplied factor when hitting a friend
FLIGHT_SPEED = 5.    # after this speed, a creature takes flight

class Thing(pygame.sprite.DirtySprite):
    '''
        A Thing (either Rock, Plant, Animal, Predictor, ...)
    '''
    def __init__(self, pos, mass = 500, ID = ID_ROCK):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.ID = ID
        self.radius = 3 + int(math.sqrt(mass/math.pi))
        self.calories = mass                                                     # ~ body mass
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

        if self.calories < 1:
            self.kill()
            return

        # Wrap
        self.wrap(world)

        while self.dirty:
            # Check for overlap with objects / terrain (if we are a rock or plant; else it is handled elsewhere)
            color,collision_obj,terrain_centre = world.check_collisions_p(self.pos,self.radius,self)
            if terrain_centre is not None:
                # overlap with terrain
                self.kill()
                self.dirty = False
                print("A rock or something fell into the water")
                #TODO: SlideOff(self, terrain_centre, 5.)
            if collision_obj is not None:
                if collision_obj.ID == ID_ROCK or collision_obj.ID == ID_PLANT:
                    # Overlap with rock or tree
                    SlideApart(self, collision_obj)
                    collision_obj.dirty = True
                    # TODO: Combine or break apart into two objects ?
                else:
                    self.dirty = False
            else:
                self.dirty = False
        return

    def hit_by(self, creature):
        '''
            A creature collides with me
        '''
        if self.ID == ID_PLANT and creature.ID == ID_ANIMAL:
            # I am a plant and the creature is designed to eat me, can take a bite relative to its size
            bite = self.radius * 0.6 # bite size
            creature.calories = creature.calories + bite  * 0.5 #digestion efficiency 
            self.calories = self.calories - bite     # 

        elif self.ID == ID_ROCK:
            # I am a rock
            creature.calories = creature.calories * 0.95
            self.pos = self.pos + creature.velocity
            #Reflect(creature)
            Slide(creature,self.pos)
            self.dirty = True

    def kill(self): # necessary?
        pygame.sprite.Sprite.kill(self)
        self.remove()
        self = None

def brain_loader(ID):
    ''' 
        Brain Loader
        ------------
        Thus we can load different 'brains' randomly if we wish.
    '''
    c = random.choice(3)
    #c = 1
    if c == 0:
        return Coded(ID)
    elif c == 1:
        return SARSA(N_LINPUTS,N_OUTPUTS)
    elif c == 2:
        return Evolu(N_LINPUTS,N_OUTPUTS)

class Creature(Thing):
    '''
        A Creature
    '''

    def __init__(self,pos,dna=None,generation=0, cal = 100.0, lim = 200, food_ID = ID_PLANT, ID = ID_ANIMAL):
        pygame.sprite.Sprite.__init__(self, self.containers)
        Thing.__init__(self, pos, mass = lim, ID = ID)
        self.images = build_image_bank(self.image)   # this is a moving sprite; load images for each angle
        self.rep_limit = lim                         # determines at what size a creature reaches full calories and may reproduce TODO get from genes
        self.calories = cal 
        self.food_ID = food_ID
        # Attributes
        self.generation = generation
        self.velocity = random.rand((2))
        self.process_actions(y=random.rand(2)*0.2)
        self.f_a = zeros(N_INPUTS, dtype=float)       
        self._calories = self.calories
        # DNA
        self.b = dna.copy_of() if dna is not None else brain_loader(self.ID)

    def move(self):
        ''' Move and Wrap '''
        self.pos = self.pos + self.velocity

    def detect_collisions(self, world):
        ''' 
            Check collisions with terrain, and other objects (if it's an object, return it).
        '''

        # (TODO: we probably want to do a global collision detection in 'world' before each round)

        self.f_a[IDX_COLIDE],collision_obj,terrain_centre = world.check_collisions_p(self.pos,self.radius*4.,self,rext=self.radius)
        self.f_a[IDX_PROBE1],o1,t1 = world.check_collisions_p(self.pos+self.pa1,self.radius*3.,self)
        self.f_a[IDX_PROBE2],o2,t2 = world.check_collisions_p(self.pos+self.pa2,self.radius*3.,self)

        if norm(self.velocity) >= FLIGHT_SPEED:
            # We are flying, cannot hit anything
            return None

        elif terrain_centre is not None and norm(self.velocity):
            ## Ouch! We ran into a wall or hit the water - this is the only collision we notice right now
            self.calories = self.calories - norm(self.velocity) - TERRAIN_DAMAGE
            Slide(self,terrain_centre)
            return None

        return collision_obj

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
            # FIGHT!
            #print "Fight! Between creatures: prey ("+str(prey.f_a[IDX_CALORIES])+") vs predator ("+str(predator.f_a[IDX_CALORIES]) + ")"
            speed_of_attack = norm(predator.velocity)
            if angle_of_attack(predator,prey) > pi/3.:
                #print "\tAttacker has wrong angle of attack (%3.2f > %3.2f)!" % (angle_of_attack(predator,prey), pi/2.)
                BounceOffFrom(predator,prey)
                predator.calories = predator.calories - speed_of_attack * BOUNCE_DAMAGE   # Ouch!
                prey.calories = prey.calories - speed_of_attack * BOUNCE_DAMAGE         # Ouch!
            else:
                bite = speed_of_attack * random.rand() * 10.
                #print "\tAttacker successful: *nom nom* (bites off %3.2f cal)." % bite
                predator.calories = predator.calories + (bite * 5.) # <-- this * 5 breaks the laws of physics to help predators, or -- meat is easier to extract calories from than plant matter
                prey.calories = prey.calories - bite
                BounceOffFrom(predator,prey)

        else:
            # The being is a comrade (TODO later: reproduction goes here, depending on angle of a approach/velocity, either mate or bounce off)
            self.calories = self.calories - norm(being.velocity) * BOUNCE_DAMAGE   # Ouch!
            being.calories = being.calories - norm(self.velocity) * BOUNCE_DAMAGE  # Ouch!
            BounceOffFrom(self,being)

    def live(self, world):

        # Burn Calories (for being alive)
        self.calories = self.calories - (0.001 * self.radius)

        # Starve?
        if self.calories < 10:
            #print "A sprite died of starvation"
            Thing(self.pos + random.randn(2)*10., mass=20, ID=ID_PLANT)
            self.kill()
            return

        # Deal with collisions in the environment
        colide = self.detect_collisions(world)
        if colide != None:
            colide.hit_by(self)

        # Normalize health level (TODO currently not used !)
        self.f_a[IDX_CALORIES] = min((self.calories/self.rep_limit),1.)

        # Reinforcement learning
        x = self.f_a[0:N_LINPUTS]          # observation ~= state
        r = self.calories - self._calories # reward
        self._calories = self.calories
        y = self.b.act(x,r)                # actions

        self.process_actions(y)

        self.wrap(world)

    def process_actions(self,y):
        '''
            Process Actions
            ---------------
            Using y[0] (angle) and y[1] (speed) component
        '''
        # New velocity vector
        speed = y[1]
        angle = y[0]
        if angle < -0.01 or angle > 0.01:
            self.velocity = rotate(self.velocity,angle)
        u = unitv(self.velocity)
        self.velocity = u * speed + (speed > 5.) * 3.
        # Update antennae (note: could save some minor speed here by moving the self.radius * 3 inside of unitv)
        self.pa1 = rotate(u * self.radius*3,0.3)
        self.pa2 = rotate(u * self.radius*3,-0.3)
        # Now move (which burns calories according to size and speed)
        self.calories = self.calories - (1.+speed)**3 * (self.radius / 10000.0)
        self.move();
        # Divide (if we are 1.4 times over the limit)
        if self.calories > (self.rep_limit * 1.4):
            Creature(self.pos+u * -self.radius * 3., dna = self.b, generation = self.generation+1, cal = self.rep_limit * 0.2, lim = self.rep_limit, food_ID = self.food_ID, ID = self.ID)
            self.calories = self.rep_limit * 1.05
            # we need to reset the gain so that also dividing loses calories it does not depress the creature (does not affect its internal reward system)
            gain = self.calories - self._calories
            self._calories = self.calories - gain 

    def update(self):

        ''' ... and draw '''
        self.image = self.images[angle_deg(self.velocity)]
