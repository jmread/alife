from alife.agents.agent import Agent
from numpy import zeros, dot, clip, zeros, tanh, dot
from numpy.random import rand, randn, choice
from alife.agents.models import SLP, MLP, ESN
import numpy as np


class SimpleEvolver(Agent):
    '''
        A simple agent based on some (specified) kind of neural network.

        Initially a random weight matrix, and thenceforth a random mutation 
        ('copy') of a parent agent, an evolution strategy is handled implicitly 
        by the environment: poor quality agents will simply not survive long 
        enough to be able to copy themselves; and thus are extinguished. 

        Thus, this agent relies entirely on generation-to-generation evolution 
        to make any progress.
    '''

    def __init__(self, obs_space, act_space, H=0, **kwargs):
        """
            Init.

            Parameters
            ----------

            obs_space : BugSpace
                observation space
            act_space : BugSpace
                action space
            H : int
                number of hidden units (negative for recurrent)

        """
        self.obs_space = obs_space
        self.act_space = act_space

        D = obs_space.shape[0]
        L = act_space.shape[0]

        if 'H' in kwargs:
            H = kwargs['H']

        if H > 0:
            self.h = MLP(D,L,H)
        elif H < 0:
            self.h = ESN(D,L,-H)
        else:
            self.h = SLP(D,L)

        # Uniq ID (for visualization)
        self.id_num = str(choice(1000))+':'
        self.generation = 1

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
        return self.h.predict(obs)

    def copy(self):
        """
            Copy.
            
            A new copy (child) of this agent, [optionally] based on this one (the parent).
        """

        new = SimpleEvolver(self.obs_space,self.act_space)
        new.generation = self.generation+1
        new.id_num = self.id_num + str(choice(10))
        new.h = self.h.copy(modify=True)

        return new

    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return ("%s %s: G%d" % (str(self.h.__class__.__name__), self.id_num,self.generation))

#    def load(self, file_name):
#        self.generation = 0 # TODO extract from filename
#        self.h = None # TODO unpickle

    def save(self, bin_path, log_path):
        # TODO pickle self.h to ~/bin_path/:module:self.__class__.__name__:self.generation.dat
        print("Save: Not yet implemented!")
        return


