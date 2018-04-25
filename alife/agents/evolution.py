from alife.agents.agent import Agent
from numpy import zeros, dot, clip, zeros, tanh, dot
from numpy.random import rand, randn, choice
import numpy as np

class Evolver(Agent):
    '''
        A Policy-Search Method.

        A very simple evolutionary method. Initially a random weight matrix, 
        this agent relies entirely on generation-to-generation evolution to 
        make any progress as a species.
    '''

    def __init__(self, obs_space, act_space, gen=1):
        """
            Init.


            Parameters
            ----------

            obs_space : BugSpace
                observation space
            act_space : BugSpace
                action space
            gen : int
                current generation

        """
        self.obs_space = obs_space
        self.act_space = act_space

        # Uniq ID (for visualization)
        self.id_num = str(choice(10000))

        # Set random weights:
        D = obs_space.shape[0]
        L = act_space.shape[0]

        density = 0.5
        self.W = randn(D,L) * (rand(D,L) >= density)     # sparse weight matrix
        self.w = randn(L) * 0.1                                 # bias

        # This is just for visualization:
        self.generation = gen            # generation
        self.log = zeros((200,D+L+1))   # for storing
        self.t = 0                       # for counting

    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return ("Evolver %s: Gen %d" % (self.id_num,self.generation))

    def act(self,obs,reward,done=False):
        """
            Act.

            Parameters
            ----------

            obs : numpy array of length D
                the state at the current time
            reward : float
                the reward signal at the current time

            Returns
            -------

            A number array of length L 
                (the action to take)
        """
        # Save some info to a log
        D = self.obs_space.shape[0]
        self.log[self.t,0:D] = obs
        self.t = (self.t + 1) % len(self.log)
        self.log[self.t,-1] = reward

        # No learning, just a simple linear reflex,
        a = dot(obs,self.W) + self.w
        # ... and clip to within the bounds of action the space.
        a[0] = clip(a[0], self.act_space.low[0], self.act_space.high[0])
        a[1] = clip(a[1], self.act_space.low[1], self.act_space.high[1])

        # More logging ...
        self.log[self.t,D:-1] = a

        # Return
        return a

    def spawn_copy(self):
        """
            Spawn.

            Returns
            -------
            
            A new copy (child) of this agent, [optionally] based on this one (the parent).
        """
        b = Evolver(self.obs_space,self.act_space,self.generation+1)

        # Make a random adjustment to the weight matrix.
        b.W = (self.W + randn(*self.W.shape) * 0.1) * (self.W > 0.0)
        b.w = b.w + randn(self.act_space.shape[0]) * 0.01
        return b

    def save(self, bin_path, log_path, obj_ID):
        """
            Save a representation of this agent.

            Here we save a .csv of the state/action/reward signals.
            (such that it could be loaded later by pandas for visualization).
        """
        D = self.obs_space.shape[0]
        L = self.act_space.shape[0]

        header = [("X%d" % j) for j in range(D)]
        header = header + [("A%d" % j) for j in range(L)]
        header.append("reward")
        print(header)
        fname = log_path+("/%d-%s.log" % (obj_ID,self.__class__.__name__))
        savetxt(fname,self.log[:,:],fmt='%4.3f',delimiter=',',header=','.join(header),comments='')
        print("Saved log to '%s'." % fname)


def linear(a):
    return a

class MLP(Evolver):

    ''' 
        A Multi-Layer Perceptron
        --------------------------------------
    '''

    W_ih = None                # weight matrix
    b_ih = None
    W_ho = None                # weight matrix
    b_ho = None

    def __init__(self, obs_space, act_space, gen=1):
        self.obs_space = obs_space
        self.act_space = act_space

        # Uniq ID (for visualization)
        self.id_num = str(choice(10000))
        self.generation = gen            # generation
        
        D = obs_space.shape[0]
        L = act_space.shape[0]

        H = 5
        density = 1.0
        scaling = 0.5

        self.W_ih = randn(D,H) * scaling * (rand(D,H) <= density)
        self.W_ho = randn(H,L) * scaling * (rand(H,L) <= density)
        self.b_ih = zeros(H)
        self.b_ho = zeros(L)
        self.f = tanh
        self.fo = linear


    def act(self,obs,reward,done=False):

        A = dot(obs,self.W_ih) + self.b_ih
        Z = self.f(A)               # non-linearity
        y = dot(Z,self.W_ho).T + self.b_ho
        y = self.fo(y)              # (non)-linearity

        return y

    def spawn_copy(self):
        """
            Spawn.
            
            A new copy (child) of this agent, [optionally] based on this one (the parent).
        """
        b = MLP(self.obs_space,self.act_space,self.generation+1)

        # Make a random adjustment to the weight matrix.
        b.W_ih = self.W_ih + 0.1 * randn(*self.W_ih.shape) 
        b.W_ho = self.W_ho + 0.1 * randn(*self.W_ho.shape)
        b.b_ih = self.b_ih + 0.01 * randn(*self.b_ih.shape)
        b.b_ho = self.b_ho + 0.01 * randn(*self.b_ho.shape)

        return b

#    def __str__(self):
#        ''' Return a string representation (e.g., a label) for this agent '''
#        return ("MLP %s: G%d" % (self.id_num,self.generation))

    def save(self, bin_path, log_path, obj_ID):
        print("Save: Not yet implemented!")
        return

class ESN(MLP):

    ''' 
        Based on an Echo State Network (ESN)
        ------------------------------------
    '''

    W_hh = None
    z = None

    def __init__(self, obs_space, act_space, gen=1):
        self.obs_space = obs_space
        self.act_space = act_space

        # Uniq ID (for visualization)
        self.id_num = str(choice(10000))
        self.generation = gen            # generation
        
        D = obs_space.shape[0]
        L = act_space.shape[0]

        # H: hidden units - sholud be as large as suitable for memory
        H = 5
        # density: high sparsity (i.e., density = 0.01) is recommended for large matrices
        density = 1.
        # Leaking rate (set to 1. for dynamical tasks)
        # scaling: keep small for linear tasks, where it hovers around the linear part of the sigmoid/tanh.
        scaling = 0.5

        self.W_ih = randn(D,H) * scaling * (rand(D,H) <= density)
        self.W_ho = randn(H,L) * scaling * (rand(H,L) <= density)
        self.W_hh = randn(H,H) * scaling * (rand(H,H) <= density)
        self.b_ih = zeros(H)
        self.b_ho = zeros(L)
        self.f = tanh
        self.fo = linear

        # Generate nodes
        self.z = zeros(H)    # nodes

        # Calculate the eigenvectors (V) of W_hh
        #V,U = eig(self.W_hh)    # sparse
        # Check that we won't be dividing by 0
        #if max(absolute(V)) <= 0.:
        #    V = V + 0.001
        # Scale the initial weights to a spectral radius of 1.
        #self.W_hh = self.W_hh / max(absolute(V))

        self.f = tanh
        self.fo = linear

    def act(self,obs,reward,done=False):
        alpha = 1

        x = obs
        self.z = (1. - alpha) * self.z + alpha * self.f( self.W_hh.dot(self.z)  + dot(self.W_ih.T, x) ) # sparse
        A_xz = dot(obs,self.W_ih) + self.b_ih
        A_zz = dot(self.z,self.W_hh)
        Z = self.f(A_xz + A_zz)               # non-linearity
        y = dot(Z,self.W_ho).T + self.b_ho
        y = self.fo(y)              # (non)-linearity

        return y

    def spawn_copy(self):
        """
            Spawn.
            
            A new copy (child) of this agent, [optionally] based on this one (the parent).
        """
        b = ESN(self.obs_space,self.act_space,self.generation+1)

        # Make a random adjustment to the weight matrix.
        b.W_ih = self.W_ih + 0.1 * randn(*self.W_ih.shape) 
        b.W_hh = self.W_hh + 0.1 * randn(*self.W_hh.shape) 
        b.W_ho = self.W_ho + 0.1 * randn(*self.W_ho.shape)
        b.b_ih = self.b_ih + 0.01 * randn(*self.b_ih.shape)
        b.b_ho = self.b_ho + 0.01 * randn(*self.b_ho.shape)

        return b

    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return ("ESN %s: G%d" % (self.id_num,self.generation))

    def save(self, bin_path, log_path, obj_ID):
        print("Save: Not yet implemented!")
        return

