#! /usr/bin/env python

import pygame

import joblib
from locals import *
from objects import *

class DrawGroup(pygame.sprite.Group):
    def draw(self, surface):
        for s in self.sprites():
            s.draw(surface)

class World:

    def __init__(self):

        self.terrain = MAP.T
        count = 0
        prosperity = 50

        ## GRID REGISTER and GRID COUNT 
        self.register = [[[None for l in xrange(MAX_GRID_DETECTION)] for k in xrange(N_ROWS)] for j in xrange(N_COLS)]
        self.regcount = zeros(self.terrain.shape,int) 

        ## INIT ##
        pygame.display.set_caption("ALife")
        self.screen = pygame.display.set_mode((SCREEN[0], SCREEN[1]))#, HWSURFACE|DOUBLEBUF)
        pygame.mouse.set_visible(1)

        ## BACKGROUND ##
        background = pygame.Surface(self.screen.get_size())
        background.fill([0, 0, 0])                  # fill with black
        for j in range(N_COLS):
            for k in range(N_ROWS):
                if self.terrain[j,k] > 0:
                    background.fill([250, 250, 250], rect=(j*GRID_SIZE,k*GRID_SIZE,GRID_SIZE,GRID_SIZE))            # rock
        background = background.convert()           # can speed up when we have an 'intense' background

        ## DISPLAY THE BACKGROUND ##
        self.screen.blit(background, [0, 0])
        pygame.display.flip()

        ## SPRITES ##
        self.allSprites = DrawGroup()
        self.herbivors = pygame.sprite.Group()
        self.resources = pygame.sprite.Group()
        self.rocks = pygame.sprite.Group()
        self.stumps = pygame.sprite.Group()

        Herbivore.containers = self.allSprites, self.herbivors
        Resource.containers = self.allSprites, self.resources
        Rock.containers = self.allSprites, self.rocks

        self.clock = pygame.time.Clock()
        
        FACTOR = 2
        for i in range(N_ROWS*((FACTOR/2)**2)):
            Resource(random_position())
        for i in range(N_ROWS*FACTOR/4*2):
            Herbivore((random_position()), cal = 75, lim = 150)
        for i in range(N_ROWS*FACTOR/6*2):
            Herbivore((random_position()),cal = 200, lim = 200, color = COLOR_RED, food_ID = ID_ANIMAL)

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
                        for s in self.herbivors:
                            joblib.dump( s.b,  "./dat/H_gen"+str(s.generation)+"_brain.dat")
                        print "SAVED."
                    elif event.key == pygame.K_l:
                        print "LOADING ..."
                        for g in range(71,77):
                            b = joblib.load( "./dat/H_gen"+str(g)+"_brain.dat")
                            Herbivore(random_position(),dna=b,generation=g)
                        print "LOADED."
                    elif event.key == pygame.K_DOWN:
                        prosperity = prosperity + 1
                        print "LOWER ENERGY INFLUX", prosperity
                    elif event.key == pygame.K_UP:
                        prosperity = prosperity - 1
                        print "HIGHER ENERGY INFLUX", prosperity
                    elif event.key == pygame.K_k:
                        print "NEW ROCK"
                        Rock(array(pygame.mouse.get_pos()),mass=30+random.rand()*1000)
                    elif event.key == pygame.K_r:
                        print "NEW RESOURCE"
                        for i in range(10):
                            Resource(random_position())
                    elif event.key == pygame.K_h:
                        print "NEW HERBIVORES"
                        for i in range(5):
                            Herbivore((random_position()))
                    elif event.key == pygame.K_p:
                        print "NEW PREDATOR"
                        Herbivore((random_position()),cal = 200, lim = 400, color = COLOR_RED, food_ID = ID_ANIMAL)
                    elif event.key == pygame.K_i:
                        print "SPRITE INFO"
                        for s in self.herbivors:
                            print "===================================="
                            print "Happiness      ", s.happiness
                            print "Generation     ", s.generation
                            print "Brain          "#, s.b.nodes

            # Make sure there is a constant flow of resources/energy into the system
            count = count + 1
            if count > prosperity and len(self.resources) < 100:
                print "*SPAWNED A NEW RESOURCE*", len(self.resources)
                Resource(random_position())
                count = 0

            # Reset reg-counts
            self.regcount = zeros((N_COLS,N_ROWS),int) 
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

                for r in self.herbivors:
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
                for r in self.herbivors:
                    # HEALTH/CALORIES
                    pygame.draw.line(self.screen, COLOR_WHITE, r.pos-10, [r.pos[0]+10,r.pos[1]-10], 1)
                    pygame.draw.line(self.screen, COLOR_WHITE, r.pos-10, [r.pos[0]-10+(r.f_a[IDX_CALORIES]*20),r.pos[1]-10], 4)
                    # HAPPINESS
                    pygame.draw.line(self.screen, COLOR_YELLOW, r.pos-15, [r.pos[0]+15,r.pos[1]-15], 1)
                    pygame.draw.line(self.screen, COLOR_YELLOW, r.pos-15, [r.pos[0]-15+(r.happiness * 30),r.pos[1]-15], 4)
                    # TEXT
                    myfont = pygame.font.SysFont("monospace", 10)
                    label = myfont.render(str(r.generation), 1, COLOR_WHITE)
                    self.screen.blit(label, r.pos - [3,-6])

            if DEBUG >= 3:

                # GRID ON
                for l in range(0,N_ROWS*GRID_SIZE,GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_LIME, [0, l], [SCREEN[0],l], 1)
                for l in range(0,N_COLS*GRID_SIZE,GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_LIME, [l, 0], [l,SCREEN[1]], 1)

            #self.resources.update()                 # <-- doing this, don't need allSprites or DrawGroup
            #rects = self.resources.draw(self.screen)
            #self.resources.draw(self.screen)        # <-- doing this, don't need allSprites or DrawGroup
            #self.herbivors.draw(self.screen)

            if DEBUG > 0:
                pygame.display.update(rects)
                pygame.display.flip()
                pygame.time.delay(FPS)



    def add_to_reg(self, sprite):
        '''
            Register this 'sprite'.
        '''
        x,y = pos2grid(sprite.pos)
        c = self.regcount[x,y] 
        if c < MAX_GRID_DETECTION:
            self.register[x][y][c] = sprite
            self.regcount[x,y] = c + 1
        else:
            print "WARNING: Grid full, not registering!"
            exit(1)

    def check_collisions_wall(self, spos, sr):
        '''
            TODO: combine elegantly with check_collisions_p
        '''

        # if collide with wall
        x, y = pos2grid(spos)
        if self.terrain[x,y] > 0:
            return True

        #if distance_from_left_wall() > sr:
        #    print " sensing the wall! " 
        #for j in [-1,+1]:
        #    if self.terrain[pos2grid(spos + i*[sr[0],0]]) > 0:

    def check_collisions_p(self, spos, sr, excl, rext=0.):
        '''
            Check Collisions
            -------------------------------------------------------------------------------
            Check for collisions of point 'spos' with radius 'sr' in grid 'x,y',
            excluding object 'excl' from search.
            If other radius 'rext' is specified, then consider this a collision, and return 
            any collided object as 'obj'.

            TODO: take list of points and radii
        '''
        x, y = pos2grid(spos)
        a = array([0.,0.,0.,])
        obj = None

        if self.terrain[x,y] > 0:
            a = array([1.,1.,1.,])
            return a, None

        # check with wall
        #for i in [-1,+1]:
        #    if self.terrain[pos2grid(spos + i*[sr[0],0])] > 0:
        #        wall = int(round(spos[0]/GRID_SIZE))
        #        a[:] = a[:] + (sr-abs([wall,spos[1]] - spos))/sr
        #for i in [-1,+1]:
        #    if self.terrain[pos2grid(spos + i*[0,sr[1]])] > 0:
        #        wall = int(round(spos[1]/GRID_SIZE))
        #        a[:] = a[:] + (sr-abs([spos[0],wall] - spos))/sr

        # else check with objects  @TODO WRAPPING MIGHT ACTUALLY BE EASIER?
        for i in [-1,0,+1]:
            p_x = min(max(x+i,0),N_COLS-1)
            for j in [-1,0,+1]:
                p_y = min(max(y+j,0),N_ROWS-1)

                lim = self.regcount[p_x,p_y]
                things = self.register[p_x][p_y]
                for i in range(lim):
                    if things[i] != excl:
                        # 0 if it is out of range, else inverse distance
                        d = proximity(spos,things[i].pos) - (sr + things[i].radius)
                        if d < 0.:
                            a = a + id2rgb(things[i].ID) * -d / sr
                            if rext > 0. and (proximity(spos,things[i].pos) - (rext + things[i].radius)) < 0:
                                obj = things[i]

        #TODO should be relative, sigmoid/logarithmic?
        a[0] = clip(a[0],0.,1.)
        a[1] = clip(a[1],0.,1.)
        a[2] = clip(a[2],0.,1.)
        return a, obj

    def check_collisions(self, s, x, y):
        '''
            Check for collisions of sprite 's' in grid 'x,y' with all sprites.
            -------------------------------------------------------------------------------
        '''

        for i in [-1,0,+1]:
            p_x = min(max(x+i,0),N_COLS-1)
            for j in [-1,0,+1]:
                p_y = min(max(y+j,0),N_ROWS-1)
                lim = self.regcount[p_x,p_y]
                things = self.register[p_x][p_y]
                for i in range(lim):
                    if things[i] != s and proximity(s.pos,things[i].pos) <= (s.radius+things[i].radius):
                        return things[i]
        return None
