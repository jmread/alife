# ALife

ALife was originally conceived as a game, then an artificial life simulation (hence the name, ALife), then a `gym`-inspired testbed for reinforcement learning agents, then a multi-player MMORPG-style game with integrated server environment for scorekeeping, then (currently) just a standalone multi-agent PettingZoo environment. The server/networking architecture and agents are now maintained in separate projects, see TODO.git and TODO.git for hosting the environment, and connecting to one with an agent, respectively.

![Screenshot](screenshot.png "Screenshot")

## Running

Quick start:
```
python run.py
```

This is a multi-agent PettingZoo environment. You can run it as per any other PettingZoo environment, see, e.g., TODO.git


##  'Gameplay'

Numerous gameplay configurations are possible involving e.g., speedrunning, bumper cars, capture the flag, king of the hill, etc. Involving the bugs (agents), plants, and obstacles/rocks. The observation and action space are kept as simple as possible to avoid the need for super-deep architectures. Vision is based on 2-pixel RGB-color vision, plus some 'health/energy' level and a rough sensor indicating which way it is pointing in the map.  


## Map Editing and Environment Design
 
To generate a new map, e.g., a 10x20 map called `new_4`: 
```
python3 -m alife.map_generator new_4 10 20
```
which will produce `new_4.map`. To edit the map:
```
python3 -m alife.map_editor alife/maps/new_4.map
```
TODO file selector?
TODO need to create `new_4.csv` if not already existent with minimal items

The following keys are available to edit a map:
TODO update

* <kbd>r</kbd> -	Add a new rock (under the mouse pointer)
* <kbd>p</kbd> -	Add a new plant (under the mouse pointer)
* <kbd>f</kbd> -	Change the position of the nest/flag (to under the mouse pointer) -- or add one if there is none
* <kbd>m</kbd> -	(Move) Change the position of the currently-selected object (to under the mouse pointer)
* <kbd>&uarr;</kbd> - Resize the selected object (rock, plant, flag, nest) -- bigger
* <kbd>&darr;</kbd> - Resize the selected object (rock, plant, flag, nest) -- smaller
* <kbd>&larr;</kbd> - Change the image of the object
* <kbd>&rarr;</kbd> - Change the image of the object
* <kbd>s</kbd> -	Save all inanimate sprites (rocks, plants, flag, nests) to the corresponding data file of the map


## Notes on Graphics

* Terrain obtained from [Open Game Art](https://opengameart.org/users/chabull) 
<!-- http://chabull.praire-chicken.com/index.html#work --> 
<!-- csaba felvegi -->
* Bug graphics from [Open Clip Art](https://openclipart.org/tags/ladybug)

