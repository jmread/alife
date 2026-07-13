import numpy as np

''' Map Tools.

    Shared (imported) by map_generator, map_editor, and graphics.
'''

def t2i(t):
    return np.dot(t.flatten(), [1, 2, 4, 8])


def i2t(i):
    return np.flip(np.array([int(x) for x in bin(i)[2:].zfill(4)])).reshape(2,2)

def convert_to_tiles(B):
    '''
    Converts a binary map B (as generated, saved to disk) into 
    a tile index map M (for drawing), and
    a terrain array T (for collisions).

    Parameters
    ----------

    B : arr(n,m) 
        A binary numpy array representing the input grid

    Returns
    -------

    M : arr(n-1,m-1) 
        A tile array

    T : arr((n-1)*2,(m-1)*2)
        A terrain array

    '''

    # Draw the tile version
    B = np.ones_like(B) - B
    M = np.zeros((B.shape[0]-1,B.shape[1]-1), dtype=int)
    T = np.zeros(((B.shape[0]-1)*2,(B.shape[1]-1)*2), dtype=int)

    for i in range(0,B.shape[0]-1): 
        for j in range(0,B.shape[1]-1): 
            t_i = B[i:i+2,j:j+2]
            M[i,j] = t2i(t_i)
            T[i*2:i*2+2,j*2:j*2+2] = t_i

    return M, T

def convert_to_bits(M):
    # Get the dimensions of the tile map
    n_rows, n_cols = M.shape
    
    # Initialize the binary bitmap
    bitmap_height = n_rows * 2
    bitmap_width = n_cols * 2
    B = np.zeros((bitmap_height, bitmap_width), dtype=int)
    
    # Convert each tile to a 2x2 block of bits
    for i in range(n_rows):
        for j in range(n_cols):
            # Get the tile value (0-15)
            B[i*2:i*2+2, j*2:j*2+2] = i2t(M[i,j])
    
    return B


def pad(matrix, padding=0):
    n_rows,n_cols = matrix.shape
    M = np.ones((n_rows+2,n_cols+2),dtype=int) * padding
    M[1:-1,1:-1] = matrix
    return M

def trim(M):
    return M[1:-1,1:-1]


def generate_grass_patch(size=128, alpha=180, density=0.5, seed=None, output_path=None):
    '''
    Generate a grass patch PNG with random tufts over a transparent background.

    The result has soft, faded edges (radial falloff + noise) so it blends
    naturally when placed on top of the sandy land tiles.

    Parameters
    ----------

    size : int
        Patch dimensions in pixels (square).
    alpha : int (0-255)
        Maximum opacity of grass pixels. Lower = more of the underlying
        terrain shows through.
    density : float (0-1)
        How much of the patch area is covered by grass.  Higher = thicker.
    seed : int or None
        Random seed for reproducible patterns.
    output_path : str / Path / None
        Destination PNG.  If None, saves to IMG_DIR/grass_patch.png.

    Returns
    -------

    Path to the saved PNG.
    '''
    import os
    from PIL import Image, ImageFilter
    from .config import IMG_DIR

    rng = np.random.default_rng(seed)

    # Random noise -> organic blobs
    noise = rng.random((size, size))
    noise_img = Image.fromarray((noise * 255).astype(np.uint8))
    noise_img = noise_img.filter(ImageFilter.GaussianBlur(radius=size / 6))
    noise = np.array(noise_img, dtype=float) / 255
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-9)

    # Radial falloff: full at centre, transparent at edges (smoothstep)
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size * 0.5)
    falloff = np.clip(1 - dist, 0, 1)
    falloff = falloff * falloff * (3 - 2 * falloff)

    # Combine noise + falloff, keep top `density` fraction (relative threshold)
    mask = noise * falloff
    thresh = np.quantile(mask, 1 - density)
    mask = np.clip((mask - thresh) / (mask.max() - thresh + 1e-9), 0, 1)

    # Grass colour: sample from grass.png, add slight variation
    grass_src = Image.open(os.path.join(IMG_DIR, 'grass.png')).convert('RGB').resize((size, size))
    grass_rgb = np.array(grass_src, dtype=np.int16)
    variation = rng.integers(-12, 12, (size, size, 1))
    grass_rgb = np.clip(grass_rgb + variation, 0, 255).astype(np.uint8)

    # Assemble RGBA
    rgba = np.dstack([grass_rgb, (mask * alpha).astype(np.uint8)])
    img = Image.fromarray(rgba, 'RGBA')

    if output_path is None:
        output_path = os.path.join(IMG_DIR, 'grass_patch.png')

    img.save(output_path)
    return output_path

'''
use this code to modify the tileset
'''
#tileset = Image.open('worlds/bugworld/img/ground.png').convert("RGBA")
#tileset = Image.open('worlds/bugworld/img/tileset3.png').convert("RGBA")
#tiles = {}

# Rotate one of the pieces, into an empty spot, and incoporate the water also, into another empty spot
#(x,y) = random.choice(land[4])
#(x,y) = (2,3)
#x,y = x*128,y*128
#tile = tileset.crop((x,y,x+128,y+128))
#rile = tile.rotate(180)
#paste_x, paste_y = 6, 6
#paste_x_pixel, paste_y_pixel = paste_x * 128, paste_y * 128
#tileset_modified = tileset.copy()
#tileset_modified.paste(rile, (paste_x_pixel, paste_y_pixel))
#wile = Image.open("worlds/bugworld/img/water.png").convert("RGBA")
#paste_x, paste_y = 7, 7
#paste_x_pixel, paste_y_pixel = paste_x * 128, paste_y * 128
#tileset_modified.paste(wile, (paste_x_pixel, paste_y_pixel))
#tileset_modified.save("tileset2.png")

# Overlay two corner pieces, then smooth over with GIMP to make a land bridge, rotate it also, and use the last two empty slots
#(x,y) = (5,3)
#x,y = x*128,y*128
#tile1 = tileset.crop((x,y,x+128,y+128)).convert("RGBA")
#(x,y) = (7,3)
#x,y = x*128,y*128
#tile2 = tileset.crop((x,y,x+128,y+128)).convert("RGBA")
#paste_x, paste_y = 6, 7
#paste_x_pixel, paste_y_pixel = paste_x * 128, paste_y * 128
#tileset_modified = tileset.copy()
#combined_tile = Image.alpha_composite(tile1, tile2)
#tileset_modified.paste(combined_tile, (paste_x_pixel, paste_y_pixel))
#rile_combined = combined_tile.rotate(90)
#paste_x, paste_y = 7, 6
#paste_x_pixel, paste_y_pixel = paste_x * 128, paste_y * 128
#tileset_modified.paste(rile_combined, (paste_x_pixel, paste_y_pixel))
#tileset_modified.save("tileset3.png")
#tileset3 = Image.open("tileset3.png")
#tileset3.show() 
#rile = tile.rotate(180)
#---------


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Generate grass patch PNGs.")
    p.add_argument("-n", "--count", type=int, default=5, help="number of patches to generate")
    p.add_argument("--size", type=int, default=128, help="patch size in pixels")
    p.add_argument("--alpha", type=int, default=180, help="max opacity (0-255)")
    p.add_argument("--density", type=float, default=0.5, help="grass coverage (0-1)")
    args = p.parse_args()

    import os
    from .config import IMG_DIR

    for i in range(args.count):
        name = f"grass_patch_{i:02d}.png"
        path = generate_grass_patch(
            size=args.size, alpha=args.alpha, density=args.density,
            seed=i, output_path=os.path.join(IMG_DIR, name),
        )
        print("Generated %s" % path)

