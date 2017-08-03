ALife V0.20
===========

This is just one of many projects creating 'artificial life' in a simple artificial world, wherefrom emeregent behaviour may arise. Unlike many related projects, the sprites in this one do not rely entirely on evolution to improve their behaviour generation-by-generation, but use *reinforcement learning* in order to evolve useful behavious inside of one generation.

![Screenshot](screenshot.png "Screenshot")

The creatures are rather simple. Green dots are plant food, blue dots are herbivores and red dots are predators. Input is of the form of two antennae sensors plus the body as a third sensor, each of which has three binary detectors (for RGB colour). Two actions indicate a velocity vector to take. Speed in indicated by the length of the tail. A health bar bar are displayed (depending on the debug level). The reward is the health gained since the previous time step.

Requirements
------------
	
* pygame - http://pygame.org/ - provides the graphics
* numpy - http://www.numpy.org/ - provides nice vector representations for vector algebra

Getting Started
---------------

If you have all the requirements, then run, for example,

```
python ALife.py dat/maps/map_med.txt
```

to load with the map `map_med.txt` (optional). 

No interaction is required. But the following keys are available:

* <kbd>d</kbd> -	Cycle debug level (2,3,0,1, where 0 turns off graphics for faster processing)
* <kbd>r</kbd> -	Add a new 'resource' (where the mouse ponder)
* <kbd>h</kbd> -	Add a new 'herbivore' (where the mouse ponder)
* <kbd>p</kbd> -	Add a new 'predator' (where the mouse ponder)
* <kbd>k</kbd> -	Add a new 'rock' (under mouse pointer)
<!--* <kbd>s</kbd> -	Saving current objects to files-->
<!--* <kbd>l</kbd> -	Load objects from files-->
* <kbd>&uarr;</kbd> - More energy input (more resources appear automatically)
* <kbd>&darr;</kbd> - Less energy input (fewer resources appear automatically)

and on debug level 3, hover the mouse pointer over a sprite to see more debug info (currently, to the command line).


Related Projects
----------------

I've run across some related projects with some nice demos on YouTube:

* https://www.youtube.com/watch?v=2kupe2ZKK58
* https://www.youtube.com/watch?list=PLC9058E743A6155C1&v=1Jou4ggCFKQ
* https://sites.google.com/site/scriptbotsevo/

