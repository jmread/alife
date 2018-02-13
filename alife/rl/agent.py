import numpy as np
import random
import pickle
import string

class Agent():

    id_num = 0

    def __init__(self, obs_space, act_space):
        """
            Init.


            Parameters
            ----------

            The spaces that define the environment.

            obs_space : BugSpace
                observation space
            act_space : BugSpace
                action space

        """
        # Assign a random id label
        self.id_num = ''.join(random.choice(string.ascii_uppercase + string.digits) for ch in range(6))

    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return ("%s: %s" % (self.id_num,self.__class__.__name__))

    def save(self,bin_path,log_path,obj_ID):
        ''' 
            Parameters
            ----------

            bin_path : string
                a path to store, e.g., binary files which can be used to fully
                load an agent from disk.

            log_path : string
                a path to store, e.g., log files which can be used to inspect/
                visualize the agent.

            obj_ID : int
                the ID of the object that this agent controlled in the 
                environment
        '''
        fname = bin_path+'/' + str(self.id_num) + '.dat'

        pickle.dump( self, open( fname, "wb" ) )

#    def load(self,fname):
#        ''' Load an agent from a file '''
#        raise NotImplemntedError
#        return None

    def act(self,obs,reward,done=False):
        '''
            Act.

            In the style of AI gym; given 
                - an observation (of the environment currently) and 
                - a reward (obtained in the last time step)
            it returns an action (to carry out). 
        '''
        raise NotImplemntedError

    def spawn_copy(self):
        """
            Spawn.

            This function is called automatically when the agent reaches a 
            certain level of energy/fitness -- it produces a copy of the agent.

            Returns
            -------
            
            A new copy (child) of this agent, [optionally] based on this one (the parent).
        """
        raise NotImplemntedError
