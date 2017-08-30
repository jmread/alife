ALife V0.25a
============

This is just one of many projects creating 'artificial life' in a simple artificial world, wherefrom emeregent behaviour may arise. Unlike many related projects, the sprites in this one do not rely entirely on evolution to improve their behaviour generation-by-generation, but use *reinforcement learning* in order to evolve useful behavious inside of one generation.

![Screenshot](screenshot.png "Screenshot")

A simple world, there are resources, herbivores, predators, and obstacles. Herbivores and predators have a brain, where input is of the form of two antennae sensors plus the body as a third sensor, each of which has three binary detectors (for RGB colour). Two output actions indicate angle and speed of movement. Creatures may take flight if speed component is above a certain value. The reward is the health gained since the previous time step. After a certain level, a creature automatically reproduces (this does not affect the reward).

Requirements
------------
	
* pygame - http://pygame.org/ - provides the graphics
* numpy - http://www.numpy.org/ - provides nice vector representations for vector algebra

Getting Started
---------------

If you have all the requirements, then run, for example,

```
	python ALife.py dat/maps/map_islands2.dat 5
```

to load with the map from the file `map_islands2.dat` (optional). The map can be edited by hand in the text file. By default, an empty map is used (no terrain). The number indicates how many creatures are to be spawned on initialization; 0 is none, 8 is a lot.

No interaction is required. But the following keys are available:

* <kbd>g</kbd> -	Toggle graphics (graphics off for faster processing)
* <kbd>d</kbd> -	Toggle grid 
* <kbd>r</kbd> -	Add a new 'resource' (where the mouse ponder)
* <kbd>h</kbd> -	Add a new 'herbivore' (where the mouse ponder)
* <kbd>p</kbd> -	Add a new 'predator' (where the mouse ponder)
* <kbd>k</kbd> -	Add a new 'rock' (under mouse pointer)
<!--* <kbd>s</kbd> -	Saving current objects to files-->
<!--* <kbd>l</kbd> -	Load objects from files-->
* <kbd>&uarr;</kbd> - More energy input (more resources appear automatically)
* <kbd>&darr;</kbd> - Less energy input (fewer resources appear automatically)

Click on a creature to view debug info relating to that creature (sensors, health, etc.)


Related Projects
----------------

I've run across some related projects with some nice demos on YouTube:
 [1](https://www.youtube.com/watch?v=2kupe2ZKK58), 
 [2](https://www.youtube.com/watch?list=PLC9058E743A6155C1&v=1Jou4ggCFKQ), 
 [3](https://sites.google.com/site/scriptbotsevo/).


Notes on Graphics
-----------------

* Terrain obtained from from [Open Game Art](https://opengameart.org/users/chabull)
* Sprites (bugs) from [Open Clip Art](https://openclipart.org/tags/ladybug)
