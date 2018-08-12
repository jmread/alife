import numpy as np
from numpy.random import randn, rand

def linear(a):
    return a

class SLP():
    ''' 
        A Single-Layer Perceptron
        -------------------------
    '''

    W_io = None                # weight matrix
    b_io = None

    def __init__(self, D, L):
        self.D = D
        self.L = L
        self.reset()


    def reset(self, density=1.0, scaling=0.5):
        self.W_io = randn(self.D,self.L) * scaling * (rand(self.D,self.L) >= density)     # sparse weight matrix
        self.b_io = randn(self.L) * 0.1                                 # bias
        self.fo = linear

    def predict(self,x):

        a = np.dot(x,self.W_io) + self.b_io
        return self.fo(a)

    def copy(self, modify=False):

        b = SLP(self.D,self.L)

        b.W_io = self.W_io.copy()
        b.b_io = self.b_io.copy()

        if modify:
            # Make a random adjustment to the weight matrix.
            b.modify()

        return b

    def modify(self, alpha=0.01, alpha_b=0.01, prob_reset=0.1):

        if rand() < prob_reset:
            self.reset()

        # Make a random adjustment to the weight matrix.
        self.W_io = self.W_io + alpha * randn(*self.W_io.shape) 
        self.b_io = self.b_io + alpha_b * randn(*self.b_io.shape)

class MLP():

    ''' 
        A Multi-Layer Perceptron
        --------------------------------------
    '''

    W_ih = None                # weight matrix
    b_ih = None
    W_ho = None                # weight matrix
    b_ho = None

    def __init__(self, D, L, H=10):
        self.D = D
        self.L = L
        self.H = H
        self.reset()


    def reset(self, density=1.0, scaling=0.5):
        self.W_ih = randn(self.D,self.H) * scaling * (rand(self.D,self.H) <= density)
        self.W_ho = randn(self.H,self.L) * scaling * (rand(self.H,self.L) <= density)
        self.b_ih = np.zeros(self.H)
        self.b_ho = np.zeros(self.L)
        self.f = np.tanh
        self.fo = linear

    def predict(self,x):

        A = np.dot(x,self.W_ih) + self.b_ih
        Z = self.f(A)
        y = np.dot(Z,self.W_ho).T + self.b_ho
        y = self.fo(y)

        return y

    def copy(self, modify=False):

        b = MLP(self.D,self.L,self.H)

        # Make a random adjustment to the weight matrix.
        b.W_ih = self.W_ih.copy()
        b.W_ho = self.W_ho.copy()
        b.b_ih = self.b_ih.copy()
        b.b_ho = self.b_ho.copy()

        if modify:
            b.modify()

        return b

    def modify(self, alpha=0.01, alpha_b=0.01, prob_reset=0.1):

        if rand() < prob_reset:
            self.reset()

        # Make a random adjustment to the weight matrix.
        self.W_ih = self.W_ih + alpha * randn(*self.W_ih.shape) 
        self.W_ho = self.W_ho + alpha * randn(*self.W_ho.shape)
        self.b_ih = self.b_ih + alpha_b * randn(*self.b_ih.shape)
        self.b_ho = self.b_ho + alpha_b * randn(*self.b_ho.shape)

class ESN(MLP):

    ''' 
        Based on an Echo State Network (ESN)
        ------------------------------------
    '''

    W_hh = None
    z = None

    def __init__(self, D, L, H=10):
        self.D = D
        self.L = L
        self.H = H
        self.reset()
        
    def reset(self, density=1.0, scaling=0.5):
        D,H,L = self.D,self.H,self.L

        self.W_ih = randn(D,H) * scaling * (rand(D,H) <= density)
        self.W_ho = randn(H,L) * scaling * (rand(H,L) <= density)
        self.W_hh = randn(H,H) * scaling * (rand(H,H) <= density)
        self.b_ih = np.zeros(H)
        self.b_ho = np.zeros(L)
        self.f = np.tanh
        self.fo = linear

        self.z = np.zeros(H)    # nodes

        # Calculate the eigenvectors (V) of W_hh
        #V,U = eig(self.W_hh)    # sparse
        # Check that we won't be dividing by 0
        #if max(absolute(V)) <= 0.:
        #    V = V + 0.001
        # Scale the initial weights to a spectral radius of 1.
        #self.W_hh = self.W_hh / max(absolute(V))

    def predict(self,x):
        alpha = 1

        self.z = (1. - alpha) * self.z + alpha * self.f( self.W_hh.dot(self.z)  + np.dot(self.W_ih.T, x) ) # sparse
        A_xz = np.dot(x,self.W_ih) + self.b_ih
        A_zz = np.dot(self.z,self.W_hh)
        Z = self.f(A_xz + A_zz)               # non-linearity
        y = np.dot(Z,self.W_ho).T + self.b_ho
        y = self.fo(y)              # (non)-linearity

        return y

    def copy(self, modify=False):

        b = ESN(self.D,self.L,self.H)

        # Make a random adjustment to the weight matrix.
        b.W_ih = self.W_ih.copy()
        b.W_hh = self.W_hh.copy()
        b.W_ho = self.W_ho.copy()
        b.b_ih = self.b_ih.copy()
        b.b_ho = self.b_ho.copy()
        b.z = np.zeros(*b.z.shape)

        if modify:
            b.modify()

        return b

    def modify(self, alpha=0.01, alpha_b=0.01, prob_reset=0.1):

        if rand() < prob_reset:
            self.reset()

        self.W_ih = self.W_ih + alpha * randn(*self.W_ih.shape) 
        self.W_hh = self.W_hh + alpha * randn(*self.W_hh.shape) 
        self.W_ho = self.W_ho + alpha * randn(*self.W_ho.shape)
        self.b_ih = self.b_ih + alpha_b * randn(*self.b_ih.shape)
        self.b_ho = self.b_ho + alpha_b * randn(*self.b_ho.shape)
