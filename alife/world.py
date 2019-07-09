#! /usr/bin/env python

import pygame

import time
import yaml

from graphics import *
from objects import *

# Parameters
TILE_SIZE = 64               # tile size (width and height, in pixels)
MAX_GRID_DETECTION = 100     # maximum number of objects that can be detected at once

class DrawGroup(pygame.sprite.Group):
    def draw(self, surface):
        for s in self.sprites():
            s.draw(surface)

def load_map(fname):
    ''' Load a map from a text file '''
    MAP = zeros((10,10),dtype=int)
    if fname is not None:
        MAP = genfromtxt(fname, delimiter = 1, dtype=str)
    return MAP[1:-1,1:-1]

def get_conf(fname='conf.yml',section='world'):
    #return yaml.load(open(fname), Loader=yaml.FullLoader)[section]
    return yaml.load(open(fname))[section]

class World:
    """
        A generic world (environment) that objects exist in. 

        * Can be used for either Arcade, RPG, or RTS-style game. 
        * Sprite-specific logic is handled in objects.py.
    """

    def __init__(self,fname=None,init_sprites=2):

        # Load the configuration
        cfg = get_conf(section='world')
        FPS = cfg['fps']

        map_codes = load_map(fname)                  # load the map
        self.N_ROWS = map_codes.shape[0]
        self.N_COLS = map_codes.shape[1]
        self.WIDTH = self.N_COLS * TILE_SIZE
        self.HEIGHT = self.N_ROWS * TILE_SIZE
        SCREEN = array([self.WIDTH, self.HEIGHT])

        ## GRID REGISTER and GRID COUNT 
        self.register = [[[None for l in range(MAX_GRID_DETECTION)] for k in range(self.N_ROWS)] for j in range(self.N_COLS)]
        #self.regcount = zeros(map_codes.shape,int) 
        self.regcount = zeros((self.N_COLS,self.N_ROWS),int) 

        ## INIT ##
        pygame.display.set_caption("ALife / Bug World [map: %s]" % fname)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))#, HWSURFACE|DOUBLEBUF)
        pygame.mouse.set_visible(1)

        ## BACKGROUND ##
        from graphics import build_map_png as build_map
        background, self.terrain = build_map(self.screen.get_size(),self.N_COLS,self.N_ROWS,TILE_SIZE,map_codes)

        ## DISPLAY THE BACKGROUND ##
        self.screen.blit(background, [0, 0])
        pygame.display.flip()

        ## SPRITES ##
        self.allSprites = DrawGroup()
        self.creatures = pygame.sprite.Group()
        self.plants = pygame.sprite.Group()
        self.splatters = pygame.sprite.Group()

        Creature.containers = self.allSprites, self.creatures
        Thing.containers = self.allSprites, self.plants
        Splatter.containers = self.splatters

        self.clock = pygame.time.Clock()
        info_text = "Loading .."
        self.score = {}
        
        # Some rocks and plants
        FACTOR = init_sprites
        for i in range(int(self.N_ROWS*FACTOR/10*self.N_COLS)):
            Thing(self.random_position(), mass=100+random.rand()*1000, ID=ID_ROCK)
        for i in range(int(self.N_ROWS*FACTOR/5*self.N_COLS)):
            Thing(self.random_position(), mass=100+random.rand()*cfg['max_plant_size'], ID=ID_PLANT)
        # The flag!
        self.flag = Thing(self.random_position(), mass=800, ID=ID_MISC)

        # Get a list of the agents we may deploy 
        agents = get_conf(section='bugs').values()

        self.allSprites.clear(self.screen, background)

        ## MAIN LOOP ##
        growth_rate = cfg['growth_rate']             # How often to change iteration / add a plant
        step = 0                                     # Current iteration
        selected_obj = None 
        GRAPHICS_ON = True
        GRID_ON = False
        INFO_ON = False
        self.FPS = FPS
        while True:
            self.clock.tick(self.FPS)

            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                if event.type == pygame.KEYUP:
                    if selected_obj is not None:
                        selected_obj.selected = array([-0.0,0.])
                if event.type == pygame.KEYDOWN:
                    if selected_obj is not None:
                        # Human intervention in selected agent
                        if event.key == pygame.K_UP:
                            selected_obj.selected = array([-0.0,3.])
                        elif event.key == pygame.K_DOWN:
                            selected_obj.selected = array([-0.0,10.1])
                        if event.key == pygame.K_RIGHT:
                            selected_obj.selected = array([+pi/8,0.])
                        elif event.key == pygame.K_LEFT:
                            selected_obj.selected = array([-pi/8,0.])
                        if event.key == pygame.K_DELETE:
                            self.remove_score(selected_obj.ssID)
                            selected_obj.kill()
                    if event.key == pygame.K_g:
                        GRAPHICS_ON = (GRAPHICS_ON != True)
                    elif event.key == pygame.K_d:
                        GRID_ON = (GRID_ON != True)
                    elif event.key == pygame.K_s and selected_obj is not None:
                        # WARNING: MAY NOT BE IMPLEMENTED IN ALL OBJECTS
                        selected_obj.brain.save("./dat/dna/")
                        print("[Saved] ...")
                    elif event.key == pygame.K_l:
                        # TODO FIX
                        print("[Warning] Functionality currently broken ...")
                        #for filename in glob.glob('./dat/dna/*.dat'):
                        #    brain = pickle.load(open(filename, "rb"))
                        #    meta_data = filename.split(".")
                        #    ID = int(meta_data[2])
                        #    params = (200,200,int(meta_data[5]),ID,ID-1)
                        #    if ID == ID_OTHER:
                        #        params = (200,400,int(meta_data[5]),ID,ID-1)
                        #    print("Loaded Creature ID=%d from %s ..." % (params[3],filename))
                        #    Creature(array(pygame.mouse.get_pos()+random.randn(2)*TILE_SIZE),dna=brain, energy = params[0], ID = params[3])
                    elif event.key == pygame.K_PLUS:
                        self.FPS = self.FPS + 50
                        print("FPS: %d" % self.FPS)
                    elif event.key == pygame.K_MINUS:
                        self.FPS = self.FPS - 50
                        print("FPS: %d" % self.FPS)
                    elif event.key == pygame.K_COMMA:
                        growth_rate = growth_rate + 100
                        print("Lower energy influx (new plant every %d ticks)" % growth_rate)
                    elif event.key == pygame.K_PERIOD:
                        growth_rate = max(growth_rate - 100,10)
                        print("Higher energy influx (new plant every %d ticks)" % growth_rate)
                    elif event.key == pygame.K_1:
                        # Add a rock
                        Thing(array(pygame.mouse.get_pos()),mass=500, ID=ID_ROCK)
                    elif event.key == pygame.K_2:
                        # Change Flag Position
                        self.flag.pos = array(pygame.mouse.get_pos())
                    elif event.key == pygame.K_3:
                        # Add a plant
                        Thing(array(pygame.mouse.get_pos()), mass=100+random.rand()*cfg['max_plant_size'], ID=ID_PLANT)
                    elif event.key >= pygame.K_4 and event.key <= pygame.K_9:
                        K = event.key - pygame.K_4
                        if len(agents) > K:
                            print("New Bug")
                            Creature(array(pygame.mouse.get_pos()), dna = list(agents)[K], ID = ID_ANIMAL + K)
                    elif event.key == pygame.K_r:
                        print("=== RESET SCORE ===")
                        self.score = {}
                    elif event.key == pygame.K_h:
                        INFO_ON = (INFO_ON != True)
                        print("=== HELP ===")
                        # TODO Add to banner/text here

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print("Click")
                    if selected_obj is not None:
                        selected_obj.selected = None
                    selected_obj = self.quick_collision(pygame.mouse.get_pos())

            # Make sure there is a constant flow of resources/energy into the system
            step = step + 1
            if step % growth_rate == 0:
                #n_plants = len(self.plants)
                #p = self.random_position()
                #if p is not None and n_plants < 30:
                #    Thing(p, mass=100+random.rand()*cfg['max_plant_size'], ID=ID_PLANT)
                # Update the banner info (we do this each growth tick)
                info_text = "Stats and Scores:\n%d ticks\n%d bugs, %d objs\n" % (step,len(self.creatures),len(self.plants))
                for key,val in self.score.items():
                    info_text += "| %s: %7.1f\n" % (key,val)
                print(info_text)

            # Reset reg-counts and Register all sprites
            self.regcount = zeros((self.N_COLS,self.N_ROWS),int) 
            for r in self.allSprites:
                self.add_to_register(r)

            # Routine
            for r in self.allSprites:
                r.live(self)
            for r in self.splatters:
                r.live(self)

            if GRAPHICS_ON:

                # Update sprites
                self.allSprites.update()
                # Draw the background (TODO later: redraw only active tiles)
                self.screen.blit(background, [0,0]) 
                # Draw the grid (and anything else useful for debugging)
                if GRID_ON:
                    # GRID ON
                    for l in range(0,self.N_ROWS*TILE_SIZE,TILE_SIZE):
                        pygame.draw.line(self.screen, COLOR_WHITE, [0, l], [SCREEN[0],l], 1)
                    for l in range(0,self.N_COLS*TILE_SIZE,TILE_SIZE):
                        pygame.draw.line(self.screen, COLOR_WHITE, [l, 0], [l,SCREEN[1]], 1)
                # Draw splatter
                self.splatters.update()
                more_rects = self.splatters.draw(self.screen)
                pygame.display.update(more_rects)
                # Draw the sprites (TODO later: redraw only the 'dirty' sprites)
                rects = self.allSprites.draw(self.screen)
                # Draw the selected sprite
                if selected_obj is not None:
                    selected_obj.draw_selected(self.screen)
                # Draw text info/help
                if INFO_ON:
                    draw_banner(self.screen, info_text, align='r')
                # Display
                pygame.display.update(rects)
                pygame.display.flip()
                pygame.time.delay(self.FPS)

    def remove_score(self, name):
        ''' remove from the score board '''
        if name in self.score:
            del self.score[name]

    def increment_score(self, name, points):
        ''' increment the score board '''
        if name in self.score:
            self.score[name] = self.score[name] + points
        else:
            self.score[name] = points

    def centre_position(self):
        return array([self.WIDTH/2,self.HEIGHT/2])

    def random_position(self, on_empty=False):
        ''' Find a random position somewhere on the screen over land tiles
            (if specified -- only on an empty tile) '''
        j_list = list(range(self.terrain.shape[0]))
        random.shuffle(j_list)
        k_list = list(range(self.terrain.shape[1]))
        random.shuffle(k_list)
        for j in j_list:
            for k in k_list:
                if not (self.terrain[j,k] > 0) and not (self.regcount[k,j] > 0 and on_empty):
                    return self.grid2pos((k,j)) + random.rand(2) * TILE_SIZE - TILE_SIZE*0.5
        # There are no empty tiles
        print("Warning: No empty tiles to place stuff on")
        return self.random_position(on_empty=False)

    def grid2pos(self,grid_square):
        ''' Grid reference to point (mid-point of the grid-square) '''
        x,y = grid_square
        px = x * float(TILE_SIZE) + 0.5 * TILE_SIZE
        py = y * float(TILE_SIZE) + 0.5 * TILE_SIZE
        return array([px,py])

    def pos2grid(self,p):
        ''' Position (point) to grid reference ''' 
        # N.B. we could also wrap around 
        rx = clip(int(p[0]/TILE_SIZE),0,self.N_COLS-1)
        ry = clip(int(p[1]/TILE_SIZE),0,self.N_ROWS-1)
        return rx,ry

    def distance_to_wall(self,p,my_tile,ne_tile):
        ''' Return the closest point on the tile edge to point 'p'.

            p: 
                my current position
            my_tile: 
                the tile I'm in
            ne_tile: 
                neighboring tile 

            1. check if the tile is vertically or horizontally aligned with our 
                tile (or neither)
            2. return the distance to the edge of the tile

            Return: 
                the distance to the neighbouring tile
        '''

        p_ne = self.grid2pos(ne_tile)

        if ne_tile[0] == my_tile[0]:
            # Horizontally aligned
            return abs(p_ne[0] - p[0]) - TILE_SIZE * 0.5
        elif ne_tile[1] == my_tile[1]:
            # Vertically aligned
            return abs(p_ne[1] - p[1]) - TILE_SIZE * 0.5
        else:
            # Neither (diagonal to us)
            p_diff = abs(p_ne - p) - TILE_SIZE * 0.5
            return sqrt(dot(p_diff,p_diff))

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

    def quick_collision(self, s_point): 
        '''
            Check collisions of some point s_point.
            Return the object below it, or None if there is none.
        '''
        g_x, g_y = self.pos2grid(s_point)
        things = self.register[g_x][g_y]
        for i in range(self.regcount[g_x,g_y]):
            if overlap(s_point,1,things[i].pos,things[i].radius) > 0.:
                return things[i]
        return None

    def collision_to_vision(self, s_point, s_radius, excl=None, s_collision_radius=1):
        '''
            What an object sees in the environment. 
            --------------------------------------

            A sprite may be made up of different objects (body, antennae, 
            etc.) 

            These objects are defined by the parameters below. 

            Check collisions of some circle s (defined by s_point and s_radius) in the world.

            The point and radius specified do not necessarily have refer to a sprite.

            Parameters
            ----------

            s_point : tuple (x,y)
                the centre point of the object of interest

            s_radius : float
                the detection radius of the object

            excl : Thing
                exclude this object from the search (e.g., the sprite itself!)

            s_collision_radius : float
                The actual radius of the object (it's actual body) which thus 
                implies a collision (rather than a simple detection). 
                The default 1 implies a single point (no mass)


            Returns
            -------
            
            A tuple (color,object,type) where 
                vision : the [R,G,B] color of the resulting collisions 
                thing : the Thing that we collided with (None if terrain)
                type : the centre point of terrain tile we collided with 
                        (and None if not collided with terrain)

            Notes
            -----

            TODO: if touching object (inverse distance = 1, then all other objects are ignored)
            TODO: even if touching, the antennae should give mixed colours back
                (maybe need a special option to this function for that -- and some refactoring)

        '''
        TOUCH_THRESHOLD = 0.9        # maximum visual field occupied by color if not actually touching anything

        # We are currently in grid square (x,y)
        grid_x, grid_y = self.pos2grid(s_point)

        # By default, we don't see anything (pure blackness)
        vision = id2rgb[ID_VOID]
        # .. and we don't collide with anything.
        thing = None

        # Check collision with current tile
        if self.terrain[grid_y,grid_x] > 0:
            # We are colliding with (i.e., we are over) impassable terrain
            vision = id2rgb[ID_ROCK]
            return vision, None, self.grid2pos((grid_x,grid_y))

        # Check collisions with objects in current and neighbouring tiles  
        for i in [-1,0,+1]:
            g_x = (grid_x + i) % self.N_COLS
            for j in [-1,0,+1]:
                g_y = (grid_y + j) % self.N_ROWS

                # off the edge of the map
                #if g_x < 0 or g_x >= N_COLS or g_y < 0 or g_y > self.N_ROWS:

                # If we are looking at terrain tile ...
                if i != 0 and j != 0 and self.terrain[g_y,g_x] > 0:
                    # ... check proximity to it.

                    # (distance of my outer self to the wall) 
                    d = self.distance_to_wall(s_point,(grid_x,grid_y),(g_x,g_y)) - s_collision_radius
                    # (max distance that I can be to the wall while still touching it) 
                    d_max = s_radius - s_collision_radius
                    if d < d_max: 
                        # We are touching the wall
                        vision = vision + object2rgb(excl.ID,ID_ROCK) * get_intensity((d_max - d) / d_max, float(TILE_SIZE)/s_collision_radius)

                # Check for collisions with other objects in this tile
                things = self.register[g_x][g_y]
                n_things = self.regcount[g_x,g_y]    # (n_things <= len(things))
                for i in range(n_things):
                    # If this object is not me, ...
                    if things[i] != excl:

                        # ... how much overlap with this thing?
                        olap = overlap(s_point,s_radius,things[i].pos,things[i].radius)

                        if olap > 0.:

                            # If the overlap greater than the outer + inner radius ...
                            if olap > (s_radius + s_collision_radius):
                                # it means we are completely overlapped by this object, return it now
                                return object2rgb(excl.ID,things[i].ID), things[i], None

                            # distance of the outer - inner radius
                            d = (s_radius - s_collision_radius)

                            # If the overlap is greater than the (outer - inner) radius ...
                            if olap > d:
                                # it means the thing is touching us, save it but don't return yet
                                thing = things[i]
                                vision = vision + object2rgb(excl.ID,things[i].ID) * get_intensity(1., float(things[i].radius)/s_collision_radius)

                            # Otherwise ... (if the overlap is greater than 0, but not touching or covering us)
                            else:
                                # it means the object is in visual range, so we add the relevant intensity to our 'vision'
                                # N.B. max vision reached when touching collision radius!
                                vision = vision + object2rgb(excl.ID,things[i].ID) * get_intensity(olap / d, float(things[i].radius)/s_collision_radius)

        # If we get this far, we are not touching anything ..
        if thing is not None:
            vision = clip(vision,0.0,1.) 
        else:
            # (we should only reach 1.0 if actually touching some thing -- even if visual field is overwhelmed)
            # TODO could be relative, sigmoid/logarithmic, Gaussian ?
            vision = clip(vision,0.0,TOUCH_THRESHOLD) 
        return vision, thing, None

def object2rgb(ID_self, ID_other):
#    '''
#        If object 1 of ID_self is in vision range of object 2 of ID_other, 
#        return the color seen by ID_self. 
#    '''
    return id2rgb[ID_other]
#    if ID_self is None or ID_other < ID_ANIMAL:
#        # A plant and a rock always looks the same
#        return id2rgb[ID_other]
#    elif ID_self == ID_other:
#        # Of the same species
#        return id2rgb[ID_ANIMAL]
#    else:
#        # Another species
#        return id2rgb[ID_OTHER]

def get_intensity(prox, prop):
    ''' 
        Calculate Vision Intensity.

        Parameters
        ----------

        prox : float
            the relative distance to the object (should be in [0,1] where 1 is 
            touching)
        prop : float
            the size ratio of the object to us (where = 1 if same size, 0.1 if we
            are 10 times bigger than the object, etc.)

        Returns
        -------
        
        An intensity in [0,1] depending on size proportion and (inversely) on 
        distance. 
    '''
    # We ignore the size for now, thus just return proximity.
    return prox
