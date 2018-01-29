#! /usr/bin/env python

import pygame

import joblib, glob, time, datetime        # <-- for saving and loading agents from disk

from graphics import *
from objects import *

# Parameters
FPS = 60                                    # <-- higher = less CPU
GRID_SIZE = 64                              # tile size
VISION = GRID_SIZE*0.5                      # vision in the murky waters
MAX_GRID_DETECTION = 100                    # maximum number of objects that can be detected at once
RESOURCE_LIMIT = 1000                       # maximum number of plants

class DrawGroup(pygame.sprite.Group):
    def draw(self, surface):
        for s in self.sprites():
            s.draw(surface)

def load_map(s):
    ''' load a map from a text file '''
    MAP = zeros((10,10),dtype=int)
    if s is not None:
        MAP = genfromtxt(s, delimiter = 1, dtype=str)
    return MAP[1:-1,1:-1]

def get_list(filename):
    with open(filename) as f:
        return f.read().splitlines()

def random_position(world):
    ''' A random position somewhere on the screen '''
    # TODO: only return positions over land!
    k = random.choice(world.terrain.shape[0])
    j = random.choice(world.terrain.shape[1])
    while world.terrain[k,j] > 0:
        k = random.choice(world.terrain.shape[0])
        j = random.choice(world.terrain.shape[1])
    return world.grid2pos((j,k)) + random.randn(2) * GRID_SIZE/3.

class World:

    def __init__(self,fname=None,init_sprites=2):

        map_codes = load_map(fname)                  # load the map
        self.N_ROWS = map_codes.shape[0]
        self.N_COLS = map_codes.shape[1]
        self.WIDTH = self.N_COLS * GRID_SIZE
        self.HEIGHT = self.N_ROWS * GRID_SIZE
        SCREEN = array([self.WIDTH, self.HEIGHT])

        step = 0
        prosperity = 50

        ## GRID REGISTER and GRID COUNT 
        self.register = [[[None for l in range(MAX_GRID_DETECTION)] for k in range(self.N_ROWS)] for j in range(self.N_COLS)]
        self.regcount = zeros(map_codes.shape,int) 

        ## INIT ##
        pygame.display.set_caption("ALife")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))#, HWSURFACE|DOUBLEBUF)
        pygame.mouse.set_visible(1)

        ## BACKGROUND ##
        from graphics import build_map_png as build_map
        background, self.terrain = build_map(self.screen.get_size(),self.N_COLS,self.N_ROWS,GRID_SIZE,map_codes)

        ## DISPLAY THE BACKGROUND ##
        self.screen.blit(background, [0, 0])
        pygame.display.flip()

        ## SPRITES ##
        self.allSprites = DrawGroup()
        self.creatures = pygame.sprite.Group()
        self.plants = pygame.sprite.Group()
        self.rocks = pygame.sprite.Group()
        self.stumps = pygame.sprite.Group()

        Creature.containers = self.allSprites, self.creatures
        Thing.containers = self.allSprites, self.plants

        self.clock = pygame.time.Clock()
        
        # Some rocks and plants
        FACTOR = init_sprites
        for i in range(int(self.N_ROWS*((FACTOR/2)**2))):
            Thing(random_position(self), mass=100+random.rand()*1000, ID=ID_ROCK)
        for i in range(int(self.N_ROWS*((FACTOR/2)**2))):
            Thing(random_position(self), mass=100+random.rand()*1000, ID=ID_PLANT)

        # Get a list of the agents we may deploy 
        agents_available = get_list('agents_to_use.txt')

        # Some animate creatures
        for i in range(int(self.N_ROWS*FACTOR/4*2)):
            Creature((random_position(self)), dna = agents_available[random.choice(len(agents_available))], cal = 75, lim = 150)
        for i in range(int(self.N_ROWS*FACTOR/6*2)):
            Creature((random_position(self)), dna = agents_available[random.choice(len(agents_available))], cal = 200, lim = 400, ID = ID_PREDATOR, food_ID = ID_ANIMAL)

        self.allSprites.clear(self.screen, background)

        ## MAIN LOOP ##
        sel_obj = None 
        GRAPHICS_ON = True
        GRID_ON = False
        while True:
            self.clock.tick(FPS)
            save_to_file = False

            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        GRAPHICS_ON = (GRAPHICS_ON != True)
                    elif event.key == pygame.K_d:
                        GRID_ON = (GRID_ON != True)
                    elif event.key == pygame.K_s:
                        save_to_file = True
                    elif event.key == pygame.K_l:
                        print("Loading ...")
                        for filename in glob.glob('./dat/dna/*.dat'):
                            brain = pickle.load(open(filename, "rb"))
                            meta_data = filename.split(".")
                            ID = int(meta_data[2])
                            params = (100,200,int(meta_data[5]),ID,ID_PLANT)
                            if ID == ID_PREDATOR:
                                params = (200,400,int(meta_data[5]),ID,ID_ANIMAL)
                            print("Loaded Creature ID=%d (Gen. %d) from %s ..." % (params[3],params[2],filename))
                            Creature(array(pygame.mouse.get_pos()),dna=brain,generation = params[2], cal = params[0], lim = params[1], ID = params[3], food_ID = params[4])
                    elif event.key == pygame.K_DOWN:
                        prosperity = prosperity + 1
                        print("Lower energy influx (new plant every %d ticks)" % prosperity)
                    elif event.key == pygame.K_UP:
                        prosperity = prosperity - 1
                        print("Higher energy influx (new plant every %d ticks)" % prosperity)
                    elif event.key == pygame.K_k:
                        print("New Rock")
                        Thing(array(pygame.mouse.get_pos()),mass=500, ID=ID_ROCK)
                    elif event.key == pygame.K_r:
                        print("New Plant")
                        Thing(array(pygame.mouse.get_pos()), mass=100+random.rand()*1000, ID=ID_PLANT)
                    elif event.key == pygame.K_h:
                        agent = agents_available[random.choice(len(agents_available))]
                        print("New Creature [%s]" % agent)
                        Creature(array(pygame.mouse.get_pos()), dna = agent)
                    elif event.key == pygame.K_p:
                        agent = agents_available[random.choice(len(agents_available))]
                        print("New Predator [%s] % agent")
                        Creature(array(pygame.mouse.get_pos()), dna = agent, cal = 200, lim = 400, ID = ID_PREDATOR, food_ID = ID_ANIMAL)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print("Click")
                    a_sth,sel_obj,square = self.check_collisions_p(pygame.mouse.get_pos(), 20., None, rext=0.)

            # Make sure there is a constant flow of resources/energy into the system
            step = step + 1
            if step % prosperity == 0 and len(self.plants) < RESOURCE_LIMIT:
                p = random_position(self)
                Thing(p, mass=100+random.rand()*1000, ID=ID_PLANT)
                print("Time step %d; %d creatures alive" % (step,len(self.creatures)))

            # Reset reg-counts
            self.regcount = zeros((self.N_COLS,self.N_ROWS),int) 
            # Register all sprites
            for r in self.allSprites:
                self.add_to_register(r)

            ## Routine
            for r in self.allSprites:
                r.live(self)

            if GRAPHICS_ON:

                # Draw
                self.allSprites.update()
                self.screen.blit(background, [0, 0])

            if GRAPHICS_ON:

                for r in self.creatures:
                    # Feelers
                    pygame.draw.line(self.screen, rgb2color(r.state[IDX_PROBE1],id2rgb[r.ID]), r.pos, r.pos+r.pa1, 1)
                    pygame.draw.line(self.screen, rgb2color(r.state[IDX_PROBE2],id2rgb[r.ID]), r.pos, r.pos+r.pa2, 1)
                    # Tail / Wings
                    if norm(r.velocity) > FLIGHT_SPEED:
                        # (if in flight)
                        u = unitv(r.velocity)
                        wing1 = rotate(u * r.radius*2,+pi/2.8)
                        wing2 = rotate(u * r.radius*2,-pi/2.8)
                        #pygame.draw.line(self.screen, id2rgb[r.ID], r.pos, r.pos+(r.velocity * -5.), 2)
                        pygame.draw.line(self.screen, id2rgb[r.ID], r.pos, r.pos-wing1, 6)
                        pygame.draw.line(self.screen, id2rgb[r.ID], r.pos, r.pos-wing2, 6)

                # Selecting an object (for debugging)
                if sel_obj is not None and sel_obj.ID > 3:
                    #pygame.draw.circle(self.screen, COLOR_WHITE, (int(sel_obj.pos[0]),int(sel_obj.pos[1])), int(sel_obj.radius*2), 3)
                    anchor = self.WIDTH/4
                    pygame.draw.rect(self.screen, COLOR_BLACK, (anchor,5,self.WIDTH/2,25))
                    myfont = pygame.font.SysFont("monospace", 17)
                    s = str(sel_obj)
                    label = myfont.render(s, 1, COLOR_WHITE)
                    self.screen.blit(label, [anchor+1,6])
                    if save_to_file:
                        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
                        fname = ("./dat/dna/Obj.%d.%s.%s.%d.%s.dat" % (sel_obj.ID,str(sel_obj.__class__.__name__),str(sel_obj.brain.__class__.__name__),sel_obj.generation,str(st)))
                        sel_obj.brain.save(fname)
                        print("Saved agent to '%s'." % fname)
                    # Body
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.state[IDX_COLIDE],id2rgb[sel_obj.ID]), (int(sel_obj.pos[0]),int(sel_obj.pos[1])), int(sel_obj.radius + 3), 4)
                    # Rangers
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.state[IDX_PROBE1],COLOR_BLACK), (int((sel_obj.pos+sel_obj.pa1)[0]),int((sel_obj.pos+sel_obj.pa1)[1])), int(sel_obj.radius*3.), 2)
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.state[IDX_PROBE2],COLOR_BLACK), (int((sel_obj.pos+sel_obj.pa2)[0]),int((sel_obj.pos+sel_obj.pa2)[1])), int(sel_obj.radius*3.), 2)
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.state[IDX_COLIDE],COLOR_BLACK), (int(sel_obj.pos[0]),int(sel_obj.pos[1])), int(sel_obj.radius*4.), 3)
                    # Health/Calories/Energy level
                    pygame.draw.line(self.screen, COLOR_WHITE, sel_obj.pos-20, [sel_obj.pos[0]+20,sel_obj.pos[1]-20], 1)
                    pygame.draw.line(self.screen, COLOR_WHITE, sel_obj.pos-20, [sel_obj.pos[0]-20+(sel_obj.state[IDX_ENERGY]*40),sel_obj.pos[1]-20], 5)

            if GRID_ON:

                # GRID ON
                for l in range(0,self.N_ROWS*GRID_SIZE,GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_WHITE, [0, l], [SCREEN[0],l], 1)
                for l in range(0,self.N_COLS*GRID_SIZE,GRID_SIZE):
                    pygame.draw.line(self.screen, COLOR_WHITE, [l, 0], [l,SCREEN[1]], 1)

            #self.plants.update()                 # <-- doing this, don't need allSprites or DrawGroup
            #rects = self.plants.draw(self.screen)
            #self.plants.draw(self.screen)        # <-- doing this, don't need allSprites or DrawGroup
            #self.creatures.draw(self.screen)

            if GRAPHICS_ON:
                rects = self.allSprites.draw(self.screen)
                pygame.display.update(rects)
                pygame.display.flip()
                pygame.time.delay(FPS)



    def grid2pos(self,xy):
        ''' grid reference to numpy coordinate array '''
        x,y = xy
        px = x * GRID_SIZE + 0.5 * GRID_SIZE
        py = y * GRID_SIZE + 0.5 * GRID_SIZE
        return array([px,py])

    def pos2grid(self,p):
        ''' position to grid reference TODO: WRAP? '''
        rx = max(min(int(p[0]/GRID_SIZE),self.N_COLS-1),0)
        ry = max(min(int(p[1]/GRID_SIZE),self.N_ROWS-1),0)
        return rx,ry

    def point_on_the_wall_closest_to_me(self,p,tile,grid):
        ''' I am at point p in square tile = (x,y), return the closest point of the tile with centre (tx,ty) '''
        x = tile[0]
        tx,ty = grid
        tile_wall = self.grid2pos((tx,ty))
        if tx == x:
            # (tile is to the right or left)
            tile_wall[1] = p[1]
        else:
            # (tile is above or below)
            tile_wall = self.grid2pos((tx,ty))
            tile_wall[0] = p[0]
        return tile_wall

    def add_to_register(self, sprite):
        '''
            Register this sprite.
        '''
        x,y = self.pos2grid(sprite.pos)
        c = self.regcount[x,y] 
        if c < MAX_GRID_DETECTION:
            self.register[x][y][c] = sprite
            self.regcount[x,y] = c + 1
        else:
            print("WARNING: Grid full, not registering!")
            exit(1)

    def check_collisions_p(self, s_point, s_radius, excl, rext=0.):
        '''
            Check Collisions
            -------------------------------------------------------------------------------

            Check for collisions of point 's_point' with radius 's_radius'
            -- excluding object 'excl' from search.
            -- If radius 'rext' is specified, then consider this a collision.

            Return (A,B,C) where
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

        # Check collisions with objects in current and neighbouring tiles  
        # (TODO: Wrapping might actually be easier!)
        for i in [-1,0,+1]:
            p_x = (x + i) % self.N_COLS
            # p_x = min(max(x+i,0),self.N_COLS-1)
            for j in [-1,0,+1]:
                p_y = (y + j) % self.N_ROWS
                # p_y = min(max(y+j,0),self.N_ROWS-1)

                # This tile is terrain -- check for proximity with it!
                if i != 0 and j != 0 and self.terrain[p_y,p_x] > 0:
                    wall_point = self.point_on_the_wall_closest_to_me(s_point,(x,y),(p_x,p_y))
                    d = proximity(s_point, wall_point) - (s_radius + (GRID_SIZE * 0.5)) # (wall 'radius' is half a tile)
                    if d < 0.:
                        # In visual range, so calulate how much of the vision blocked (as done below) ...
                        a = a + id2rgb[ID_ROCK] * -d / s_radius

                # The neighbouring tile is empty -- check for collisions with other objects!
                things = self.register[p_x][p_y]
                for i in range(self.regcount[p_x,p_y]):
                    # Is this object something other than myself? 
                    if things[i] != excl:
                        # How far are we from it ?
                        d = proximity(s_point,things[i].pos) - (s_radius + things[i].radius)
                        if d < -s_radius:
                            # We are touching! Return this object.
                            return id2rgb[things[i].ID], things[i], None
                        elif d < 0.:
                            # In visual range, so calulate how much of the vision blocked 
                            # (should be a function of radius [i.e., weight] and inverse distance [to target]) 
                            # ... and add it to the input spectrum
                            a = a + id2rgb[things[i].ID] * -d / s_radius
                            if  rext > 0. and (proximity(s_point,things[i].pos) - (rext + things[i].radius)) < 0:
                                obj = things[i]

        # We should only reach 1.0 if actually touching, even if visual field is overwhelmed;
        # (if we got this far, we didn't collide totally)
        # TODO should be relative, sigmoid/logarithmic ?
        a = clip(a,0.0,0.9)
        #a = clip(0.95/(1. + exp(-a-1.)),0.0,0.95)
        #print("a",a)
        return a, obj, None

