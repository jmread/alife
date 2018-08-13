from random import shuffle
from numpy import *

'''
    Map Generator
    -------------

    A simple tile-based random-map generator. 
    Performs a depth-first search on all map states by placing tiles one at a time. 

    Simply run this script (change parameters if you wish). 
'''

# Parameters
N_row = 6
N_col = 10
n_max = 250 # Max number of attempts before giving up

# Map
M = ones((N_row,N_col)) * -1
# Counter
n = 0

# Map tiles
tiles = {
        -1 : array([[2,2],
                    [2,2]]),
        0 : array([[0,0],
                   [0,0]]),
        1 : array([[0,0],
                   [1,1]]), 
        2 : array([[1,0],
                   [1,0]]),                       
        3 : array([[0,1],
                   [0,1]]),                       
        4 : array([[1,0],
                   [1,1]]),                       
        5 : array([[0,1],
                   [1,1]]),                       
        6 : array([[1,1],
                   [1,0]]),                       
        7 : array([[1,1],
                   [0,0]]),                       
        8 : array([[1,1],
                   [0,1]]),                       
        9 : array([[0,1],     
                   [0,0]]),                       
        10 : array([[1,0],     
                    [0,0]]),                       
        11 : array([[0,0],     
                    [1,0]]),                       
        12 : array([[0,0],     
                    [0,1]]),    
        13 : array([[1,1],
                    [1,1]]),                       
}

# Tile symbols
sym = [ ' ' , 'v' , '[' , ']' , '\\' , '/' , '+' , '^' , 'L' , 'C' , 'D' , '&' , '-' , '~', 'x'  ]

def compatible(t_1,t_2,offset):
    ''' 
        Check compatibility
        -------------------

        t_1 is the base, t_2 is at t_1 + offset,
            do they fit together?

        offset = (t_1 - t_2)
        offset = [0,+1] := t_2 below 
        offset = [0,-1] := t_2 above
        offset = [+1,0] := t_2 to the right
        offset = [-1,0] := t_2 to the left
    '''
    row_offset,col_offset = offset

    if t_2 < 1:
        return 2
    elif offset[1] == -1:
        # 1 2 
        return sum(tiles[t_1][:,1] == tiles[t_2][:,0])
    elif offset[1] == +1:
        # 2 1 
        return sum(tiles[t_1][:,0] == tiles[t_2][:,1])
    elif offset[0] == +1:
        # 1 
        # 2 / [0,+1]
        return sum(tiles[t_1][0,:] == tiles[t_2][1,:])
    elif offset[0] == -1:
        # 1 
        # 2 / [0,-1]
        return sum(tiles[t_1][1,:] == tiles[t_2][0,:])



# Testing
#for i in range(10):
#    ref = random.choice(14)
#    other = random.choice(15)-1
#    for offset in [[-1,0],[+1,0],[0,-1],[0,+1]]:
#        print(compatible(ref,other,offset))
#exit(1)


def check_fit(M,pos):
    '''
        Check the fit of a tile at pos = (row,col) in the map M.


        Returns
        -------

        True, if it fits.
    '''
    (r_row,r_col) = pos
    for offset in [[-1,0],[+1,0],[0,-1],[0,+1]]:
        o_row = r_row - offset[0]
        o_col = r_col - offset[1]
        if o_row >= N_row:
            o_row = 0
        elif o_row < 0:
            o_row = N_row - 1
        if o_col >= N_col:
            o_col = 0
        elif o_col < 0:
            o_col = N_col - 1
        if compatible(M[r_row,r_col],M[o_row,o_col],offset) < 2:
            return False
    return True



def new_states(M,pos):
    '''
        Expand map M by trying different permitted combos of tile pos = (row,col).

        Returns
        -------

        Return all new M (in a list) with all permitted tiles at (row,col).
    '''
    (row,col) = pos
    l = []
    tile_types = arange(14)
    shuffle(tile_types)
    for c in tile_types:
        M_ = M.copy()
        M_[row,col] = c
        if check_fit(M_,[row,col]):
            l.append(M_)
    return l


# Keep track of visited states.
visited = {
    str(M) : 1
}

def write_out(M,fname='test.dat'): 
    # Write out in ALife map format.
    f = open(fname,"w") 
    f.write("+"+str("------------------------------"[0:N_col*2])+"+\n")
    for i in range(N_row):
        f.write('|')
        for j in range(N_col):
            f.write(str(sym[int(M[i,j])])+'.')
        f.write("|\n|"+str("............................."[0:N_col*2])+"|\n")
    f.write("+"+str("------------------------------"[0:N_col*2])+"+\n")

def expand(M):
    '''
        Expand
        ------

        We do a depth-first search all map states. A goal state is one
        where all tiles are in place and compatible.
    '''
    global n, n_max
    n = n + 1
    if n > n_max:
        # (Could not finish; write out any just for curiosity)
        print("Could not complete.")
        write_out(M)
        exit(1)

    empty_x, empty_y = where(M == -1) 

    # Printout search status
    print(len(empty_x),n)

    if len(empty_x) <= 0:
        # We completed the map! We're done.
        print(M)
        write_out(M)
        exit(1)

    # For each empty tile slot ...
    for i in range(len(empty_x)):
        # For each possible tile in that slot ...
        for M_ in new_states(M,(empty_x[i],empty_y[i])):
            # Expand if not yet visited ...
            hsh = str(M_)
            if hsh not in visited:
               expand(M_)
               visited[hsh] = 1
            #else:
            #    print("...")


M = expand(M)
