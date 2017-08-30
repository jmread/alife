from numpy import *
from numpy.linalg import norm

def proximity(p1, p2):
    ''' proximity (standard Euclidean distance)'''
    return norm(p1 - p2)

def SlideApart(s,o):
    ''' object s slide away from object o '''
    v_diff = s.pos - o.pos                # vector from one to the other
    d_now = norm(v_diff)          # distance from centres
    d_after = s.radius + o.radius # but they should be this far apart
    if d_after > d_now:
        # they are overlapping
        u = unitv(v_diff)
        velocity = u * (v_diff * 0.75 + random.randn()) 
        s.pos = s.pos + velocity
        o.pos = o.pos - velocity

def SlideOff(s,p, speed=1.):
    ''' object s slide away from point p '''
    u = unitv(s.pos - p)
    velocity = u * speed + random.randn()
    s.pos = s.pos + velocity

def Slide(s,p):
    ''' object s slide off point p '''
    speed = max(1.0,norm(s.velocity))
    u = unitv(s.pos - p)
    s.velocity = u * speed
    s.move()

def Reflect(s):
    ''' reflect (when the other object doesn't move, like a wall or a heavy rock'''
    s.velocity = -s.velocity
    s.move()

def BounceOffFrom(s,e):
    ''' two objects bounds off each other '''
    # todo: the heavier one should bounce less
    # todo use the new slide?
    st = s.velocity
    et = e.velocity
    s.velocity - e.velocity
    overlap = (s.radius + e.radius) - norm(s.pos - e.pos)
    v = unitv(s.velocity - e.velocity) * (overlap + 2.)
    s.velocity = -v
    e.velocity = +v
    e.move()
    s.move()
    s.velocity = st
    e.velocity = et

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
    a = int(arctan2(v[0],v[1]) * 180. / pi)
    if a < 0:
        a = 360 + a
    return a

def angle_of_attack(attacker, defender):
    ''' the angle between an attacker and a defender '''
    x = (defender.pos - attacker.pos)
    v = attacker.velocity
    return arccos(dot(x,v)/(norm(x)*norm(v)))

