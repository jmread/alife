ALife V0.12
===========

This is just one of many projects creating 'artificial life', wherefrom emeregent behaviour may arise. Unlike many related projects, the sprites in this one do not rely entirely on evolution to improve their behaviour, but use (relatively basic) reinforcement learning techinques in order to evolve useful behavious inside of one generation.

![Screenshot](screenshot.png "Screenshot")

The creatures are rather simple. Green dots are plant food, blue dots are herbivores and red dots are omnivores (but they don't process plant food as well as the herbivores). Input is of the form of two antennae plus the body as a third sensor, each of which has three binary range detectors (for RGB), forming a simple eye, plus a hunger sensor, for a total of 10 inputs. Outputs is simply a velocity. Speed in indicated by the length of the tail. A health bar and a 'happiness' bar are displayed (depending on the debug level).

Requirements
------------
	
* pygame - http://pygame.org/ - provides the graphics
* numpy - http://www.numpy.org/ - provides a nice vector representation
* cerebro - https://github.com/jmread/cerebro - provides the 'brain' with implementations of recurrent neural networks and reinforcement learning

Getting Started
---------------

If you have all the requirements, then run

```
$ ./ALife.py
```

and just watch. No interaction is required. But the following keys are available:

* <kbd>d</kbd> -	Cycle debug level 
* <kbd>r</kbd> -	New 'resource'
* <kbd>h</kbd> -	New 'herbivore'
* <kbd>p</kbd> -	New 'predator'
* <kbd>k</kbd> -	New 'rock' (under mouse pointer)
* <kbd>i</kbd> -	Print out info
* <kbd>s</kbd> -	Saving current objects to files
* <kbd>l</kbd> -	Load objects from files
* <kbd>&uarr;</kbd> - More energy input (more resources)
* <kbd>&darr;</kbd> - Less energy input (more resources)


Related Projects:
-----------------

I've run across some related projects with some nice demos on YouTube:

* https://www.youtube.com/watch?v=2kupe2ZKK58
* https://www.youtube.com/watch?list=PLC9058E743A6155C1&v=1Jou4ggCFKQ
* https://sites.google.com/site/scriptbotsevo/

