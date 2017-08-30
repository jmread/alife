# Maps

Maps in the new image-tile format are named `.dat`. Older, simpler (vector style) maps are named `.txt`.

## Graphical maps (.dat format)

Each image tile is represented by 4 characters in a square, where only the top left indicates the tile code, e.g., 

```
	 v.
	 ..
```

indicates a shoreline tile. The basic tiles are '~' indicating a water tile, and '.' indicating a land tile. 
To see how this works, see the file `graphics.py`.

