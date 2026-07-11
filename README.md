# ALife

ALife was originally conceived as a game, then an artificial life simulation (hence the name, ALife), then a `gym`-inspired testbed for reinforcement learning agents, then a multi-player MMORPG-style game with integrated server environment for scorekeeping, then (currently) just a standalone multi-agent PettingZoo environment. The server/networking architecture and agents are now maintained in separate projects, see TODO.git and TODO.git for hosting the environment, and connecting to one with an agent, respectively.

![Screenshot](screenshot.png "Screenshot")

## Running

Quick start:
```
python run.py
```

This is a multi-agent PettingZoo environment. You can run it as per any other PettingZoo environment. 


##  'Gameplay'

Numerous gameplay configurations are possible involving e.g., speedrunning, bumper cars, capture the flag, king of the hill, etc. Involving the bugs (agents), plants, and obstacles/rocks. The observation and action space are kept as simple as possible to avoid the need for super-deep architectures. Vision is based on 2-pixel RGB-color vision, plus some 'health/energy' level and a rough sensor indicating which way it is pointing in the map.  

## Map Editing and Environment Design
 
To generate a new map, run 
```
python3 -m alife.map_editor 
```
and specify the name of the new map. To edit an existing map:
```
python3 -m alife.map_editor new_4.map
```

Press <kbd>h</kbd> to see the keys for editing. 

## Notes on Graphics

* Terrain and decor obtained from [Open Game Art](https://opengameart.org/users/chabull) 
<!-- http://chabull.praire-chicken.com/index.html#work --> 
<!-- Csaba Felvegi -->
* Bug graphics from [Open Clip Art](https://openclipart.org/tags/ladybug)

