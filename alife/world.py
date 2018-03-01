#! /usr/bin/env python

import pygame

from graphics import *
from objects import *

# For saving and loading agents from disk
import joblib, glob, time, datetime

# Parameters
FPS = 60                     # <-- higher = less CPU
GRID_SIZE = 64               # tile size
VISION = GRID_SIZE*0.5       # vision in the murky waters
MAX_GRID_DETECTION = 100     # maximum number of objects that can be detected at once
RESOURCE_LIMIT = 1000        # maximum number of plants
TOUCH_THRESHOLD = 0.9        # maximum visual field occupied by color if not actually touching anything

def get_intensity(dist, radius):
    ''' 
        Return a pixel intensity for our vision depending (inversely) on 
        how close we are to something, and how large that thing is.
    '''
    return (-dist / radius) * (dist < 0.)

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
    ''' A random position somewhere on the screen (over land tiles) '''
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
        pygame.display.set_caption("ALife / Bug World")
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
            Creature((random_position(self)), dna = agents_available[random.choice(len(agents_available))], energy = 75, energy_limit = 150)
        for i in range(int(self.N_ROWS*FACTOR/6*2)):
            Creature((random_position(self)), dna = agents_available[random.choice(len(agents_available))], energy = 200, energy_limit = 400, ID = ID_PREDATOR, food_ID = ID_ANIMAL)

        self.allSprites.clear(self.screen, background)

        ## MAIN LOOP ##
        sel_obj = None 
        GRAPHICS_ON = True
        GRID_ON = False
        self.FPS = FPS
        while True:
            self.clock.tick(self.FPS)

            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g:
                        GRAPHICS_ON = (GRAPHICS_ON != True)
                    elif event.key == pygame.K_d:
                        GRID_ON = (GRID_ON != True)
                    elif event.key == pygame.K_s and sel_obj is not None:
                        print("Save ...")
                        #time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
                        sel_obj.brain.save("./dat/dna/", "./dat/log/", sel_obj.ID)
                    elif event.key == pygame.K_l:
                        print("Loading ...")
                        for filename in glob.glob('./dat/dna/*.dat'):
                            brain = pickle.load(open(filename, "rb"))
                            meta_data = filename.split(".")
                            ID = int(meta_data[2])
                            params = (100,200,int(meta_data[5]),ID,ID-1)
                            if ID == ID_PREDATOR:
                                params = (200,400,int(meta_data[5]),ID,ID-1)
                            print("Loaded Creature ID=%d from %s ..." % (params[3],filename))
                            Creature(array(pygame.mouse.get_pos()+random.randn(2)*GRID_SIZE),dna=brain, energy = params[0], energy_limit = params[1], ID = params[3], food_ID = params[4])
                    elif event.key == pygame.K_LEFT:
                        self.FPS = self.FPS - 10
                        print("FPS: %d" % self.FPS)
                    elif event.key == pygame.K_RIGHT:
                        self.FPS = self.FPS + 10
                        print("FPS: %d" % self.FPS)
                    elif event.key == pygame.K_DOWN:
                        prosperity = prosperity + 1
                        print("Lower energy influx (new plant every %d ticks)" % prosperity)
                    elif event.key == pygame.K_UP:
                        prosperity = prosperity - 1
                        print("Higher energy influx (new plant every %d ticks)" % prosperity)
                    elif event.key == pygame.K_r:
                        print("New Rock")
                        Thing(array(pygame.mouse.get_pos()),mass=500, ID=ID_ROCK)
                    elif event.key == pygame.K_p:
                        print("New Plant")
                        Thing(array(pygame.mouse.get_pos()), mass=100+random.rand()*1000, ID=ID_PLANT)
                    elif event.key == pygame.K_b:
                        agent = agents_available[random.choice(len(agents_available))]
                        print("New small Bug [%s]" % agent)
                        Creature(array(pygame.mouse.get_pos()), dna = agent)
                    elif event.key == pygame.K_u:
                        agent = agents_available[random.choice(len(agents_available))]
                        print("New big Bug [%s]" % agent)
                        Creature(array(pygame.mouse.get_pos()), dna = agent, energy = 200, energy_limit = 400, ID = ID_PREDATOR, food_ID = ID_ANIMAL)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print("Click")
                    a_sth,sel_obj,square = self.check_collisions(pygame.mouse.get_pos(), 20., None, collision_radius=0.)

            # Make sure there is a constant flow of resources/energy into the system
            step = step + 1
            if step % prosperity == 0 and len(self.plants) < RESOURCE_LIMIT:
                p = random_position(self)
                Thing(p, mass=100+random.rand()*1000, ID=ID_PLANT)
                print("Time step %d; %d bugs alive" % (step,len(self.creatures)))

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
                    pygame.draw.line(self.screen, rgb2color(r.observation[IDX_PROBE1],id2rgb[r.ID]), r.pos, r.pos+r.pa1, 1)
                    pygame.draw.line(self.screen, rgb2color(r.observation[IDX_PROBE2],id2rgb[r.ID]), r.pos, r.pos+r.pa2, 1)
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
                    # Body
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.observation[IDX_COLIDE],id2rgb[sel_obj.ID]), (int(sel_obj.pos[0]),int(sel_obj.pos[1])), int(sel_obj.radius + 3), 4)
                    # Rangers
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.observation[IDX_PROBE1],COLOR_BLACK), (int((sel_obj.pos+sel_obj.pa1)[0]),int((sel_obj.pos+sel_obj.pa1)[1])), int(sel_obj.radius*3.), 2)
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.observation[IDX_PROBE2],COLOR_BLACK), (int((sel_obj.pos+sel_obj.pa2)[0]),int((sel_obj.pos+sel_obj.pa2)[1])), int(sel_obj.radius*3.), 2)
                    pygame.draw.circle(self.screen, rgb2color(sel_obj.observation[IDX_COLIDE],COLOR_BLACK), (int(sel_obj.pos[0]),int(sel_obj.pos[1])), int(sel_obj.radius*4.), 3)
                    # Health/Calories/Energy level
                    pygame.draw.line(self.screen, COLOR_WHITE, sel_obj.pos-20, [sel_obj.pos[0]+20,sel_obj.pos[1]-20], 1)
                    pygame.draw.line(self.screen, COLOR_WHITE, sel_obj.pos-20, [sel_obj.pos[0]-20+(sel_obj.observation[IDX_ENERGY]*40),sel_obj.pos[1]-20], 5)

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
                pygame.time.delay(self.FPS)



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

    def closest_point_on_wall(self,p,tile,grid):
        ''' Return the point on border of tile=[x,y] which is closes to point p '''
        x = tile[0]
        tx,ty = grid
        tile_wall = self.grid2pos((tx,ty))
        if tx == x:
            # (tile is to the right or left)
            tile_wall[1] = p[1]
        else:
            # (tile is above or below)
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

    def check_collisions(self, s_point, s_radius, excl=None, collision_radius=0.):
        '''
            Check collisions of some circle s (defined by s_point and s_radius) in the world.

            The point and radius specified do not necessarily have to be a sprite.

            TODO: take list of points and radii
            TODO: if touching object (inverse distance = 1, then all other objects are ignored)

            Parameters
            ----------

            s_point : tuple (x,y)
                the centre point of the object of interest

            s_radius : float
                the radius of the object

            excl : Thing
                exclude this object from the search

            collision_radius : float
                if radius 'collision_radius' is specified, then return the object we collide with


            Returns
            -------
            
            A tuple (color,object,type) where 
                vision : the [R,G,B] color of the resulting collisions 
                thing : the Thing that we collided with (None if terrain)
                type : the type of terrain we collided with (None if Thing)

        '''

        # We are currently in grid (x,y)
        x, y = self.pos2grid(s_point)

        # By default, we don't see anything (pure blackness)
        vision = array([0.,0.,0.,])
        thing = None

        if self.terrain[y,x] > 0:
            # We are colliding with (over) impassable terrain
            vision = array([1.,1.,1.,])
            return vision, None, self.grid2pos((x,y))

        # Check collisions with objects in current and neighbouring tiles  
        for i in [-1,0,+1]:
            p_x = (x + i) % self.N_COLS
            for j in [-1,0,+1]:
                p_y = (y + j) % self.N_ROWS

                # If we are looking at terrain ...
                if i != 0 and j != 0 and self.terrain[p_y,p_x] > 0:
                    # ... check proximity to it.
                    wall_point = self.closest_point_on_wall(s_point,(x,y),(p_x,p_y))
                    d = proximity(s_point, wall_point) - (s_radius + (GRID_SIZE * 0.5)) # (wall 'radius' is half a tile)
                    vision = vision + id2rgb[ID_ROCK] * get_intensity(d,s_radius)

                # Check for collisions with other objects in this tile
                things = self.register[p_x][p_y]
                for i in range(self.regcount[p_x,p_y]):
                    # Check if I should skip this object
                    if things[i] != excl:
                        # Else, how far are we from it ?
                        d = proximity(s_point,things[i].pos) - (s_radius + things[i].radius)
                        if d < -s_radius:
                            # We are touching, return this object.
                            return id2rgb[things[i].ID], things[i], None
                        elif d < 0.:
                            # We are in visual range, add the relevant intensity to our 'vision'
                            vision = vision + id2rgb[things[i].ID] * get_intensity(d, s_radius)
                            if  collision_radius > 0. and (proximity(s_point,things[i].pos) - (collision_radius + things[i].radius)) < 0:
                                thing = things[i]

        # We should only reach 1.0 if actually touching, even if visual field is overwhelmed;
        # (and if we got this far, we are not touching anything)
        vision = clip(vision,0.0,TOUCH_THRESHOLD) # TODO could be relative, sigmoid/logarithmic ?
        return vision, thing, None

