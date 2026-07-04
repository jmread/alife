import numpy as np
from numpy.linalg import norm

def collision(p1, r1, p2, r2):
    ''' Circle-circle collision.

        Collision information from circle (p1,r1) with circle (p2,r2). 

        Returns 
        -------

        vdiff : array-like (2d)
            the vector specifying the direction
            
        overlap : float
            the amount of overlap (negative distance, if there is no overlap)

        d : float
            the distance between the two objects
    '''

    # The vector between the objects
    v_diff = p1 - p2

    # The length between the objects
    d = max(norm(v_diff),0.01)

    # Calculate the overlap (sum of radii - distance between centers)
    overlap = (r1 + r2) - d 

    return v_diff, overlap, d

def overlap(p1, r1, p2, r2):
    ''' 
    Returns the overlap of circle (p1,r1) with circle (p2,r2).
    Note: The overlap will be positive if the circles are colliding. 
    '''
    return collision(p1,r1,p2,r2)[1]

def slide_off(p1,speed,p2,min_dist=3.):
    ''' Object 'p1' slides off/away from point 'p2' acccording to its own velocity 
    (and by at least 'min_dist') '''
    velocity = unitv(p1 - p2) #* min_dist
    return velocity * max(min_dist,speed)

def rotate(v, theta=0.1):
    ''' rotation of vector v by angle theta '''
    c = np.cos(theta)
    s = np.sin(theta)
    M = np.array([[c,-s],[s,c]])
    return M.dot(v)

def unitv(v):
    ''' unit vector of v '''
    d = norm(v)
    if d == 0:
        return np.array([0., 1.])
    return v / d

def angle_deg(v):
    ''' angle of a vector v (in degrees) '''
    a = int(np.arctan2(v[0],v[1]) * 180. / np.pi)
    if a < 0:
        a = 360 + a
    return a

def cos_sim(v1,v2):
    ''' cosine similarity: the cosine of the angle between v1 and v2 
    (not necessarily normalized -- we do it here)'''
    return np.dot(v1,v2)/(norm(v1)*norm(v2))

def get_centres(n_row,n_col,tile_size): 
    ''' returns a numpy array M of shape (n_row,n_col,2) where M[i,j] returns 
    (x,y); the center point of the i-th row and j-th column, supposing tile size 
    tile_size: where x is the horizontal, and y the vertical coordinates '''
    rows = np.arange(n_col) * tile_size + tile_size/2     # the rows, i.e., j
    cols = np.arange(n_row) * tile_size + tile_size/2     # the cols, i.e., i
    X = np.tile(rows,(n_row,1))
    Y = np.tile(cols.T,(n_col,1)).T
    return np.dstack((X, Y)).astype(int)

def get_tiles(right,bottom):
    if bottom == 1 and right == 1:
        return [(+0,+0),(+1,+1),(+1,-0),(0,+1)]
    if bottom == 1 and right == 0: 
        return [(+0,+0),(+1,-1),(+1,-0),(0,-1)]
    if bottom == 0 and right == 0:
        return [(+0,+0),(-1,-1),(-1,-0),(0,-1)]
    if bottom == 0 and right == 1: 
        return [(+0,+0),(-1,+1),(-1,-0),(0,+1)]
def dist_point_to_rect3(p, r, width, height): 
    '''  '''
    px = p[0]
    py = p[1]
    x = r[0]
    y = r[1]
    dx = max(abs(px - x) - width / 2, 0)
    dy = max(abs(py - y) - height / 2, 0)
    return np.sqrt( dx * dx + dy * dy )

