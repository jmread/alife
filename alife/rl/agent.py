from numpy import *
import pickle

class Agent():

    def __init__(self, S, A):
        """
            Init.


            Parameters
            ----------

            S : BugSpace
                observation space
            A : BugSpace
                action space

        """
        self.S = S
        self.A = A

    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return str(self.__class__.__name__)

    def act(self,x,r,done=False):
        '''
            In the style of AI-GYM; returns an action, given a state and reward.
        '''
        raise NotImplemntedError

#    def load(self,file_name):
#        '''
#            Load an agent from a file
#        '''
#        raise NotImplemntedError
#        return None

    def save(self,file_name):
        '''
            Save a representation of this agent to disk.
        '''
        pickle.dump( self, open( file_name, "wb" ) )

    def spawn(self):
        """
            Spawn.

            Returns
            -------
            
            A new copy (child) of this agent, [optionally] based on this one (the parent).
        """
        raise NotImplemntedError
