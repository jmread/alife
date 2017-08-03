#! /usr/bin/env python

import pygame

import joblib, glob, time, datetime
from objects import *

class DrawGroup(pygame.sprite.Group):
    def draw(self, surface):
        for s in self.sprites():
            s.draw(surface)

def load_map(s):
    ''' load a map from a text file '''
    MAP = zeros((10,10),dtype=int)
    if s is not None:
        MAP = genfromtxt(s, delimiter = 1, dtype=int)
    return MAP

def random_position(SCREEN):
    ''' random positions somewhere on the screen '''
    return random.rand(2) * SCREEN

class World:

    def __init__(self,fname=None,init_sprites=0):

        self.terrain = load_map(fname)
        self.N_ROWS = self.terrain.shape[0]
        self.N_COLS = self.terrain.shape[1]
        self.WIDTH = self.N_COLS * GRID_SIZE
        self.HEIGHT = self.N_ROWS * GRID_SIZE
        SCREEN = array([self.WIDTH, self.HEIGHT])

        count = 0
        prosperity = 50

        ## GRID REGISTER and GRID COUNT 
        self.register = [[[None for l in xrange(MAX_GRID_DETECTION)] for k in xrange(self.N_ROWS)] for j in xrange(self.N_COLS)]
        self.regcount = zeros(self.terrain.shape,int) 

        ## INIT ##
        pygame.display.set_caption("ALife")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))#, HWSURFACE|DOUBLEBUF)
        pygame.mouse.set_visible(1)

        ## BACKGROUND ##
        background = pygame.Surface(self.screen.get_size())
        background.fill([0, 0, 0])                  # fill with black
        for j in range(self.N_COLS):
            for k in range(self.N_ROWS):
                if self.terrain[k,j] > 0:
                    background.fill(tid2rgb[self.terrain[k,j]], rect=(j*GRID_SIZE,k*GRID_SIZE,GRID_SIZE,GRID_SIZE))            # rock
        background = background.convert()           # can speed up when we have an 'intense' background

        ## DISPLAY THE BACKGROUND ##
        self.screen.blit(background, [0, 0])
        pygame.display.flip()

        ## SPRITES ##
        self.allSprites = DrawGroup()
        self.creatures = pygame.sprite.Group()
        self.resources = pygame.sprite.Group()
        self.rocks = pygame.sprite.Group()
        self.stumps = pygame.sprite.Group()

        Creature.containers = self.allSprites, self.creatures
        Thing.containers = self.allSprites, self.resources

        self.clock = pygame.time.Clock()
        
        FACTOR = init_sprites
        for i in range(self.N_ROWS*((FACTOR/2)**2)):
            Thing(random_position(SCREEN), ID=ID_PLANT)
        for i in range(self.N_ROWS*FACTOR/4*2):
            Creature((random_position(SCREEN)), cal = 75, lim = 150)
        for i in range(self.N_ROWS*FACTOR/6*2):
            Creature((random_position(SCREEN)),cal = 200, lim = 400, ID = ID_PREDATOR, food_ID = ID_ANIMAL)

        self.allSprites.clear(self.screen, background)

        ## MAIN LOOP ##
        DEBUG = 2
        while True:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_d:
                        DEBUG = (DEBUG + 1) % 4
                        print "DEBUG = ", DEBUG
                    elif event.key == pygame.K_s:
                        print "SAVING ..."
                        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M')
                        print st
                        counter = 1
                        for s in self.creatures:
                            joblib.dump( s,  "./dat/dna/C"+str(counter)+"_"+str(st)+"_G"+str(s.generation)+".dat")
                            counter = counter + 1
                        print "SAVED."
                    elif event.key == pygame.K_l:
                        print "LOADING ..."
                        import glob
                        for filename in glob.glob('./dat/dna/*.dat'):
                            temp = joblib.load(filename)
                            print("Load gen %d Creature ..." % temp.generation)
                            Creature(random_position(SCREEN),generation = temp.generation, cal = temp.calories, lim = temp.cal_limit, ID = temp.ID, food_ID = temp.food_ID)
                            temp = None
                        print "LOADED."
                    elif event.key == pygame.K_DOWN:
                        prosperity = prosperity + 1
                        print "LOWER ENERGY INFLUX", prosperity
                    elif event.key == pygame.K_UP:
                        prosperity = prosperity - 1
                        print "HIGHER ENERGY INFLUX", prosperity
                    elif event.key == pygame.K_k:
                        print "NEW ROCK"
                        Thing(array(pygame.mouse.get_pos()),mass=500, ID=ID_ROCK)
                    elif event.key == pygame.K_r:
                        print "NEW RESOURCE"
                        Thing(array(pygame.mouse.get_pos()), ID=ID_PLANT)
                    elif event.key == pygame.K_h:
                        print "NEW CREATURE"
                        Creature(array(pygame.mouse.get_pos()))
                    elif event.key == pygame.K_p:
                        print "NEW PREDATOR"
                        Creature(array(pygame.mouse.get_pos()),cal = 200, lim = 400, ID = ID_PREDATOR, food_ID = ID_ANIMAL)

            # Make sure there is a constant flow of resources/energy into the system
            count = count + 1
            if count > prosperity and len(self.resources) < 100:
                Thing(random_position(SCREEN), ID=ID_PLANT)
                count = 0

            # Reset reg-counts
            self.regcount = zeros((self.N_COLS,self.N_ROWS),int) 
            # Register all sprites
            for r in self.allSprites:
                self.add_to_reg(r)

            ## Routine
            for r in self.allSprites:
                r.live(self)

            self.allSprites.update()

            if DEBUG > 0:

                # Draw
                self.screen.blit(background, [0, 0])
                # GRID STOP
                rects = self.allSprites.draw(self.screen)

            if DEBUG >= 1:

                for r in self.creatures:
                    # FEELERS
                    pygame.draw.line(self.screen, rgb2color(r.f_a[IDX_PROBE1],r.color), r.pos, r.pos+r.pa1, 3)
                    pygame.draw.line(self.screen, rgb2color(r.f_a[IDX_PROBE2],r.color), r.pos, r.pos+r.pa2, 3)
                    pygame.draw.circle(self.screen, rgb2color(r.f_a[IDX_PROBE1],COLOR_BLACK), (int((r.pos+r.pa1)[0]),int((r.pos+r.pa1)[1])), int(r.radius*3.), 1)
                    pygame.draw.circle(self.screen, rgb2color(r.f_a[IDX_PROBE2],COLOR_BLACK), (int((r.pos+r.pa2)[0]),int((r.pos+r.pa2)[1])), int(r.radius*3.), 1)
                    # TAIL
                    pygame.draw.line(self.screen, r.color, r.pos, r.pos+(r.velocity * -20.), 1)

                    # BODY
                    pygame.draw.circle(self.screen, rgb2color(r.f_a[IDX_COLIDE],r.color), (int(r.pos[0]),int(r.pos[1])), int(r.radius), 1)
                    pygame.draw.circle(self.screen, rgb2color(r.f_a[IDX_COLIDE],COLOR_BLACK), (int(r.pos[0]),int(r.pos[1])), int(r.radius*4.), 1)

            if DEBUG >= 2:

                # STATUS BARS
                for r in self.creatures:
                    # HEALTH/CALORIES
                    pygame.draw.line(self.screen, COLOR_WHITE, r.pos-10, [r.pos[0]+10,r.pos[1]-10], 1)
                    pygame.draw.line(self.screen, COLOR_WHITE, r.pos-10, [r.pos[0]-10+(r.f_a[IDX_CALORIES]*20),r.pos[1]-10], 4)
                    # TEXT
                    myfont = pygame.font.SysFont("monospace", 10)
                    label = myfont.render(str(r.generation), 1, COLOR_WHITE)
                    self.screen.blit(label, r.pos - [3,-6])

            if DEBUG >= 3:

                # GRID ON
                for l in range(0,self.N_ROWS*GRID_SIZE,GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_LIME, [0, l], [SCREEN[0],l], 1)
                for l in range(0,self.N_COLS*GRID_SIZE,GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_LIME, [l, 0], [l,SCREEN[1]], 1)

                # Selecting an object (for debugging)
                a_sth,sel_obj,square = self.check_collisions_p(pygame.mouse.get_pos(), 2., None, rext=0.)
                if sel_obj is not None and sel_obj.ID > 2:
                    pygame.draw.circle(self.screen, COLOR_WHITE, (int(sel_obj.pos[0]),int(sel_obj.pos[1])), int(sel_obj.radius*2), 1)
                    print "===================================="
                    print "Generation     ", sel_obj.generation
                    #print "Brain          "#, s.b.nodes
                    print "Observations   ", sel_obj.f_a
                    print "Outputs        ", sel_obj.velocity
                    print "Calories       ", sel_obj.calories

            #self.resources.update()                 # <-- doing this, don't need allSprites or DrawGroup
            #rects = self.resources.draw(self.screen)
            #self.resources.draw(self.screen)        # <-- doing this, don't need allSprites or DrawGroup
            #self.creatures.draw(self.screen)

            if DEBUG > 0:
                pygame.display.update(rects)
                pygame.display.flip()
                pygame.time.delay(FPS)



    def grid2pos(self,(x,y)):
        ''' grid reference to numpy coordinate array '''
        px = x * GRID_SIZE + 0.5 * GRID_SIZE
        py = y * GRID_SIZE + 0.5 * GRID_SIZE
        return array([px,py])

    def pos2grid(self,p):
        ''' position to grid reference '''
        rx = max(min(int(p[0]/GRID_SIZE),self.N_COLS-1),0)
        ry = max(min(int(p[1]/GRID_SIZE),self.N_ROWS-1),0)
        return rx,ry

    def add_to_reg(self, sprite):
        '''
            Register this 'sprite'.
        '''
        x,y = self.pos2grid(sprite.pos)
        c = self.regcount[x,y] 
        if c < MAX_GRID_DETECTION:
            self.register[x][y][c] = sprite
            self.regcount[x,y] = c + 1
        else:
            print "WARNING: Grid full, not registering!"
            exit(1)

    def check_collisions_p(self, s_point, s_radius, excl, rext=0.):
        '''
            Check Collisions
            -------------------------------------------------------------------------------

            Check for collisions of point 's_point' with radius 's_radius'
            -- excluding object 'excl' from search.

            If other radius 'rext' is specified, then consider this a collision, and 
            return (A,B,C) where
                A : the color of the object we collided with
                B : the object itself that we collided with (None if terrain)
                C : the type of terrain we collided with (None if object)

            TODO: take list of points and radii

            TODO: if touching object (inverse distance = 1, then all other objects are ignored)
        '''

        # We are currently in grid (x,y)
        x, y = self.pos2grid(s_point)

        # By default, we are not colliding with anything
        a = array([0.,0.,0.,])
        obj = None

        if self.terrain[y,x] > 0:
            # Already inside (clashing against) the wall
            a = array([1.,1.,1.,])
            return a, None, self.grid2pos((x,y))

        # else check with objects  @TODO WRAPPING MIGHT ACTUALLY BE EASIER?
        for i in [-1,0,+1]:
            p_x = min(max(x+i,0),self.N_COLS-1)
            for j in [-1,0,+1]:
                p_y = min(max(y+j,0),self.N_ROWS-1)

                lim = self.regcount[p_x,p_y]
                things = self.register[p_x][p_y]
                for i in range(lim):
                    if things[i] != excl:
                        # if not itself, take the distance ...
                        d = proximity(s_point,things[i].pos) - (s_radius + things[i].radius)
                        if d < -s_radius:
                            # actually touching, ... so return only for this object
                            return id2rgb[things[i].ID], things[i], None
                        elif d < 0.:
                            # in range, so calulate how much of the vision blocked
                            # (should be a function of radius and inverse distance) and add it to the input spectrum
                            a = a + id2rgb[things[i].ID] * -d / s_radius * 0.8
                            if rext > 0. and (proximity(s_point,things[i].pos) - (rext + things[i].radius)) < 0:
                                obj = things[i]

        # Should never be 1, even if really close -- only 1.0 if actually touching!
        # ... if we got this far, we didn't collide totally
        # TODO should be relative, sigmoid/logarithmic ?
        a[0] = clip(a[0],0.,0.9)
        a[1] = clip(a[1],0.,0.9)
        a[2] = clip(a[2],0.,0.9)
        return a, obj, None

#    def check_collisions(self, s, x, y):
#        # NOTE: NOT ACTUALLY USED ATM
#        '''
#            Check for collisions of sprite 's' in grid 'x,y' with all sprites.
#            -------------------------------------------------------------------------------
#        '''
#
#        for i in [-1,0,+1]:
#            p_x = min(max(x+i,0),self.N_COLS-1)
#            for j in [-1,0,+1]:
#                p_y = min(max(y+j,0),self.N_ROWS-1)
#                lim = self.regcount[p_x,p_y]
#                things = self.register[p_x][p_y]
#                for i in range(lim):
#                    if things[i] != s and proximity(s.pos,things[i].pos) <= (s.radius+things[i].radius):
#                        return things[i]
#        return None
