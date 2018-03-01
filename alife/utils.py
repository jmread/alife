from numpy import *
from numpy.linalg import norm

def proximity(p1, p2):
    ''' proximity (Euclidean distance)'''
    return norm(p1 - p2)

def slide_apart(obj_1,obj_2):
    ''' object obj_1 and obj_2 slide away from each other '''

    # The vector between the objects
    v_diff = obj_1.pos - obj_2.pos

    # Overlap
    overlap = (obj_1.radius + obj_2.radius) - norm(v_diff)

    # If objects are are overlapping ...
    if overlap > 0:
        # ... slide apart 
        u = unitv(v_diff)
        velocity = u * overlap/2.
        obj_1.pos = obj_1.pos + velocity
        obj_2.pos = obj_2.pos - velocity

def slide_off(s,p,min_dist=5.):
    ''' Object 's' slides off point 'p' acccording to its own velocity 
    (and at least 'min_dist') '''
    speed = max(min_dist,norm(s.velocity))
    u = unitv(s.pos - p)
    s.velocity = u * speed
    s.move()

def rotate(v, theta=0.1):
    ''' rotation vector v by angle theta '''
    c = cos(theta)
    s = sin(theta)
    M = array([[c,-s],[s,c]])
    return M.dot(v)

def unitv(v):
    ''' unit vector of v '''
    d = norm(v)
    if d == 0:
        return array([0.,-1.])
    return v / d

def angle_deg(v):
    ''' angle of a vector v (in degrees) '''
    a = int(arctan2(v[0],v[1]) * 180. / pi)
    if a < 0:
        a = 360 + a
    return a

def angle_of_attack(obj_1, obj_2):
    ''' the angle between two objects: obj_1 and a obj_2 wrt obj_1 '''
    x = (obj_2.pos - obj_1.pos)
    v = obj_1.velocity
    return arccos(dot(x,v)/(norm(x)*norm(v)))

