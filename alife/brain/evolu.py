from numpy import *

class Evolu():
    '''
        Evolu
        -----
        * Performs using a random weight matrix.
        * Relies entirely on generation-to-generation evolution to make any progress.
    '''

    def __init__(self,D,L):
        self.D = D
        self.L = L
        self.W = random.randn(D,L) * (random.rand(D,L) >= 0.5)
        self.w = random.randn(L) * 0.1

    def act(self,x,r,done=False):
        a = dot(x,self.W) + self.w
        return a

    def copy_of(self):
        b = Evolu(self.D,self.L)
        b.W = (self.W + random.randn(self.D,self.L) * 0.1) * (self.W > 0.0)
        b.w = b.w + random.randn(self.L) * 0.01
        return b



