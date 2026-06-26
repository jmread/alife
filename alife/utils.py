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

#def slide_apart(obj_1,obj_2):
#    ''' Objects obj_1 and obj_2 slide away from each other until they no longer
#        touch each other '''
#
#    # Calculate the collision / overlap
#    v_diff, overlap, d = collision(obj_1.pos,obj_1.radius,obj_2.pos,obj_2.radius)
#
#    # If objects are are overlapping ...
#    if overlap > 0:
#        # ... slide them apart 
#        u = v_diff / d
#        velocity = u * overlap/1.9 + 1.
#        obj_1.pos = obj_1.pos + velocity
#        obj_2.pos = obj_2.pos - velocity

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

#def angle_of_attack(obj_1, obj_2):
#    ''' the angle (in radians) between object obj_1 approaching obj_2 
#        returns
#            0 if the same object
#    '''
#    x = obj_2.pos - obj_1.pos
#    xnorm = norm(x) # vector between the two
#    if xnorm <= 0:
#        # they objects are on the same pixel
#        return 0.
#    # The angle between vector x and v
#    return np.arccos(np.dot(x/xnorm,obj_1.unitv))

#def angles_of_attack(obj_1, obj_2):
#    ''' the angles between two objects: obj_1 and a obj_2 
#    wrt each other.'''
#    return [np.arccos(np.dot(unitv(obj_2.pos - obj_1.pos),obj_1.unitv)), 
#            np.arccos(np.dot(unitv(obj_1.pos - obj_2.pos),obj_2.unitv))]


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
    
#def mass2rad(m):
#    return 3 + int(np.sqrt(m/np.pi))
#    #return 10 + 10 * int(np.sqrt(m/np.pi))

#def rad2mass(r):
#    return np.pi*(r - 3)**2
#
#print(mass2rad(350))

#def tile_collide(square, circle):
#    '''
#    check collision between square and circle
#    '''

#def get_tile_square(c, l):
#    '''
#        given a square defined by a center point and length (of each 4 sides), 
#        return the 
#    '''
#    tile_rect = pygame.Rect(p[0] - TILE_SIZE/2,p[1] - TILE_SIZE/2,TILE_SIZE,TILE_SIZE)

def dist_point_to_rect3(p, r, width, height): 
    '''  '''
    px = p[0]
    py = p[1]
    x = r[0]
    y = r[1]
    dx = max(abs(px - x) - width / 2, 0)
    dy = max(abs(py - y) - height / 2, 0)
    return np.sqrt( dx * dx + dy * dy )

#def dist_point_to_rect2(p, r, width, height): 
#    '''
#    point centre
#    rectangle centre
#    rectangle width x height
#    '''
#    R = np.zeros((2,2))
#    R[0,:] = r
#    R[1,:] = [width,height]
#    return dist_point_to_rect(p, R)

#def dist_point_to_rect(p, r): 
#    '''
#        Parameters
#        ----------
#        p : np.array
#            a point
#        r : np.array
#            a rectangle, where r[0,:] is the centre point,
#            and r[1,0] is the width, r[1,1] is the height
#        array p, where x is
#        returns 0 if inside?
#    '''
#    x = p[0]
#    y = p[1]
#    dx = max(np.min(r[:,0]) - x, 0, x - np.max(r[:,0]))
#    dy = max(np.min(r[:,1]) - y, 0, y - np.max(r[:,1]))
#    return np.linalg.norm(np.array([dx,dy]))

#if __name__ == '__main__':
#
#    r = np.array([[10,10], 
#                  [20,20]])
#    p = np.array([5,5])
#    print(r,p,dist_point_to_rect(p,r))
#    M = get_centres(2,3,64)
##    print(M[:,:,0])
#    print(M[:,:,1])
#    #print(M.shape)
#    print(M[1,2])
#    #print(M[0,2])


