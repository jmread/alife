import pygame
from pygame.locals import *

from locals import *
#from cbrain import CBrain
from sbrain import SARSA as RBrain
set_printoptions(precision=4)

class Thing(pygame.sprite.DirtySprite):
    '''
        To replace Resource
    '''
    def __init__(self, pos, mass = 200, ID = ID_ROCK):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.color = id2rgb[ID]*255
        self.ID = ID
        self.radius = 3 + int(math.sqrt(mass/math.pi))
        self.calories = mass                                                     # ~ body mass
        self.pos = pos
        self.dirty = True
        self.rect, self.image = self.build_image(self.radius,self.color)

    def build_image(self,rad,color):
        image = pygame.Surface((rad*2, rad*2))
        image.fill(COLOR_TRANSPARENT)
        image.set_colorkey(COLOR_TRANSPARENT)
        pygame.draw.circle(image, color, (rad,rad), rad )
        rect=image.get_rect(center=self.pos)
        return rect,image

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
        if self.dirty:
            # check for collision 
            x, y = world.pos2grid(self.pos)
            while world.terrain[y,x] > 0:
                # TODO USE A NEW Slide(s,o) function here
                self.pos = self.pos + random.randn(2) * 10.0
                x, y = world.pos2grid(self.pos)
            # wrap
            self.wrap(world)
            self.dirty = False

        return

    def hit_by(self, creature):
        '''
            A creature collides with me
        '''
        if self.ID == ID_PLANT and creature.ID == ID_ANIMAL:
            # I am a plant and the creature is designed to eat me, can take a bite relative to its size
            bite = self.radius * 0.9 # bite size
            creature.calories = creature.calories + bite   # * digestion efficiency 
            self.calories = self.calories - bite     # 

        elif self.ID == ID_ROCK:
            # I am a rock
            creature.calories = creature.calories * 0.95
            self.pos = self.pos + creature.velocity
            Reflect(creature)
            self.dirty = True

        elif self.ID == ID_ANIMAL:
            # I am an egg
            if creature.ID == ID_PREDATOR:
                creature.calories = creature.calories + self.calories   # * digestion efficiency 
            self.calories = 0

        if self.calories < 1:
            print "Thing died"
            self.kill()
            return

    def kill(self): # necessary?
        pygame.sprite.Sprite.kill(self)
        self.remove()
        self = None


class Creature(Thing):
    '''
        A Creature
    '''

    def __init__(self,pos,dna=None,generation=0, cal = 100.0, lim = 200, food_ID = ID_PLANT, ID = ID_ANIMAL):
        pygame.sprite.Sprite.__init__(self, self.containers)
        Thing.__init__(self, pos, mass = lim, ID = ID)
        self.cal_limit = lim
        self.calories = cal                           # TODO get from genes
        print "New Creature ID " + str(self.ID)
        self.food_ID = food_ID
        # Attributes
        self.generation = generation
        self.velocity = random.rand((2))
        self.process_actions(y=random.rand(2)*0.2)
        self.f_a = zeros(N_INPUTS, dtype=float)       
        self._calories = self.calories
        # DNA
        self.b = dna.copy_of() if dna is not None else RBrain(N_LINPUTS,N_OUTPUTS)

    def move(self):
        ''' Move and Wrap '''
        self.pos = self.pos + self.velocity

    def detect_collisions(self, world):
        ''' 
            Check collisions with terrain, and other objects (if it's an object, return it).
        '''

        # (TODO: we probably want to do a global collision detection in 'world' before each round)

        self.f_a[IDX_COLIDE],collision_obj,terrain_centre = world.check_collisions_p(self.pos,self.radius*4.,self,rext=self.radius)
        if terrain_centre is not None:
            ## Ouch! We ran into a wall
            self.calories = self.calories - norm(self.velocity) 
            Slide(self,terrain_centre)
            return None
        self.f_a[IDX_PROBE1],o1,t1 = world.check_collisions_p(self.pos+self.pa1,self.radius*3.,self)
        self.f_a[IDX_PROBE2],o2,t2 = world.check_collisions_p(self.pos+self.pa2,self.radius*3.,self)

        return collision_obj

    def hit_by(self, being):
        '''
            A being hits me.
        '''

        if self.ID == being.food_ID or being.ID == self.food_ID:
            # It could eat me, or I could eat it -- we must fight!
            predator = self
            prey = being
            if self.ID == being.food_ID:
                # I am the prey!
                predator = being
                prey = self
            # FIGHT!
            print "Fight! Between creatures: prey ("+str(prey.f_a[IDX_CALORIES])+") vs predator ("+str(predator.f_a[IDX_CALORIES]) + ")"
            speed_of_attack = norm(predator.velocity)
            if angle_of_attack(predator,prey) > pi/2.:
                print "\tAttacker has wrong angle of attack (%3.2f > %3.2f)!" % (angle_of_attack(predator,prey), pi/2.)
                BounceOffFrom(predator,prey)
                predator.calories = predator.calories - speed_of_attack * 10.   # Ouch!
                prey.calories = prey.calories - speed_of_attack * 10.           # Ouch!
            else:
                bite = speed_of_attack * random.rand() * 10.
                print "\tAttacker successful: *nom nom* (bites off %3.2f cal)." % bite
                predator.calories = predator.calories + bite
                prey.calories = prey.calories - bite
                BounceOffFrom(predator,prey)

        else:
            # The being is a comrade (TODO later: mating goes here, depending on angle of a approach/velocity, either mate or bounce off)
            self.calories = self.calories - norm(being.velocity)   # Ouch!
            being.calories = being.calories - norm(self.velocity)  # Ouch!
            BounceOffFrom(self,being)

    def live(self, world):

        # Deal with collisions in the environment
        colide = self.detect_collisions(world)
        if colide != None:
            colide.hit_by(self)

        # Normalize health level (TODO this isn't used for much really !)
        self.f_a[IDX_CALORIES] = min((self.calories/self.cal_limit),1.)

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
            Using angle and speed component
        '''
        # New velocity vector
        speed = y[1]
        angle = y[0]
        if angle < -0.01 or angle > 0.01:
            self.velocity = rotate(self.velocity,angle)
        u = unitv(self.velocity)
        self.velocity = u * speed
        # Update antennae (note: could save some minor speed here by moving the self.radius * 3 inside of unitv)
        self.pa1 = rotate(u * self.radius*3,0.3)
        self.pa2 = rotate(u * self.radius*3,-0.3)
        # Now move
        self.move();
        self.calories = self.calories - (1.+speed)**3 * (self.cal_limit / 100000.0)   #@TTTT should go inside move ??
        # Divide
        if self.calories > (self.cal_limit * 1.4):
            print "Divide", self.calories, "into", self.cal_limit * 0.2, "and", self.cal_limit * 1.05
            Creature(self.pos+unitv(self.velocity) * -self.radius * 3., dna = self.b, generation = self.generation+1, cal = self.cal_limit * 0.2, lim = self.cal_limit, food_ID = self.food_ID, ID = self.ID)
            gain = self.calories - self._calories
            self.calories = self.cal_limit * 1.05
            self._calories = self.calories - gain    # this is so that dividing is not damaging to the happiness/reward

    def update(self):

        if self.calories < 10:
            print "A sprite died of starvation"
            if self.food_ID == ID_ANIMAL:
                Thing(self.pos + random.randn(2)*10., mass=10, ID=ID_PLANT)
            self.kill()
            return

        # Burn Calories --- this is the only difference from Thing wrt move().
        self.calories = self.calories - (0.0001 * self.cal_limit)
