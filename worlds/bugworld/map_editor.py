#! /usr/bin/env python3

import sys
import time

import json
import struct

# Numpy
import numpy as np
np.set_printoptions(threshold=np.inf, precision=1)

# Pygame
import pygame

from graphics import N_array, COLOR_WHITE, get_label

IDX_id = 0                     # int : object id; either ID_ROCK, ID_PLANT, ID_ANIMAL, etc.
IDX_x = 1                      # int             
IDX_y = 2                      # int             
IDX_pos = [IDX_x, IDX_y]       # [int,int]                              
IDX_rad = 3                    # int
IDX_img = 4                    # int : image id; the 'coat' for a given sprite of type id              

TILE_SIZE = 64               # tile size (width and height, in pixels)

from graphics import build_image_bank, build_bg_png as build_map, build_image_png, ID_ROCK, ID_PLANT, ID_VOID, ID_ANIMAL, ID_NEST, ID_FLAG, f_array

def is_point_in_circle(p, c, r):
    # Calculate the squared distance between point p and center c
    distance_squared = np.sum((np.array(p) - np.array(c))**2)
    # Check if the squared distance is less than or equal to r squared
    return distance_squared <= r**2

def get_object(things, p): 
    for i,thing in enumerate(things): 
        if is_point_in_circle(p, thing[IDX_pos],IDX_rad * 2):
            print("SELECTED", thing)
            return i, thing
    return -1, None

def editor_interface(world_info):

    '''
        Map Editor Interface
        --------------------

    '''

    # Extract info
    bname_map = world_info['basename']
    fname_sprites = bname_map+'.csv'
    fname_map = bname_map+'.dat'

    # Build the map (based on world_name)
    print('[Map-Editor] Got world info: (map: %s).' % (fname_map))

    map_codes = np.genfromtxt(fname_map, delimiter = 1, dtype=str)[1:-1,1:-1]
    WIDTH = map_codes.shape[1] * TILE_SIZE
    HEIGHT = map_codes.shape[0] * TILE_SIZE

    # Open the sreen 
    pygame.font.init()
    pygame.display.set_caption("God Agent [map: %s]" % fname_map)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))#, HWSURFACE|DOUBLEBUF)
    pygame.mouse.set_visible(1)

    # Fetch the background (map)
    background = build_map(screen.get_size(),TILE_SIZE,map_codes)

    # Draw the background on the screen
    screen.blit(background, [0, 0])
    pygame.display.flip()

    #image = build_image_png([0,0],int(sprites[i,IDX_rad]),int(sprites[i,IDX_id]),int(sprites[i,IDX_img]))[1]
    things = []

    try: 
        print("[World] Load Sprites ..")
        things = np.loadtxt(fname_sprites,delimiter=',',dtype=int)
    except:
        print("[World] Error: ", sys.exc_info()[0])
        print("      > No sprite file found...")

    th_sel = None
    i_sel = -1

    n = len(things)
    images = [None for _ in range(100)]

    for i, thing in enumerate(things): 
        p = thing[1:3]
        r = thing[3]
        print(p,r)
        if images[i] is None: 
            images[i] = build_image_png(thing[IDX_pos],thing[IDX_rad],thing[IDX_id],thing[IDX_img])[1]
        screen.blit(images[i], p - r)

    pygame.display.flip()

    clock = pygame.time.Clock()
    running = True
    while running:

        clock.tick(24)
        screen.blit(background, [0,0]) 

        for i, thing in enumerate(things): 
            screen.blit(images[i], thing[IDX_pos] - thing[IDX_rad])
            name_label = get_label("%d" % i)
            screen.blit(name_label, thing[IDX_pos] - thing[IDX_rad])

        for event in pygame.event.get():
            # quit
            if event.type == pygame.QUIT:
                running = False
            # select an object
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s: 
                    print(things)
                    np.savetxt(fname_sprites, things, delimiter=',',fmt='%d')
                if event.key == pygame.K_f: 
                    print("new flag")
                    pos = pygame.mouse.get_pos()
                    thing = [ID_FLAG, pos[0], pos[1], 15, 0]
                    things = np.insert(things, n, thing, axis=0)
                    thing = things[n]
                    images[n] = build_image_png(thing[IDX_pos],thing[IDX_rad],thing[IDX_id],thing[IDX_img])[1]
                    n = n + 1
                if th_sel is not None:
                    #if event.key == pygame.K_DELETE:
                    #    self.remove_from_fixed_register(selected_obj)
                    #    selected_obj.kill()
                    #elif event.key == pygame.K_m:
                    #    self.remove_from_fixed_register(selected_obj)
                    #    selected_obj.pos = np.array(pygame.mouse.get_pos())
                    #    self.add_to_fixed_register(selected_obj)
                    if event.key == pygame.K_m: 
                        pos=np.array(pygame.mouse.get_pos())
                        if th_sel is not None:
                            th_sel[IDX_pos] = pos
                            images[i_sel] = build_image_png(th_sel[IDX_pos],th_sel[IDX_rad],th_sel[IDX_id],th_sel[IDX_img])[1]
                    if event.key == pygame.K_UP:
                        th_sel[IDX_rad] += 1
                        images[i_sel] = build_image_png(th_sel[IDX_pos],th_sel[IDX_rad],th_sel[IDX_id],th_sel[IDX_img])[1]
                    elif event.key == pygame.K_DOWN:
                        th_sel[IDX_rad] -= 1
                        images[i_sel] = build_image_png(th_sel[IDX_pos],th_sel[IDX_rad],th_sel[IDX_id],th_sel[IDX_img])[1]
                    if event.key == pygame.K_RIGHT:
                        th_sel[IDX_img] = (th_sel[IDX_img] + 1) % N_array[th_sel[IDX_id]]
                        images[i_sel] = build_image_png(th_sel[IDX_pos],th_sel[IDX_rad],th_sel[IDX_id],th_sel[IDX_img])[1]
                    elif event.key == pygame.K_LEFT:
                        th_sel[IDX_img] = (th_sel[IDX_img] - 1) % N_array[th_sel[IDX_id]]
                        images[i_sel] = build_image_png(th_sel[IDX_pos],th_sel[IDX_rad],th_sel[IDX_id],th_sel[IDX_img])[1]

            if event.type == pygame.MOUSEBUTTONDOWN:
                print("click @ ", str(pygame.mouse.get_pos()))
                i_sel, th_sel = get_object(things, pygame.mouse.get_pos())
                if th_sel is not None:
                    print("select %s @ %s" % (th_sel, str(pygame.mouse.get_pos())))

            if th_sel is not None:
                pygame.draw.circle(screen, COLOR_WHITE, th_sel[IDX_pos], th_sel[IDX_rad] + 3, 4)

            pygame.display.flip()

        #time.sleep(1)


#sys.argv[1]
bname_map = "../dat/maps/new_2"
editor_interface(world_info = { 'basename' : bname_map })

