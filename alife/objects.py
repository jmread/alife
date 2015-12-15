import pygame
from pygame.locals import *

from locals import *
from cerebro.brain import make_brain
from cerebro.functions import linear
set_printoptions(precision=4)

class Resource(pygame.sprite.DirtySprite):
    '''
        A resource just sits or floats around waiting to be eaten.
    '''

    def __init__(self, pos, mass = 200, color = COLOR_GREEN):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.ID = 3
        # attributes
        self.radius = 3 + int(math.sqrt(mass/math.pi))
        self.calories = mass                                                     # ~ body mass
        self.pos = pos
        # pre-buf / image
        self.rect, self.image = self.build_image(self.radius,color)

    def build_image(self,rad,color):
        image = pygame.Surface((rad*2, rad*2))
        image.fill(COLOR_TRANSPARENT)
        image.set_colorkey(COLOR_TRANSPARENT)
        pygame.draw.circle(image, color, (rad,rad), rad )
        rect=image.get_rect(center=self.pos)
        return rect,image

    def wrap(self):
        ''' wrap objects around the screen '''
        if self.pos[0] >= SCREEN[0]:
            self.pos[0] = 1.
        elif self.pos[0] < 0 :
            self.pos[0] = SCREEN[0]-1

        if self.pos[1] >= SCREEN[1] :
            self.pos[1] = 1.
        elif self.pos[1] < 0:
            self.pos[1] = SCREEN[1]-1

    def live(self, world):
        ''' just bounce around growing '''
        x,y = pos2grid(self.pos)   
        if world.terrain[x,y] > 0:
            self.kill()

    def hit_by(self, being):
        # ... with food
        bite = being.radius * 0.1                                         # bite size
        if being.food_ID == self.ID:
            # being designed to eat me (Resource), can take a bigger bite
            bite = being.radius * 0.9                                         # bite size
        being.calories = being.calories + bite   # * digestion efficiency 
        self.calories = self.calories - bite     # 
        if self.calories < 0:
            print "Resource eaten"
            self.kill()
            self = None

    def update(self):
        ''' just die or move '''

        if self.calories < 1:
            print "Resource eaten"
            self.kill()
            return

    def draw(self, surface):
        surface.blit(self.image, self.pos - self.radius)

    def kill(self): # necessary?
        pygame.sprite.Sprite.kill(self)
        self.remove()

class Rock(Resource):
    '''
        A Rock
    '''
    def __init__(self, pos, mass = 100, color = COLOR_WHITE):
        Resource.__init__(self, pos, mass, color)
        self.carrier = None
        self.ID = 1

    def live(self, world):
        if self.carrier != None and self.carrier.hold: 
            self.pos = self.pos + self.carrier.pa1 

    def hit_by(self, being):
        being.calories = being.calories * 0.95
        Reflect(being)

class Herbivore(Resource):
    '''
        A Herbivore
    '''

    def __init__(self,pos,dna=None,generation=0, cal = 100.0, lim = 200, food_ID = ID_PLANT, color = COLOR_BLUE):
        pygame.sprite.Sprite.__init__(self, self.containers)
        Resource.__init__(self, pos, mass = lim, color = color)
        self.cal_limit = lim
        self.calories = cal                           # TODO get from genes
        self.ID = 4 + (food_ID != ID_PLANT)
        print "NEW BEING OF ID " + str(self.ID)
        self.food_ID = food_ID
        self.color = color
        # Attributes
        self.generation = generation
        self.velocity = random.randn(2)*0.2                                      # velocity vector 
        u = unitv(self.velocity)
        self.pa1 = rotate(u * self.radius*3,0.3)       # antennae 1
        self.pa2 = rotate(u * self.radius*3,-0.3)      # antennae 2
        self.hold = 0.0
        self.f_a = zeros(N_INPUTS, dtype=float)       
        #self.f_a[IDX_BIAS] = 1.
        # DNA
        # TODO learn OR select the reward-(summary) function
        #self.b = brain(MLPpf(N_INPUTS,N_HIDDEN,N_OUTPUTS,density=1.0),tau=(10+random.choice(100)),test=False)
        self.b = None
        #self.b = make_brain(N_INPUTS,20,N_OUTPUTS,f_desc="DE2",use_bias=False,density=0.5,tau=(1+random.choice(100)))
        if (dna is not None) and (random.rand() < 0.9): # (with a small chance of total mutation)
            self.b = dna.copy_of()
        else:
            self.b = make_brain(N_LINPUTS,random.choice([-5,-1,0,0,10,15,20,25,50]),N_OUTPUTS,f_desc="DE2",use_bias=False,density=clip(random.rand(),0.1,1.0),tau=(1+random.choice(100)))

        self.happiness = 0.

    def move(self):
        ''' move and wrap '''
        self.pos = self.pos + self.velocity
        self.wrap();                                                # wrap (if necessary)

    def divide(self):
        # Spawn a new being
        self.calories = self.calories * 0.45
        Herbivore(self.pos+unitv(self.velocity) * -self.radius * 3.,self.b,self.generation+1,self.calories, food_ID = self.food_ID,  color = self.color)

    def set_input(self, world):
        ''' 
            return collisions with food and comrades
        '''

        # (TODO: we probably want to do a global collision detection in 'world' before each round)

        ###################################################
        # CHECK COLLISIONS (PROXIMITY)
        ###################################################
        if world.check_collisions_wall(self.pos,self.radius):
            # Ouch! We ran into a wall
            self.calories = self.calories * 0.95
            Reflect(self)
            return None
        self.f_a[IDX_COLIDE],col = world.check_collisions_p(self.pos,self.radius*4.,self,rext=self.radius)
        self.f_a[IDX_PROBE1],o1 = world.check_collisions_p(self.pos+self.pa1,self.radius*3.,self)
        self.f_a[IDX_PROBE2],o2 = world.check_collisions_p(self.pos+self.pa2,self.radius*3.,self)

        # Normalize health level
        self.f_a[IDX_CALORIES] = min((self.calories/self.cal_limit),1.)

        return col

    def hit_by(self, being):
        '''
            A being hits me (self)
        '''

        if self.ID == being.food_ID or being.ID == self.food_ID:
            # it could eat me, or I could eat it
            attacker = self
            defender = being
            if self.ID == being.food_ID:
                # it could eat me, I must defend!
                attacker = being
                defender = self
            # FIGHT!
            print "Fight! Between beings: defender ("+str(defender.f_a[IDX_CALORIES])+") and attacker ("+str(attacker.f_a[IDX_CALORIES]) + ")"
            if angle_of_attack(attacker,defender) > pi/2.:
                print "\tattacker has wrong angle of attack!, =", angle_of_attack(attacker,defender)
                BounceOffFrom(attacker,defender)
                attacker.calories = attacker.calories * 0.95   # Ouch!
                defender.calories = defender.calories * 0.90   # Ouch!
            elif random.rand() < (attacker.f_a[IDX_CALORIES] / defender.f_a[IDX_CALORIES]):
                print "\tand eats it."
                attacker.calories = attacker.calories + defender.calories * 0.5
                defender.kill()
                defender = None
            else: # kick
                print "\tbut is kicked off."
                attacker.calories = attacker.calories * 0.95
                BounceOffFrom(attacker,being)

        else:
            # ... the being is a comrade
            self.calories = self.calories - magv(being.velocity)   # Ouch!
            being.calories = being.calories - magv(self.velocity)   # Ouch!
            BounceOffFrom(self,being)

    def live(self, world):

        colide = self.set_input(world)

        if colide != None:
            colide.hit_by(self)

        x = self.f_a[0:N_LINPUTS]
        y = self.b.fire(x)

        self.process_actions(y)
        self.happiness = self.f_a[IDX_CALORIES] #self.w_r.dot(self.f_a) 
        self.b.learn(1.-self.happiness)

    def process_actions(self,y):
        # MOVEMENT

        # New velocity vector
        speed = min(magv(y),8.)
        u = unitv(self.velocity + unitv(y))
        self.velocity = u * speed
        # Update antennae
        self.pa1 = rotate(u * self.radius*3,0.3)
        self.pa2 = rotate(u * self.radius*3,-0.3)
        # Now move
        self.move();
        self.calories = self.calories - (1.+speed)**3 * (self.cal_limit / 100000.0)   #@TTTT should go inside move ??

        # DIVIDE
        if self.calories > (self.cal_limit * 1.4):
            print "--!--"
            Herbivore(self.pos+unitv(self.velocity) * -self.radius * 3., dna = self.b, generation = self.generation+1, cal = self.cal_limit * 0.2, lim = max(self.cal_limit + int(random.randn()),10.), food_ID = self.food_ID,  color = self.color)
            self.calories = self.cal_limit * 1.05

    def update(self):

        if self.calories < 5:
            print "A sprite died of starvation"
            self.kill()
            return

        # BURN CALORIES --- the only difference to Resource wrt move() is that we burn calories -- although should also be the case for Resource 
        self.calories = self.calories - (0.0001 * self.cal_limit)
